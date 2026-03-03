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
uv run python -m pytest           # Run all tests
uv run python -m pytest path/to/test_file.py::test_name  # Run a single test
uv run python -m ruff check .     # Lint
uv run python -m ruff format .    # Format
```

## Project
Read PROJECT.md for a high-level definition of the project.
Reade MILESTONES.md for the development plan