# Configuration API

Reference for configuration and policy files that drive framework behavior.

Key files

- Package scripts: `package.json` (lint, validate, examples)
- Instructions: `.github/instructions/*.instructions.md` (scoped policies)
- Workflows: `.github/workflows/*.yml` (CI link-check, CI validation)
- Markdown lint: `.markdownlint.json`
- Prettier: `.prettierrc` and `.prettierignore`

Usage

- Prefer npm scripts (e.g., `npm run validate`) over raw commands
- Follow file placement policy (`.github/instructions/file-organization.instructions.md`)
