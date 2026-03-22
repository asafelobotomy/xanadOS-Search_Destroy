# AGENTS.md — xanadOS Search & Destroy

This repository keeps its shared AI-agent guidance in the files below.

## Primary Instruction Files

- `.github/copilot-instructions.md` — main GitHub Copilot operating instructions, workflow rules, and project overrides
- `CLAUDE.md` — concise repository guidance for Claude-based agents

## Supporting Agent Assets

- `.github/agents/` — agent definitions and handoff boundaries
- `.github/skills/` — on-demand skills and procedures
- `.github/prompts/` — reusable prompt files
- `.github/instructions/` — path-specific instruction stubs
- `.github/hooks/` — lifecycle hook configuration and scripts
- `.copilot/workspace/` — workspace heartbeat, identity, and memory files

## Repository Baseline

- Language: Python 3.13+
- Package manager: `uv`
- Test command: `uv run pytest`
- Type check: `uv run mypy app/`
- Lint: `uv run ruff check app/`
- Three-check ritual: `uv run pytest && uv run mypy app/ && uv run ruff check app/`

## Working Rule

Before changing repository files, read the relevant instruction file for the path you are editing and follow the process in `.github/copilot-instructions.md`.
