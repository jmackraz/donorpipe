# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–13) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones
### Milestone 13 - Improvement of filters
* Improvement of filters to include service, missing, dupe, discrepancies
* Different semantics for different tx types

### Milestone 14 - Side-by-Side Views
* Use case: fix missing receipts/donations 
* Period comparisons
* Sync'd or independent:
  * Filters
  * Scrolling


## Backlog
**Production Checklist:**
* Logins for team
* Clean up data organization
* Set up test_org organization
* Logging, alarms

**General:**
* (nah) baby CI/CD just to make pushes easier for me?
* Merge in csvstore
* sort out files
  * directories to rsync
  * script to rsync and bounce/reload (now it's just browser refresh)
  * sanitization script runs routinely
* Separate engine for automated downloading
* Serve a cached serialized graph 
* Forced refresh (data version?)

**UI:**
* Add notice about proprietary data
* tune keyboard shortcuts, document
* test mobile form factor
* Filter out cash donations when appropriate
  * More filters.  day/week/month/year.  donor/recipient. service.  missing donations/receipt.  too many receipts.
* comparison view - mis-linked receipts



**Demo:**
* Realistic fake data
* Demo account