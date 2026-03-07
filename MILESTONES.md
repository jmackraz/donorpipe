# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–10) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones

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

