# Heartbeat — xanadOS Search & Destroy

> Event-driven health checks that keep the agent aligned with real project state.

## Pulse

`HEARTBEAT_OK`

## Triggers

Fire the heartbeat when:

- Session starts
- After modifying >5 files
- After any refactor, migration, or restructure task
- After dependency manifest changes
- After CI failure resolution
- After completing any user-requested task
- On the trigger phrase "Check your heartbeat"
- After template upgrade

## Checks

Run all checks when the heartbeat fires:

| # | Check | Command / Action | Pass criteria |
|---|-------|-----------------|---------------|
| C1 | Tests pass | `uv run pytest` | Exit 0 |
| C2 | Types pass | `uv run mypy app/` | Exit 0 |
| C3 | Lint passes | `uv run ruff check app/` | Exit 0 |
| C4 | Dep audit | Count runtime deps in `pyproject.toml` | ≤ 40 |
| C5 | Waste scan | Review recent changes for waste (§6) | No critical waste |
| C6 | Memory consolidation | Review MEMORY.md for stale entries | No entries >90 days |
| C7 | Metrics freshness | Compare LOC via `wc -l app/**/*.py \| tail -1` | Trending down or flat |
| C8 | Settings drift | Compare §10 values against actual project state | No drift |
| C9 | Agent compatibility | Verify agent files reference correct model names | All valid |

## Retrospective

Answer these questions internally after task completion or explicit trigger:

1. **Q1**: What changed? (files, LOC delta, deps)
2. **Q2**: Did any baseline get breached? If so, what action was taken?
3. **Q3**: What waste was eliminated or introduced?
4. **Q4**: What should the user know? (surface to user if non-empty)
5. **Q5**: What should be remembered for next time? (surface to user if non-empty)
6. **Q6**: Should SOUL.md be updated with new heuristics?
7. **Q7**: Should USER.md be updated with new observations?
8. **Q8**: Should MEMORY.md be updated with new facts?

Persist insights to the indicated workspace files. Surface Q4/Q5 to the user if non-empty.

## Agent Notes

> Notes for the next heartbeat. Written by the agent.

- Bootstrap completed 2026-03-21. First post-bootstrap heartbeat should verify all checks pass.

## History

> Keep last 5 entries.

| Date | Trigger | Pulse | Alerts |
|------|---------|-------|--------|
| 2026-03-21 | Bootstrap | HEARTBEAT_OK | Initial setup — checks not yet run |
