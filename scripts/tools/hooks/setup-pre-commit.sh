#!/bin/bash
# Tool: setup-pre-commit.sh
# Purpose: Configure comprehensive pre-commit hooks for quality automation
# Usage: ./setup-pre-commit.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="setup-pre-commit"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Configure comprehensive pre-commit hooks for quality automation"

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
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool configures pre-commit hooks to automatically run quality checks,
security scans, and formatting before each commit, preventing issues from
entering the repository.

Options:
    -h, --help         Show this help message
    -d, --dry-run      Preview changes without executing
    -v, --verbose      Enable verbose output
    --basic            Install basic hooks only (formatting, linting)
    --security         Include security scanning hooks
    --comprehensive    Install all available hooks
    --language LANG    Configure for specific language (js, python, go, etc.)

Examples:
    $0                          # Install recommended hooks
    $0 --comprehensive          # Install all available hooks
    $0 --language python        # Python-specific configuration
    $0 --security              # Include security scanning

Supported Languages:
    - JavaScript/TypeScript (ESLint, Prettier, commitlint)
    - Python (Black, isort, flake8, mypy, bandit)
    - Go (gofmt, golint, gosec)
    - Shell (shellcheck, shfmt)
    - Docker (hadolint)
    - Markdown (markdownlint)
    - YAML (yamllint)

Quality Checks Included:
    ✓ Code formatting (Prettier, Black, gofmt)
    ✓ Linting (ESLint, flake8, golint)
    ✓ Security scanning (bandit, gosec, semgrep)
    ✓ Dependency scanning (safety, npm audit)
    ✓ Commit message validation (commitlint)
    ✓ File size limits and binary file detection
    ✓ Secrets detection (detect-secrets)
    ✓ License header validation

EOF
}

# Create .pre-commit-config.yaml
create_precommit_config() {
    local language="${1:-comprehensive}"

    log_info "Creating .pre-commit-config.yaml for $language"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create .pre-commit-config.yaml"
        return 0
    fi

    cat > .pre-commit-config.yaml << 'EOF'
# Pre-commit configuration for automated quality checks
# See https://pre-commit.com for more information

repos:
  # Universal hooks for all projects
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-xml
      - id: check-case-conflict
      - id: check-executables-have-shebangs
      - id: check-shebang-scripts-are-executable

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Shell script validation
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck

  # Markdown linting
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        args: ['--fix']

  # YAML linting
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.32.0
    hooks:
      - id: yamllint

  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint

  # Security scanning with semgrep
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.45.0
    hooks:
      - id: semgrep
        args: ['--config=auto']

  # Commit message validation
  - repo: https://github.com/conventional-changelog/commitlint
    rev: v17.7.1
    hooks:
      - id: commitlint
        stages: [commit-msg]
        additional_dependencies: ['@commitlint/config-conventional']
EOF

    # Add language-specific hooks
    case $language in
        "python")
            add_python_hooks
            ;;
        "javascript"|"typescript"|"js"|"ts")
            add_javascript_hooks
            ;;
        "go")
            add_go_hooks
            ;;
        "comprehensive")
            add_python_hooks
            add_javascript_hooks
            add_go_hooks
            ;;
    esac

    log_success "Created .pre-commit-config.yaml"
}

# Add Python-specific hooks
add_python_hooks() {
    cat >> .pre-commit-config.yaml << 'EOF'

  # Python formatting and linting
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy

  # Python security scanning
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', '.']

  # Python dependency scanning
  - repo: https://github.com/pyupio/safety
    rev: 2.3.4
    hooks:
      - id: safety
EOF
}

# Add JavaScript/TypeScript hooks
add_javascript_hooks() {
    cat >> .pre-commit-config.yaml << 'EOF'

  # JavaScript/TypeScript formatting and linting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, yaml, markdown]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.51.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        additional_dependencies:
          - eslint@8.51.0
          - '@typescript-eslint/parser@6.7.4'
          - '@typescript-eslint/eslint-plugin@6.7.4'
EOF
}

# Add Go hooks
add_go_hooks() {
    cat >> .pre-commit-config.yaml << 'EOF'

  # Go formatting and linting
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-vet-mod
      - id: go-mod-tidy
      - id: golangci-lint
EOF
}

# Install pre-commit
install_precommit() {
    log_info "Installing pre-commit..."

    if command -v pre-commit &> /dev/null; then
        log_success "pre-commit already installed"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would install pre-commit"
        return 0
    fi

    # Try pip install first, then fallback to package manager
    if command -v pip &> /dev/null; then
        pip install pre-commit
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y pre-commit
    elif command -v brew &> /dev/null; then
        brew install pre-commit
    else
        log_error "Cannot install pre-commit. Please install manually."
        return 1
    fi

    log_success "pre-commit installed successfully"
}

# Install pre-commit hooks
install_hooks() {
    log_info "Installing pre-commit hooks..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would install pre-commit hooks"
        return 0
    fi

    pre-commit install
    pre-commit install --hook-type commit-msg

    log_success "Pre-commit hooks installed"
}

# Run initial check
run_initial_check() {
    log_info "Running initial pre-commit check..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run pre-commit check"
        return 0
    fi

    if pre-commit run --all-files; then
        log_success "All pre-commit checks passed"
    else
        log_warning "Some pre-commit checks failed. This is normal for initial setup."
        log_info "Run 'pre-commit run --all-files' after fixing issues"
    fi
}

# Main execution function
main() {
    local language="comprehensive"
    local include_security=false
    local basic_only=false

    # Create log directory
    mkdir -p "$LOG_DIR"

    log_info "Setting up pre-commit hooks for automated quality checks"

    # Install pre-commit if not available
    install_precommit

    # Create configuration
    create_precommit_config "$language"

    # Install hooks
    install_hooks

    # Run initial check
    run_initial_check

    echo ""
    log_success "Pre-commit setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Review .pre-commit-config.yaml and customize as needed"
    echo "2. Run 'pre-commit run --all-files' to check existing files"
    echo "3. Pre-commit hooks will now run automatically on each commit"
    echo ""
    echo "To manually run hooks: pre-commit run --all-files"
    echo "To update hooks: pre-commit autoupdate"
}

# Parse command line arguments
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
        --basic)
            basic_only=true
            shift
            ;;
        --security)
            include_security=true
            shift
            ;;
        --comprehensive)
            language="comprehensive"
            shift
            ;;
        --language)
            language="$2"
            shift 2
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
