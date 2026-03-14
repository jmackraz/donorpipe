# Milestone Plan for DonorPipe

## Overview
Completed milestones (1–18.5) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones
### Milestone 19 - Content management
This is a major milestone in several phases.
We may want to work on a feature branch for this.

#### Goals
* Simplify management of CSV files
  * Rather than deploy copies of the CSV files around, we should be able to deploy a single serialized graph of data.
* A mix of automated and manual download of reports
* Automated processing and data updates

#### Behavior
* Automated downloads are initiated on a schedule or on demand by admin.
* Updates down the pipeline for data changes:
  * New CSV triggers recalculation of serialized graph
  * New serialized graph triggers deployment to staging and/or production
  * Front end updates with new data,

#### Special use case
1. A user (bookkeeper) uses the app to enter or correct data in QBO.
2. They want to (quickly) see their changes reflected in the app.
3. If we have a way to download the CSV automatically, they can use the app to invoke the download (and consequentely
   the updates)
4. If we don't have a way to download, the user can download a CSV file manually to their computer and then do something with it, for example:
  * Copy the file to google drive or other shared location
  * Upload the file to the app
  * Put it into some other convenient, reliable and secure sharing pipeline we can use.

#### Sub-milestones

##### Milestone 19a - Pre-built graph serving
`build_graphs.sh` writes `graph.json` per account; `graph_route.py` serves the pre-built file (503 if not present — no CSV fallback). Decouples data processing from request handling.

Status: Complete.

##### Milestone 19b - Automated downloads
Automated download of export files from donation/payment processors on a schedule or on demand.
* **Stripe** — API-based, straightforward
* **PayPal** — investigate API availability
* **DonorBox** — confirm plan tier supports API access
* **Benevity** — investigate API availability

Status: Not started.

##### Milestone 19c - QBO OAuth2 download
Automated download of QBO "Sales Transaction Export" report.
* QBO has a "run report" API in addition to entity queries (either works)
* OAuth2 is the main complexity — 100-day refresh token lifecycle
* Report format is a fixed custom export

Status: Not started.

  

## Backlog
**Production Checklist:**
* Logging, alarms

**Architecture:**
* Merge in trickybit.csvstore (not anytime soon)


**UI:**
* Add notice about proprietary data
* Keyboard shortcuts — navigation, focus and selection (M14 phase 3)
* Keyboard shortcuts — complete filter shortcut set requiring FilterBar focus (M14 phase 3)
* tune keyboard shortcuts, document
* add "transaction id" filter, works with "copy ID" for emailing, etc.
* "What's New" message pops up if unseen, can reach through help or something

**Demo:**
* Realistic fake data (BIG. DONE!)