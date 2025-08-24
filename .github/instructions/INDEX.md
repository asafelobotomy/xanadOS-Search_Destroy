# Instruction Files Index

Purpose: quick map of instruction files, their scopes, and purpose. Keep scopes tight.

- `agent-workflow.instructions.md` — applyTo: **/* — mandatory workflow and quality gates
- `documentation-awareness.instructions.md` — applyTo: docs/** — prefer existing docs
- `toolshed-usage.instructions.md` — applyTo: scripts/** — prefer toolshed over new scripts
- `testing.instructions.md` — applyTo: **/{test,tests,spec,__tests__}/**/* — testing standards
- `security.instructions.md` — applyTo: **/*.{js,ts,py,rb,go,java,php,cs,rs,kt,swift}` — security rules
- `version-control.instructions.md` — applyTo: .github/** — version control
	policies (repo-level; Copilot cues added)
- `file-organization.instructions.md` — repository placement standards (human reference)
- `code-quality.instructions.md` — code quality policies (human reference)
- `debugging.instructions.md` — debugging guidance (human reference)

Note: Major instruction files now include concise Copilot usage cues, model
routing, and token tips. Prefer path-scoped instructions; avoid unnecessary
global applyTo patterns.
