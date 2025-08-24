---
applyTo: "**/*"
---

# Repository custom instructions (lean)

Purpose: give Copilot only what it needs to build, test, lint, and open mergeable PRs here.
Keep details in `/docs`; keep this file short and operational.

## Build, test, lint

- Build/validate: see scripts under `scripts/tools/` and package scripts.
- Lint markdown: `npm run lint` (uses markdownlint)
- Validate templates: `npm run validate`

## Minimal repo map

- `.github/instructions/`: scoped rules for Copilot (read when relevant)
- `.github/chatmodes/` and `.github/prompts/`: chat modes and prompt files
- `docs/`: human-facing guides and references
- `scripts/tools/`: toolshed; prefer these over writing new scripts

See full guide: `docs/guides/COPILOT-INSTRUCTIONS-GUIDE.md`.

## Coding standards (imperative, short)

- Prefer small, focused changes with tests or validation output.
- Don’t duplicate tools or docs; search `scripts/tools/` and `docs/` first.
- Follow security and testing instructions when files match their scope.
- Update `CHANGELOG.md` for notable changes; use conventional commits.

## PR merge criteria

- Lint and validation pass (markdownlint + template validation).
- Changes are scoped, documented (if needed), and follow file placement rules.
- No secrets or sensitive data added.

## Ask, Edit, Agent (when to use)

- Ask: plan, summarize, route tasks, or find related files.
- Edit: targeted code/doc edits in one or two files.
- Agent: multi-step changes that can run linters/tests and iterate.

## Model routing (practical default)

- Complex refactors/algorithms: reasoning model (OpenAI o1/o3 or similar).
- Code review, TDD, rewriting docs/tests: Claude Sonnet class.
- Multimodal/cross-language or large-context summarization: Gemini Pro class.
- Boilerplate scaffolding or quick edits: fast general model.

Always pick the smallest capable model; switch up for harder reasoning.

## References

- Agent workflow: `.github/instructions/agent-workflow.instructions.md`
- Toolshed usage: `.github/instructions/toolshed-usage.instructions.md`
- Docs awareness: `.github/instructions/documentation-awareness.instructions.md`
- Security/testing: `.github/instructions/security.instructions.md`, `testing.instructions.md`
- Full framework guide: `docs/guides/COPILOT-INSTRUCTIONS-GUIDE.md`
