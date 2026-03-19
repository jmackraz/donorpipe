# DonorPipe Operations

This document covers running, deploying, and managing DonorPipe across environments.

---

## Day-to-Day Operations

### Update graphs

#### Hardwired update (normal use)

`warehouse/update.sh` combines download + rebuild + sync in one command:

```bash
warehouse/update.sh nightly    # Download all services, rebuild, sync to staging + prod
warehouse/update.sh ondemand   # Download QBO only (for bookkeeper changes), rebuild, sync
```

#### Manual / ad-hoc update

```bash
# 1. Download fresh data from external services (Stripe, DonorBox, PayPal, QBO)
warehouse/download.sh oliveseed
warehouse/download.sh --year 2025 oliveseed                          # specific year
warehouse/download.sh oliveseed --services stripe qbo               # selected services (--services must follow account)

# 2. Rebuild changed graphs and sync to staging
warehouse/refresh.sh

# 2b. Rebuild and sync to staging, then prod if staging changed
warehouse/refresh.sh && PROD=1 warehouse/refresh.sh --sync-only
```

`refresh.sh` detects changes since the last build, rebuilds only what changed, and syncs to the target server. It exits 1 (no-op) when nothing changed — the `&&` pattern uses this to gate the prod sync.

> **Note:** Automated graph refresh (scheduled + on-demand trigger) is planned for Milestone 20.

### Update config

```bash
./scripts/push-config.sh              # Push staging_config.json to staging, restart api
PROD=1 ./scripts/push-config.sh      # Push prod_config.json to prod, restart api
```

### Update help docs

```bash
./scripts/push-help.sh               # Push docs/help.md to staging
PROD=1 ./scripts/push-help.sh        # Push docs/help.md to prod
```

No container restart needed — the API reads the file on each request.

### Logs / Restart

```bash
./scripts/logs.sh                    # All containers (staging)
./scripts/logs.sh api                # API only (staging)
PROD=1 ./scripts/logs.sh             # All containers (prod)
PROD=1 ./scripts/logs.sh api         # API only (prod)

./scripts/restart.sh                 # Restart all (staging)
./scripts/restart.sh api             # Restart api only (staging)
PROD=1 ./scripts/restart.sh          # Restart all (prod)
PROD=1 ./scripts/restart.sh api      # Restart api only (prod)
```

---

## Deploy

Run when code changes (app, frontend, or Dockerfile).

```bash
./scripts/deploy.sh                  # Build + deploy to staging (punkinpi.local)
PROD=1 ./scripts/deploy.sh           # Build + deploy to prod (linux/amd64 images + TLS)
```

### Full deploy (images + config + help + graphs)

```bash
./scripts/deploy-all.sh              # Staging
PROD=1 ./scripts/deploy-all.sh       # Production
```

Runs `deploy.sh`, `push-config.sh`, `push-help.sh`, and `warehouse/sync-graphs.sh oliveseed test_org` in sequence.

---

## Data Management

### Refresh sanitized test data

```bash
warehouse/sanitize.sh
```

Reads `sanitize[]` from `warehouse_config.json` and re-generates the `test_org` data from real data. Run this after real data has been updated to keep test/demo data current.

### Build graphs manually

Use this when you want to build without going through `refresh.sh` (e.g. first-time setup or forced rebuild):

```bash
./scripts/build_graphs.sh --config warehouse/warehouse_config.json            # All accounts
./scripts/build_graphs.sh --config warehouse/warehouse_config.json oliveseed  # One account
```

The config must have `data_base` pointing to the local path where CSVs live.

### Sync pre-built graphs

```bash
./warehouse/sync-graphs.sh oliveseed test_org           # Sync to staging
PROD=1 ./warehouse/sync-graphs.sh oliveseed             # Sync to prod
```

No API restart needed — the route reads graph.json from disk on each request.

---

## Dev

**URL:** http://localhost:5173

```bash
./scripts/dev.sh                                           # Start API (port 8000) + frontend (port 5173)
```

Press Ctrl+C to stop both. Config is read from `DPIPE_DEV_CONFIG` (default: `warehouse/warehouse_config.json`).

### Individual servers

```bash
uv run fastapi dev src/donorpipe/api/app.py               # API only
uv run python scripts/fetch_graph.py --account my_org     # Fetch graph summary from API
uv run python scripts/fetch_graph.py --account my_org --json

bun scripts/fetch_graph.ts --account my_org               # Same via TS
bun scripts/fetch_graph.ts --account my_org --base-url http://localhost:8000
```

---

## Script Reference

### Operational scripts

| Script | Purpose | Key args / env vars |
|--------|---------|---------------------|
| `warehouse/update.sh` | Hardwired download + rebuild + sync for oliveseed | `[--config <path>]`, `nightly` or `ondemand` (required) |
| `warehouse/download.sh` | Download CSVs from services (Stripe, DonorBox, PayPal, QBO) | `<account>` (required), `--year`, `--config`; `--services <svc> ...` must follow account |
| `warehouse/refresh.sh` | Detect changes → rebuild graphs → sync to server | `[accounts]`, `--sync-only`, `PROD=1` |
| `warehouse/sync-graphs.sh` | Sync pre-built graph.json files to server | `<account> [account ...]`, `PROD=1` |
| `warehouse/sanitize.sh` | Regenerate sanitized test data | reads `sanitize[]` from `warehouse_config.json` |
| `scripts/build_graphs.sh` | Build graph.json from CSVs | `--config <path>`, `[account_id ...]` |
| `scripts/deploy.sh` | Build Docker images and deploy to host | `PROD=1`, `DPIPE_HOST`, `DPIPE_USER`, `DPIPE_DIR` |
| `scripts/deploy-all.sh` | Full deploy: images + config + help + graphs + warehouse update | `PROD=1` |
| `scripts/update-warehouse-pi.sh` | Update warehouse code on Pi (git pull + uv sync) | `DPIPE_HOST`, `WAREHOUSE_DIR` |
| `scripts/provision-pi-warehouse.sh` | Install systemd timer units on Pi (one-time) | `DPIPE_HOST`, `PI_USER` |
| `scripts/push-config.sh` | Copy config to host and restart api | `PROD=1`, `DPIPE_HOST`, `DPIPE_DIR` |
| `scripts/push-help.sh` | Copy docs/help.md to host | `PROD=1`, `DPIPE_HOST`, `DPIPE_DIR` |
| `scripts/logs.sh` | View container logs | `[service]`, `PROD=1` |
| `scripts/restart.sh` | Restart containers | `[service]`, `PROD=1` |
| `scripts/dev.sh` | Start local dev servers (API + frontend) | `DPIPE_DEV_CONFIG` |

### Utility scripts

| Script | Purpose | Key args |
|--------|---------|----------|
| `scripts/hash_password.py` | Generate bcrypt hash for a config user entry | `<password>` |
| `scripts/sanitize_csv.py` | Sanitize a CSV report (PII scrubbing) | `<source>` `<dest>` |
| `scripts/fetch_graph.py` | Fetch graph summary from running API | `--account`, `--json`, `--base-url` |
| `scripts/generate_graph_json.py` | Build graph.json for one account | called by `build_graphs.sh` |

### Config files

| File | Used by | Notes |
|------|---------|-------|
| `warehouse/warehouse_config.json` | Dev machine | Full config including `users` and dev-machine paths |
| `warehouse/warehouse_pi_config.json` | Pi warehouse | Pi-local paths, no `users` (auth is the API's concern) |

### warehouse_config.json keys

| Key | Purpose |
|-----|---------|
| `tokens_dir` | Directory for QBO OAuth2 token file (`qbo_tokens.json`) |
| `sanitize[]` | List of `{source, dest}` pairs used by `warehouse/sanitize.sh` |
| `accounts` | Account definitions: `data_base` (CSV root path), `data_dirs` (service subdirs) |
| `hosts` | Staging/prod targets: `host` and `dir` per environment |
| `users` | User credentials (hashed passwords + account access lists) |

---

## Pi Warehouse

The Pi runs both the Docker API/nginx and an autonomous warehouse that downloads fresh data
nightly, rebuilds graphs locally, and pushes them to the Docker data dir (staging) and to
Lightsail prod.

### Directory layout on Pi

```
~/donorpipe/                               ← Docker runtime (managed by deploy.sh)
  data/oliveseed/graph.json                ← updated here by loopback rsync

~/donorpipe_warehouse/
  donorpipe/                               ← git clone; warehouse scripts run here
  primary_repository/oliveseed/            ← CSV data + graph.json (built by warehouse)
  download_tokens/                         ← qbo_tokens.json
  logs/
```

### Update warehouse code

After a deploy that changes warehouse scripts or Python dependencies:

```bash
./scripts/update-warehouse-pi.sh           # git pull + uv sync on Pi
```

`deploy-all.sh` runs this automatically.

### Run warehouse manually (on Pi)

```bash
ssh punkinpi.local
cd ~/donorpipe_warehouse/donorpipe
warehouse/update.sh --config warehouse/warehouse_pi_config.json nightly
```

### Systemd timer

The nightly timer runs `update.sh nightly` at 03:00 (±5 min) each day.

```bash
systemctl list-timers donorpipe-nightly.timer     # Check next run
journalctl -u donorpipe-nightly.service -f        # Follow logs
journalctl -u donorpipe-nightly.service -n 100    # Last 100 lines
```

---

## First-Time / One-Time Setup

### Staging Pi setup

**Docker runtime** (required before `deploy.sh`):

```bash
# On the Pi:
mkdir -p ~/donorpipe/data
# Copy staging_config.json to ~/donorpipe/config.json
# Create ~/donorpipe/.env with:
#   DONORPIPE_JWT_SECRET=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">
```

Then run `./scripts/deploy.sh` from your dev machine to ship the images.

**Warehouse** (one-time, after Docker is running):

```bash
# On the Pi:
mkdir -p ~/donorpipe_warehouse/{primary_repository/oliveseed,download_tokens,logs}
cd ~/donorpipe_warehouse
git clone <repo-url> donorpipe
cd donorpipe
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Copy .env with all API keys (STRIPE_API_KEY, DONORBOX_*, PAYPAL_*, QBO_*):
# scp .env punkinpi.local:~/donorpipe_warehouse/donorpipe/.env

# Copy QBO tokens:
# scp <tokens-dir>/qbo_tokens.json punkinpi.local:~/donorpipe_warehouse/download_tokens/

# Seed initial CSV data (operator step — live data):
# rsync -av <local-data>/ punkinpi.local:~/donorpipe_warehouse/primary_repository/

# Ensure Pi can SSH to itself (needed for loopback rsync to ~/donorpipe/data):
ssh-keyscan punkinpi.local >> ~/.ssh/known_hosts

# From dev machine, install and enable the systemd timer:
./scripts/provision-pi-warehouse.sh
```

### Production Lightsail provisioning

Prerequisites: static IP attached, ports 80+443 open in Lightsail firewall, DNS propagated, `prod_config.json` and `.env` ready locally.

```bash
./scripts/provision.sh donorpipe.trickybit.com
```

Installs Docker + certbot, obtains a TLS cert, and runs the initial deploy.

**Lightsail firewall rules** (AWS console → Lightsail → instance → Networking → IPv4 Firewall):

| Port | Protocol |
|------|----------|
| 22   | TCP (SSH) |
| 80   | TCP (HTTP) |
| 443  | TCP (HTTPS) |

**TLS cert renewal** runs automatically via cron. To test:
```bash
ssh ubuntu@donorpipe.trickybit.com "sudo certbot renew --dry-run"
```

### QBO OAuth2 token bootstrap

QBO uses OAuth2 with a 100-day refresh token. Initial tokens are obtained from the Intuit OAuth2 Playground. If the refresh token expires, repeat this procedure.

**Prerequisites:** `QBO_CLIENT_ID` and `QBO_CLIENT_SECRET` in `.env`, and `tokens_dir` set in `warehouse_config.json`.

1. Go to [Intuit OAuth2 Playground](https://developer.intuit.com/app/developer/playground)
2. Select your app, authorize, copy `access_token`, `refresh_token`, and `realmId`
3. Create `<tokens_dir>/qbo_tokens.json`:

```json
{
  "realm_id": "<realmId from Playground>",
  "access_token": "<access_token from Playground>",
  "refresh_token": "<refresh_token from Playground>",
  "token_expiry": "<UTC expiry as ISO 8601, e.g. 2026-03-18T12:00:00+00:00>"
}
```

The downloader automatically refreshes the access token (valid 1 hour) and rotates the refresh token on every use. If a refresh fails (token expired), re-run this bootstrap.

### User management

Users are defined in the environment's config file under `"users"`:

| Environment | Config file            |
|-------------|------------------------|
| Dev         | `config.json`          |
| Staging     | `staging_config.json`  |
| Production  | `prod_config.json`     |

Only `DONORPIPE_JWT_SECRET` (in `.env`) must stay out of the repo — hashed passwords are safe to commit.

```bash
# 1. Hash the password
uv run python scripts/hash_password.py <password>

# 2. Add or update the entry in the appropriate config:
#    "users": {
#      "username": {
#        "hashed_password": "<paste hash>",
#        "accounts": ["oliveseed"]
#      }
#    }
```

After updating staging or production config, run `push-config.sh` to push and restart the api.
