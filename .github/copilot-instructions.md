# Copilot Instructions — xanadOS Search & Destroy

> **Template version**: 4.0.0 <!-- x-release-please-version --> | **Applied**: 2026-03-21
> Living document — self-edit rules in §8.
>
> **Models**: each `.github/agents/*.agent.md` pins its model. Codex models are headless-only (no interactive prompts). See [model comparison](https://docs.github.com/en/copilot/reference/ai-models/model-comparison).
>
> **⚡ Critical Reminders** — every session, every task:
>
> 1. **Test** — run `uv run pytest` before marking any task done (§3).
> 2. **PDCA** — Plan→Do→Check→Act for every non-trivial change (§5).
> 3. **Read first** — never claim or modify a file not opened this session (§4).
> 4. **Additive** — never delete existing rules without explicit user instruction (§8).

## §1 — Lean Principles

| # | Principle | This project |
|---|-----------|-------------|
| 1 | Eliminate waste (Muda) | Every line of code has a cost; every unused feature is waste |
| 2 | Map the value stream | Threat detected → file scanned → classified → reported → resolved |
| 3 | Create flow | CLI/GUI input → scan engine → ML classification → report generation → remediation |
| 4 | Establish pull | Build only what is needed, when it is needed |
| 5 | Seek perfection | Small, continuous improvements (Kaizen) over big rewrites |

**Waste taxonomy** (§6):

- Overproduction · Waiting · Transport · Over-processing · Inventory · Motion · Defects · Unused talent

---

## §2 — Operating Modes

Switch modes explicitly. Default is **Implement**.

### Implement Mode (default)

- Plan → implement → test → document in one uninterrupted flow.
- Full PDCA for every non-trivial change.
- Three-check ritual before marking a task complete.

### Review Mode

- Read-only by default. State findings before proposing fixes.
- Tag every finding with a waste category (§6).
- Use format: `[severity] | [file:line] | [waste category] | [description]`
- Severity: `critical` | `major` | `minor` | `advisory`

  <examples>
  `[critical] | [app/core/api_security_gateway.py:42] | [W7 Defects] | SQL query built by string concatenation — injection risk; use parameterised queries`
  `[minor] | [app/utils/format.py:18] | [W4 Over-processing] | One-liner wrapped in a function with no added value — consider inlining`
  </examples>

#### On-Demand Review Skills

For deeper audits, activate the matching skill (§12) instead of expanding §2:

- **Extension audits** → `extension-review` skill · **Test coverage** → `test-coverage-review` skill
- Present report first; wait for approval before writing files.

### Refactor Mode

- No behaviour changes. Tests must pass before and after.
- Measure LOC delta. Flag if a refactor increases LOC without justification.

### Planning Mode

- Produce a task breakdown before writing code.
- Estimate complexity (S/M/L/XL). Flag anything XL for decomposition.

---

## §3 — Standardised Work Baselines

| Baseline | Value | Action if exceeded |
|----------|-------|--------------------|
| File LOC (warn) | 250 lines | Flag, suggest decomposition |
| File LOC (hard) | 400 lines | Refuse to extend; decompose first |
| Dependency budget | 40 runtime deps | Propose removal before adding |
| Dependency budget (warn) | 35 runtime deps | Flag for review |
| Test command | `uv run pytest` | Must pass before task is done |
| Type check | `uv run mypy app/` | Must pass before task is done |
| Three-check ritual | `uv run pytest && uv run mypy app/ && uv run ruff check app/` | Run before marking complete |
| Integration test gate | RUN_INTEGRATION_TESTS | Set to run integration tests |
| Max subagent depth | 3 | Stop and report to user |

---

## §4 — Coding Conventions

- Language: **Python** · Runtime: **CPython 3.13+** · Package manager: **uv**
- Test framework: **pytest**
- Preferred serialisation: **JSON**

**Patterns observed in this codebase**:

- PyQt6 GUI with signal/slot patterns
- FastAPI async endpoints with dependency injection
- click CLI decorators for command-line interface
- dataclass and TypedDict models for structured data
- pathlib for all path handling

**Universal rules**:

- No `any` / untyped unless explicitly commented with `# deliberately untyped: <reason>`.
- No silent error swallowing — log or re-throw.
- No commented-out code — git history is the undo stack.
- Imports are grouped: stdlib → third-party → internal. One blank line between groups.
- Functions do one thing. If you need "and" in the name, split it.
- Read before claiming — never describe, reference, or modify a file not opened this session.
  `semantic_search` or `grep_search` confirms existence; reading the file confirms content.

---

## §5 — PDCA Cycle

Apply to every non-trivial change.

**Plan**: State the goal. List the files that will change. Estimate LOC delta.
**Do**: Implement. Write tests alongside code, not after.
**Check**: Run `uv run pytest`. Review output. Fix before proceeding.
**Act**: If baseline exceeded, address it now. Summarise what changed.

---

## §6 — Waste Catalogue (Muda)

Tag Review Mode findings with these codes:

W1 Overproduction · W2 Waiting · W3 Transport · W4 Over-processing · W5 Inventory · W6 Motion · W7 Defects · W8 Unused talent · W9 Prompt waste · W10 Context window waste · W11 Hallucination rework · W12 Verification overhead · W13 Prompt engineering debt · W14 Model-task mismatch · W15 Tool friction · W16 Over/under-trust

---

## §7 — Metrics

| Metric | Command | Target |
|--------|---------|--------|
| Total LOC | `wc -l app/**/*.py \| tail -1` | Trending down or flat |
| Test count | `uv run pytest` | Trending up |
| Type errors | `uv run mypy app/` (or `get_errors` built-in) | Zero |
| Runtime deps | count from manifest | ≤ 40 |

---

## §8 — Living Update Protocol

Copilot may edit this file when patterns stabilise. Rules:

1. **Never delete** existing rules without explicit user instruction.
2. **Additive by default** — append to sections; don't restructure them.
3. **Flag before writing** — describe the change and wait for confirmation on edits to §1–§7.
4. **Self-update trigger phrases**: "Add this to your instructions", "Remember this for next time" — these add a convention to this file.
5. **Template updates**: When the user says **"Update your instructions"** (or any variant listed in the Canonical triggers table of `AGENTS.md`), this means: go to the upstream template repository at `https://github.com/asafelobotomy/copilot-instructions-template`, fetch the latest version, compare it against the installed version, and run the update protocol defined in `UPDATE.md`. This is not a request to make arbitrary edits — it is specifically a check-for-upstream-updates command.

### Attention Budget

This file is loaded into the LLM context on every interaction. To prevent instruction-following degradation from context dilution:

| Scope | Budget | Enforced by |
|-------|--------|-------------|
| **Entire file** (§1–§13) | ≤ 800 lines | CI (`ci.yml`) |
| **§2 (Operating Modes)** | ≤ 210 lines | CI (`ci.yml`) — largest section; contains all workflow modes |
| **Other §1–§9 sections** | ≤ 120 lines each | CI (`ci.yml`) |
| **§10 (Project-Specific Overrides)** | No hard limit | Grows with project — review during heartbeat |
| **§11–§13 (protocols)** | ≤ 150 lines each | CI (`ci.yml`) |

**Overflow rule**: When a section approaches its budget, extract detailed procedures into a skill file (`.github/skills/`), a path-specific instruction file (`.github/instructions/`), or a prompt file (`.github/prompts/`). Leave a one-line reference in the main section. This keeps the always-loaded context tight while preserving the detail in on-demand files.

**Why this matters**: LLMs exhibit attention degradation in long contexts — content in the middle of a large prompt receives less focus than content near the start or end. Keeping the core instructions concise ensures every rule gets reliable attention.

### Heartbeat Protocol

Event-triggered health checks that keep the agent aligned with real project state. The heartbeat checklist lives in `.copilot/workspace/HEARTBEAT.md`.

**When to fire**: session start; after modifying >5 files; after any refactor, migration, or restructure task; after dependency manifest changes; after CI failure resolution; after completing any user-requested task; on the trigger phrase "Check your heartbeat"; or on any custom trigger defined in `HEARTBEAT.md`.

**Procedure**:

1. Read `HEARTBEAT.md` — follow it strictly. Do not infer tasks from prior sessions.
2. Run every check in the Checks section. Cross-reference: MEMORY.md (consolidation), TOOLS.md (dependency audit), SOUL.md (reasoning alignment), §10 (settings drift).
3. If the trigger is **task completion** or **explicit**, run the Retrospective section: answer each question internally, persist insights to the indicated workspace files (SOUL.md, USER.md, MEMORY.md), and surface Q4/Q5 to the user if non-empty.
4. Update Pulse: `HEARTBEAT_OK` if all checks pass; prepend `[!]` with a one-line alert for each failure.
5. Append a row to History (keep last 5).
6. Write observations to Agent Notes for the next heartbeat.
7. Report to user only if alerts exist — silent when healthy (exception: retrospective Q4/Q5 always surface when non-empty).
8. **Context limit**: if context pressure is high, run `save-context.sh`, append a resume note to Agent Notes, then continue — never abandon a task mid-flight.

### Agent Hooks

Hooks are deterministic shell commands that VS Code executes at specific lifecycle points during an agent session. Unlike instructions (soft guidance), hooks run your code with guaranteed outcomes — they enforce rules that the agent would otherwise follow probabilistically.

Hook configuration lives in `.github/hooks/copilot-hooks.json`. VS Code supports eight lifecycle events. The template ships seven starter hooks:

| Event | Script | Purpose |
|-------|--------|---------|
| `SessionStart` | `session-start.sh` | Inject project context (name, version, branch, runtimes, heartbeat pulse) |
| `PreToolUse` | `guard-destructive.sh` | Block dangerous commands; flag caution patterns for user confirmation (§5 enforcement) |
| `PostToolUse` | `post-edit-lint.sh` | Auto-format edited files using the project's formatter |
| `Stop` | `enforce-retrospective.sh` | Prevent session end if retrospective has not been run |
| `PreCompact` | `save-context.sh` | Preserve workspace state (heartbeat, memory, heuristics) before context compaction |
| `SubagentStart` | `subagent-start.sh` | Inject governance context (depth limit, inherited protocols) when a subagent spawns |
| `SubagentStop` | `subagent-stop.sh` | Log subagent completion and prompt result review |

---

## §9 — Subagent Protocol

When spawning subagents:

- Each `.github/agents/*.agent.md` declares an `agents:` allow-list restricting which subagents it may invoke. Respect these boundaries.
- Pass the full contents of this file as system context.
- Set `max_depth = 3`. Stop and surface to user if reached.
- Each subagent must run the three-check ritual before reporting done.
- Each subagent inherits the full Tool Protocol (§11), Skill Protocol (§12), and MCP Protocol (§13) — check the toolbox before building, search before coding, and flag any proposed toolbox saves to the parent.
- Subagent output must include: files changed, LOC delta, test result, any baseline breaches.

### Organization-Level Agents

GitHub organizations can publish shared agents via a `.github-private` repository with an `agents/` directory. These run alongside project-level agents. When both exist, project-level agents take precedence for same-name conflicts. The `organizationCustomAgents.enabled` VS Code setting must be on for org agents to load. See the **skill-management** skill for the full scope hierarchy.

---

## §10 — Project-Specific Overrides

Resolved values and project-specific overrides. Populated during setup; updated via §8.

<project_config>

| Config key | Resolved value |
|------------|----------------|
| `PROJECT_NAME` | xanadOS Search & Destroy |
| `LANGUAGE` | Python |
| `RUNTIME` | CPython 3.13+ |
| `PACKAGE_MANAGER` | uv |
| `TEST_COMMAND` | uv run pytest |
| `TYPE_CHECK_COMMAND` | uv run mypy app/ |
| `THREE_CHECK_COMMAND` | uv run pytest && uv run mypy app/ && uv run ruff check app/ |
| `LOC_COMMAND` | wc -l app/**/*.py \| tail -1 |
| `METRICS_COMMAND` | uv run pytest --tb=short && uv run mypy app/ && uv run ruff check app/ |
| `TEST_FRAMEWORK` | pytest |
| `LOC_WARN_THRESHOLD` | 250 |
| `LOC_HIGH_THRESHOLD` | 400 |
| `DEP_BUDGET` | 40 |
| `DEP_BUDGET_WARN` | 35 |
| `INTEGRATION_TEST_ENV_VAR` | RUN_INTEGRATION_TESTS |
| `PREFERRED_SERIALISATION` | JSON |
| `SUBAGENT_MAX_DEPTH` | 3 |
| `VALUE_STREAM_DESCRIPTION` | Threat detected → file scanned → classified → reported → resolved |
| `FLOW_DESCRIPTION` | CLI/GUI input → scan engine → ML classification → report generation → remediation |
| `PROJECT_CORE_VALUE` | Protecting Linux systems from malware and security threats |
| `SETUP_DATE` | 2026-03-21 |
| `SKILL_SEARCH_PREFERENCE` | Auto |
| `TRUST_OVERRIDES` | Default tiers (no custom overrides) |
| `MCP_STACK_SERVERS` | filesystem, git, github, fetch |
| `MCP_CUSTOM_SERVERS` | none |

</project_config>

### Verification Levels

The Graduated Trust Model assigns verification behaviour based on path patterns. Higher-trust paths allow Copilot to act with less friction; lower-trust paths require explicit approval.

| Trust tier | Default paths | Verification behaviour |
|-----------|--------------|----------------------|
| High | `tests/`, `__tests__/`, `*.test.*`, `*.spec.*`, `docs/`, `*.md` | Auto-approve: Copilot acts freely. Changes are summarised after the fact. |
| Standard | `src/`, `lib/`, `app/`, `packages/` | Review: Copilot describes the planned change and waits for approval before writing. |
| Guarded | `*.config.*`, `.*rc`, `.github/`, `.env*`, `Dockerfile`, `docker-compose*` | Pause: Copilot stops, explains the change in detail, and waits for explicit "go ahead" before any modification. |

> **Override rules**: Default tiers (no custom overrides)

### User Preferences

> Set 2026-03-21. Update via §8.

| ID | Question | Answer |
|----|----------|--------|
| S1 | Response style | Thorough |
| S2 | Experience level | Intermediate |
| S3 | Primary mode | Quality |
| S4 | Testing | Write always |
| S5 | Autonomy | Full auto |
| A6 | Code style | Strict |
| A7 | Import style | Absolute only |
| A8 | Error handling | Explicit (never swallow) |
| A9 | Documentation | Docstrings on public API |
| A10 | File size | Standard (warn 250, hard 400) |
| A11 | Dependencies | Pragmatic |
| A12 | Instruction editing | Free |
| A13 | Refactoring | Fix proactively |
| A14 | Git conventions | Conventional Commits |
| A15 | Skill search | Auto |
| A16 | Hooks | Yes |
| A17 | Prompts | Yes |
| E18 | VS Code settings | Yes |
| E19 | Trust overrides | Default |
| E20 | Subagent max depth | 3 |
| E21 | Integration env var | RUN_INTEGRATION_TESTS |
| E22 | MCP servers | Full configuration |
| E23 | Claude compat | Yes |

*(Populated from setup interview answers. See `SETUP.md` for question definitions.)*

---

## §11 — Tool Protocol

> **Parallel execution**: When multiple independent tool calls are needed (reading N files,
> running N searches, fetching N URLs), execute all in one parallel batch. Never sequence
> independent tool calls — check for data dependencies first, then parallelize everything else.

When a task requires automation or scripting, activate the **tool-protocol** skill (`.github/skills/tool-protocol/SKILL.md`) and follow its decision tree: Find → Built-in → Search → Compose → Build → Evaluate reusability.

Key rules (always loaded):

- Tools are saved to `.copilot/tools/` with a row in `INDEX.md`
- `safe` tools run without confirmation; `destructive` tools **must pause and confirm**
- Tools must be idempotent, accept arguments (no hardcoded paths), and follow §3 LOC baselines
- Subagents inherit this protocol; they flag toolbox saves to the parent agent

---

## §12 — Skill Protocol

Skills are reusable markdown-based behavioural instructions following the [Agent Skills](https://agentskills.io) open standard. Activate the **skill-management** skill (`.github/skills/skill-management/SKILL.md`) for the full discovery and activation workflow.

Key rules (always loaded):

- Skills are loaded **on demand** — read `SKILL.md` only when its `description` matches the current task
- Priority: project (`.github/skills/`) > personal (`~/.copilot/skills/`) > agent plugins (`@agentPlugins`)
- Agent plugins (VS Code 1.110+) distribute skills alongside agents — activate the **plugin-management** skill for discovery and conflict resolution
- Subagents inherit this protocol; they flag skill creation to the parent agent

---

## §13 — Model Context Protocol (MCP)

MCP enables Copilot to invoke external servers beyond built-in capabilities. Configuration lives in `.vscode/mcp.json`. Activate the **mcp-management** skill (`.github/skills/mcp-management/SKILL.md`) for server configuration and management.

Key rules (always loaded):

- **Always-on** servers: filesystem, git — enabled by default
- **Credentials-required** servers: github, fetch — need token configuration
- The MCP `memory` server has been removed — VS Code's built-in memory tool (`/memories/`) provides superior persistent storage with three scopes (user, session, repository)
- Never hardcode secrets — use `${input:}` or `${env:}` variable syntax
- Subagents inherit access; they flag new server additions to the parent agent

---

*See also: `.github/agents/` (model-pinned VS Code agents) · `.github/hooks/` (agent lifecycle hooks) · `.copilot/workspace/` (session identity) · `.copilot/tools/` (reusable tool library) · `.github/skills/` (reusable skill library) · `.vscode/mcp.json` (MCP server configuration) · `UPDATE.md` (update protocol) · `MIGRATION.md` (per-version migration registry) · `AGENTS.md` (AI agent entry point)*
