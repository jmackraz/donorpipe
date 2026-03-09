# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–15) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones

## Milestone 16 - in-app user documentation

### Goals
* Provide high-level instructions for using the app within the app itself.
* Include documentation sections for specific use cases, even if you don't yet know what to say:
  * Reconciling with bank deposits
  * Adding new online donations
  * Viewing and fixing errors in receipts:
    * Missing donations
    * Data discrepancies
    * Duplicate receipts
* There should also be a quick-reference guide for keyboard shortcuts.

### Topics
* Doc should be co-authored by agent and developer
* Help text in app should be styled to look good
* Doc may be iterated frequently; it should be deployable without a full image push.


## Backlog
**Production Checklist:**
* Logging, alarms

**Architecture:**
* Merge in trickybit.csvstore (not anytime soon)

**Improve data management:**
* Serve a cached serialized graph, no need for CSV files on servers.
* Automated scripts for downloading reports
* Update for new data
  * Calculate complete serialized data graph
  * Deploy to staging and/or production
* Dynamic updating
  * Detect or tickle new data files
  * App provides information to front-end - poll or push
  * Front end updates with new data, informs user

**UI:**
* Inspect details of any entity in the relationship graph in any detail pane
* Add notice about proprietary data
* Keyboard shortcuts — navigation, focus and selection (M14 phase 3)
* Keyboard shortcuts — complete filter shortcut set requiring FilterBar focus (M14 phase 3)
* tune keyboard shortcuts, document
* add "transaction id" filter, works with "copy ID" for emailing, etc.

**User Docs:**
* Might be easiest to author in markdown w/ agent help
* Viewer in the app, contents must be styled to look good
* Keyboard shortcut quick-reference

**Demo:**
* Realistic fake data (BIG)