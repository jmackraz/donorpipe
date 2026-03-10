# DonorPipe Help

DonorPipe reconciles donation data from multiple online giving platforms (Stripe, DonorBox, PayPal)
against QuickBooks Online receipts, helping you find missing donations, data discrepancies, and
duplicate receipts.

---

## Getting Started

After logging in, select your account from the header. DonorPipe will load all donation, payout,
and receipt data for that account.

Use the **tabs** (Donations / Receipts / Payouts) to switch between entity types, and the
**filter bar** to narrow results by date range, amount, service, or donor name.

**Keyboard shortcuts:**
- `1` — Donations tab, `2` — Receipts tab, `3` — Payouts tab
- `/` — Focus the donor search field
- `n` / `p` — Step forward / backward by one date period
- `c` — Clear all filters
- `?` — Open this help panel

---

## Reconciling with Bank Deposits

*(More detail to be added here.)*

When a payout from Stripe or PayPal lands in your bank account, you can verify it in DonorPipe:

1. Switch to the **Payouts** tab.
2. Filter by date to find the payout period matching your bank deposit.
3. Click a payout to open the detail panel, which shows the charges and donations included in
   that payout.
4. Confirm the total matches your bank statement.

---

## Adding New Online Donations

*(More detail to be added here.)*

When new donation data has been exported from your giving platforms and loaded into DonorPipe:

1. Switch to the **Donations** tab.
2. Set the date filter to the relevant period.
3. Review incoming donations by service.

---

## Viewing and Fixing Errors in Receipts

Switch to the **Receipts** tab and use the error toggle filters in the filter bar to surface
specific issues.

### Missing Donations

The **Missing** filter shows receipts that have no matching donation in the system. This may mean:

- The donation was processed through a channel not yet imported.
- The donation amount or date in QBO does not match any imported donation.

*(Steps for resolution to be added here.)*

### Data Discrepancies

The **Discrepancies** filter shows receipts where key fields (amount, date, donor name) do not
match the linked donation record.

*(Steps for resolution to be added here.)*

### Duplicate Receipts

The **Duplicates** filter shows receipts that appear to be duplicates of another receipt for the
same donation.

*(Steps for resolution to be added here.)*
