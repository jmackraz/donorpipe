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

### Milestone 15 - Side-by-Side Views
* Use case: fix missing receipts/donations 
* Period comparisons
* Sync'd or independent:
  * Filters
  * Scrolling


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

**Demo:**
* Realistic fake data (BIG)