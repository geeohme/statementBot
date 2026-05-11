"""
BrightWave PDF Renderer
=======================
Flask service that loads the generated XML statements at startup and renders
them on-the-fly to PDF using WeasyPrint.

Endpoints
---------
GET  /health                    - liveness probe
GET  /statements                - list of statements (JSON, summary only)
GET  /statements/<seq>          - raw XML
GET  /statements/<seq>/pdf      - rendered PDF
GET  /statements/<seq>/json     - parsed statement (for chatbot context)
"""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from flask import Flask, Response, abort, jsonify, send_from_directory
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML


BASE_DIR = Path(__file__).resolve().parent
STATEMENTS_DIR = Path(os.environ.get(
    "STATEMENTS_DIR",
    BASE_DIR.parent / "statements",
)).resolve()
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")


# ---------------------------------------------------------------------------
# XML → dict
# ---------------------------------------------------------------------------

def _money(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)


def _parse_statement(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()

    # meta
    meta_el = root.find("meta")
    sp = meta_el.find("servicePeriod")
    promos = [e.text for e in meta_el.findall("promoExpirations/expiration")]
    meta = {
        "accountNumber": meta_el.findtext("accountNumber"),
        "billDate": meta_el.findtext("billDate"),
        "servicePeriodStart": sp.get("start"),
        "servicePeriodEnd": sp.get("end"),
        "servicePeriodDays": int(sp.get("days")),
        "dueDate": meta_el.findtext("dueDate"),
        "statementSeq": int(meta_el.findtext("statementSeq")),
        "promoExpirations": promos,
    }

    # customer
    cust_el = root.find("customer")
    def addr(tag):
        a = cust_el.find(tag)
        return {
            "line1": a.findtext("line1"),
            "line2": a.findtext("line2"),
            "city": a.findtext("city"),
            "state": a.findtext("state"),
            "zip": a.findtext("zip"),
        }
    full_name = cust_el.findtext("name")
    customer = {
        "name": full_name,
        "firstName": full_name.split()[0],
        "memberSince": cust_el.findtext("memberSince"),
        "voiceNumber": cust_el.findtext("voiceNumber"),
        "serviceAddress": addr("serviceAddress"),
        "mailingAddress": addr("mailingAddress"),
    }

    # glance
    glance_el = root.find("billAtAGlance")
    payments = []
    for p in glance_el.findall("payments/payment"):
        payments.append({
            "date": p.get("date"),
            "method": p.get("method"),
            "label": p.get("label"),
            "amount": _money(p.text),
        })
    glance = {
        "previousBalance": _money(glance_el.findtext("previousBalance")),
        "payments": payments,
        "balanceForward": _money(glance_el.findtext("balanceForward")),
        "regularMonthlyCharges": _money(glance_el.findtext("regularMonthlyCharges")),
        "taxesFeesOther": _money(glance_el.findtext("taxesFeesOther")),
        "newCharges": _money(glance_el.findtext("newCharges")),
        "amountDue": _money(glance_el.findtext("amountDue")),
        "savingsThisMonth": _money(glance_el.findtext("savingsThisMonth")),
    }

    # remit
    remit_el = root.find("remitTo")
    remit = {
        "name": remit_el.findtext("name"),
        "po_box": remit_el.findtext("po_box"),
        "city": remit_el.findtext("city"),
        "state": remit_el.findtext("state"),
        "zip": remit_el.findtext("zip"),
    }

    # charges
    charges_el = root.find("charges")
    sections = []
    for sec in charges_el.findall("section"):
        # service-level (only "My BrightWave plan")
        services = []
        for svc in sec.findall("service"):
            disc = []
            for d in svc.findall("discount"):
                disc.append({
                    "label": d.get("label"),
                    "amount": _money(d.get("amount")),
                    "endDate": d.get("endDate") or None,
                })
            included = [e.text for e in svc.findall("included")]
            line_items = [
                {"name": li.get("name"), "amount": _money(li.get("amount"))}
                for li in svc.findall("lineItem")
            ]
            description = svc.findtext("description")
            services.append({
                "name": svc.get("name"),
                "tier": svc.get("tier"),
                "price": _money(svc.get("price")),
                "discounts": disc,
                "included": included,
                "lineItems": line_items,
                "description": description,
            })

        # plain line items (for non-service sections)
        line_items = [
            {
                "name": li.get("name"),
                "amount": _money(li.get("amount")),
                "note": li.get("note"),
            }
            for li in sec.findall("lineItem")
        ]

        # section-level discount
        disc_el = sec.find("discount")
        section_discount = Decimal("0.00")
        section_discount_label = None
        if disc_el is not None:
            section_discount = _money(disc_el.get("amount"))
            section_discount_label = disc_el.get("label")

        services_subtotal = sum((s["price"] for s in services), Decimal("0.00")) if services else None

        sections.append({
            "name": sec.get("name"),
            "total": _money(sec.get("total")),
            "services": services,
            "servicesSubtotal": services_subtotal,
            "lineItems": line_items,
            "discount": section_discount,
            "discountLabel": section_discount_label,
        })

    charges = {
        "total": _money(charges_el.get("total")),
        "sections": sections,
    }

    # taxes
    taxes_el = root.find("taxesFees")
    cats = []
    for cat in taxes_el.findall("category"):
        lines = [
            {"name": li.get("name"), "amount": _money(li.get("amount"))}
            for li in cat.findall("taxLine")
        ]
        cats.append({
            "name": cat.get("name"),
            "total": _money(cat.get("total")),
            "lines": lines,
        })
    taxes = {
        "total": _money(taxes_el.get("total")),
        "categories": cats,
    }

    return {
        "meta": meta,
        "customer": customer,
        "glance": glance,
        "remitTo": remit,
        "charges": charges,
        "taxes": taxes,
    }


# ---------------------------------------------------------------------------
# Load statements at startup
# ---------------------------------------------------------------------------

def _load_all_statements() -> dict[int, dict]:
    out: dict[int, dict] = {}
    for path in sorted(STATEMENTS_DIR.glob("statement_*.xml")):
        data = _parse_statement(path)
        seq = data["meta"]["statementSeq"]
        data["_path"] = str(path)
        out[seq] = data
    # link prior amounts (for the "what changed" diff)
    prev = None
    for seq in sorted(out):
        out[seq]["previousAmount"] = prev["glance"]["amountDue"] if prev else None
        prev = out[seq]
    return out


STATEMENTS: dict[int, dict] = _load_all_statements()


# ---------------------------------------------------------------------------
# Jinja env + filters
# ---------------------------------------------------------------------------

jenv = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

_MONTHS_LONG = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _longdate(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%b %d, %Y")


def _shortdate(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%b %d")


def _money_filter(value) -> str:
    if value is None:
        return "0.00"
    return f"{Decimal(value):.2f}"


jenv.filters["longdate"] = _longdate
jenv.filters["shortdate"] = _shortdate
jenv.filters["money"] = _money_filter
jenv.filters["upper"] = lambda s: (s or "").upper()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok", "statements": len(STATEMENTS)})


@app.route("/statements")
def list_statements():
    out = []
    for seq in sorted(STATEMENTS):
        s = STATEMENTS[seq]
        out.append({
            "seq": seq,
            "billDate": s["meta"]["billDate"],
            "servicePeriodStart": s["meta"]["servicePeriodStart"],
            "servicePeriodEnd": s["meta"]["servicePeriodEnd"],
            "amountDue": str(s["glance"]["amountDue"]),
            "promoExpirations": s["meta"]["promoExpirations"],
        })
    return jsonify(out)


@app.route("/statements/<int:seq>")
def get_xml(seq: int):
    if seq not in STATEMENTS:
        abort(404)
    path = STATEMENTS[seq]["_path"]
    return Response(Path(path).read_text(encoding="utf-8"), mimetype="application/xml")


@app.route("/statements/<int:seq>/json")
def get_json(seq: int):
    if seq not in STATEMENTS:
        abort(404)
    s = STATEMENTS[seq]
    return Response(
        _json_dumps(s),
        mimetype="application/json",
    )


@app.route("/statements/<int:seq>/pdf")
def get_pdf(seq: int):
    if seq not in STATEMENTS:
        abort(404)
    stmt = STATEMENTS[seq]
    template = jenv.get_template("statement.html")
    html_str = template.render(
        stmt=stmt,
        logo_url=str(STATIC_DIR / "logo.svg"),
        css_url=str(STATIC_DIR / "styles.css"),
    )
    pdf_bytes = HTML(string=html_str, base_url=str(BASE_DIR)).write_pdf(
        stylesheets=[CSS(filename=str(STATIC_DIR / "styles.css"))]
    )
    return Response(pdf_bytes, mimetype="application/pdf")


# ---------------------------------------------------------------------------
# JSON encoder helper
# ---------------------------------------------------------------------------

import json


def _default(o):
    if isinstance(o, Decimal):
        return str(o)
    raise TypeError(f"Unserializable: {type(o)}")


def _json_dumps(obj) -> str:
    # drop internal keys
    cleaned = {k: v for k, v in obj.items() if not k.startswith("_")}
    return json.dumps(cleaned, default=_default, indent=2)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
