# Specifications and guidelines for webui

## Overview
Users view financial transactions in a responsive React-based browser app.

## Use Cases
* Users scan compact, filtered lists of transactions of several types
* Users see relationships among entities
* When screen space permits, users can see filtered lists of transaction in side-by-side views.
  * the filteres for these lists can be independent or, more often, sync'd.
  * The scrolling of the views can be independent or sync'd
* Filters are set up through simple and fast UX

## Non-Goals (V1)
* No creation/edit/delete of transactions
* No social features, comments, “posts”
* No complex role-based permissions beyond basic auth gating (unless specified)
* No heavy “dashboard vanity metrics” unless it materially helps exploration

## Styling
* We should be able to easily swap in styling themes at development time.
* We should anticipate the agent making almost all of the changes  (agent-friendly implementation)

## UX Architecture
* One route/window to be used for all data listings
* The filter controls should be always visible when the screen permits
* There must be a way to view operational stats and the oldest/newest date range of transactions
from each service.

## UX Guidelines:**
* We will be keeping all of our data in memory, we don't need paging
* The UX operations (once data is loaded) should be very fast.  Design for speed.
* Our initial versions will have a small, closed set of users in our organization
* The UX is stable when data is updated
* We prefer simpler underlying implementations (including for style, state),
buy may anticipating adding complexity later
* The app must be keyboard driven for all key operations
* The app should be accessible to a reasonable degree, as we have a small, closed set of users.
* Prefer small components; split at ~200 lines
* No `any`. Use `unknown` + narrowing or schema validation.
* No class components.

### UX priorities
* Fast filtering, stable pagination, predictable navigation
* Clear “truth” about amounts/dates/currency
* Visible provenance (source, import batch, institution, file)
* Strong empty/error states and graceful partial data
* All UI logic must treat server responses as the source of truth.** No duplicating server state in local stores.


## UI Patterns to Implement
### Transaction List page (`/transactions`)
Must include:
* Filter bar:
  * date range (default: last 30 days or last full month — pick one and document)
  * account (multi-select if trivial)
  * amount range
  * text query
  * relationship filters (has relationships? edge types?)
* Table:
  * columns: date, account, merchant/memo, amount (right-aligned), category, relationship badge
  * sticky header if easy
  * pagination (cursor or offset; match API)
* Row click → detail
* Quick actions (read-only):
  * copy transaction id
  * open in new tab
* States:
  * loading skeleton
  * empty (“No transactions match these filters” + clear filters)
  * error (retry)

### Transaction Detail (`/transactions/:id`)
Must include:
* Header:
  * merchant/memo + amount + date + account
  * provenance block (source/import batch)
* Tabs or sections:
  1. Overview
  2. Relationships (primary)
  3. Raw JSON (internal-only toggle; behind a “developer” reveal)
* Relationships panel:
  * grouped by edge type
  * each related transaction shown in compact card row
  * navigation: click related txn to replace view; include breadcrumb/back
* Guardrails:
  * clearly show if a relationship is directional (transfer from/to)
  * show currency mismatches or partial data as warnings, not silent failures


## Data Fetching (React Query)
### Rules
* All API calls go through `src/shared/api/client.ts`
* Each feature defines typed endpoints:
  * `features/transactions/api.ts`
* Use stable query keys:
  * `['transactions', filters]`
  * `['transaction', id]`
  * `['relationships', id]`
* Cache/prefetch:
  * Prefetch detail on list row hover (optional)
  * Keep list data while navigating to detail (avoid refetch churn)

### Error normalization
API client must normalize errors into:
type ApiError = { message: string; code?: string; status?: number; details?: unknown };