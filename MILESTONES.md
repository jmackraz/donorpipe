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

##### Milestone 19b - Automated downloads
Automated download of export files from donation/payment processors on a schedule or on demand.
* **Stripe** — **COMPLETE** API-based, straightforward
* **DonorBox** — **COMPLETE** API-based; platform fee computed from amount × rate (1.75% pre-4/1/2025, 2.0% after)
* **PayPal** — investigate API availability
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

#### Milestone 20a - Manifest, Change Detection, Scheduled Refresh, Data Freshness

**Goal**: Detect when CSV files in the warehouse have changed and keep the app showing
fresh data automatically, with a clear indication of when data was last updated.

**Components**:
1. **Manifest in graph.json**: `generate_graph_json.py` adds a `_meta` block recording
   each source CSV file with `path`, `size`, `mtime`, and `sha256` checksum.
   `generated_at` timestamp also stored.
2. **Change detection** (`warehouse/should_rebuild.py`): compares current CSV stats
   against `graph._meta`; uses mtime for a fast first-pass, SHA-256 to confirm actual
   content change. Returns true only if a rebuild is needed.
3. **Scheduled refresh** (`warehouse/refresh.sh` via systemd timer): on a schedule
   (e.g., every 10–30 min) runs rclone sync from Google Drive → should_rebuild check →
   rebuild graph + sync to server if changed.
4. **App: data freshness display**: frontend reads `graph._meta.generated_at` and
   displays a "Last updated: [timestamp]" indicator. Shows a visual stale warning if
   data is older than a threshold.

Status: Not started.

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
   - `POST /admin/request-refresh` — sets status to "requested"
   - `GET /admin/refresh-status` — returns `{ status, last_updated }` (warehouse polls this)
   - `POST /admin/confirm-refresh` — warehouse calls after delivering new data; resets to green
3. **Status persistence**: small JSON file in `data_base` alongside `graph.json`.
4. **Warehouse polling service**: long-running service unit polls `GET /admin/refresh-status`
   every 30–60 seconds; triggers full refresh when requested.

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