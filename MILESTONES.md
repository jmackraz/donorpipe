# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

## Milestones
### Milestone 1: Set up project directory hierarchy

**Goal:** Directory src tree set up for best practices, to include:
* Backend models (python) and data layer
* API bindings, routes, config (for FastAPI)
* Front-end React/TypeSCript project
* CLI script
* Development scripts

### Milestone 2: Sanitized test data

**Goal:** provide a utility to sanitize CSV financial reports for use as durable test data
It is assumed that future milestones will need meaningfully rich and realistic data set, 
but production data contains sensitive information.

**Form:** a command-line python utility script that will be run outside the context of the project

**Behavior:** 
* parameters: input directory and output directory
* all CSV files in the input directory and descendants are processed to create output 
files under the output directory, in the same subdirectory structure
* processing consists of replacing the values in any column with header value containing:
'name', 'address', 'comment'
* the replacement values do not need to be believable or appealing for a demo.  For example, 
the names could be "Name 123", "Name 124" etc.  I'm open to a better way if it's not too complex.
* the value encoding format should not be changed.  It may be best to interpret fields as strings.

**Constraints:**
* Standard libraries only, but ask if worth it

**Complete when:**
* Test uses synthesized data files
* script is available in a development scripts directory
* Test suite succeeds

### Milestone 3.1: Adapt legacy backend

Before implementing this, we should discuss submilestones.

**Precondition:**
* I have copied legacy code into the 'models' directory
and two files that make up the CLI script into the 'cli' directory.
* In so doing, I relocated the two cli files, which were originally
in the same directory as the models.

**Goals:**
* The legacy code runs successfully in this project structure

The cli command, from the top level project directory is:

```bash
env OSF_EXPORTS=testdata uv run src/donorpipe/cli/model_cli.py -d Stripe DonorBox QBO
```

**Behavior:**
* The legacy code has been analyzed and remembered
* The CLI script executes without exception and ingests the test data

**Done when:**
* The CLI functions
* User confirms the CSVs are being ingested

### Milestone 3.2: Improve the legacy code

**Goals:the legacy code is improved**

**Behavior:**
* The legacy code is typed
* The legacy code has automated tests
* Suggestions are discussed and implemented, with decisions recorded

**Done when:**
* The legacy code is typed
* Test suite succeeds
* Suggestions are implemented
* Decisions are documented

**Constraints:**
* Don't refactor the legacy code

**Decisions:**
* Type checker: pyright
* Testing: light unit tests; code is stable and well-exercised
* Pydantic: deferred to Milestone 5 where FastAPI integration makes it natural
* Type annotations: inline PEP 484 hints, no structural refactoring


### Milestone 4: Serialize graph

**Goal:** Serialization and deserialization in python

**Approach:**
* Follow the proposals and decisions in docs/relationshps.md to change the implementation of runtime
relationships and test.  Adapt model_cli.py to suit if needed and test.
* Use the new model classes to serialize the graph into a JSON payload and save it to a file in a good place
for later consumption during development.
* Use the new model classes to deserialize the JSON payload into a graph (Python only)
* Write an alternative initialization method for TransactionStore that uses the JSON payload as a cache, instead of
reading CSV files.
* Test.

**Non-goals:**
* Work on the API
* Do any TypeScript
* Make the loading-from-cache consider timestamps or be smart.

**Done when:**
* Tests pass
* Serialization of test data is saved to a file

### Milestone 5: API

**Goal:** Bring up a REST API exposing the backend

**Approach:**
* Set up FastAPI for development
* Models are instantiated subject to new config scheme
* Implement a GET method that returns the entire serialized graph
  * It takes a single parameter as a stub for the 'oganization account id'
* A simple CLI script (python) demonstrates how to fetch and decode the graph
provided today by the CLI

### Milestone 6: CLI uses the API

**Goal:** Make a modified version of the model_cli.py that can use the API instead of direct import of the backend.

**Requirement:** Same cli script can operate in either mode--read CSV or use API.  

**Done when:** model_cli.py performs equivalently using either API or cvs scanning.  Test by diffing serialized 
graph output for the two modes.

### Milestone 7: Core TypeScript functionality

**Goal:** Get the deserialization and object model working for JavaScript in a standalone (non-browser) context

**Behavior:**
* Set up project for TypeScript development in the frontend src directory
* New script set up for cli running and debugging (Node or other, please recommend)
* It has a transaction class abstractions as laid forth in relationships.md
* The script connects to API, retreives serialized graph
* It deserializes the transaction object graph
* Tested
* Reusable in a practical sense for running in a browser context

**Done when:**
* Tests written to validate 

### Milestone 8: Skeletal Front-End

**Goal:** Bring up a React/TypeScript subproject that connects to the backend as a minimal
responsive app

**Non-goals:**
* Complex styling
* Fancy controls/UI
* Auth

**Behavior:**
* App runs in Chrome
* App incorporates code from prior milestone
    * Connects to API and fetches serialized graph
    * Deserializes into object graph
* Displays donations in a simple scrolling view
* Demonstrates asynchronous refresh of data (e.g. on on_click)
* Shows timing for fetch and dedode of graph data

**Guidelines:**
* Prefer simplicity over performance optimization

**To Decide:** Although this milestone doesn't focus on styling, I don't want it to be difficult
to add later.  Is this a good time to add a theme and styling for the UX as we build?    Include your recommendation 
in your plan.

**Done when:**
Let's discuss.  I do not know the best practices for testing web apps.  It may
be more complex than necessary.

The test and acceptace criteria may be human.

* The app is tested in Chrome
* A single GET, decode, display is tested from the app
* The backend does not throw exceptions
* The page loads succesfully
* The Chrome logs are clean of errors and warnings

### Milestone 9: UX Function

**Goal:** The primary views and responsive layout of the app are in place

**Non-goal:** Fancy styling, theming, tranisitions

We should discuss our approach to specifying the UX features and layout I have in mind.

### Milestone 10: Nice styling and polish !NOT NEEDED!

**Goal:** Upgrade the UX design to high standards

### Milestone 11: Auth and Account Silos

**Goal:** Protect per-organization data with individual user accounts.

**Decisions:**
- Auth protocol: OAuth2 password flow with JWT, using FastAPI's built-in security
  utilities (`python-jose`, `passlib[bcrypt]`)
- User store: a `users.json` file (or section in `config.json`) with hashed passwords
  and org membership — no database required
- No self-service registration or password reset; admin manages users by editing the
  config file and generating bcrypt hashes via a helper script
- Tokens are stateless (verified by signature, no server-side session state)
- Container-friendly; migrate to Cognito if audience grows to warrant it

**Behavior:**
- `POST /token` — accepts `username` + `password` (form-encoded), returns a signed JWT
  on success or 401 on failure
- `GET /accounts/{account_id}/graph` — requires a valid JWT (`Authorization: Bearer <token>`);
  returns 401 if missing/invalid, 403 if user is not a member of that account
- JWT contains: `sub` (username), `accounts` (list of accessible account IDs), `exp` (expiry ~8h)
- Frontend: login form POSTs to `/token`, stores JWT in React memory (not localStorage);
  attaches it as `Authorization` header on every graph fetch
- `scripts/hash_password.py` generates bcrypt hashes for admin use

**Non-goals:**
- Self-service password reset or registration UI
- MFA
- Admin management UI

**Done when:**
- `POST /token` returns JWT for valid credentials; 401 for invalid
- Graph endpoint returns 401 without token, 403 if user lacks org membership, 200 if authorized
- Frontend login form works end-to-end; unauthenticated users cannot reach data
- Existing tests still pass; new tests cover auth happy path and error cases
- `scripts/hash_password.py` generates a usable bcrypt hash

**Key files:**
- `src/donorpipe/api/auth.py` — JWT creation, verification, user lookup
- `src/donorpipe/api/app.py` — add `/token` route
- `src/donorpipe/api/graph_route.py` — add auth dependency
- `src/donorpipe/api/config.py` — add user/membership model
- `frontend/src/` — login form, auth context, header injection in `useGraph.ts`
- `scripts/hash_password.py` — new helper

### Milestone 12: Local Deployment (Raspberry Pi)

**Goal:** Host the app on a Raspberry Pi 4 for local network use.

**Platform:** Raspberry Pi 4 (ARM64), Docker already installed.

**Architecture:**
- Two Docker containers managed by Docker Compose:
  - `api`: FastAPI backend (Python 3.13, built from `Dockerfile`)
  - `nginx`: serves built React static files + reverse-proxies `/api/` and `/token` to `api`
- nginx is the only container with a published port (80)
- FastAPI is only reachable inside the Docker network

**nginx routing:**
- `GET /` and `/assets/` → serve `frontend/dist/`
- `POST /token`, `GET /api/...` → proxy to `api:8000`

**Deployment workflow (`scripts/deploy.sh`):**
1. `bun run build` in `frontend/` to produce `frontend/dist/`
2. `docker compose build` to build both images
3. Copy images to Pi via `docker save | ssh | docker load`
4. SSH to Pi and run `docker compose up -d`

**Configuration:**
- `config.json` and `users.json` mounted as volumes; JWT signing key passed as env var
- `DONORPIPE_CONFIG` env var points to mounted config file

**Non-goals:**
- HTTPS (added in M13)
- CI/CD, automatic rollback, fleet management

**Done when:**
- `docker compose up` on the Pi serves the app at `http://pi-hostname/`
- Auth (M11) works end-to-end on the Pi
- `scripts/deploy.sh` completes a full deploy from a developer laptop in one command
- `GET /health` returns 200
- `docker compose logs` shows structured log output

**New files:**
- `Dockerfile` — multi-stage Python build
- `docker-compose.yml` — defines `api` and `nginx` services
- `nginx/nginx.conf` — routing rules
- `scripts/deploy.sh` — full deploy script
- Health check route in `src/donorpipe/api/app.py`

### Milestone 13: Public Deployment (AWS Lightsail)

**Goal:** Make the app publicly accessible over HTTPS to a small audience.

**Platform:** AWS Lightsail (existing instance), ~$10/month (2GB RAM).
Domain name already owned.

**Architecture:** Identical to M12 — same Docker Compose setup — with two additions:
1. nginx config gains TLS (port 443) via Let's Encrypt certificate
2. Port 80 redirects to 443

**HTTPS approach:**
- Certbot obtains a free Let's Encrypt certificate proving domain ownership
- Certificate files mounted into the nginx container as a volume
- Certbot renewal cron job runs on the host and reloads nginx on renewal:
  `docker compose exec nginx nginx -s reload`
- No load balancer, no ACM, no additional AWS cost for TLS

**AWS bill of materials (~$10/month total):**
- Lightsail instance (2GB/1vCPU/60GB): $10/month
- Static IP (attached to running instance): free
- TLS certificate (Let's Encrypt): free
- Data transfer (3TB/month included): free
- Lightsail DNS zone: free
- Domain name: already owned

**Reproducibility:**
- Lightsail instance provisioning documented as a CloudFormation template or
  launch script covering: instance creation, Docker install, repo clone, initial Certbot run
- `scripts/deploy.sh` used for all subsequent deploys (same as M12)

**Done when:**
- App reachable at `https://yourdomain.com`
- TLS certificate valid; HTTP redirects to HTTPS
- Auth (M11) works end-to-end over HTTPS
- `scripts/deploy.sh` deploys an update from developer laptop in one command
- CloudFormation template or `scripts/provision.sh` can provision a fresh instance from scratch
- `GET /health` returns 200

**Modified files from M12:**
- `nginx/nginx.conf` — add port 443, TLS cert paths, HTTP→HTTPS redirect
- `src/donorpipe/api/app.py` — update CORS allowed origins to include production domain
- New: CloudFormation template or `scripts/provision.sh`

