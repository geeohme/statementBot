# Explaining bill changes

When the customer asks "why did my bill change?" or "why is it higher this month?", follow this process:

## 1. Identify the comparison

- Default to **most recent bill vs the one before it** unless the customer specifies otherwise.
- State the comparison clearly: "Comparing your **May 2026** bill ($X) to your **April 2026** bill ($Y), your bill went up by **+$Z**."

## 2. Walk the bill top-to-bottom

Compare the two statements section by section in this order, and only mention sections that actually changed:

1. **Previous balance / Payments / Balance forward** — did a payment not post? Is there a past-due amount?
2. **My BrightWave plan** — Internet, TV, Voice prices and discounts.
3. **Streamstore** — added/removed apps, or rate changes.
4. **Add ons** — DVR, channel packs, fees.
5. **Equipment & services** — new boxes, returned boxes.
6. **Taxes, fees and other charges** — usually scale with regular charges.

## 3. Surface the drivers in a table

For any non-trivial change, show a "what changed" markdown table (see response-standards.md).

## Common change patterns

### Promotional discount expired
Most common driver of bill jumps. Example: the **3 Product Discount** ends, and a -$40.00 monthly credit goes away. The bill goes up by $40 plus a small bump in taxes (because taxes scale with regular charges).

### Introductory rate ended
A new-customer rate on a service line (commonly Internet) is built into the price. When it ends, the price jumps back to the standard rate. Example: Internet $95 → $120 = **+$25.00** jump on a single line.

### Multiple promos expired in the same cycle
Most painful for customers — explain *each* expired promo separately, show subtotals, and finish with the combined impact.

### Plan change / proration mid-cycle
If a customer changed plans partway through a billing period, the statement will show partial charges and partial credits for both the old and new plans. Walk them through both halves and reconcile to the net charge.

### Service added or removed (LOB change)
- **Added:** a partial charge for the new service from the change date through the end of the period, plus any setup fee. If it was added to a bundle, the bundle discount may also change.
- **Removed:** a credit for the unused portion of the removed service, and any bundle discount tied to that service is also removed.

### Equipment changes
- **Box added:** monthly equipment charge starts; a partial-month charge may apply.
- **Box returned:** monthly charge stops; a partial-month credit may apply. Unreturned equipment can result in a non-return fee on a later statement.

### Late fee
Triggered when the prior balance wasn't paid by the due date. Usually a flat dollar amount on the next bill. Today's account doesn't carry one — if you see one, explain when it was assessed and what would prevent it next time.

### Balance forward / negative balance
- **Balance forward > $0:** the prior bill wasn't fully paid; that amount carries over and is added to the new charges.
- **Negative balance (credit):** the prior bill was overpaid, a refund was issued, or a credit was applied. It reduces the amount due this month.

### Loyalty credit ended
Tenure-based credits run for a stated duration. When they end, the bill goes up by the credit amount. Don't speculate about *why* the credit was originally granted — just explain that it expired.

### Bundle promo loss (e.g., mobile cancellation)
If a customer cancelled a service that anchored a bundle discount (mobile, for instance), the bundle credit goes away on the next statement. (Not applicable to today's account — flagged here so you can answer hypotheticals correctly.)

### Disconnection / final bill
Final bills can include partial-month charges for any service period before the disconnect date, prorated credits, and any unreturned-equipment fees. (Not applicable to today's account.)
