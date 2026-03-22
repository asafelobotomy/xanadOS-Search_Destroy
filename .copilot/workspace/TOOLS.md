# Tools & Commands — xanadOS Search & Destroy

> Quick reference for project commands and tool configurations.
> Updated by the agent as new tools are discovered.

## Core Commands

| Purpose | Command |
|---------|---------|
| Run tests | `uv run pytest` |
| Type check | `uv run mypy app/` |
| Lint | `uv run ruff check app/` |
| Format | `uv run ruff format app/` |
| Three-check | `uv run pytest && uv run mypy app/ && uv run ruff check app/` |
| Count LOC | `wc -l app/**/*.py \| tail -1` |
| Install deps | `uv sync` |
| Add dep | `uv add <package>` |
| Run app | `uv run python -m app` |

## Toolbox

> Reusable tools saved to `.copilot/tools/`. See `INDEX.md` in that directory.

| Tool | Purpose | Trust |
|------|---------|-------|
| | | |

## Discovered Workflow Patterns

> Workflows and shortcuts noticed during sessions.

| Pattern | Details |
|---------|---------|
| Terminal restrictions | `chmod`, `xargs`, `find -exec` blocked by policy — use git or glob alternatives |

## Extension Registry

> VS Code extensions relevant to this project.

| Extension | Purpose |
|-----------|---------|
| charliermarsh.ruff | Python linting and formatting |
| ms-python.python | Python language support |
| ms-python.mypy-type-checker | Type checking |
