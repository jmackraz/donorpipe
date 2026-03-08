# DonorPipe Operations

This document covers running, deploying, and managing DonorPipe across environments.

---

## Production

> **Status:** Not yet deployed. See [Milestone 13](../MILESTONES.md) for the planned AWS Lightsail deployment.

Planned URL: `https://<domain>` (TBD)

Deploy command (same as staging, targeting the production host):
```bash
PI_HOST=<prod-host> ./scripts/deploy.sh
```

---

## Staging (Pi)

The staging environment runs on a Raspberry Pi at `donorpipe.local`.

**URL:** http://donorpipe.local

### Deploy

```bash
./scripts/deploy.sh                                        # Build and deploy to Pi (PI_HOST=donorpipe.local)
PI_HOST=mypi.local ./scripts/deploy.sh                    # Deploy to a different host
```

### First-time Pi setup (run once on the Pi)

```bash
mkdir -p ~/donorpipe/data
# Copy staging_config.json to ~/donorpipe/config.json; set data_base to "/data"
# Create ~/donorpipe/.env with: DONORPIPE_JWT_SECRET=<your-secret>
```

### Logs

```bash
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose logs -f"        # All services
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose logs -f api"    # API only
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose logs -f nginx"  # Nginx only
```

### Restart

```bash
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose restart"                                     # Restart without recreating
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose down && docker compose up -d && docker compose logs -f"  # Full restart + stream logs
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose ps"             # Check container status
ssh jim@$PI_HOST "curl -s http://localhost:8000/health"            # Check API directly
```

### Update config

```bash
rsync -av staging_config.json jim@$PI_HOST:~/donorpipe/config.json
```

### Update data

```bash
rsync -av --delete ./data/ jim@$PI_HOST:~/donorpipe/data/          # Sync local data/ to Pi
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
