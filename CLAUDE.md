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

## Running the Dev Environment

```bash
./scripts/dev.sh                                           # Start API + frontend; open http://localhost:5173
```

This starts both servers and prints the URL. Press Ctrl+C to stop both.

### Individual servers

```bash
uv run fastapi dev src/donorpipe/api/app.py               # API only (port 8000)
uv run python scripts/fetch_graph.py --account my_org     # Fetch graph summary
uv run python scripts/fetch_graph.py --account my_org --json  # Fetch full JSON
```

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

## Frontend Notes
* Amounts are stored as integers (cents). Filter inputs from the user are in dollars
and must be multiplied by 100 before comparison.
* Virtual scroll uses a fixed row height of 48px with overscan 8 (`useVirtualizer`).