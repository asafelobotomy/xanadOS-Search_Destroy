#!/bin/bash

# Tool: setup-repository.sh
# Purpose: Initialize repository with industry-standard version control
# Usage: ./setup-repository.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="setup-repository"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Initialize repository with industry-standard version control"

# Configuration
LOG_DIR="logs/toolshed"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_DIR/setup-repository.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$LOG_DIR/setup-repository.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_DIR/setup-repository.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOG_DIR/setup-repository.log"
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool sets up a repository with:
- Git configuration and commit templates
- Comprehensive .gitignore
- Semantic versioning (VERSION file)
- CHANGELOG.md structure
- GitHub workflows and templates
- Branch protection and hooks

Options:
    -h, --help         Show this help message
    -d, --dry-run      Preview changes without executing
    -v, --verbose      Enable verbose output
    --version          Show version information
    --skip-git         Skip Git configuration
    --skip-github      Skip GitHub templates and workflows
    --skip-hooks       Skip Git hooks setup

Examples:
    $0                 # Full repository setup
    $0 --dry-run       # Preview what would be created
    $0 --skip-github   # Setup without GitHub-specific files

EOF
}

# Initialize logging
setup_logging() {
    mkdir -p "$LOG_DIR"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [START] Repository setup initiated" >> "$LOG_DIR/setup-repository.log"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if git is installed
    if ! command -v git >/dev/null 2>&1; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi

    # Check if we're in a git repository or can initialize one
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        if [[ "$DRY_RUN" == "false" ]]; then
            log_info "Initializing Git repository..."
            git init
            log_success "Git repository initialized"
        else
            log_info "[DRY RUN] Would initialize Git repository"
        fi
    else
        log_success "Git repository detected"
    fi
}

# Create Git commit message template
create_commit_template() {
    log_info "Creating Git commit message template..."

    local template_content='# <type>[optional scope]: <description>
#
# [optional body]
#
# [optional footer(s)]

# Type can be one of:
# feat:     A new feature
# fix:      A bug fix
# docs:     Documentation only changes
# style:    Changes that do not affect the meaning of the code
# refactor: A code change that neither fixes a bug nor adds a feature
# perf:     A code change that improves performance
# test:     Adding missing tests or correcting existing tests
# build:    Changes that affect the build system or external dependencies
# ci:       Changes to CI configuration files and scripts
# chore:    Other changes that don'\''t modify src or test files
# revert:   Reverts a previous commit

# Examples:
# feat(auth): add OAuth2 authentication
# fix(ui): resolve button alignment issue
# docs: update installation instructions
# refactor: simplify validation logic

# Remember:
# - Use the imperative mood in the subject line
# - Do not end the subject line with a period
# - Separate subject from body with a blank line
# - Use the body to explain what and why vs. how
# - Each line should be no longer than 72 characters'

    if [[ "$DRY_RUN" == "false" ]]; then
        echo "$template_content" > .gitmessage
        git config commit.template .gitmessage
        log_success "Commit message template created and configured"
    else
        log_info "[DRY RUN] Would create .gitmessage and configure Git"
    fi
}

# Configure Git settings
configure_git() {
    log_info "Configuring Git settings..."

    if [[ "$DRY_RUN" == "false" ]]; then
        # Configure pull strategy
        git config pull.rebase false

        # Set default branch
        git config init.defaultBranch main

        # Configure useful aliases
        git config alias.co checkout
        git config alias.br branch
        git config alias.ci commit
        git config alias.st status
        git config alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
        git config alias.unstage 'reset HEAD --'
        git config alias.last 'log -1 HEAD'

        log_success "Git configuration completed"
    else
        log_info "[DRY RUN] Would configure Git settings and aliases"
    fi
}

# Create comprehensive .gitignore
create_gitignore() {
    log_info "Creating comprehensive .gitignore..."

    if [[ -f .gitignore ]] && [[ "$DRY_RUN" == "false" ]]; then
        log_warning ".gitignore already exists, backing up to .gitignore.backup"
        cp .gitignore .gitignore.backup
    fi

    local gitignore_content='# Node.js dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Optional REPL history
.node_repl_history

# Output of '\''npm pack'\''
*.tgz

# Yarn Integrity file
.yarn-integrity

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE and Editor files
.vscode/settings.json
.vscode/launch.json
.vscode/tasks.json
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Logs
logs/
*.log

# Backup files
*.bak
*.backup
*.old

# Test outputs
test-results/
test-reports/
.pytest_cache/

# Build outputs
build/
dist/
out/

# Package managers
.yarn/
.pnp.*

# Security
*.key
*.pem
*.p12
*.pfx
secrets/
.secrets

# Local configuration
config.local.*
settings.local.*

# Documentation build
docs/_build/
site/

# Jupyter Notebook
.ipynb_checkpoints

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Docker
.dockerignore
Dockerfile.local

# Kubernetes
*.kubeconfig

# Archive and backups
archive/workspace-backup-*
archive/.tmp/
archive/*.processing
archive/*.staging

# Toolshed logs
logs/toolshed/'

    if [[ "$DRY_RUN" == "false" ]]; then
        echo "$gitignore_content" > .gitignore
        log_success ".gitignore created with comprehensive patterns"
    else
        log_info "[DRY RUN] Would create comprehensive .gitignore"
    fi
}

# Create VERSION file for semantic versioning
create_version_file() {
    log_info "Creating VERSION file for semantic versioning..."

    local version_content='# Semantic Versioning
VERSION_MAJOR=1
VERSION_MINOR=0
VERSION_PATCH=0
VERSION_BUILD=$(git rev-list --count HEAD 2>/dev/null || echo "0")

# Current version string
VERSION="${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}"
VERSION_FULL="${VERSION}.${VERSION_BUILD}"

echo $VERSION_FULL'

    if [[ "$DRY_RUN" == "false" ]]; then
        echo "$version_content" > VERSION
        chmod +x VERSION
        log_success "VERSION file created with semantic versioning"
    else
        log_info "[DRY RUN] Would create VERSION file"
    fi
}

# Create CHANGELOG.md
create_changelog() {
    log_info "Creating CHANGELOG.md..."

    local changelog_content="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository setup with industry-standard version control
- Git configuration and commit templates
- Semantic versioning system
- Comprehensive .gitignore patterns

## [1.0.0] - $(date +%Y-%m-%d)

### Added

- Initial project setup
- Version control implementation
- Professional development standards

### Security

- Comprehensive .gitignore to prevent sensitive data commits
- Git configuration following security best practices"

    if [[ "$DRY_RUN" == "false" ]]; then
        echo "$changelog_content" > CHANGELOG.md
        log_success "CHANGELOG.md created"
    else
        log_info "[DRY RUN] Would create CHANGELOG.md"
    fi
}

# Create GitHub workflows and templates
create_github_files() {
    if [[ "$SKIP_GITHUB" == "true" ]]; then
        log_info "Skipping GitHub files creation"
        return
    fi

    log_info "Creating GitHub workflows and templates..."

    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p .github/workflows
        mkdir -p .github/ISSUE_TEMPLATE

        # Create basic CI workflow
        cat > .github/workflows/ci.yml << 'EOF'
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

permissions:
  contents: read
  issues: write
  pull-requests: write
  checks: write

jobs:
  validation:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: |
          if [ -f package.json ]; then
            npm ci
          else
            echo "No package.json found, skipping npm install"
          fi

      - name: Run validation scripts
        run: |
          if [ -f scripts/tools/validation/validate-structure.sh ]; then
            chmod +x scripts/tools/validation/validate-structure.sh
            ./scripts/tools/validation/validate-structure.sh
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
          format: 'table'
EOF

        # Create pull request template
        cat > .github/pull_request_template.md << 'EOF'
# Pull Request

## Summary

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test improvements
- [ ] CI/CD changes

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
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] New and existing unit tests pass locally with my changes
EOF

        # Create bug report template
        cat > .github/ISSUE_TEMPLATE/bug_report.yml << 'EOF'
name: Bug Report
description: File a bug report to help us improve
title: "[Bug]: "
labels: ["bug", "triage"]

body:
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
        3. See error
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: What environment are you using?
      placeholder: |
        - OS: [e.g. macOS, Ubuntu]
        - Browser: [e.g. Chrome, Firefox]
        - Version: [e.g. 1.0.0]
    validations:
      required: true
EOF

        log_success "GitHub workflows and templates created"
    else
        log_info "[DRY RUN] Would create GitHub workflows and templates"
    fi
}

# Setup Git hooks
setup_git_hooks() {
    if [[ "$SKIP_HOOKS" == "true" ]]; then
        log_info "Skipping Git hooks setup"
        return
    fi

    log_info "Setting up Git hooks..."

    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p .git/hooks

        # Create commit-msg hook for conventional commits
        cat > .git/hooks/commit-msg << 'EOF'
#!/bin/sh
# Validate conventional commit message format

commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!" >&2
    echo "Expected: <type>[optional scope]: <description>" >&2
    echo "Example: feat(auth): add OAuth2 authentication" >&2
    exit 1
fi
EOF

        chmod +x .git/hooks/commit-msg
        log_success "Git hooks configured"
    else
        log_info "[DRY RUN] Would setup Git hooks"
    fi
}

# Main execution function
main() {
    log_info "Starting repository setup..."

    setup_logging
    check_prerequisites

    if [[ "$SKIP_GIT" != "true" ]]; then
        create_commit_template
        configure_git
    fi

    create_gitignore
    create_version_file
    create_changelog
    create_github_files
    setup_git_hooks

    log_success "Repository setup completed!"

    echo ""
    echo "Next steps:"
    echo "1. Review and customize the created files as needed"
    echo "2. Stage and commit these changes:"
    echo "   git add ."
    echo "   git commit -m \"feat: implement industry-standard repository setup\""
    echo "3. Create initial tag:"
    echo "   git tag -a v1.0.0 -m \"Initial release\""
    echo ""
    log_success "Repository is now ready for professional development!"
}

# Parse command line arguments
SKIP_GIT=false
SKIP_GITHUB=false
SKIP_HOOKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --version)
            echo "$TOOL_NAME version $TOOL_VERSION"
            exit 0
            ;;
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --skip-github)
            SKIP_GITHUB=true
            shift
            ;;
        --skip-hooks)
            SKIP_HOOKS=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage >&2
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"
