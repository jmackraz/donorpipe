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

### CLI with local test data

`OSF_EXPORTS` normally points to Google Drive (set in shell environment). Override it to use `testdata/` locally:

```bash
env OSF_EXPORTS=testdata uv run src/donorpipe/cli/model_cli.py -d Stripe DonorBox QBO
```

Note: `testdata/` has Stripe, DonorBox, and QBO — no Paypal dir (omit it). Missing dirs are handled gracefully.

> **TODO (laptop setup):** Copy this `OSF_EXPORTS` override pattern to `~/.claude/CLAUDE.md` so it's available across all projects on the new machine.

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

## Environment Variables

### Backend (Python)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DONORPIPE_JWT_SECRET` | Yes | — | Secret key for signing/verifying JWT auth tokens. Generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`. Set in `.env`. |
| `DONORPIPE_CONFIG` | No | `config.json` | Path to the config file. Defaults to `config.json` in the working directory. |
| `OSF_EXPORTS` | No | — | Base directory prepended to relative data dir args. In production this points to Google Drive. Override with `testdata/` for local development (see CLI example above). |
| `DONORPIPE_HELP` | No | `docs/help.md` | Path to the Markdown file served as in-app help content. |

### Frontend (Vite/TypeScript)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | No | `""` (same origin) | Base URL for API requests. Leave unset when the frontend is served by the same server. Set to e.g. `http://localhost:8000` for local frontend-only dev against a separate API process. |

### Warehouse Downloaders (`warehouse/downloads/`)

These variables enable the automated download services. Set in `.env`. Services without
credentials are skipped silently. `tokens_dir` in `warehouse_config.json` must also be set
for QBO.

| Variable | Required for | Description |
|---|---|---|
| `STRIPE_API_KEY` | Stripe | Stripe secret API key |
| `DONORBOX_EMAIL` | DonorBox | Org login email |
| `DONORBOX_API_KEY` | DonorBox | DonorBox API key |
| `PAYPAL_CLIENT_ID` | PayPal | PayPal app client ID |
| `PAYPAL_SECRET_KEY` | PayPal | PayPal OAuth2 client secret |
| `QBO_CLIENT_ID` | QBO | Intuit app client ID |
| `QBO_CLIENT_SECRET` | QBO | Intuit app client secret |

QBO also requires `tokens_dir` set in `warehouse_config.json` pointing to a directory
containing `qbo_tokens.json` (see `docs/OPERATIONS.md` for bootstrap procedure).

### Scripts (`scripts/*.sh`)

These variables control which host the deployment/ops scripts target. All have sensible defaults.

| Variable | Default | Description |
|---|---|---|
| `PROD` | `0` | Set to `1` to target production instead of the staging host (`punkinpi.local`). |
| `DPIPE_HOST` | `punkinpi.local` (staging) or `ubuntu@donorpipe.trickybit.com` (prod) | SSH target host. Override to deploy to a different machine. |
| `DPIPE_USER` | `""` (staging) or `ubuntu` (prod) | SSH user. Prepended to `DPIPE_HOST` if non-empty. |
| `DPIPE_DIR` | `~/donorpipe` | Remote directory where the app is installed. |
| `DPIPE_DEV_CONFIG` | `warehouse/warehouse_config.json` | Config file used by `scripts/dev.sh`. Override to run against a different local config (e.g. `config.json` for testdata). |

### Warehouse Poller (`warehouse/poll_refresh.sh`)

Required on the Pi for the on-demand refresh feature. Set in `.env`.

| Variable | Required | Description |
|---|---|---|
| `DPIPE_SERVICE_USER` | Yes | Username for the warehouse API service account |
| `DPIPE_SERVICE_PASS` | Yes | Password for the warehouse API service account |
| `DPIPE_API_BASE` | Yes | Space-separated API base URLs to poll (e.g. `"https://staging.url https://donorpipe.trickybit.com"`). Single URL also works. |
| `DPIPE_POLL_INTERVAL` | No | Seconds between polls (default: 30) |

## Project
Read PROJECT.md for a high-level definition of the project.
Read MILESTONES.md for the development plan
Read docs/OPERATIONS.md for running, deploying, and managing users across environments.
When needed, find Snippets in docs/SCRATCH.md
When needed, information about entity relationships is in docs/relationships.md
When needed, high-level information about the UI is in docs/webui_spec.md

## Guidelines
* When we add or modify keyboard shortcuts, update that section of docs/help.md

## Key Requirement
This application processes reports of charitable donation activity.  The "real data" exported or fectched
from the various services contains personal information, including names, addresses, emails, philanthropic interests,
personal notes and so on.
* The agent is not to consume real data.
* This includes but is not limited to exported report files, payloads returned from service APIs,
our serialized graph created from the reports.
* The operator will test, compare or pull information out of real files as needed.



## Frontend Notes
* Amounts are stored as floats (dollars). Filter inputs from the user are in dollars and can be compared directly.
* Virtual scroll uses a fixed row height of 48px with overscan 8 (`useVirtualizer`).