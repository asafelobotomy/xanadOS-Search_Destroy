#!/bin/bash

# Version Control Implementation Script for GitHub Copilot Agents
# Implements industry-standard version control practices automatically

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository. Initialize with 'git init' first."
        exit 1
    fi
    print_success "Git repository detected"
}

# Create commit message template
create_commit_template() {
    print_status "Creating Git commit message template..."

    cat > .gitmessage << 'EOF'
# <type>[optional scope]: <description>
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
# chore:    Other changes that don't modify src or test files
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
# - Each line should be no longer than 72 characters
EOF

    git config commit.template .gitmessage
    print_success "Commit message template created and configured"
}

# Configure Git settings
configure_git() {
    print_status "Configuring Git settings..."

    # Configure pull strategy
    git config pull.rebase false
    print_success "Pull strategy set to merge"

    # Set default branch
    git config init.defaultBranch main
    print_success "Default branch set to main"

    # Configure useful aliases
    git config alias.co checkout
    git config alias.br branch
    git config alias.ci commit
    git config alias.st status
    git config alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

    print_success "Git aliases configured"
}

# Create comprehensive .gitignore
create_gitignore() {
    if [ -f .gitignore ]; then
        print_warning ".gitignore already exists, backing up to .gitignore.backup"
        cp .gitignore .gitignore.backup
    fi

    print_status "Creating comprehensive .gitignore..."

    cat > .gitignore << 'EOF'
# Node.js dependencies
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

# Output of 'npm pack'
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

# Archive
archive/workspace-backup-*
EOF

    print_success ".gitignore created with comprehensive patterns"
}

# Create VERSION file
create_version_file() {
    print_status "Creating VERSION file for semantic versioning..."

    cat > VERSION << 'EOF'
# Semantic Versioning
VERSION_MAJOR=1
VERSION_MINOR=0
VERSION_PATCH=0
VERSION_BUILD=$(git rev-list --count HEAD 2>/dev/null || echo "0")

# Current version string
VERSION="${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}"
VERSION_FULL="${VERSION}.${VERSION_BUILD}"

echo $VERSION_FULL
EOF

    chmod +x VERSION
    print_success "VERSION file created with semantic versioning"
}

# Create CHANGELOG.md
create_changelog() {
    print_status "Creating CHANGELOG.md..."

    cat > CHANGELOG.md << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Version control implementation with industry standards
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
- Git configuration following security best practices
EOF

    print_success "CHANGELOG.md created"
}

# Create GitHub workflows directory and basic CI
create_github_workflows() {
    print_status "Creating GitHub workflows..."

    mkdir -p .github/workflows

    cat > .github/workflows/ci.yml << 'EOF'
name: Continuous Integration

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
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
          if [ -f scripts/validation/validate-version-control.sh ]; then
            chmod +x scripts/validation/validate-version-control.sh
            ./scripts/validation/validate-version-control.sh
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

  markdown-lint:
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
        run: |
          if ls *.md 1> /dev/null 2>&1; then
            markdownlint "*.md" --ignore node_modules --ignore archive || true
          else
            echo "No markdown files found"
          fi
EOF

    print_success "GitHub CI workflow created"
}

# Create basic GitHub templates
create_github_templates() {
    print_status "Creating GitHub templates..."

    mkdir -p .github/ISSUE_TEMPLATE

    # Pull request template
    cat > .github/pull_request_template.md << 'EOF'
# Pull Request

## Summary

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Tests pass locally
- [ ] Manual testing completed
- [ ] No regressions identified

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have made corresponding changes to the documentation
- [ ] New and existing tests pass locally with my changes
EOF

    # Bug report template
    cat > .github/ISSUE_TEMPLATE/bug_report.yml << 'EOF'
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug"]

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
EOF

    print_success "GitHub templates created"
}

# Create utility scripts directory
create_utility_scripts() {
    print_status "Creating utility scripts..."

    mkdir -p scripts/utils
    mkdir -p scripts/validation

    # Simple validation script
    cat > scripts/validation/validate-version-control.sh << 'EOF'
#!/bin/bash

# Basic version control validation script

set -e

echo "Validating version control implementation..."

# Check required files
required_files=(".gitignore" ".gitmessage" "CHANGELOG.md" "VERSION")

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
        exit 1
    fi
done

# Check git configuration
if git config --get commit.template > /dev/null 2>&1; then
    echo "✓ Git commit template configured"
else
    echo "✗ Git commit template not configured"
    exit 1
fi

echo "✅ Version control validation passed!"
EOF

    chmod +x scripts/validation/validate-version-control.sh

    print_success "Utility scripts created"
}

# Main execution
main() {
    echo "================================================"
    echo "Version Control Implementation for GitHub Copilot"
    echo "================================================"
    echo ""

    check_git_repo
    create_commit_template
    configure_git
    create_gitignore
    create_version_file
    create_changelog
    create_github_workflows
    create_github_templates
    create_utility_scripts

    echo ""
    echo "================================================"
    echo "Version Control Implementation Complete!"
    echo "================================================"
    echo ""
    echo "Next steps:"
    echo "1. Review and customize the created files as needed"
    echo "2. Stage and commit these changes:"
    echo "   git add ."
    echo "   git commit -m \"feat: implement industry-standard version control\""
    echo "3. Create initial tag:"
    echo "   git tag -a v1.0.0 -m \"Initial release\""
    echo "4. Validate implementation:"
    echo "   ./scripts/validation/validate-version-control.sh"
    echo ""
    echo "✅ Repository is now ready for professional development!"
}

# Run main function
main "$@"
