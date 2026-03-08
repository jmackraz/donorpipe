# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Management

This project uses [uv](https://docs.astral.sh/uv/) for dependency and environment management (Python 3.13+).

```bash
uv add <package>          # Add a dependency
uv run <command>          # Run a command in the project environment
uv sync                   # Sync dependencies from pyproject.toml
```

## Common Commands

```bash
uv run python -m pytest                                    # Run all tests
uv run python -m pytest tests/models/                     # Run model unit tests
uv run python -m pytest path/to/test_file.py::test_name  # Run a single test
uv run pyright src/donorpipe/                             # Type-check
uv run python -m ruff check .                             # Lint
uv run python -m ruff format .                            # Format
```

## New Dev Environment Setup

One-time steps when setting up a fresh clone:

**1. Install system tools** (if not already present):
```bash
# Install uv (Python package/env manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install bun (JS runtime/package manager)
curl -fsSL https://bun.sh/install | bash
```

**2. Install Python dependencies:**
```bash
uv sync
```

**3. Install frontend dependencies:**
```bash
cd frontend && bun install
```

**4. Create `.env`** in the project root with:
```
DONORPIPE_JWT_SECRET=<your-secret>
```
Generate a secret with: `python3 -c "import secrets; print(secrets.token_hex(32))"`

**5. Ensure `config.json`** exists in the project root (copy from a template or existing config; must have `"users"` and `"accounts"` keys and `"data_base"` pointing to a local data directory).

After these steps, `./scripts/dev.sh` should work.

---

## Running the Dev Environment

```bash
./scripts/dev.sh                                           # Start API + frontend; open http://localhost:5173
```

## Deployment

```bash
./scripts/deploy.sh                                        # Build images and deploy to Pi (PI_HOST=donorpipe.local)
PI_HOST=mypi.local ./scripts/deploy.sh                    # Deploy to a different host
```

**First-time Pi setup** (run once on the Pi before first deploy):
```bash
mkdir -p ~/donorpipe/data
# Copy config.json to ~/donorpipe/config.json; set data_base to "/data"
# Create ~/donorpipe/.env with: DONORPIPE_JWT_SECRET=<your-secret>
```

**Viewing logs on Pi:**
```bash
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose logs -f"        # All services
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose logs -f api"    # API only
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose logs -f nginx"  # Nginx only
```

**Restarting containers on Pi:**
```bash
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose restart"                                    # Restart without recreating
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose down && docker compose up -d && docker compose logs -f"  # Full restart + stream logs
ssh jim@$PI_HOST "cd ~/donorpipe && docker compose ps"             # Check container status
ssh jim@$PI_HOST "curl -s http://localhost:8000/health"            # Check API directly
```

**Updating data files on Pi:**
```bash
rsync -av --delete ./data/ jim@$PI_HOST:~/donorpipe/data/  # Sync local data/ to Pi
```

This starts both servers and prints the URL. Press Ctrl+C to stop both.

### Individual servers

```bash
uv run fastapi dev src/donorpipe/api/app.py               # API only (port 8000)
uv run python scripts/fetch_graph.py --account my_org     # Fetch graph summary
uv run python scripts/fetch_graph.py --account my_org --json  # Fetch full JSON
uv run python scripts/hash_password.py <password>         # Hash a password for config.json
```

## User Management

Users are stored in `config.json` under the `"users"` key alongside accounts. Only
`DONORPIPE_JWT_SECRET` (in `.env`) must stay out of the repo — hashed passwords are safe to commit.

**Add a new user or change a password:**
```bash
# 1. Hash the password
uv run python scripts/hash_password.py <newpassword>

# 2. Add or update the entry in config.json:
#    "users": {
#      "username": {
#        "hashed_password": "<paste hash>",
#        "accounts": ["my_org"]
#      }
#    }
```

`accounts` lists the account IDs (keys under `"accounts"`) the user can access.

## Frontend (TypeScript / Bun)

```bash
cd frontend
bun test                                                   # Run all TS tests
bun run typecheck                                          # tsc -b --noEmit
bun run dev                                                # Start Vite dev server (port 5173)
bun run build                                              # Production build

# Fetch graph from running API (mirrors the Python script above)
bun scripts/fetch_graph.ts --account my_org               # Print entity counts
bun scripts/fetch_graph.ts --account my_org --json        # Print full JSON
bun scripts/fetch_graph.ts --account my_org --base-url http://localhost:8000
```

Config is read from `config.json` by default. Override with `DONORPIPE_CONFIG=/path/to/config.json`.

## Project
Read PROJECT.md for a high-level definition of the project.
Read MILESTONES.md for the development plan
When needed, find Snippets in docs/SCRATCH.md
When needed, information about entity relationships is in docs/relationships.md
When needed, high-level information about the UI is in docs/webui_spec.md


## Guidelines
* When I ask you to modify a file or files, ask before changing any other files.
* As we add functionality, update the 'run' instructions to include new tools
and command-line scripts.
* When a milestone is committed as done, move its spec from `MILESTONES.md` to
`docs/COMPLETED_MILESTONES.md`.
* When a new dev of ops shell command is added, document it in `CLAUDE.md`
* Don't commit without asking or being explicitly instructed

## Frontend Notes
* Amounts are stored as floats (dollars). Filter inputs from the user are in dollars and can be compared directly.
* Virtual scroll uses a fixed row height of 48px with overscan 8 (`useVirtualizer`).