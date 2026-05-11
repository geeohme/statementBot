# BrightWave bill structure

Every BrightWave monthly statement has the same anatomy. Use these names when referring to parts of the bill — they match what the customer sees on the printed PDF.

## Page 1 — Summary

- **Account header** — Account number, billing date, service period ("Services From … to …"), page number.
- **"Hello {first name}"** greeting.
- **Your bill at a glance** — the running balance: previous balance, payment(s) applied, balance forward, regular monthly charges, taxes/fees, **new charges**, and **amount due**.
- **Your bill explained** — a callout box explaining anything notable this month (savings, promo expirations, etc.).
- **Autopay note** — if enabled, says when the automatic payment will run.
- **Remit stub** at the bottom (account number, due date, amount due, mailing address).

## Page 2 — Detail

- **Regular monthly charges** — broken into four sections:
  1. **My BrightWave plan** — recurring service charges (Internet, TV, Voice) with sub-line items and applicable discounts.
  2. **Streamstore** — third-party streaming apps billed through BrightWave (HBO Max, Peacock, Apple TV+, etc.).
  3. **Add ons** — extras (DVR Service, Premium Channel Pack, HD Technology Fee).
  4. **Equipment & services** — leased hardware (TV Box + Remote, etc.).
- **Taxes, fees and other charges**:
  - **Other charges** — regulatory pass-throughs (Federal Universal Service Fund, Regulatory Cost Recovery).
  - **Taxes & government fees** — Sales Tax, State Excise Tax, Franchise Fee, 911 Fee.
- **What's included** sidebar — recap of what the customer is subscribed to.

## How charges combine

```
My BrightWave plan total
   = (Internet price + TV price + Voice price)  −  plan-level discounts
Streamstore total = sum of streaming line items
Add ons total = sum of add-on line items
Equipment total = sum of equipment line items

Regular monthly charges = sum of the four section totals

Taxes total = "Other charges" + "Taxes & government fees"

New charges  = Regular monthly charges + Taxes total
Amount due   = Balance forward + New charges
```

Every number on the bill is derivable from the JSON in your context — never invent one.

## Discount semantics

- **Guarantee Discount** — a long-running price-lock built into the service price (the Internet line shows the post-discount price already; the discount label is informational).
- **3 Product Discount** — a bundle credit applied for keeping all three lines (Internet + TV + Voice). Subtracted from the plan subtotal.
- **Introductory Rate** — a 12-month new-customer rate baked into a service price. When it ends, the underlying price jumps back to the "normal" rate.
- **Loyalty Credit** — a tenure-based credit (none on this account currently, but if a customer asks, this is what they mean).
- **Promo expirations** show up in the statement's `meta.promoExpirations` field — flag those proactively when explaining a bill that has them.
