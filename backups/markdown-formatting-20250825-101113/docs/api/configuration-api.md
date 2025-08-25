# Configuration API

Reference for configuration and policy files that drive framework behavior.

Key files

- Package scripts: `package.JSON` (lint, validate, examples)
- Instructions: `.GitHub/instructions/*.instructions.md` (scoped policies)
- Workflows: `.GitHub/workflows/*.yml` (CI link-check, CI validation)
- Markdown lint: `.markdownlint.JSON`
- Prettier: `.prettierrc`and`.prettierignore`

Usage

- Prefer npm scripts (e.g., `npm run validate`) over raw commands
- Follow file placement policy (`.GitHub/instructions/file-organization.instructions.md`)
