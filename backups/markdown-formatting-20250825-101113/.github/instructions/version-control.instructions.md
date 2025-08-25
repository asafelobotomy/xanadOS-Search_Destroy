---
applyTo: ".GitHub/**"
priority: "high"
enforcement: "mandatory"
---

# Version Control Implementation Instructions - MANDATORY

<!-- markdownlint-disable MD013 MD036 MD031 MD022 MD032 MD040 -->

## Copilot usage quick cues

- Ask: confirm if version-control setup or policy edits are in scope; if not,

  skip heavy content and proceed.

- Edit: small CI or template tweaks; keep diffs minimal and reference

  existing scripts.

- Agent: full VC bootstrap or workflow overhaul; require validation output

  and a short summary of changes.

### Model routing

- Reasoning model: branching strategy, policy design, or complex migrations.
- Claude Sonnet class: review CI, templates, and policy diffs for quality.
- Gemini Pro class: summarize long logs or compare workflows across files.
- Fast general model: simple config edits and small fixes.

### Token economy tips

- Link to this file instead of inlining long sections in PRs or comments.
- Prefer running validation scripts and paste only the summary output.

## Policy Classification

- **Enforcement Level**: MANDATORY for all GitHub Copilot agents
- **Scope**: All repositories requiring professional development standards
- **Compliance**: Required for enterprise-grade development
- **Review Cycle**: Implementation required before any development work

## Executive Summary

All GitHub Copilot agents MUST implement comprehensive industry-standard version control when working on any repository.
This includes Git configuration, branching strategies, commit conventions, CI/CD workflows, and quality assurance automation
Version control implementation is a prerequisite for professional development practices.

## 🎯 **MANDATORY: Version Control Implementation Checklist**

Before beginning any development work, agents MUST implement these version control standards:

### ✅ **Core Git Configuration**

## 1. Commit Message Templates

```bash

## Create .gitmessage file

cat > .gitmessage << 'EOF'

## <type>[optional scope]: <description>

#

## [optional body]

#

## [optional footer(s)]

## Type can be one of

## feat:     A new feature

## fix:      A bug fix

## docs:     Documentation only changes

## style:    Changes that do not affect the meaning of the code

## refactor: A code change that neither fixes a bug nor adds a feature

## perf:     A code change that improves performance

## test:     Adding missing tests or correcting existing tests

## build:    Changes that affect the build system or external dependencies

## ci:       Changes to CI configuration files and scripts

## chore:    Other changes that don't modify src or test files

## revert:   Reverts a previous commit

EOF

## Configure Git to use template

Git config commit.template .gitmessage
```

## 2. Essential Git Configuration

```bash

## Configure pull strategy

Git config pull.rebase false

## Set default branch

Git config init.defaultBranch main

## Configure useful aliases

Git config alias.co checkout
Git config alias.br branch
Git config alias.ci commit
Git config alias.st status
Git config alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
```

## 3. Comprehensive .gitignore

```bash

## Create comprehensive .gitignore (minimum required patterns)

cat > .gitignore << 'EOF'

## Dependencies

node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

## Build outputs

dist/
build/
out/

## Environment variables

.env
.env.local
.env.development.local
.env.test.local
.env.production.local

## OS generated files

.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

## IDE files

*.swp
*.swo
*~
.idea/
*.iml

## Logs

logs/
*.log

## Temporary files

.tmp/
temp/
*.tmp

## Backup files

*.backup
*.bak
*.orig

## Cache directories

.cache/
.npm/
.yarn/

## Archive exclusions

archive/.tmp/
archive/*.processing
archive/*.staging

## Test output

test-results/
test-output/
EOF
```

### ✅ **Semantic Versioning System**

## 1. VERSION File

```bash

## Create VERSION file with semantic versioning

cat > VERSION << 'EOF'

## Semantic Versioning

VERSION_MAJOR=1
VERSION_MINOR=0
VERSION_PATCH=0

VERSION_BUILD=$(Git rev-list --count HEAD 2>/dev/null || echo "0")

## Current version string

VERSION="${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}"
VERSION_FULL="${VERSION}.${VERSION_BUILD}"

echo $VERSION_FULL
EOF
```

## 2. CHANGELOG.md

```bash

## Create CHANGELOG.md following Keep a Changelog format

cat > CHANGELOG.md << 'EOF'

## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](HTTPS://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](HTTPS://semver.org/spec/v2.0.0.HTML).

## [Unreleased]

### Added

- Initial project setup
- Version control implementation

## [1.0.0] - $(date +%Y-%m-%d)

### Added 2

- Initial release
- Basic project structure

EOF
```

### ✅ **GitHub Workflows Implementation**

## 1. Continuous Integration Workflow

```bash

## Create .GitHub/workflows/ci.yml

mkdir -p .GitHub/workflows
cat > .GitHub/workflows/ci.yml << 'EOF'
name: Continuous Integration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  issues: write
  pull-requests: write
  checks: write

jobs:
  validation:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20]

    steps:

- name: Checkout repository

  uses: actions/checkout@v4
  with:
  fetch-depth: 0

- name: Setup Node.js ${{ matrix.node-version }}

  uses: actions/setup-node@v4
  with:
  node-version: ${{ matrix.node-version }}
  cache: 'npm'

- name: Install dependencies

  run: npm ci

- name: Run linting

  run: npm run lint
  continue-on-error: true

- name: Run tests

  run: npm test
  continue-on-error: true

- name: Verify repository structure

  run: |
  if [-f "scripts/validation/verify-structure.sh"]; then
  chmod +x scripts/validation/verify-structure.sh
  ./scripts/validation/verify-structure.sh
  fi

  security-scan:
  runs-on: ubuntu-latest
  steps:

- name: Checkout repository

  uses: actions/checkout@v4

- name: Run Trivy vulnerability scanner

  uses: aquasecurity/trivy-action@master
  with:
  scan-type: 'fs'
  scan-ref: '.'
  format: 'sarif'
  output: 'trivy-results.sarif'

- name: Upload Trivy scan results

  uses: GitHub/codeql-action/upload-sarif@v3
  with:
  sarif_file: 'trivy-results.sarif'

  Markdown-lint:
  runs-on: ubuntu-latest
  steps:

- name: Checkout repository

  uses: actions/checkout@v4

- name: Setup Node.js

  uses: actions/setup-node@v4
  with:
  node-version: '18'

- name: Install markdownlint-cli

  run: npm install -g markdownlint-cli

- name: Run Markdown lint

  run: markdownlint "**/*.md" --ignore node_modules --ignore archive
EOF
```

## 2. Release Management Workflow

```bash

## Create .GitHub/workflows/release.yml

cat > .GitHub/workflows/release.yml << 'EOF'
name: Release Management

on:
  push:
    tags:

- 'v*'

  workflow_dispatch:
  inputs:
  version:
  description: 'Version to release (e.g., v1.0.0)'
  required: true
  type: string

permissions:
  contents: write
  packages: write
  issues: write
  pull-requests: write

jobs:
  validate-version:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.extract.outputs.version }}
      is_prerelease: ${{ steps.extract.outputs.is_prerelease }}
    steps:

- name: Checkout

  uses: actions/checkout@v4
  with:
  fetch-depth: 0

- name: Extract version info

  id: extract
  run: |
  if ["${{ GitHub.event_name }}" = "workflow_dispatch"]; then
  VERSION="${{ GitHub.event.inputs.version }}"
  else
  VERSION="${{ GitHub.ref_name }}"
  fi

  echo "version=${VERSION}" >> $GITHUB_OUTPUT

  if [[ $VERSION =~ -[a-zA-Z] ]]; then
  echo "is_prerelease=true" >> $GITHUB_OUTPUT
  else
  echo "is_prerelease=false" >> $GITHUB_OUTPUT
  fi

  create-release:
  runs-on: ubuntu-latest
  needs: [validate-version]
  steps:

- name: Checkout

  uses: actions/checkout@v4
  with:
  fetch-depth: 0

- name: Generate release notes

  id: release_notes
  run: |
  VERSION=${{ needs.validate-version.outputs.version }}
  sed -n "/## \[${VERSION#v}\]/,/## \[/p" CHANGELOG.md | head -n -1 > release_notes.md

  if [! -s release_notes.md]; then
  echo "## Changes in $VERSION" > release_notes.md
  echo "" >> release_notes.md
  echo "See [CHANGELOG.md](CHANGELOG.md) for details." >> release_notes.md
  fi

- name: Create GitHub Release

  uses: softprops/action-gh-release@v1
  with:
  tag_name: ${{ needs.validate-version.outputs.version }}
  name: Release ${{ needs.validate-version.outputs.version }}
  body_path: release_notes.md
  prerelease: ${{ needs.validate-version.outputs.is_prerelease }}
  files: |
  CHANGELOG.md
  README.md
  env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
EOF
```

### ✅ **GitHub Templates**

## 1. Pull Request Template

```bash

## Create .GitHub/pull_request_template.md

cat > .GitHub/pull_request_template.md << 'EOF'

## Pull Request Template

## Summary

Brief description of the changes in this PR.

## Type of Change

Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test improvements
- [ ] CI/CD changes

## Changes Made

- [ ] Add detailed list of changes
- [ ] Include any new files created
- [ ] Note any files modified or removed
- [ ] Mention configuration changes

## Testing

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Manual testing completed
- [ ] No regressions identified

## Validation

- [ ] Code follows project style guidelines
- [ ] Quality checks complete
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] New and existing unit tests pass locally with my changes

EOF
```

## 2. Issue Templates

```bash

## Create issue templates directory

mkdir -p .GitHub/ISSUE_TEMPLATE

## Bug report template

cat > .GitHub/ISSUE_TEMPLATE/bug_report.yml << 'EOF'
name: Bug Report
description: File a bug report to help us improve
title: "[Bug]: "
labels: ["bug", "triage"]
assignees: []

body:

- type: Markdown

  attributes:
  value: |
  Thanks for taking the time to fill out this bug report!

- type: textarea

  id: what-happened
  attributes:
  label: What happened?
  description: Also tell us, what did you expect to happen?
  placeholder: Tell us what you see!
  validations:
  required: true

- type: textarea

  id: steps
  attributes:
  label: Steps to Reproduce
  description: Please provide detailed steps to reproduce the issue
  placeholder: |

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

  validations:
  required: true

- type: checkboxes

  id: terms
  attributes:
  label: Code of Conduct
  description: By submitting this issue, you agree to follow our Code of Conduct
  options:

- label: I agree to follow this project's Code of Conduct

  required: true
EOF

## Feature request template

cat > .GitHub/ISSUE_TEMPLATE/feature_request.yml << 'EOF'
name: Feature Request
description: Suggest an idea for this project
title: "[Feature]: "
labels: ["enhancement", "feature-request"]
assignees: []

body:

- type: Markdown

  attributes:
  value: |
  Thanks for suggesting a new feature! Please provide as much detail as possible.

- type: textarea

  id: problem
  attributes:
  label: Is your feature request related to a problem?
  description: A clear and concise description of what the problem is.
  placeholder: I'm always frustrated when...
  validations:
  required: true

- type: textarea

  id: solution
  attributes:
  label: Describe the solution you'd like
  description: A clear and concise description of what you want to happen.
  validations:
  required: true
EOF
```

### ✅ **Automation Scripts**

## 1. Git Workflow Helper

```bash

## Create scripts/utils/Git-workflow.sh

mkdir -p scripts/utils
cat > scripts/utils/Git-workflow.sh << 'EOF'

## !/bin/bash

## Git Workflow Helper Script

## Implements industry-standard branching strategy

set -e

## Configuration

DEFAULT_BRANCH="main"
VERSION_FILE="VERSION"

## Colors for output

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

## Create feature branch

create_feature_branch() {
    local feature_name="$1"

    if [-z "$feature_name"]; then
        print_error "Feature name is required"
        echo "Usage: $0 feature <feature-name>"
        exit 1
    fi

    local branch_name="feature/$feature_name"

    print_status "Creating feature branch: $branch_name"

## Ensure we're on main and it's up to date

    Git checkout "$DEFAULT_BRANCH"
    Git pull origin "$DEFAULT_BRANCH"

## Create and switch to feature branch

    Git checkout -b "$branch_name"
    print_success "Created and switched to $branch_name"

## Set up tracking

    Git push -u origin "$branch_name" || true
}

## Show current status

show_status() {
    print_status "Git Workflow Status"
    echo ""
    echo "Current branch: $(Git branch --show-current)"
    echo "Repository status:"
    Git status --short
    echo ""
    echo "Recent commits:"
    Git log --oneline -5
}

## Main script logic

case "$1" in
    "feature")
        create_feature_branch "$2"
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Git Workflow Helper"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  feature <name>     Create a new feature branch"
        echo "  status             Show repository status"
        echo ""
        echo "Examples:"
        echo "  $0 feature user-authentication"
        echo "  $0 status"
        exit 1
        ;;
esac
EOF

chmod +x scripts/utils/Git-workflow.sh
```

## 2. Version Control Validation Script

```bash

## Create scripts/validation/validate-version-control.sh

mkdir -p scripts/validation
cat > scripts/validation/validate-version-control.sh << 'EOF'

## !/bin/bash 2

## Version Control Standards Validation Script

set -e

## Colors

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_failure() {
    echo -e "${RED}[✗]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

## Check required files

check_required_files() {
    print_status "Checking required version control files..."

    local required_files=(
        ".gitignore"
        ".gitmessage"
        "CHANGELOG.md"
        "VERSION"
    )

    for file in "${required_files[@]}"; do
        if [-f "$file"]; then
            print_success "Required file exists: $file"
        else
            print_failure "Required file missing: $file"
        fi
    done
}

## Check GitHub workflows

check_github_workflows() {
    print_status "Checking GitHub Actions workflows..."

    if [-f ".GitHub/workflows/ci.yml"]; then
        print_success "CI workflow exists"
    else
        print_failure "CI workflow missing"
    fi

    if [-f ".GitHub/workflows/release.yml"]; then
        print_success "Release workflow exists"
    else
        print_failure "Release workflow missing"
    fi
}

## Generate report

generate_report() {
    echo ""
    echo "======================================"
    echo "Version Control Validation Report"
    echo "======================================"
    echo ""
    echo "Total Checks: $TOTAL_CHECKS"
    echo -e "Passed: ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "Failed: ${RED}$CHECKS_FAILED${NC}"
    echo ""

    local pass_percentage=$((CHECKS_PASSED * 100 / TOTAL_CHECKS))
    echo "Pass Rate: $pass_percentage%"

    if [$CHECKS_FAILED -eq 0]; then
        echo -e "${GREEN}✓ All version control standards met!${NC}"
    else
        echo -e "${RED}✗ Version control improvements needed${NC}"
    fi
}

## Main execution

main() {
    echo "Version Control Standards Validator"
    echo ""

    check_required_files
    check_github_workflows

    generate_report
}

main "$@"
EOF

chmod +x scripts/validation/validate-version-control.sh
```

## 🔄 **Implementation Workflow**

### **Step 1: Use Automated Git Setup Tools**

Before manual configuration, check for existing automated setup tools:

```bash

## Use pre-built Git automation tools from toolshed

./scripts/tools/Git/setup-repository.sh --help
./scripts/tools/Git/setup-repository.sh --dry-run
./scripts/tools/Git/workflow-helper.sh --help
```

### **Step 2: Initialize Version Control**

```bash

## Run this command to implement all version control standards

./scripts/utils/implement-version-control.sh
```

### **Step 3: Validate Implementation**

```bash

## Verify all standards are met using automated validation

./scripts/validation/validate-version-control.sh
./scripts/tools/validation/validate-structure.sh --category Git
```

### **Step 4: Initial Commit**

```bash

## Stage all version control files

Git add .

## Commit with conventional format

Git commit -m "feat: implement industry-standard version control system

- Add comprehensive Git configuration and commit templates
- Implement semantic versioning with VERSION and CHANGELOG files
- Create CI/CD workflows for automated testing and releases
- Add GitHub templates for issues and pull requests
- Configure Git aliases and productivity tools
- Add validation scripts for compliance checking

BREAKING CHANGE: Repository now follows industry-standard version control practices"

## Create initial release tag

Git tag -a v1.0.0 -m "Initial release with version control implementation"
```

## 📋 **Conventional Commit Format**

All commits MUST follow this format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### **Commit Types:**

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring (no new features or fixes)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependency changes
- `ci`: CI/CD configuration changes
- `chore`: Maintenance tasks

### **Examples:**

```bash
Git commit -m "feat(auth): add OAuth2 authentication"
Git commit -m "fix(ui): resolve button alignment issue"
Git commit -m "docs: update installation instructions"
Git commit -m "refactor: simplify validation logic"
```

## 🛡️ **Security and Quality Standards**

### **Automated Security Scanning**

- Trivy vulnerability scanning on every PR
- Dependency review for security issues
- Secret detection in commit history
- SARIF report generation for security dashboard

### **Quality Gates**

- Markdown linting for documentation quality
- Link checking to prevent broken references
- Spell checking for professional documentation
- Code formatting validation

### **Branch Protection Rules**

```bash

## Recommended branch protection settings

## - Require pull request reviews

## - Require status checks to pass

## - Require branches to be up to date

## - Restrict pushes to main branch

## - Require signed commits (recommended)

```

## 📊 **Success Metrics**

### **Compliance Indicators:**

- ✅ 100% conventional commit adherence
- ✅ All CI/CD workflows passing
- ✅ Semantic versioning implemented
- ✅ Security scans with zero critical issues
- ✅ Documentation quality maintained

### **Quality Assurance:**

- All version control files present and configured
- GitHub workflows functional and validated
- Branch protection rules enabled
- Automated testing and deployment pipelines active

## 🚨 **Enforcement Policy**

### **MANDATORY Requirements:**

1. **Pre-Development**: Implement version control before any code changes
2. **Commit Standards**: All commits must follow conventional format
3. **Quality Gates**: All CI/CD checks must pass before merging
4. **Documentation**: Update CHANGELOG.md for all significant changes
5. **Security**: Address all critical security scan findings

### **Validation Commands:**

```bash

## Validate version control implementation

./scripts/validation/validate-version-control.sh

## Check commit message format

Git log --oneline -10 | grep -E '^[a-f0-9]+ (feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?: .+'

## Verify CI/CD workflows

ls -la .GitHub/workflows/

## Check GitHub templates

ls -la .GitHub/ISSUE_TEMPLATE/ .GitHub/pull_request_template.md
```

---

## This version control implementation is MANDATORY for all GitHub Copilot agents to ensure professional development standards and enterprise-grade repository management
