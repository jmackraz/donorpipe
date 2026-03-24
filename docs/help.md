# DonorPipe Help

DonorPipe interconnects donation data reported from multiple online giving platforms (DonorBox, Benevity, Stripe, PayPal)
and compares them against QuickBooks Online sales receipts, helping you to:
* Create sales receipts for new online donations correctly into QBO
* Reconcile bank deposits with QBO sales receipts
* Identify and fix data-entry errors and duplicates in QBO receipts

We no longer have to:
* Manually download CSV reports from each platform
* Pick through large CSVs to create sales receipts for online donations.
* Struggle to reconcile bank deposits against the several online donations that can be batched in a single payout.
## Online Donations Transactions
A typical scenario for online donations:
1. A donor makes an online **_donation_** in DonorBox, and pays with their credit card.
2. DonorBox creates a **_charge_** in Stripe
3. We create a **_sales receipt_** in QBO for the online donation (from their exported report)
4. This all happens a second time, after which Stripe makes a **_payout_** for __both__ donations, in the form of a **_deposit_** to our bank account.
5. When we reconcile the bank deposit, we have to identify the two (or sometimes more) online donations 
that are included in that payout.

![DonorPipe donation pipeline diagram](/donation_pipeline.svg)

---
## Getting Started
Use the **tabs** (Donations / Receipts / Payouts) to switch between entity types, and the
**filter bar** to narrow results by date range, amount, service, or donor name.

Click on a listed item to see its details in the detail panel. All related transactions are shown in the _Relationships_
section of the detail panel. 

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
3. Click the item to open the detail panel, the _Relationships_ section shows the donations included in
   that payout.
4. Use that list to match the bank deposit to donations in QBO.

---
## Adding New Online Donations
We enter online donations into QBO manually. One reason is to assign classes correctly. Our recipe
has been to download CSV reports from our giving platforms, and copy select fields into QBO.

This app presents the information from those CSV reports in a way that's ready to enter.

Donations are flagged as "missing" if they do not have a matching receipt in QBO.

1. Switch to the **Donations** tab.
2. Enable the "Missing" filter, to see only donations that are missing a receipt. (But first, see Note below.)
3. Select each donation in turn and use the information in the detail panel to create a Sales Receipt QBO.

**NOTE**:
It is a good practice to first fix any receipts that are missing their donation link (see below). 
If that link is not made, it is easy to accidentally create a duplicate receipt for a donation.

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

### Viewing your QBO Additions and Corrections
Much of the data work is done by adding receipts in QBO for donations that need them, and correcting any data omissions, 
discrepancies, and duplications.  It's nice to see your changes updated in the app.  To do so:
1. Click the Refresh icon (circular arrow) at the right of the header near the latest-updated date.
2. In a minute or two, the system will notice, do a fresh download from QBO, and update the web app.
3. In your browser, you'll see in the same header area that new data has arrived. Click
to refresh your browser view and see your changes.