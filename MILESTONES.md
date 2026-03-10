# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–17) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones

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
* Add notice about proprietary data
* Keyboard shortcuts — navigation, focus and selection (M14 phase 3)
* Keyboard shortcuts — complete filter shortcut set requiring FilterBar focus (M14 phase 3)
* tune keyboard shortcuts, document
* add "transaction id" filter, works with "copy ID" for emailing, etc.
* "What's New" message pops up if unseen, can reach through help or something

**Demo:**
* Realistic fake data (BIG)