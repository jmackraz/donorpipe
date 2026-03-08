# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–13) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones

# Backlog
* ops manual
  * include CMS
  * ops scripts (dev, stage, prod) from CLAUDE.md
  * include arch overview
  * include dev/stage/prod push processes
  * include log monitor commands
  * keep updated, occasionally validate
* baby CI/CD just to make pushes easier for me?
* Add notice about proprietary data
* Logging, alarms
* tune keyboard shortcuts, document
* CMS system
  * REST interface for uploading (sanity checks?)
  * Separate engine for automated downloading
  * Trigger reload
  * Works well for dev iterations
* Realistic fake data
* Merge in csvstore
* test mobile form factor
* Filter out cash donations when appropriate
  * More filters.  day/week/month/year.  donor/recipient. service.  missing donations/receipt.  too many receipts.
* comparison view - mis-linked receipts
* Serve a cached serialized graph 