---
applyTo: "**/*.{js,ts,tsx,jsx,py,rb,go,java,php,cs,rs,kt,swift,sh,md}"
---

# Code Quality and Formatting Standards - MANDATORY

## Copilot usage quick cues

- Ask: style/lint rule clarifications, quick fixes suggestions, or config diffs.
- Edit: apply auto-fixes to a single file; request minimal diff and keep rules intact.
- Agent: repo-wide formatting/linting with toolshed usage and a PASS/FAIL summary.

### Model routing

- Reasoning model: non-trivial rule design and conflicting-rule mediation.
- Claude Sonnet class: code review + targeted refactors guided by tests.
- Gemini Pro class: large doc/code sweeps or summarizing linter logs.
- Fast general model: quick formatting and small rule tweaks.

### Token economy tips

- Link to the exact script under scripts/tools rather than pasting long output.
- Ask for patches or staged diffs instead of full-file reprints.

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: All repositories with code content
- **Compliance**: Required for code quality assurance
- **Review Cycle**: Quarterly assessment and updates

## Executive Summary

This policy establishes comprehensive standards for code quality, linting, and formatting based on
industry best practices from ShellCheck, markdownlint, Prettier, and EditorConfig standards. All
GitHub Copilot agents MUST implement and maintain these standards to ensure consistent, high-quality
code across all repositories.

## Placeholders, TODOs, and Stubs Policy (MANDATORY)

- Avoid unnecessary placeholders/stubs. Prefer delivering minimal, working

  implementations or omitting features until ready.

- When a placeholder/TODO is unavoidable, you MUST:
- Use a clear marker in code or docs: `TODO(scope): description` or

  `PLACEHOLDER(scope): description` with an expected resolution date.

- Open a tracking issue and reference it inline (e.g., `(#123)`), or add it

  to the repository placeholder log (see below).

- Minimize surface area: keep the stub small, isolated, and non-breaking.
- The repository SHOULD have little to no placeholders. Clean them as a priority

  during refactors or when touching nearby code.

## Shell Script Standards (ShellCheck)

### Core Requirements

#### ShellCheck Installation and Usage

````bash

## Docker-based linting (recommended)

Docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable scripts/**/*.sh

## Local installation

sudo apt-get install shellcheck  # Ubuntu/Debian
brew install shellcheck          # macOS

```Markdown

### Mandatory Configuration

```YAML

## .GitHub/workflows/shellcheck.yml

name: ShellCheck
on: [push, pull_request]
jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:

- uses: actions/checkout@v3
- name: Run ShellCheck

  uses: Docker://koalaman/shellcheck:stable
  with:
  args: --severity=warning scripts/**/*.sh

```Markdown

### Shell Script Quality Standards

### Shebang Requirements

```bash

## !/bin/bash          # For bash-specific features

## !/bin/sh            # For POSIX compatibility

```Markdown

### Quoting Standards

```bash

## CORRECT: Always quote variables

echo "$var"
echo "${array[@]}"

## INCORRECT: Unquoted variables

echo $var
echo ${array[@]}

```Markdown

### Error Handling

```bash

## MANDATORY: Set error handling

set -euo pipefail

## MANDATORY: Check command success

if ! command -v Git >/dev/null 2>&1; then
    echo "Error: Git is required" >&2
    exit 1
fi

```Markdown

### Portability Requirements

- Use `[[ ]]`for bash,`[ ]` for POSIX sh
- Avoid bash-specific features in `#!/bin/sh` scripts
- Use `printf`instead of`echo` for portable output
- Test with different shells when claiming POSIX compliance

### Shell Formatting Standards (shfmt)

#### Required Configuration

```bash

## Format all scripts with Google Shell Style Guide

shfmt -i 2 -ci -w scripts/**/*.sh

## CI/CD integration

shfmt -i 2 -ci -d scripts/**/*.sh  # Check without modifying

```Markdown

### Formatting Rules

- **Indentation**: 2 spaces (no tabs)
- **Case Indentation**: Enabled (`-ci`)
- **Binary Operations**: Next line alignment
- **Function Braces**: Same line as function name

## Markdown Standards (markdownlint)

### Core Requirements 2

#### Installation and Setup

```bash

## Global installation

npm install -g markdownlint-cli2

## Project-specific

npm install --save-dev markdownlint-cli2

```Markdown

### Mandatory Configuration 2

### `.markdownlint.JSON`

```JSON
{
  "default": true,
  "MD003": { "style": "atx" },
  "MD007": { "indent": 2 },
  "MD013": { "line_length": 100 },
  "MD022": true,
  "MD025": { "front_matter_title": false },
  "MD031": true,
  "MD032": true,
  "MD033": { "allowed_elements": ["br"] },
  "MD040": true,
  "MD041": false
}

```Markdown

#### Critical Rules Enforcement

### Heading Standards

- MD001: Heading levels increment by one
- MD003: ATX heading style (`# Header`)
- MD022: Headings surrounded by blank lines

### Code Block Standards

- MD031: Fenced code blocks surrounded by blank lines
- MD040: Fenced code blocks have language specified

### List Standards

- MD007: Unordered list indentation (2 spaces)
- MD032: Lists surrounded by blank lines

### Line Standards

- MD009: No trailing spaces
- MD012: No multiple consecutive blank lines
- MD013: Line length limit (100 characters)

### VS Code Integration

### `.VS Code/settings.JSON`

```JSON
{
  "markdownlint.config": {
    "MD013": { "line_length": 100 },
    "MD022": true,
    "MD031": true,
    "MD032": true,
    "MD040": true
  }
}

```Markdown

## Code Formatting Standards (Prettier)

### Core Requirements 3

#### Installation and Configuration

```bash

## Project installation

npm install --save-dev prettier

## Global installation 2

npm install -g prettier

```Markdown

### Mandatory Configuration 3

### `.prettierrc`

```JSON
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "quoteProps": "as-needed",
  "trailingComma": "es5",
  "bracketSpacing": true,
  "bracketSameLine": false,
  "arrowParens": "avoid",
  "endOfLine": "lf",
  "embeddedLanguageFormatting": "auto"
}

```Markdown

### `.prettierignore`

```text

## Dependencies

node_modules/
vendor/

## Build outputs

dist/
build/

_.min._

## Generated files

coverage/
.next/
.nuxt/

## Documentation

docs/generated/

```Markdown

### Language-Specific Standards

### JavaScript/TypeScript

- Single quotes for strings
- Semicolons required
- Trailing commas in multiline structures
- 2-space indentation

### JSON

- Double quotes (JSON standard)
- No trailing commas
- 2-space indentation

### CSS/SCSS

- Single quotes for strings
- No trailing semicolons on last property
- 2-space indentation

### VS Code Integration 2

### `.VS Code/settings.JSON` 2

```JSON
{
  "editor.defaultFormatter": "esbenp.prettier-VS Code",
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "prettier.requireConfig": true,
  "prettier.useEditorConfig": false,
  "[JavaScript]": {
    "editor.defaultFormatter": "esbenp.prettier-VS Code"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-VS Code"
  },
  "[JSON]": {
    "editor.defaultFormatter": "esbenp.prettier-VS Code"
  }
}

```Markdown

## EditorConfig Standards

### Core Requirements 4

#### Mandatory `.editorconfig`

```ini
root = true

## All files

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

## JavaScript/TypeScript 2

[*.{js,ts,jsx,tsx}]
indent_size = 2
quote_type = single

## Python/Java/C-based languages

[*.{py,java,c,cpp,cs,go,rs,kt}]
indent_size = 4

## Makefile (requires tabs)

[Makefile]
indent_style = tab

## Markdown (preserve trailing spaces for line breaks)

[*.md]
trim_trailing_whitespace = false

## Windows batch files

[*.bat]
end_of_line = crlf

## Tab-separated values

[*.tsv]
indent_style = tab

## YAML

[*.{yml,YAML}]
indent_size = 2

## XML/HTML

[*.{XML,HTML}]
indent_size = 2

## Configuration files

[*.{JSON,jsonc}]
indent_size = 2

```Markdown

### Platform-Specific Rules

### Windows Compatibility

- Batch files: `end_of_line = crlf`
- PowerShell scripts: `end_of_line = crlf`

### Unix Compatibility

- Shell scripts: `end_of_line = lf`
- All other files: `end_of_line = lf`

## Integration and Automation

### CI/CD Pipeline Integration

#### GitHub Actions Example

```YAML
name: Code Quality
on: [push, pull_request]

jobs:
  lint-and-format:
    runs-on: ubuntu-latest
    steps:

- uses: actions/checkout@v3
- name: Setup Node.js

  uses: actions/setup-node@v3
  with:
  node-version: '18'

- name: Install dependencies

  run: npm ci

- name: Run ShellCheck

  uses: Docker://koalaman/shellcheck:stable
  with:
  args: --severity=warning scripts/**/*.sh

- name: Lint Markdown

  run: npx markdownlint-cli2 "**/*.md"

- name: Check Prettier formatting

  run: npx prettier --check .

- name: Validate EditorConfig

  uses: editorconfig-checker/action-editorconfig-checker@main

```Markdown

### Pre-commit Hooks

### `.pre-commit-config.YAML`

```YAML
repos:

- repo: <HTTPS://GitHub.com/shellcheck-py/shellcheck-py>

  rev: v0.9.0.6
  hooks:

- id: shellcheck

  args: [--severity=warning]

- repo: <HTTPS://GitHub.com/igorshubovych/markdownlint-cli>

  rev: v0.37.0
  hooks:

- id: markdownlint
- repo: <HTTPS://GitHub.com/pre-commit/mirrors-prettier>

  rev: v3.0.3
  hooks:

- id: prettier
- repo: <HTTPS://GitHub.com/editorconfig-checker/editorconfig-checker.Python>

  rev: 2.7.3
  hooks:

- id: editorconfig-checker

```Markdown

### VS Code Workspace Configuration

### `.VS Code/settings.JSON` (Complete)

```JSON
{
  "editor.defaultFormatter": "esbenp.prettier-VS Code",
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "prettier.requireConfig": true,
  "prettier.useEditorConfig": false,
  "markdownlint.config": {
    "MD013": { "line_length": 100 },
    "MD022": true,
    "MD031": true,
    "MD032": true,
    "MD040": true
  },
  "shellcheck.enable": true,
  "shellcheck.run": "onSave",
  "[shellscript]": {
    "editor.defaultFormatter": "foxundermoon.shell-format"
  },
  "[Markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-VS Code",
    "editor.wordWrap": "on"
  }
}

```Markdown

## Validation and Compliance

### Automated Validation Tools

```bash

## !/bin/bash

## validate-code-quality.sh

set -euo pipefail

echo "🔍 Running code quality checks..."

## ShellCheck validation

if command -v shellcheck >/dev/null 2>&1; then
    echo "📋 Checking shell scripts..."
    find . -name "*.sh" -type f -exec shellcheck {} +
else
    echo "⚠️  ShellCheck not found, using Docker..."
    Docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable scripts/**/*.sh
fi

## Markdown validation

if command -v markdownlint-cli2 >/dev/null 2>&1; then
    echo "📝 Checking Markdown files..."
    markdownlint-cli2 "**/*.md"
else
    echo "⚠️  markdownlint-cli2 not found"
    exit 1
fi

## Prettier validation

if command -v prettier >/dev/null 2>&1; then
    echo "🎨 Checking code formatting..."
    prettier --check .
else
    echo "⚠️  Prettier not found"
    exit 1
fi

## EditorConfig validation

if command -v editorconfig-checker >/dev/null 2>&1; then
    echo "⚙️  Checking EditorConfig compliance..."
    editorconfig-checker
else
    echo "⚠️  EditorConfig checker not found"
fi

echo "✅ All code quality checks passed!"

```Markdown

### Compliance Checklist

#### Repository Assessment

- [ ] ShellCheck configuration present and functional
- [ ] All shell scripts pass ShellCheck validation
- [ ] Markdown linting configuration implemented
- [ ] All Markdown files pass linting rules
- [ ] Prettier configuration exists and enforced
- [ ] All code files formatted consistently
- [ ] EditorConfig file present and comprehensive
- [ ] CI/CD pipeline includes quality checks
- [ ] Pre-commit hooks configured (optional but recommended)
- [ ] VS Code workspace settings optimized

#### Quality Gates

### Blocking Issues

- ShellCheck errors (not warnings)
- Critical Markdown violations (MD031, MD040, MD022)
- Prettier formatting inconsistencies
- EditorConfig violations

### Warning Issues

- ShellCheck warnings
- Non-critical Markdown style issues
- Performance optimization opportunities

## Implementation Requirements

### For GitHub Copilot Agents

1. **Immediate Compliance**
- Install required tools (shellcheck, markdownlint-cli2, prettier)
- Create configuration files in repository root
- Run initial validation and fix all issues
- Set up VS Code workspace integration
2. **Ongoing Responsibilities**
- Enforce quality standards on all new code
- Monitor and fix quality regressions
- Update configurations as tools evolve
- Train team members on quality standards
3. **Reporting Requirements**
- Document quality metrics and trends
- Report blocking issues immediately
- Track compliance across repositories
- Maintain audit trails for quality changes

### Tool Installation Commands

```bash

## Complete setup script

## !/bin/bash 2

set -euo pipefail

echo "🚀 Setting up code quality tools..."

## Install ShellCheck

if ! command -v shellcheck >/dev/null 2>&1; then
    if [["$OSTYPE" == "Linux"*]]; then
        sudo apt-get update && sudo apt-get install -y shellcheck
    elif [["$OSTYPE" == "darwin"*]]; then
        brew install shellcheck
    fi
fi

## Install Node.js tools

npm install -g markdownlint-cli2 prettier

## Install VS Code extensions (if VS Code is available)

if command -v code >/dev/null 2>&1; then
    code --install-extension DavidAnson.VS Code-markdownlint
    code --install-extension esbenp.prettier-VS Code
    code --install-extension timonwong.shellcheck
    code --install-extension EditorConfig.EditorConfig
    code --install-extension foxundermoon.shell-format
fi

echo "✅ Code quality tools installation complete!"

```text

## Automated Quality Tools Integration

### Pre-Built Quality Automation

GitHub Copilot agents MUST use the comprehensive quality tools available in the
toolshed before creating custom quality scripts:

#### Quality Management Tool

```bash

## Comprehensive quality checking with auto-fix capabilities

./scripts/tools/quality/check-quality.sh --check Markdown --fix
./scripts/tools/quality/check-quality.sh --format JSON --report quality.JSON
./scripts/tools/quality/check-quality.sh --help  # View all options

```text

### Pre-Commit Quality Gates

```bash

## Setup comprehensive pre-commit hooks with quality validation

./scripts/tools/hooks/setup-pre-commit.sh --languages Python,JavaScript
./scripts/tools/hooks/setup-pre-commit.sh --security-scanning --dry-run

```text

### Integration with Repository Management

```bash

## Repository structure validation with quality checks

./scripts/tools/validation/validate-structure.sh --category quality
./scripts/tools/validation/validate-structure.sh --JSON --output results.JSON

```text

### Tool Benefits

- **Consistent Standards**: All quality tools follow the same interface patterns
- **Multi-Language Support**: Automated detection and validation for various languages
- **Auto-Fix Capabilities**: Automatic correction of common quality issues
- **Comprehensive Reporting**: JSON and human-readable output formats
- **CI/CD Integration**: Ready for automated pipeline integration

### Usage Priority

1. **First**: Use existing quality tools from `scripts/tools/quality/`
2. **Second**: Extend existing tools with new language support
3. **Third**: Create new tools following established patterns
4. **Never**: Recreate functionality that exists in the toolshed

**Reference**: See `scripts/tools/README.md` for complete quality tool documentation.

## Version Control Integration

### Mandatory Implementation

All GitHub Copilot agents MUST implement comprehensive version control standards
as part of code quality requirements. This includes:

#### Git Configuration Standards

- Conventional commit message templates (`.gitmessage`)
- Standardized Git aliases for productivity
- Semantic versioning with `VERSION`file and`CHANGELOG.md`
- Comprehensive `.gitignore` with project-appropriate patterns

#### CI/CD Quality Gates

- Automated code quality validation in CI pipeline
- Security scanning with Trivy and dependency review
- Markdown linting and link checking integration
- Automated formatting validation with Prettier

#### Required Workflows

```bash

## Implement version control before any code work

./.GitHub/instructions/version-control.instructions.md

## Validate implementation

./scripts/validation/validate-version-control.sh

## Use conventional commits

Git commit -m "feat: implement code quality standards

- Add ShellCheck, markdownlint, and Prettier configuration
- Set up CI/CD workflows with quality gates
- Configure VS Code workspace for consistent formatting
- Implement pre-commit hooks for quality validation"

```text

### Quality Integration Commands

```bash

## Combined quality and version control validation

./scripts/validation/validate-code-quality.sh
./scripts/validation/validate-version-control.sh

## Git workflow with quality checks

./scripts/utils/Git-workflow.sh feature code-quality-improvements

```text

See `.GitHub/instructions/version-control.instructions.md` for complete implementation details.

## Related Policies

- **Version Control Policy**: `.GitHub/instructions/version-control.instructions.md` - MANDATORY
- Documentation Policy: `.GitHub/instructions/docs-policy.instructions.md`
- Archive Management Policy: `.GitHub/instructions/archive-policy.instructions.md`
- Security Guidelines: `.GitHub/instructions/security.instructions.md`
- Testing Standards: `.GitHub/instructions/testing.instructions.md`

## Policy Metadata

- **Created**: Current implementation date
- **Last Updated**: Current date
- **Version**: 1.1
- **Next Review**: Quarterly
- **Enforcement**: Mandatory for all GitHub Copilot agents
- **Compliance Tracking**: Required in all repository assessments

**ENFORCEMENT NOTICE**: This policy is MANDATORY for all GitHub Copilot agents.
Non-compliance will result in repository quality issues and additional oversight
procedures. All code work must follow these standards without exception.

## Version control implementation is a prerequisite for all development work
````
