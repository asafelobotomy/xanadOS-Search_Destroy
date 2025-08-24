# Instruction Files Index

Purpose: quick map of instruction files, their scopes, and purpose. Keep scopes tight.

## Active Instructions (Applied by GitHub Copilot)

- `agent-workflow.instructions.md` — applyTo: \_\_/\*\_\_ — mandatory workflow and quality gates
- `documentation-awareness.instructions.md` — applyTo: docs/\*\* — prefer existing docs
- `toolshed-usage.instructions.md` — applyTo: scripts/\*\* — prefer toolshed over new scripts
- `testing.instructions.md` — applyTo: \*\*/{test,tests,spec,\_\_tests\_\_}/\*\*/\* — testing standards
- `security.instructions.md` — applyTo: \*\*/\*.{js,ts,py,rb,go,java,php,cs,rs,kt,swift}` —
  security rules
- `version-control.instructions.md` — applyTo: .GitHub/\*\* — version control policies
  (repo-level; Copilot cues added)

## Reference Instructions (Human Documentation)

- `file-organization.instructions.md` — repository placement standards
- `code-quality.instructions.md` — code quality policies and validation
- `debugging.instructions.md` — debugging guidance and troubleshooting
- `docs-policy.instructions.md` — documentation structure and standards
- `archive-policy.instructions.md` — archival and deprecation guidelines

## Usage Notes

- **Active instructions** include Copilot usage cues, model routing, and token optimization tips
- **Path-scoped instructions** target specific file types and directories
- **Reference instructions** provide comprehensive human-readable policies
- All instructions follow the agent-workflow for systematic implementation

## Documentation Structure Alignment

Instructions reference the following documentation structure:

- `docs/guides/` — How-to guides and comprehensive documentation
- `docs/tutorials/` — Step-by-step learning materials
- `docs/reference/` — Quick-lookup specifications and references
- `docs/api/` — API documentation and integration guides
- `docs/guides/troubleshooting.md` — Problem resolution guide

Prefer path-scoped instructions over broad global patterns for better targeting.
