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
Read docs/OPERATIONS.md for running, deploying, and managing users across environments.
When needed, find Snippets in docs/SCRATCH.md
When needed, information about entity relationships is in docs/relationships.md
When needed, high-level information about the UI is in docs/webui_spec.md


## Frontend Notes
* Amounts are stored as floats (dollars). Filter inputs from the user are in dollars and can be compared directly.
* Virtual scroll uses a fixed row height of 48px with overscan 8 (`useVirtualizer`).