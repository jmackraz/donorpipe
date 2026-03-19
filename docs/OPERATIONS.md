# DonorPipe Operations

This document covers running, deploying, and managing DonorPipe across environments.

---

## Production

**URL:** https://donorpipe.trickybit.com
**Host:** AWS Lightsail — `ubuntu@donorpipe.trickybit.com`

### Lightsail firewall rules

In the AWS console → Lightsail → instance → **Networking** tab → **IPv4 Firewall**, ensure these ports are open:

| Port | Protocol |
|------|----------|
| 22   | TCP (SSH) |
| 80   | TCP (HTTP) |
| 443  | TCP (HTTPS) |

### First-time setup (run once, locally)

Prerequisites: static IP attached, ports 80+443 open in Lightsail firewall, DNS propagated, `prod_config.json` and `.env` ready locally.

```bash
./scripts/provision.sh donorpipe.trickybit.com
```

This installs Docker + certbot on the host, obtains a TLS cert, and does the initial deploy.

### Deploy

```bash
PROD=1 ./scripts/deploy.sh
```

Builds images for `linux/amd64` locally, ships them to the host, and restarts containers with the prod compose override (TLS on port 443).

### Full deploy (app + config + data)

```bash
PROD=1 ./scripts/deploy-all.sh
```

Runs `deploy.sh`, `push-config.sh`, and `warehouse/sync-graphs.sh oliveseed test_org` in sequence.

### Logs / Restart

```bash
PROD=1 ./scripts/logs.sh             # All services
PROD=1 ./scripts/logs.sh api         # API only
PROD=1 ./scripts/restart.sh          # Restart all
PROD=1 ./scripts/restart.sh api      # Restart api only
```

### Build and deploy pre-built graphs

Build `graph.json` from local CSVs (admin machine), then sync to the server. Once deployed, the API serves from the pre-built file on each request — no CSV parsing, no CSV files needed on the server.

```bash
# 1. Build graph.json for all accounts (uses data_base paths from the config)
./scripts/build_graphs.sh --config <local-build-config.json>

# Or build a specific account:
./scripts/build_graphs.sh --config <local-build-config.json> oliveseed

# 2. Sync graph.json to staging
./warehouse/sync-graphs.sh oliveseed test_org

# 2. Sync graph.json to prod
PROD=1 ./warehouse/sync-graphs.sh oliveseed
```

The config passed to `build_graphs.sh` must have `data_base` pointing to the local path where CSVs live on the admin machine (not the server-side `/data/...` path). No API restart is needed after syncing — the route reads from disk on each request.

### Update data

**OBSOLETE** We don't push the data we push the derived graphs
Real data:
```bash
PROD=1 ./scripts/sync-data.sh
```

Sanitized fake data to test/demo account:
```bash
PROD=1 ./scripts/sync-test-data.sh
```

### Update config

```bash
PROD=1 ./scripts/push-config.sh
```

Copies `prod_config.json` to the host and restarts the api container.

### Update help docs

```bash
PROD=1 ./scripts/push-help.sh
```

Copies `docs/help.md` to the host. No container restart needed — the API reads the file on each request.

### TLS cert renewal

Renewal runs automatically via cron (`/etc/cron.d/certbot-renew`). To test manually:
```bash
ssh ubuntu@donorpipe.trickybit.com "sudo certbot renew --dry-run"
```

---

## Staging (Pi)

The staging environment runs on a Raspberry Pi at `punkinpi.local`.

**URL:** http://punkinpi.local

### Deploy

```bash
./scripts/deploy.sh                                        # Build and deploy to Pi (DPIPE_HOST=punkinpi.local)
DPIPE_HOST=mypi.local ./scripts/deploy.sh                 # Deploy to a different host
DPIPE_USER=ubuntu ./scripts/deploy.sh                     # Deploy with a specific SSH user (prod defaults to ubuntu)
```

### First-time Pi setup (run once on the Pi)

```bash
mkdir -p ~/donorpipe/data
# Copy staging_config.json to ~/donorpipe/config.json; set data_base to "/data"
# Create ~/donorpipe/.env with: DONORPIPE_JWT_SECRET=<your-secret>
```

### Full deploy (app + config + data)

```bash
./scripts/deploy-all.sh
```

Runs `deploy.sh`, `push-config.sh`, and `warehouse/sync-graphs.sh oliveseed test_org` in sequence.

### Logs

```bash
./scripts/logs.sh            # All services
./scripts/logs.sh api        # API only
./scripts/logs.sh nginx      # Nginx only
```

### Restart

```bash
./scripts/restart.sh         # Restart all containers
./scripts/restart.sh api     # Restart api only
```

### Update config

```bash
./scripts/push-config.sh
```

Copies `staging_config.json` to the host and restarts the api container.

### Update data

**OBSOLETE** We don't push the data we push the derived graphs
```bash
./scripts/sync-data.sh       # Sync local data/ to Pi
```

---

## Warehouse (data sanitization + sync)

Config: `warehouse/warehouse_config.json` — defines sanitize operations, account→source mappings, and host targets.

### Download fresh data

```bash
warehouse/download.sh <account_id>
warehouse/download.sh --year 2025 <account_id>
```

Fetches CSVs from external services (Stripe, DonorBox, etc.) into the given account's `data_base` directory. Exactly one account must be specified. API keys must be set in `.env`; services without a key are skipped silently. Only use for real data accounts — sanitized accounts are refreshed via `warehouse/sanitize.sh`.

Note: all services download the same data regardless of account. The account argument determines where files land. Multi-account download support will require per-account download configuration when the time comes.

### QBO token setup (one-time + renewal)

QBO uses OAuth2 with a 100-day refresh token. Initial tokens are obtained from the Intuit
OAuth2 Playground; if the refresh token expires, this procedure must be repeated.

**Prerequisites:** `QBO_CLIENT_ID` and `QBO_CLIENT_SECRET` set in `.env`, and `tokens_dir`
set in `warehouse_config.json`.

**Bootstrap procedure:**
1. Go to [Intuit OAuth2 Playground](https://developer.intuit.com/app/developer/playground)
2. Select your app, authorize, and copy the `access_token`, `refresh_token`, and `realmId`
3. Create `<tokens_dir>/qbo_tokens.json`:
```json
{
  "realm_id": "<realmId from Playground>",
  "access_token": "<access_token from Playground>",
  "refresh_token": "<refresh_token from Playground>",
  "token_expiry": "<UTC expiry as ISO 8601, e.g. 2026-03-18T12:00:00+00:00>"
}
```

The downloader automatically refreshes the access token (valid 1 hour) using the refresh
token and writes updated values back to the file. The refresh token itself is valid for
100 days; the downloader rotates it on every use.

**If a refresh fails** (e.g. the refresh token has expired), the download will fail with
a clear error message. Repeat the bootstrap procedure to get fresh tokens.

### Rebuild and sync changed graphs

```bash
# Sync to staging (normal frequent run):
warehouse/refresh.sh [account_id ...]

# Sync to staging, then prod only if staging actually synced:
warehouse/refresh.sh [accounts] && PROD=1 warehouse/refresh.sh --sync-only [accounts]

# Sync to prod unconditionally (skip rebuild, e.g. after a manual build):
PROD=1 warehouse/refresh.sh --sync-only [account_id ...]
```

Checks each account's data directory for changes since the last build. Rebuilds `graph.json` and syncs to staging only for accounts whose data has changed. Processes all accounts in the config if none are specified. Safe to run frequently — exits 1 (no-op) when nothing has changed, 0 when it synced.

`--sync-only` skips change detection and build; goes straight to sync. The `&&` pattern uses the exit code to gate the prod sync: if staging found no changes (exit 1), prod is skipped too.

Intended workflow: run `download.sh` on a longer schedule (e.g. hourly), and `refresh.sh` on a shorter schedule (e.g. every few minutes) to pick up both scheduled and manual downloads promptly.

### Refresh sanitized data

```bash
warehouse/sanitize.sh
```

Reads each entry in `sanitize[]` from config and runs `scripts/sanitize_csv.py source → dest` for each.

### Sync accounts to staging

**OBSOLETE** We don't push the data we push the derived graphs
```bash
warehouse/sync-data.sh <account> [account ...]
```

### Sync accounts to prod
**OBSOLETE** We don't push the data we push the derived graphs

```bash
PROD=1 warehouse/sync-data.sh <account> [account ...]
```

---

## Dev

**URL:** http://localhost:5173

### Start

```bash
./scripts/dev.sh                                           # Start API + frontend
```

Press Ctrl+C to stop both servers.

### Individual servers

```bash
uv run fastapi dev src/donorpipe/api/app.py               # API only (port 8000)
uv run python scripts/fetch_graph.py --account my_org     # Fetch graph summary
uv run python scripts/fetch_graph.py --account my_org --json  # Fetch full JSON

bun scripts/fetch_graph.ts --account my_org               # Same via TS script
bun scripts/fetch_graph.ts --account my_org --json
bun scripts/fetch_graph.ts --account my_org --base-url http://localhost:8000
```

---

## User Management

Users are defined in the environment's config file under the `"users"` key:

| Environment | Config file            |
|-------------|------------------------|
| Dev         | `config.json`          |
| Staging     | `staging_config.json`  |
| Production  | `prod_config.json`     |

Only `DONORPIPE_JWT_SECRET` (in `.env`) must stay out of the repo — hashed passwords are safe to commit.

### Add or change a user's password

```bash
# 1. Hash the password
uv run python scripts/hash_password.py <password>

# 2. Add or update the entry in the appropriate config file:
#    "users": {
#      "username": {
#        "hashed_password": "<paste hash>",
#        "accounts": ["my_org"]
#      }
#    }
```

`accounts` lists the account IDs (keys under `"accounts"`) the user can access.

After updating staging or production config, push the file to the server and restart the API container.
