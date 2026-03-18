# Milestone Plan for DonorPipe

## Overview
Completed milestones (1–19a) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

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

##### Milestone 19a.a - Set up repository operations
This is mostly an operator set of tasks.

**Repository** COMPLETE
1. Set up primary repository directory
2. Create a config file for it
3. Initialize Stripe and DonorBox by downloading years since 2023
4. Initialize other with copies of manual downloads
6. Sanitize to create test_org/
5. Build graph for 'oliveseed'
6. Test dev.

**Staging**
1. Fresh deployment of staging, clean out data directory
2. Deploy graph manually
3. Use refresh.sh to deploy graph, test update detection
4. Test staging **NEXT TO DO**
5. Automate updates to staging (mac job scheduling different than staging & prod?)

**Production**
1. Repeat staging steps
2. Add prod to refresh config.
3. Announce.

**RClone**
1. Get it set up
2. Clone new stuff from gdrive (not stripe, donorbox) to primary
3. Update stripe, donorbox in gdrive from primary

**Move Warehouse to Pi**
1. Deploy code to Pi
2. Copy primary to pi
3. Set up rclone
4. Set up automation

##### Milestone 19b - Automated downloads
Automated download of export files from donation/payment processors on a schedule or on demand.
* **Stripe** — **COMPLETE** API-based, straightforward
* **DonorBox** — **COMPLETE** API-based; platform fee computed from amount × rate (1.75% pre-4/1/2025, 2.0% after)
* **PayPal** — API is readily available. It looks like 'transaction history' will be fine. I'll capture the schema via
Postman for this.
* **Benevity** — No automated options, other than browser automation
Status: Stripe and DonorBox complete.  Benevity excluded.

**DonorBox Platform Fees** - empirically determined to be:
* 1.75% until 4/1/2025
* 2.0% after 4/1/2025 


##### Milestone 19c - QBO OAuth2 download
Automated download of QBO "Sales Transaction Export" report.
* QBO has a "run report" API in addition to entity queries (either works)
* OAuth2 is the main complexity — 100-day refresh token lifecycle
* Report format is a fixed custom export

Status: Not started.

### Milestone 20 - Update from manual downloads

#### Milestone 20b - Triggered Refresh (Bookkeeper UI + Warehouse Polling)

**Goal**: Let the bookkeeper request a data refresh from within the app and see when
it has completed, without needing access to the warehouse server.

**Architecture**: Bookkeeper clicks "New data please" in the app. The app sets a
"refresh requested" status. The warehouse (on the Pi) polls the app API every 30–60
seconds; when it sees "requested", it runs a full refresh cycle, then calls back to
confirm completion. The app returns to green.

**Components**:
1. **UI**: "New data please" button (admin/bookkeeper role). Status badge replaces the
   static timestamp: green = current, red = refresh requested/in-progress.
2. **API endpoints** (new):
   - `POST /admin/request-refresh` — records `refresh_requested_at` timestamp
   - `GET /admin/refresh-status` — returns `{ pending, requested_at, last_updated }`;
     `pending` is derived by comparing `requested_at` to `graph._meta.generated_at`
3. **Status persistence**: `data_base/refresh_state.json` — written by the app only
   (by policy; no file-permission enforcement). `data_base/graph.json` is written by
   the warehouse only. Format: `{ "requested_at": "<ISO timestamp or null>" }`.
   Human-readable and editable for operational convenience.
4. **Status derivation**: no explicit "confirm" step. If `graph._meta.generated_at >=
   requested_at`, the request is satisfied. The warehouse just delivers new data;
   the app derives freshness from timestamps alone.
5. **Warehouse polling service**: long-running service unit polls `GET /admin/refresh-status`
   every 30–60 seconds; triggers full refresh when `pending` is true.

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