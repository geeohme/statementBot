"""
BrightWave Cable — Statement XML generator
==========================================

Generates 6 sequential monthly statements for a single demo account.
- Months 1-5: normal recurring charges (with active promos)
- Month 6:    "3 Product Discount" expires AND "Internet Introductory Rate" expires
              => total bill jumps by ~$68 / ~21%

Math is driven entirely by line items — section totals and bill totals are
computed, never hard-coded, so the output always reconciles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from xml.dom import minidom


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def D(value) -> Decimal:
    """Decimal with 2-place rounding for currency."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def prettify(elem: ET.Element) -> str:
    rough = ET.tostring(elem, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class LineItem:
    name: str
    amount: Decimal
    note: str | None = None  # e.g. "Qty 2 @ $14.00 each"


@dataclass
class Service:
    """A top-level service inside the 'My BrightWave plan' section."""
    name: str            # "Internet" / "TV" / "Voice"
    tier: str            # "1 Gig" / "Ultimate TV" / "BrightWave Voice"
    price: Decimal
    line_items: list[LineItem] = field(default_factory=list)
    included: list[str] = field(default_factory=list)
    base_discount: Decimal = Decimal("0.00")
    base_discount_label: str | None = None
    base_discount_end: str | None = None
    description: str | None = None


@dataclass
class Section:
    name: str
    line_items: list[LineItem] = field(default_factory=list)
    discount: Decimal = Decimal("0.00")
    discount_label: str | None = None
    services: list[Service] = field(default_factory=list)  # only used for "My BrightWave plan"

    @property
    def total(self) -> Decimal:
        if self.services:
            services_total = sum((s.price for s in self.services), Decimal("0.00"))
            return D(services_total + self.discount)
        return D(sum((li.amount for li in self.line_items), Decimal("0.00")) + self.discount)


@dataclass
class TaxLine:
    name: str
    amount: Decimal


@dataclass
class TaxCategory:
    name: str
    items: list[TaxLine]

    @property
    def total(self) -> Decimal:
        return D(sum((li.amount for li in self.items), Decimal("0.00")))


# ---------------------------------------------------------------------------
# Static account data
# ---------------------------------------------------------------------------

ACCOUNT = {
    "number": "458529",
    "customer_name": "Lawrence O'Donnell",
    "member_since": "2013-05-16",
    "service_address": {
        "line1": "425 W 53rd St",
        "line2": "Apt 7B",
        "city": "New York",
        "state": "NY",
        "zip": "10019",
    },
    "mailing_address": {
        "line1": "425 W 53rd St",
        "line2": "Apt 7B",
        "city": "New York",
        "state": "NY",
        "zip": "10019",
    },
    "voice_number": "(212) 555-0142",
    "payment_method": "Automatic Payment (EFT)",
    "remit_to": {
        "name": "BrightWave Cable",
        "po_box": "PO Box 6480",
        "city": "New York",
        "state": "NY",
        "zip": "10101-6480",
    },
}


# ---------------------------------------------------------------------------
# Cycle definitions
# ---------------------------------------------------------------------------

@dataclass
class Cycle:
    seq: int                    # 1..6
    bill_date: date
    service_start: date
    service_end: date
    due_date: date
    prior_payment_date: date    # when previous month's EFT cleared


CYCLES: list[Cycle] = [
    Cycle(1, date(2025, 12,  3), date(2025, 12, 16), date(2026, 1, 15), date(2025, 12, 24), date(2025, 11, 25)),
    Cycle(2, date(2026,  1,  3), date(2026,  1, 16), date(2026, 2, 15), date(2026,  1, 24), date(2025, 12, 25)),
    Cycle(3, date(2026,  2,  3), date(2026,  2, 14), date(2026, 3, 15), date(2026,  2, 24), date(2026,  1, 25)),
    Cycle(4, date(2026,  3,  3), date(2026,  3, 16), date(2026, 4, 15), date(2026,  3, 24), date(2026,  2, 25)),
    Cycle(5, date(2026,  4,  3), date(2026,  4, 16), date(2026, 5, 15), date(2026,  4, 24), date(2026,  3, 25)),
    Cycle(6, date(2026,  5,  3), date(2026,  5, 16), date(2026, 6, 15), date(2026,  5, 24), date(2026,  4, 25)),
]


# ---------------------------------------------------------------------------
# Build the charges sections for a given cycle
# ---------------------------------------------------------------------------

def build_sections(cycle: Cycle) -> tuple[list[Section], dict]:
    """
    Returns (sections, meta). meta carries any flags used downstream
    (e.g., whether promos expired this cycle).
    """
    is_promo_loss = cycle.seq == 6

    # ----- "My BrightWave plan" -----
    # Internet: $95 normally (includes the $15 60-mo Guarantee).
    # When intro promo expires (cycle 6), price jumps to $120 (still incl. Guarantee).
    internet_price = D("120.00") if is_promo_loss else D("95.00")
    internet = Service(
        name="Internet",
        tier="1 Gig",
        price=internet_price,
        included=["Unlimited Data Option", "BrightWave WiFi Gateway"],
        base_discount=D("-15.00"),
        base_discount_label="60-month $15.00 Guarantee Discount",
        base_discount_end="2030-10-15",
    )

    tv = Service(
        name="TV",
        tier="Ultimate TV",
        price=D("131.95"),
        description=(
            "Includes Limited Basic, Sports & News, Kids & Family, "
            "Entertainment, 50+ Additional Channels, Streampix, "
            "HD Programming, and 20 Hours of DVR Service."
        ),
        line_items=[
            LineItem("Ultimate TV", D("90.50")),
            LineItem("Broadcast TV Fee", D("34.85")),
            LineItem("Regional Sports Fee", D("6.60")),
        ],
    )

    voice = Service(
        name="Voice",
        tier="BrightWave Voice",
        price=D("30.00"),
        description=(
            "Unlimited Local and Long Distance Calls. International "
            "Calling Included To Several Countries With Others "
            "Available At An Additional Charge."
        ),
    )

    # 3 Product Discount: $40 normally; gone in cycle 6.
    plan_discount = D("0.00") if is_promo_loss else D("-40.00")
    plan_section = Section(
        name="My BrightWave plan",
        services=[internet, tv, voice],
        discount=plan_discount,
        discount_label="3 Product Discount" if not is_promo_loss else "3 Product Discount (EXPIRED)",
    )

    # ----- Streamstore -----
    streamstore = Section(
        name="Streamstore",
        line_items=[
            LineItem("HBO Max", D("18.49")),
            LineItem("Peacock Premium", D("10.99")),
            LineItem("Apple TV+", D("6.50")),
        ],
    )

    # ----- Add ons -----
    addons = Section(
        name="Add ons",
        line_items=[
            LineItem("DVR Service", D("10.00")),
            LineItem("Premium Channel Pack", D("13.49")),
            LineItem("HD Technology Fee", D("5.00")),
        ],
    )

    # ----- Equipment & services -----
    equipment = Section(
        name="Equipment & services",
        line_items=[
            LineItem("TV Box + Remote", D("28.00"), note="Qty 2 @ $14.00 each"),
        ],
    )

    sections = [plan_section, streamstore, addons, equipment]

    meta = {
        "is_promo_loss": is_promo_loss,
        "promo_loss_detail": [
            "3 Product Discount expired",
            "Internet 12-month Introductory Rate expired (Internet $95 → $120)",
        ] if is_promo_loss else [],
    }
    return sections, meta


def build_taxes(regular_total: Decimal) -> list[TaxCategory]:
    """
    Taxes scale roughly with regular charges so the math 'feels right'.
    We model fixed dollar amounts for tiny fees and scaled percents for taxes,
    then nudge the last item to hit a clean total.
    """
    # Fixed federal/regulatory fees
    other = TaxCategory(
        name="Other charges",
        items=[
            TaxLine("Federal Universal Service Fund", D("0.74")),
            TaxLine("Regulatory Cost Recovery", D("1.14")),
        ],
    )

    # Government taxes — scale Sales/Excise; keep flat fees flat.
    # Target rate of ~4.46% on regular charges (matches sample).
    scale = regular_total / D("309.42")
    sales_tax       = D(D("1.60") * scale)
    state_excise    = D(D("5.29") * scale)
    franchise_fee   = D(D("3.50") * scale)
    fee_911         = D("1.52")  # flat 911 fee doesn't scale

    govt = TaxCategory(
        name="Taxes & government fees",
        items=[
            TaxLine("Sales Tax", sales_tax),
            TaxLine("State Excise Tax", state_excise),
            TaxLine("Franchise Fee", franchise_fee),
            TaxLine("911 Fee", fee_911),
        ],
    )
    return [other, govt]


# ---------------------------------------------------------------------------
# XML emission
# ---------------------------------------------------------------------------

def section_to_xml(section: Section, parent: ET.Element) -> None:
    sec_el = ET.SubElement(parent, "section", {
        "name": section.name,
        "total": money(section.total),
    })

    if section.services:
        for svc in section.services:
            svc_el = ET.SubElement(sec_el, "service", {
                "name": svc.name,
                "tier": svc.tier,
                "price": money(svc.price),
            })
            if svc.description:
                ET.SubElement(svc_el, "description").text = svc.description
            if svc.base_discount_label:
                ET.SubElement(svc_el, "discount", {
                    "label": svc.base_discount_label,
                    "amount": money(svc.base_discount),
                    "endDate": svc.base_discount_end or "",
                    "appliedToBase": "true",
                })
            for inc in svc.included:
                ET.SubElement(svc_el, "included").text = inc
            for li in svc.line_items:
                ET.SubElement(svc_el, "lineItem", {
                    "name": li.name,
                    "amount": money(li.amount),
                })

    for li in section.line_items:
        attrs = {"name": li.name, "amount": money(li.amount)}
        if li.note:
            attrs["note"] = li.note
        ET.SubElement(sec_el, "lineItem", attrs)

    if section.discount != Decimal("0.00") or section.discount_label:
        ET.SubElement(sec_el, "discount", {
            "label": section.discount_label or "Discount",
            "amount": money(section.discount),
        })


def build_statement_xml(cycle: Cycle, prior_amount_due: Decimal) -> tuple[ET.Element, dict]:
    sections, meta = build_sections(cycle)
    regular_total = D(sum((s.total for s in sections), Decimal("0.00")))
    tax_categories = build_taxes(regular_total)
    taxes_total = D(sum((c.total for c in tax_categories), Decimal("0.00")))
    new_charges = D(regular_total + taxes_total)

    # Previous balance / payment / balance forward
    previous_balance = prior_amount_due
    payment = -previous_balance     # EFT clears it
    balance_forward = D(previous_balance + payment)  # 0.00
    amount_due = D(balance_forward + new_charges)

    # Savings line ("You saved $X this month")
    plan_disc = abs(sections[0].discount)
    internet_guarantee = D("15.00")  # always on
    savings = D(plan_disc + internet_guarantee)

    # ---- root
    root = ET.Element("statement")

    meta_el = ET.SubElement(root, "meta")
    ET.SubElement(meta_el, "accountNumber").text = ACCOUNT["number"]
    ET.SubElement(meta_el, "billDate").text = cycle.bill_date.isoformat()
    ET.SubElement(meta_el, "servicePeriod", {
        "start": cycle.service_start.isoformat(),
        "end": cycle.service_end.isoformat(),
        "days": str((cycle.service_end - cycle.service_start).days + 1),
    })
    ET.SubElement(meta_el, "dueDate").text = cycle.due_date.isoformat()
    ET.SubElement(meta_el, "statementSeq").text = str(cycle.seq)
    if meta["is_promo_loss"]:
        promo_el = ET.SubElement(meta_el, "promoExpirations")
        for detail in meta["promo_loss_detail"]:
            ET.SubElement(promo_el, "expiration").text = detail

    # customer
    cust_el = ET.SubElement(root, "customer")
    ET.SubElement(cust_el, "name").text = ACCOUNT["customer_name"]
    ET.SubElement(cust_el, "memberSince").text = ACCOUNT["member_since"]
    ET.SubElement(cust_el, "voiceNumber").text = ACCOUNT["voice_number"]

    for tag, src in (("serviceAddress", ACCOUNT["service_address"]),
                     ("mailingAddress", ACCOUNT["mailing_address"])):
        addr_el = ET.SubElement(cust_el, tag)
        ET.SubElement(addr_el, "line1").text = src["line1"]
        ET.SubElement(addr_el, "line2").text = src["line2"]
        ET.SubElement(addr_el, "city").text = src["city"]
        ET.SubElement(addr_el, "state").text = src["state"]
        ET.SubElement(addr_el, "zip").text = src["zip"]

    # bill at a glance
    glance = ET.SubElement(root, "billAtAGlance")
    ET.SubElement(glance, "previousBalance").text = money(previous_balance)
    payments_el = ET.SubElement(glance, "payments")
    if cycle.seq > 1:  # only show payment if there was a prior balance
        ET.SubElement(payments_el, "payment", {
            "date": cycle.prior_payment_date.isoformat(),
            "method": "EFT",
            "label": "EFT Payment - thank you",
        }).text = money(payment)
    ET.SubElement(glance, "balanceForward").text = money(balance_forward)
    ET.SubElement(glance, "regularMonthlyCharges").text = money(regular_total)
    ET.SubElement(glance, "taxesFeesOther").text = money(taxes_total)
    ET.SubElement(glance, "newCharges").text = money(new_charges)
    ET.SubElement(glance, "amountDue").text = money(amount_due)
    ET.SubElement(glance, "savingsThisMonth").text = money(savings)

    # remit
    remit_el = ET.SubElement(root, "remitTo")
    for k, v in ACCOUNT["remit_to"].items():
        ET.SubElement(remit_el, k).text = v

    # charges
    charges_el = ET.SubElement(root, "charges", {"total": money(regular_total)})
    for sec in sections:
        section_to_xml(sec, charges_el)

    # taxes & fees
    taxes_el = ET.SubElement(root, "taxesFees", {"total": money(taxes_total)})
    for cat in tax_categories:
        cat_el = ET.SubElement(taxes_el, "category", {
            "name": cat.name,
            "total": money(cat.total),
        })
        for li in cat.items:
            ET.SubElement(cat_el, "taxLine", {
                "name": li.name,
                "amount": money(li.amount),
            })

    summary = {
        "seq": cycle.seq,
        "bill_date": cycle.bill_date.isoformat(),
        "service_period": f"{cycle.service_start.isoformat()} → {cycle.service_end.isoformat()}",
        "days": (cycle.service_end - cycle.service_start).days + 1,
        "regular": regular_total,
        "taxes": taxes_total,
        "new_charges": new_charges,
        "amount_due": amount_due,
        "savings": savings,
    }
    return root, summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    out_dir = Path(__file__).parent / "statements"
    out_dir.mkdir(exist_ok=True)

    # Seed prior balance for cycle 1.
    # We pick a value that matches what cycles 1-5 will produce so the running
    # bill cycle is consistent (previous balance = last cycle's new charges).
    # We'll compute it by building a "ghost" cycle 0 with the same rules.
    ghost_cycle = Cycle(0, date(2025, 11, 3), date(2025, 11, 16), date(2025, 12, 15),
                        date(2025, 11, 24), date(2025, 10, 25))
    _, ghost_summary = build_statement_xml(ghost_cycle, prior_amount_due=Decimal("0.00"))
    prior_due = ghost_summary["new_charges"]

    print(f"{'#':>2} {'Bill date':10} {'Service period':25} {'Days':>4} "
          f"{'Regular':>10} {'Taxes':>8} {'Total':>10} {'Savings':>9}")
    print("-" * 92)

    for cycle in CYCLES:
        root, summary = build_statement_xml(cycle, prior_due)
        path = out_dir / f"statement_{cycle.seq:03d}_{cycle.bill_date:%Y-%m}.xml"
        path.write_text(prettify(root), encoding="utf-8")
        print(f"{summary['seq']:>2} {summary['bill_date']} "
              f"{summary['service_period']:25} {summary['days']:>4} "
              f"${money(summary['regular']):>9} ${money(summary['taxes']):>7} "
              f"${money(summary['amount_due']):>9} ${money(summary['savings']):>8}")
        prior_due = summary["new_charges"]


if __name__ == "__main__":
    main()
