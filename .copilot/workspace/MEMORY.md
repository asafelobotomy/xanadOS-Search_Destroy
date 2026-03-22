# Memory Strategy — xanadOS Search & Destroy

> Guidelines for what to remember and how to organise knowledge.
> Coexists with VS Code's built-in `/memories/` system.

## Principles

1. **Prefer built-in memory** for cross-project preferences and user-wide settings.
2. **Use this file** for project-specific architectural decisions, recurring errors, team conventions, and known gotchas.
3. **Keep entries concise** — one line per fact when possible.
4. **Date entries** for freshness tracking.
5. **Prune stale entries** during heartbeat retrospectives.

## Coexistence with `/memories/`

| Scope | Where to store |
|-------|---------------|
| User preferences (cross-project) | `/memories/` (built-in) |
| Session-specific notes | `/memories/session/` (built-in) |
| Project architecture decisions | This file (MEMORY.md) |
| Project-specific gotchas | This file (MEMORY.md) |
| Repository conventions | `/memories/repo/` (built-in) |

## Architectural Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-21 | Template v4.0.0 installed | Full Lean/Kaizen Copilot template with hooks, skills, MCP |

## Recurring Error Patterns

| Date | Error | Root cause | Fix |
|------|-------|-----------|-----|
| | | | |

## Team Conventions

| Convention | Details |
|-----------|---------|
| Commits | Conventional Commits format |
| Imports | Absolute only |
| Errors | Never swallow — log or re-raise |
| Paths | pathlib for all path handling |
| Models | dataclass and TypedDict |

## Known Gotchas

| Date | Gotcha | Workaround |
|------|--------|-----------|
| 2026-03-21 | Terminal blocks chmod, xargs, find -exec | Use `git update-index --chmod=+x` or glob patterns |
| 2026-03-21 | .gitignore has `*secret*` pattern | Added negation for `.github/hooks/scripts/scan-secrets.sh` |

## Maintenance

- Review during heartbeat retrospectives
- Prune entries older than 90 days unless still relevant
- Merge duplicate entries
