# CLAUDE.md — xanadOS Search & Destroy

> This file provides context to Claude Code (claude.ai/code) when working in this repository.

## Project

**xanadOS Search & Destroy** — a Python security scanner and system protection suite for Linux.

## Quick Reference

| Item | Value |
|------|-------|
| Language | Python 3.13+ |
| Runtime | CPython |
| Package manager | uv |
| Test command | `uv run pytest` |
| Type check | `uv run mypy app/` |
| Lint | `uv run ruff check app/` |
| Format | `uv run ruff format app/` |
| Three-check | `uv run pytest && uv run mypy app/ && uv run ruff check app/` |

## Architecture

- `app/` — main application code (core scanning, API, GUI, ML, monitoring, reporting, utils)
- `tests/` — pytest test suite
- `config/` — configuration files (TOML, JSON, YARA rules)
- `docs/` — project documentation
- `scripts/` — build and utility scripts
- `models/` — ML model artifacts and metadata

## Conventions

- Absolute imports only
- No silent error swallowing — log or re-raise
- No commented-out code
- Functions do one thing
- File LOC: warn at 250, hard limit at 400
- Dependency budget: 40 runtime deps max
- All paths via `pathlib`

## Before Finishing

Always run the three-check ritual:

```bash
uv run pytest && uv run mypy app/ && uv run ruff check app/
```
