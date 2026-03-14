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

Runs `deploy.sh`, `push-config.sh`, and `warehouse/sync-data.sh oliveseed testdata` in sequence.

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
./warehouse/sync-graphs.sh oliveseed testdata

# 2. Sync graph.json to prod
PROD=1 ./warehouse/sync-graphs.sh oliveseed
```

The config passed to `build_graphs.sh` must have `data_base` pointing to the local path where CSVs live on the admin machine (not the server-side `/data/...` path). No API restart is needed after syncing — the route reads from disk on each request.

### Update data

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

Runs `deploy.sh`, `push-config.sh`, and `warehouse/sync-data.sh oliveseed testdata` in sequence.

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

```bash
./scripts/sync-data.sh       # Sync local data/ to Pi
```

---

## Warehouse (data sanitization + sync)

Config: `warehouse/warehouse_config.json` — defines sanitize operations, account→source mappings, and host targets.

### Refresh sanitized data

```bash
warehouse/sanitize.sh
```

Reads each entry in `sanitize[]` from config and runs `scripts/sanitize_csv.py source → dest` for each.

### Sync accounts to staging

```bash
warehouse/sync-data.sh <account> [account ...]
```

### Sync accounts to prod

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
