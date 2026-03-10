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
- `f` — Toggle the filter panel open/closed
- `/` — Focus the donor search field (opens filter panel if collapsed)
- `n` / `p` — Step forward / backward by one date period
- `c` — Clear all filters
- `Escape` — Collapse the filter panel
- `?` — Open this help panel

---

## Reconciling with Bank Deposits
Deposits in the bank account correspond to payouts listed here. When reconciling
a deposit in QBO, we need to match it up with the donation or donations that it paid out.

1. Switch to the **Payouts** tab.
2. Filter (e.g., by date) to find the payout item matching your bank deposit.
3. Click the item to open the detail panel, which shows the donations included in
   that payout.
4. Use that list to match the bank deposit to donations in QBO.

---
## Adding New Online Donations
We enter online donations into QBO manually. One reason is to assign classes correctly. Our recipe
has been to download CSV reports from our giving platforms, and copy select fields into QBO.

This app presents the information from those CSV reports in a way that's ready to enter.

Donations are flagged as "missing" if they do not have a matching receipt in QBO.

1. Switch to the **Donations** tab.
2. Enable the "Missing" filter.
3. Select each donation in turn and use the information in the detail panel to enter it into QBO.

**Note:** It is a good practice to first fix any receipts that are missing their donation link (see below). 
If that link is not made, it is easy to create a duplicate receipt.

---

## Viewing and Fixing Errors in Receipts

Switch to the **Receipts** tab and use the error toggle filters in the filter bar to surface
specific issues.

### Missing Donations

A Receipt is flagged as "missing" if it is not paired with a corresponding online Donation.

- The receipt was for a donation by a check or ACH, and is not recorded as an online donation.
- The reference ID in the receipt was entered incorrectly. This was a frequent error when donations
were copied from a raw CSV report.

1. Switch to the **Receipts** tab.
2. Enable the "Missing" filter.
3. Select one listed receipt.
4. In the detail panel, click "Find Donation" to display the best guess of the corresponding donation.
5. Open the receipt in QBO (search by receipt number)
6. Copy the reference ID from the donation detail, and paste it into QBO.

### Data Discrepancies

The **Discrepancies** filter shows receipts where key fields (amount, date, donor name) do not
match the linked donation record.

Most of the time, there's an intended difference between the donor name in QBO and the name on the donation.
1. Switch to the **Receipts** tab or the **Donations** tab.
2. Enable the "Discrepancies" filter
3. Click to see the specific discrepancies
4. Correct errors in QBO or ignore them.

### Duplicate Receipts

Duplicate receipts may have been accidentally created for a single donation.

1. Switch to the **Donations** tab.
2. Enable the "Duplicates" filter.
3. Select a listed donation to see the duplicate receipts.
4. You can click on each receipt shown to see its details.
5. In QBO, decide which receipt to delete. One of them may have been reconciled to a banking deposit.

