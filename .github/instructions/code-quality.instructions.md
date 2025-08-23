# Code Quality and Formatting Standards - MANDATORY

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: All repositories with code content
- **Compliance**: Required for code quality assurance
- **Review Cycle**: Quarterly assessment and updates

## Executive Summary

This policy establishes comprehensive standards for code quality, linting, and formatting based on industry best practices from ShellCheck, markdownlint, Prettier, and EditorConfig standards. All GitHub Copilot agents MUST implement and maintain these standards to ensure consistent, high-quality code across all repositories.

## Shell Script Standards (ShellCheck)

### Core Requirements

#### ShellCheck Installation and Usage

```bash

# Docker-based linting (recommended)

docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable scripts/**/*.sh

# Local installation

sudo apt-get install shellcheck  # Ubuntu/Debian
brew install shellcheck          # macOS
```markdown

#### Mandatory Configuration

```yaml

# .github/workflows/shellcheck.yml

name: ShellCheck
on: [push, pull_request]
jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run ShellCheck
        uses: docker://koalaman/shellcheck:stable
        with:
          args: --severity=warning scripts/**/*.sh
```markdown

#### Shell Script Quality Standards

**Shebang Requirements:**
```bash
#!/bin/bash          # For bash-specific features
#!/bin/sh            # For POSIX compatibility
```markdown

**Quoting Standards:**
```bash

# CORRECT: Always quote variables

echo "$var"
echo "${array[@]}"

# INCORRECT: Unquoted variables

echo $var
echo ${array[@]}
```markdown

**Error Handling:**
```bash

# MANDATORY: Set error handling

set -euo pipefail

# MANDATORY: Check command success

if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is required" >&2
    exit 1
fi
```markdown

**Portability Requirements:**
- Use `[[ ]]` for bash, `[ ]` for POSIX sh
- Avoid bash-specific features in `#!/bin/sh` scripts
- Use `printf` instead of `echo` for portable output
- Test with different shells when claiming POSIX compliance

### Shell Formatting Standards (shfmt)

#### Required Configuration

```bash

# Format all scripts with Google Shell Style Guide

shfmt -i 2 -ci -w scripts/**/*.sh

# CI/CD integration

shfmt -i 2 -ci -d scripts/**/*.sh  # Check without modifying
```markdown

#### Formatting Rules

- **Indentation**: 2 spaces (no tabs)
- **Case Indentation**: Enabled (`-ci`)
- **Binary Operations**: Next line alignment
- **Function Braces**: Same line as function name

## Markdown Standards (markdownlint)

### Core Requirements

#### Installation and Setup

```bash

# Global installation

npm install -g markdownlint-cli2

# Project-specific

npm install --save-dev markdownlint-cli2
```markdown

#### Mandatory Configuration

**`.markdownlint.json`:**
```json
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
```markdown

#### Critical Rules Enforcement

**Heading Standards:**
- MD001: Heading levels increment by one
- MD003: ATX heading style (`# Header`)
- MD022: Headings surrounded by blank lines

**Code Block Standards:**
- MD031: Fenced code blocks surrounded by blank lines
- MD040: Fenced code blocks have language specified

**List Standards:**
- MD007: Unordered list indentation (2 spaces)
- MD032: Lists surrounded by blank lines

**Line Standards:**
- MD009: No trailing spaces
- MD012: No multiple consecutive blank lines
- MD013: Line length limit (100 characters)

### VS Code Integration

**`.vscode/settings.json`:**
```json
{
  "markdownlint.config": {
    "MD013": { "line_length": 100 },
    "MD022": true,
    "MD031": true,
    "MD032": true,
    "MD040": true
  }
}
```markdown

## Code Formatting Standards (Prettier)

### Core Requirements

#### Installation and Configuration

```bash

# Project installation

npm install --save-dev prettier

# Global installation

npm install -g prettier
```markdown

#### Mandatory Configuration

**`.prettierrc`:**
```json
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
```markdown

**`.prettierignore`:**
```text

# Dependencies

node_modules/
vendor/

# Build outputs

dist/
build/
*.min.*

# Generated files

coverage/
.next/
.nuxt/

# Documentation

docs/generated/
```markdown

#### Language-Specific Standards

**JavaScript/TypeScript:**
- Single quotes for strings
- Semicolons required
- Trailing commas in multiline structures
- 2-space indentation

**JSON:**
- Double quotes (JSON standard)
- No trailing commas
- 2-space indentation

**CSS/SCSS:**
- Single quotes for strings
- No trailing semicolons on last property
- 2-space indentation

### VS Code Integration

**`.vscode/settings.json`:**
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "prettier.requireConfig": true,
  "prettier.useEditorConfig": false,
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```markdown

## EditorConfig Standards

### Core Requirements

#### Mandatory `.editorconfig`

```ini
root = true

# All files

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

# JavaScript/TypeScript

[*.{js,ts,jsx,tsx}]
indent_size = 2
quote_type = single

# Python/Java/C-based languages

[*.{py,java,c,cpp,cs,go,rs,kt}]
indent_size = 4

# Makefile (requires tabs)

[Makefile]
indent_style = tab

# Markdown (preserve trailing spaces for line breaks)

[*.md]
trim_trailing_whitespace = false

# Windows batch files

[*.bat]
end_of_line = crlf

# Tab-separated values

[*.tsv]
indent_style = tab

# YAML

[*.{yml,yaml}]
indent_size = 2

# XML/HTML

[*.{xml,html}]
indent_size = 2

# Configuration files

[*.{json,jsonc}]
indent_size = 2
```markdown

### Platform-Specific Rules

**Windows Compatibility:**
- Batch files: `end_of_line = crlf`
- PowerShell scripts: `end_of_line = crlf`

**Unix Compatibility:**
- Shell scripts: `end_of_line = lf`
- All other files: `end_of_line = lf`

## Integration and Automation

### CI/CD Pipeline Integration

#### GitHub Actions Example

```yaml
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
        uses: docker://koalaman/shellcheck:stable
        with:
          args: --severity=warning scripts/**/*.sh

      - name: Lint Markdown
        run: npx markdownlint-cli2 "**/*.md"

      - name: Check Prettier formatting
        run: npx prettier --check .

      - name: Validate EditorConfig
        uses: editorconfig-checker/action-editorconfig-checker@main
```markdown

### Pre-commit Hooks

**`.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck
        args: [--severity=warning]

  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier

  - repo: https://github.com/editorconfig-checker/editorconfig-checker.python
    rev: 2.7.3
    hooks:
      - id: editorconfig-checker
```markdown

### VS Code Workspace Configuration

**`.vscode/settings.json` (Complete):**
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
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
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.wordWrap": "on"
  }
}
```markdown

## Validation and Compliance

### Automated Validation Tools

```bash
#!/bin/bash

# validate-code-quality.sh

set -euo pipefail

echo "🔍 Running code quality checks..."

# ShellCheck validation

if command -v shellcheck >/dev/null 2>&1; then
    echo "📋 Checking shell scripts..."
    find . -name "*.sh" -type f -exec shellcheck {} +
else
    echo "⚠️  ShellCheck not found, using Docker..."
    docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable scripts/**/*.sh
fi

# Markdown validation

if command -v markdownlint-cli2 >/dev/null 2>&1; then
    echo "📝 Checking markdown files..."
    markdownlint-cli2 "**/*.md"
else
    echo "⚠️  markdownlint-cli2 not found"
    exit 1
fi

# Prettier validation

if command -v prettier >/dev/null 2>&1; then
    echo "🎨 Checking code formatting..."
    prettier --check .
else
    echo "⚠️  Prettier not found"
    exit 1
fi

# EditorConfig validation

if command -v editorconfig-checker >/dev/null 2>&1; then
    echo "⚙️  Checking EditorConfig compliance..."
    editorconfig-checker
else
    echo "⚠️  EditorConfig checker not found"
fi

echo "✅ All code quality checks passed!"
```markdown

### Compliance Checklist

#### Repository Assessment

- [ ] ShellCheck configuration present and functional
- [ ] All shell scripts pass ShellCheck validation
- [ ] Markdown linting configuration implemented
- [ ] All markdown files pass linting rules
- [ ] Prettier configuration exists and enforced
- [ ] All code files formatted consistently
- [ ] EditorConfig file present and comprehensive
- [ ] CI/CD pipeline includes quality checks
- [ ] Pre-commit hooks configured (optional but recommended)
- [ ] VS Code workspace settings optimized

#### Quality Gates

**Blocking Issues:**
- ShellCheck errors (not warnings)
- Critical markdown violations (MD031, MD040, MD022)
- Prettier formatting inconsistencies
- EditorConfig violations

**Warning Issues:**
- ShellCheck warnings
- Non-critical markdown style issues
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

# Complete setup script

#!/bin/bash
set -euo pipefail

echo "🚀 Setting up code quality tools..."

# Install ShellCheck

if ! command -v shellcheck >/dev/null 2>&1; then
    if [[ "$OSTYPE" == "linux"* ]]; then
        sudo apt-get update && sudo apt-get install -y shellcheck
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install shellcheck
    fi
fi

# Install Node.js tools

npm install -g markdownlint-cli2 prettier

# Install VS Code extensions (if VS Code is available)

if command -v code >/dev/null 2>&1; then
    code --install-extension DavidAnson.vscode-markdownlint
    code --install-extension esbenp.prettier-vscode
    code --install-extension timonwong.shellcheck
    code --install-extension EditorConfig.EditorConfig
    code --install-extension foxundermoon.shell-format
fi

echo "✅ Code quality tools installation complete!"
```markdown

## Related Policies

- Documentation Policy: `.github/instructions/docs-policy.instructions.md`
- Archive Management Policy: `.github/instructions/archive-policy.instructions.md`
- Security Guidelines: `.github/instructions/security.instructions.md`
- Testing Standards: `.github/instructions/testing.instructions.md`

## Policy Metadata

- **Created**: Current implementation date
- **Last Updated**: Current date
- **Version**: 1.0
- **Next Review**: Quarterly
- **Enforcement**: Mandatory for all GitHub Copilot agents
- **Compliance Tracking**: Required in all repository assessments

---

**ENFORCEMENT NOTICE**: This policy is MANDATORY for all GitHub Copilot agents. Non-compliance will result in repository quality issues and additional oversight procedures. All code work must follow these standards without exception.
