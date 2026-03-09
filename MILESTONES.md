# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–13) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones
### Milestone 14 - Improvement of filters

**Goals:**
* We add filter criteria with defaults that important for the app.
* We craft an excellent keyboard shortcut system for filtering.
* Filters are as common as possible across listings of different types.
  * E.g., filtering for 'missing' will find receipts with missing donations in the Receipts list, and 
  donations with missing receipts in the Donations list.
  * E.g., the 'missing' filter will remain in the filter bar, but ignored when viewing payouts.

**Filters:**
All conditions persist but are ignored when viewing listings where they are not relevant.
* **Missing** matches receipts with missing donations, and donations with missing receipts. 
* **Discrepancies** Matches receipts with discrepancies,
* **Duplicates** Matches donations with duplicate receipts
* **Donor** Matches donations with a specific donor, by pattern 
* **Service** Matches receipts with a single specific service,
* **Date range** Matches receipts with a specific date range, see note below.

**Note on Date Range:**
* Should take the form:
  * Start date
  * Interval: day, week, month, year
* Ranges are aligned on the natural interval, e.g., a start date of 5 Jan 2020 and an interval of month will
  match 1 Jan 2020 to 31 Jan 2020.
* A keyboard shortcut will change the start date to the beginning of the next natural interval.  For example,
  if the start date is 5 Jan 2020 and the interval is month, pressing 'n' will change the start date to 1 Feb 2020.
* The keyboard shortcut 'p' will do the same for the previous interval.

**Phase 1:**
* Implement the UI for all of these filters (in FilterBar)
* Implement all filters except date range.

**Phase 2:**
* Implement date range filter.
* Implement keyboard shortcuts for date range.
  * These shortcuts should be 'global' in that they do not require the FilterBar to have focus.
  * These should be 'n' for 'next interval', 'p' for 'previous interval', and 'c' for 'clear' (already implemented).

**Phase 3:**
* Design and implement a set of shortcuts for navigation, focus and selection.
* Design and implement a complete set of shortcuts for filters
  * These will require the FilterBar to have focus.

### Milestone 15 - Handle Receipts with Missing Donations 
#### Goals
* Help the user find the right donation for a given receipt when the relationship to a donation is missing.
* Help the user make corrections to the receipt in QBO (usually by correcting the reference ID)

#### Common causes:
* Reference ID was not entered when creating the receipt.  It should be the raw transaction ID of the online donation.
* The reference ID was entered incorrectly.  In particular, when receipts are created from Benevity donations,
the payment ID is sometimes entered as the reference ID, instead of the line-item transaction ID.
* The donation is not an online donation, it's usually Direct Cash Donations.  We should suppress those receipts 
much of the time.
* The report containing the corresponding donation is missing from our dataset. (rare)

#### Approach
* When inspecting a receipt with a missing donation, we offer to try to automatically identify
the donation. 
* When we display the donation we guessed, we offer a button to copy the raw trnasaction ID of the donation to
the clipboard. That's convenient for pasting into QBO.
* As an alternative, we offer to initialize the filter criteria to roughly match the receipt, so the
user can browse donations that might be related to the receipt. While browsing the donations, the user needs to be able to easily review
the receipt to be matched.

#### UI Ideas
* In the details pane of any receipt, if the donation is missing, and the "product" is not "Direct Cash Donation",
we offer two buttons:
  * **Find Donation:** we will replace the detail pane of the receipt with the detail of our best-guess donation (or a  
  message if we can't find one).
  The "Copy ID" and close buttons work as usual, except that when closed, we return to the receipt detail, we don't close the detail pane.
  * **Manual Search:** We will "remember" the receipt, initialize the filter criteria, and switch to the Donations list.
  When a receipt is "memorized" in this way, there will be a button in the detail page of each donation to display the
  detail of the memorized receipt.  It is the counterpart of the "Find Donation" button.  When displaying the memorized 
  receipt, there is a button to "Forget this receipt"

#### Initializing the filter criteria
* To be determined.
* It should include "Missing"
* An amount range is calculated to be within 10% of the net amount of the receipt.
* The date range is calculated to be the week containing the receipt.

#### Identifying the donation
* First, we filter the donations by the same filter criteria as above.
* Any donations in that filtered set who are missing receipts are strong candidates.
* The strongest candidate is the one with the closest net amount.
* If there are multiple candidates, pick one arbitrarily.
* If there are no candidates, loosen the filter criteria and try again, details TBD.

## Backlog
**Production Checklist:**
* Logins for team
* Logging, alarms

**Architecture:**
* Merge in trickybit.csvstore (not anytime soon)
* Serve a cached serialized graph 
* Forced refresh (data version?)

**UI:**
* Add notice about proprietary data
* tune keyboard shortcuts, document
* Filter out cash donations when appropriate
* comparison view - mis-linked receipts (BIG)
* add "transaction id" filter, works with "copy ID" for emailing, etc.

**Demo:**
* Realistic fake data (BIG)