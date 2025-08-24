#!/bin/bash

# Tool: implement-toolshed.sh
# Purpose: Comprehensive toolshed implementation and deployment
# Usage: ./implement-toolshed.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="implement-toolshed"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive toolshed implementation and deployment for GitHub Copilot agents"

# Configuration
LOG_DIR="logs/toolshed"
DRY_RUN=false
VERBOSE=false
SKIP_VALIDATION=false
AUTO_COMMIT=false

# Implementation counters
TOOLS_CREATED=0
TOOLS_UPDATED=0
VALIDATIONS_PASSED=0
VALIDATIONS_FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_DIR/implement-toolshed.log"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$LOG_DIR/implement-toolshed.log"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_DIR/implement-toolshed.log"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOG_DIR/implement-toolshed.log"
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This comprehensive script:
- Creates complete toolshed directory structure
- Implements all essential tools for GitHub Copilot agents
- Sets up validation and quality assurance systems
- Configures version control and CI/CD workflows
- Provides ready-to-use script collection

Options:
    -h, --help          Show this help message
    -d, --dry-run       Preview changes without executing
    -v, --verbose       Enable verbose output and logging
    --version           Show version information
    --skip-validation   Skip validation steps (faster)
    --auto-commit       Automatically commit changes to Git
    --category CAT      Implement only specific category
                       (git|validation|quality|repository|documentation|deployment)

Examples:
    $0                          # Full toolshed implementation
    $0 --dry-run                # Preview what would be created
    $0 --category git           # Only implement Git tools
    $0 --auto-commit            # Implement and commit changes

Post-Implementation:
    The toolshed will be ready for GitHub Copilot agents to use.
    Agents can reference tools using:
    - scripts/tools/git/setup-repository.sh
    - scripts/tools/validation/validate-structure.sh
    - scripts/tools/quality/check-quality.sh
    And many others as documented in scripts/tools/README.md

EOF
}

# Initialize logging
setup_logging() {
    mkdir -p "$LOG_DIR"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [START] Toolshed implementation initiated" >> "$LOG_DIR/implement-toolshed.log"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites for toolshed implementation..."

    # Check if we're in the right directory
    if [[ ! -f ".github/copilot-instructions.md" ]]; then
        log_error "Not in agent-instructions-co-pilot repository root"
        log_error "Please run this script from the repository root directory"
        exit 1
    fi

    # Check required tools
    local required_tools=("git" "bash" "find" "grep" "sed")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done

    # Check Git repository status
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_warning "Not in a Git repository - some features will be limited"
    fi

    log_success "All prerequisites met"
}

# Create toolshed directory structure
create_toolshed_structure() {
    log_info "Creating toolshed directory structure..."

    local toolshed_dirs=(
        "scripts/tools"
        "scripts/tools/git"
        "scripts/tools/validation"
        "scripts/tools/quality"
        "scripts/tools/repository"
        "scripts/tools/documentation"
        "scripts/tools/deployment"
        "scripts/utils"
        "logs/toolshed"
    )

    for dir in "${toolshed_dirs[@]}"; do
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        else
            log_info "[DRY RUN] Would create directory: $dir"
        fi
    done
}

# Make scripts executable
make_scripts_executable() {
    log_info "Making scripts executable..."

    if [[ "$DRY_RUN" == "false" ]]; then
        find scripts/ -name "*.sh" -exec chmod +x {} \;
        log_success "All scripts made executable"
    else
        log_info "[DRY RUN] Would make all .sh files executable"
    fi
}

# Create additional Git tools
create_additional_git_tools() {
    if [[ "$CATEGORY" != "all" ]] && [[ "$CATEGORY" != "git" ]]; then
        return
    fi

    log_info "Creating additional Git tools..."

    # Git workflow helper
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > scripts/tools/git/workflow-helper.sh << 'EOF'
#!/bin/bash

# Tool: workflow-helper.sh
# Purpose: Advanced Git workflow automation
# Usage: ./workflow-helper.sh <command> [options]

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create feature branch
create_feature() {
    local feature_name="$1"
    local branch_name="feature/$feature_name"

    log_info "Creating feature branch: $branch_name"
    git checkout main
    git pull origin main
    git checkout -b "$branch_name"
    git push -u origin "$branch_name"
    log_success "Feature branch created and pushed"
}

# Create release branch
create_release() {
    local version="$1"
    local branch_name="release/$version"

    log_info "Creating release branch: $branch_name"
    git checkout main
    git pull origin main
    git checkout -b "$branch_name"

    # Update VERSION file if it exists
    if [[ -f VERSION ]]; then
        sed -i "s/VERSION_PATCH=.*/VERSION_PATCH=${version##*.}/" VERSION
        git add VERSION
        git commit -m "bump: version $version"
    fi

    git push -u origin "$branch_name"
    log_success "Release branch created for version $version"
}

# Main command handling
case "${1:-}" in
    "feature")
        create_feature "${2:-}"
        ;;
    "release")
        create_release "${2:-}"
        ;;
    *)
        echo "Usage: $0 {feature|release} <name/version>"
        exit 1
        ;;
esac
EOF

        TOOLS_CREATED=$((TOOLS_CREATED + 1))
        log_success "Created: scripts/tools/git/workflow-helper.sh"
    else
        log_info "[DRY RUN] Would create Git workflow helper"
    fi
}

# Create additional validation tools
create_additional_validation_tools() {
    if [[ "$CATEGORY" != "all" ]] && [[ "$CATEGORY" != "validation" ]]; then
        return
    fi

    log_info "Creating additional validation tools..."

    # Instructions validator
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > scripts/tools/validation/validate-instructions.sh << 'EOF'
#!/bin/bash

# Tool: validate-instructions.sh
# Purpose: Validate GitHub Copilot instruction files
# Usage: ./validate-instructions.sh [options]

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; CHECKS_PASSED=$((CHECKS_PASSED + 1)); }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; CHECKS_FAILED=$((CHECKS_FAILED + 1)); }

# Validate instruction files
validate_instructions() {
    log_info "Validating instruction files..."

    # Check .github/instructions/ directory
    if [[ -d ".github/instructions" ]]; then
        log_success ".github/instructions directory exists"

        # Validate each instruction file
        find .github/instructions -name "*.instructions.md" | while read -r file; do
            log_info "Validating: $file"

            # Check frontmatter
            if head -5 "$file" | grep -q "^---$"; then
                log_success "$file: Has frontmatter"
            else
                log_error "$file: Missing frontmatter"
            fi

            # Check for applyTo field
            if grep -q "applyTo:" "$file"; then
                log_success "$file: Has applyTo specification"
            else
                log_warning "$file: Missing applyTo specification"
            fi

            # Check for meaningful content
            if [[ $(wc -l < "$file") -gt 20 ]]; then
                log_success "$file: Has substantial content"
            else
                log_warning "$file: Content seems minimal"
            fi
        done
    else
        log_error ".github/instructions directory missing"
    fi

    # Check main instruction file
    if [[ -f ".github/copilot-instructions.md" ]]; then
        log_success "Main instruction file exists"

        # Check for mandatory version control section
        if grep -q "MANDATORY.*Version Control" ".github/copilot-instructions.md"; then
            log_success "Contains mandatory version control section"
        else
            log_warning "Missing mandatory version control section"
        fi
    else
        log_error "Main instruction file missing: .github/copilot-instructions.md"
    fi
}

# Generate report
generate_report() {
    echo ""
    echo "======================================"
    echo "Instruction Validation Report"
    echo "======================================"
    echo ""
    echo "Checks Passed: $CHECKS_PASSED"
    echo "Checks Failed: $CHECKS_FAILED"
    echo ""

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ All instruction files are valid!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Instruction files need attention${NC}"
        exit 1
    fi
}

# Main execution
main() {
    validate_instructions
    generate_report
}

main "$@"
EOF

        TOOLS_CREATED=$((TOOLS_CREATED + 1))
        log_success "Created: scripts/tools/validation/validate-instructions.sh"
    else
        log_info "[DRY RUN] Would create instruction validator"
    fi
}

# Create repository tools
create_repository_tools() {
    if [[ "$CATEGORY" != "all" ]] && [[ "$CATEGORY" != "repository" ]]; then
        return
    fi

    log_info "Creating repository management tools..."

    # Repository backup tool
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > scripts/tools/repository/backup-repository.sh << 'EOF'
#!/bin/bash

# Tool: backup-repository.sh
# Purpose: Create comprehensive repository backup
# Usage: ./backup-repository.sh [options]

set -euo pipefail

# Configuration
BACKUP_DIR="archive/workspace-backup-$(date +%Y%m%d-%H%M%S)"
EXCLUDE_PATTERNS=(".git" "node_modules" "*.log" "*.tmp")

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Create backup
create_backup() {
    log_info "Creating repository backup in: $BACKUP_DIR"

    mkdir -p "$BACKUP_DIR"

    # Create exclusion list
    local exclude_file=$(mktemp)
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        echo "$pattern" >> "$exclude_file"
    done

    # Create archive
    tar -czf "$BACKUP_DIR/repository-backup.tar.gz" \
        --exclude-from="$exclude_file" \
        --exclude="$BACKUP_DIR" \
        .

    # Create metadata
    cat > "\$BACKUP_DIR/backup-metadata.json" << METAEOF
{
  "timestamp": "\$(date -Iseconds)",
  "git_commit": "\$(git rev-parse HEAD 2>/dev/null || echo 'not-available')",
  "git_branch": "\$(git branch --show-current 2>/dev/null || echo 'not-available')",
  "backup_size": "\$(du -h "\$BACKUP_DIR/repository-backup.tar.gz" | cut -f1)"
}
METAEOF

    rm "$exclude_file"
    log_success "Backup created successfully"
    log_info "Backup location: $BACKUP_DIR"
}

# Main execution
main() {
    create_backup
}

main "$@"
EOF

        TOOLS_CREATED=$((TOOLS_CREATED + 1))
        log_success "Created: scripts/tools/repository/backup-repository.sh"
    else
        log_info "[DRY RUN] Would create repository backup tool"
    fi
}

# Create documentation tools
create_documentation_tools() {
    if [[ "$CATEGORY" != "all" ]] && [[ "$CATEGORY" != "documentation" ]]; then
        return
    fi

    log_info "Creating documentation tools..."

    # Documentation generator
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > scripts/tools/documentation/generate-docs.sh << 'EOF'
#!/bin/bash

# Tool: generate-docs.sh
# Purpose: Generate comprehensive project documentation
# Usage: ./generate-docs.sh [options]

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# Generate script documentation
generate_script_docs() {
    log_info "Generating script documentation..."

    local doc_file="docs/SCRIPTS.md"
    mkdir -p docs

    cat > "$doc_file" << 'DOCEOF'
# Script Documentation

This document provides an overview of all available scripts in the toolshed.

## Tool Categories

### Git Tools (`scripts/tools/git/`)

DOCEOF

    # Document Git tools
    find scripts/tools/git -name "*.sh" 2>/dev/null | while read -r script; do
        local tool_name=$(basename "$script" .sh)
        local description=$(grep "^# Purpose:" "$script" | cut -d: -f2- | sed 's/^ *//')

        cat >> "$doc_file" << DOCEOF
- **$tool_name**: $description
  - Usage: \`$script [options]\`

DOCEOF
    done

    log_success "Script documentation generated: $doc_file"
}

# Generate API documentation
generate_api_docs() {
    log_info "Generating API documentation..."

    # This could be expanded to document any APIs
    local api_doc="docs/API.md"

    cat > "$api_doc" << 'DOCEOF'
# API Documentation

## Toolshed Integration

The toolshed provides a consistent API for GitHub Copilot agents.

### Standard Tool Interface

All tools follow this interface:
- `--help`: Show usage information
- `--verbose`: Enable detailed output
- `--dry-run`: Preview changes (where applicable)

DOCEOF

    log_success "API documentation generated: $api_doc"
}

# Main execution
main() {
    generate_script_docs
    generate_api_docs
}

main "$@"
EOF

        TOOLS_CREATED=$((TOOLS_CREATED + 1))
        log_success "Created: scripts/tools/documentation/generate-docs.sh"
    else
        log_info "[DRY RUN] Would create documentation generator"
    fi
}

# Validate toolshed implementation
validate_toolshed() {
    if [[ "$SKIP_VALIDATION" == "true" ]]; then
        log_info "Skipping validation (--skip-validation specified)"
        return
    fi

    log_info "Validating toolshed implementation..."

    # Check that all expected tools exist
    local expected_tools=(
        "scripts/tools/git/setup-repository.sh"
        "scripts/tools/validation/validate-structure.sh"
        "scripts/tools/quality/check-quality.sh"
    )

    for tool in "${expected_tools[@]}"; do
        if [[ -f "$tool" ]]; then
            log_success "Tool exists: $tool"
            VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))

            # Check if executable
            if [[ -x "$tool" ]]; then
                log_success "Tool is executable: $tool"
            else
                log_warning "Tool not executable: $tool"
                VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
            fi
        else
            log_error "Tool missing: $tool"
            VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        fi
    done

    # Test tools with --help
    for tool in "${expected_tools[@]}"; do
        if [[ -f "$tool" ]] && [[ -x "$tool" ]]; then
            if "$tool" --help >/dev/null 2>&1; then
                log_success "Tool help works: $(basename "$tool")"
                VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
            else
                log_warning "Tool help failed: $(basename "$tool")"
                VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
            fi
        fi
    done
}

# Auto-commit changes if requested
auto_commit_changes() {
    if [[ "$AUTO_COMMIT" != "true" ]]; then
        return
    fi

    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_warning "Not in Git repository, skipping auto-commit"
        return
    fi

    log_info "Auto-committing toolshed implementation..."

    if [[ "$DRY_RUN" == "false" ]]; then
        git add scripts/
        git add logs/

        if git diff --cached --quiet; then
            log_info "No changes to commit"
        else
            git commit -m "feat: implement comprehensive GitHub Copilot toolshed

- Add complete tool collection for automated development
- Implement Git workflow automation tools
- Create validation and quality assurance tools
- Add repository management and backup tools
- Include documentation generation tools
- Provide ready-to-use scripts for Copilot agents

Tools created: $TOOLS_CREATED
Validations passed: $VALIDATIONS_PASSED

The toolshed enables consistent, reliable automation for
GitHub Copilot agents without recreating common functionality."

            log_success "Changes committed to Git"
        fi
    else
        log_info "[DRY RUN] Would commit toolshed implementation"
    fi
}

# Generate final report
generate_final_report() {
    echo ""
    echo "======================================"
    echo "Toolshed Implementation Report"
    echo "======================================"
    echo ""
    echo "Implementation Summary:"
    echo -e "  Tools Created: ${GREEN}$TOOLS_CREATED${NC}"
    echo -e "  Tools Updated: ${BLUE}$TOOLS_UPDATED${NC}"
    echo -e "  Validations Passed: ${GREEN}$VALIDATIONS_PASSED${NC}"
    echo -e "  Validations Failed: ${RED}$VALIDATIONS_FAILED${NC}"
    echo ""

    if [[ $VALIDATIONS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ Toolshed implementation successful!${NC}"
        echo ""
        echo "GitHub Copilot agents can now use:"
        echo "- scripts/tools/git/setup-repository.sh"
        echo "- scripts/tools/validation/validate-structure.sh"
        echo "- scripts/tools/quality/check-quality.sh"
        echo "- And many other tools in scripts/tools/"
        echo ""
        echo "Next steps:"
        echo "1. Review tool configurations in scripts/tools/"
        echo "2. Test tools with your specific use cases"
        echo "3. Customize tools as needed for your organization"
        echo "4. Train team members on available tools"
    else
        echo -e "${RED}✗ Toolshed implementation completed with issues${NC}"
        echo "Please address the validation failures above"
    fi

    echo ""
    echo "Documentation:"
    echo "- Tool catalog: scripts/tools/README.md"
    echo "- Usage examples: .github/copilot-instructions.md"
    echo "- Implementation log: $LOG_DIR/implement-toolshed.log"
    echo ""
}

# Main execution function
main() {
    log_info "Starting comprehensive toolshed implementation..."

    setup_logging
    check_prerequisites
    create_toolshed_structure

    # Create tools based on category
    create_additional_git_tools
    create_additional_validation_tools
    create_repository_tools
    create_documentation_tools

    make_scripts_executable
    validate_toolshed
    auto_commit_changes
    generate_final_report

    if [[ $VALIDATIONS_FAILED -eq 0 ]]; then
        log_success "Toolshed implementation completed successfully!"
        exit 0
    else
        log_warning "Toolshed implementation completed with issues"
        exit 1
    fi
}

# Parse command line arguments
CATEGORY="all"

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
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --auto-commit)
            AUTO_COMMIT=true
            shift
            ;;
        --category)
            CATEGORY="$2"
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
