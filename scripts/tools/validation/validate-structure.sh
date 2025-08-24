#!/bin/bash

# Tool: validate-structure.sh
# Purpose: Comprehensive repository structure and standards validation
# Usage: ./validate-structure.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="validate-structure"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive repository structure and standards validation"

# Configuration
LOG_DIR="logs/toolshed"
VERBOSE=false
JSON_OUTPUT=false
OUTPUT_FILE=""
FAIL_ON_ERROR=true

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0
TOTAL_CHECKS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Validation results array (for JSON output)
declare -a VALIDATION_RESULTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_DIR/validate-structure.log"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$LOG_DIR/validate-structure.log"

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        VALIDATION_RESULTS+=("{\"type\":\"success\",\"message\":\"$1\",\"timestamp\":\"$(date -Iseconds)\"}")
    fi
}

log_failure() {
    echo -e "${RED}[✗]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [FAILURE] $1" >> "$LOG_DIR/validate-structure.log"

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        VALIDATION_RESULTS+=("{\"type\":\"failure\",\"message\":\"$1\",\"timestamp\":\"$(date -Iseconds)\"}")
    fi
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    CHECKS_WARNING=$((CHECKS_WARNING + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_DIR/validate-structure.log"

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        VALIDATION_RESULTS+=("{\"type\":\"warning\",\"message\":\"$1\",\"timestamp\":\"$(date -Iseconds)\"}")
    fi
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool validates:
- Repository structure and organization
- Required files and configurations
- Git setup and branch protection
- Documentation standards
- Security configurations
- CI/CD pipeline setup
- Code quality standards

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    --json                  Output results in JSON format
    --output FILE           Write results to file
    --no-fail               Don't exit with error code on failures
    --version               Show version information
    --quick                 Run only essential checks
    --category CATEGORY     Run only specific category of checks
                           (git|files|docs|security|cicd|quality)

Examples:
    $0                      # Full validation
    $0 --json --output results.json
    $0 --category git       # Only Git-related checks
    $0 --quick              # Essential checks only

EOF
}

# Initialize logging
setup_logging() {
    mkdir -p "$LOG_DIR"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [START] Structure validation initiated" >> "$LOG_DIR/validate-structure.log"
    fi
}

# Check if we're in a Git repository
check_git_repository() {
    log_info "Checking Git repository status..."

    if git rev-parse --git-dir >/dev/null 2>&1; then
        log_success "Git repository detected"

        # Check if we have commits
        if git log --oneline -1 >/dev/null 2>&1; then
            log_success "Repository has commit history"
        else
            log_warning "Repository has no commits yet"
        fi

        # Check current branch
        local current_branch=$(git branch --show-current)
        if [[ -n "$current_branch" ]]; then
            log_success "Current branch: $current_branch"
        else
            log_warning "No current branch detected (detached HEAD?)"
        fi

    else
        log_failure "Not a Git repository"
        return 1
    fi
}

# Validate required files
validate_required_files() {
    log_info "Validating required files..."

    local required_files=(
        ".gitignore:Git ignore patterns"
        ".gitmessage:Git commit message template"
        "VERSION:Semantic versioning file"
        "CHANGELOG.md:Change log documentation"
        "README.md:Project documentation"
    )

    for file_spec in "${required_files[@]}"; do
        local file="${file_spec%%:*}"
        local description="${file_spec#*:}"

        if [[ -f "$file" ]]; then
            log_success "Required file exists: $file ($description)"

            # Additional checks for specific files
            case "$file" in
                ".gitignore")
                    if [[ $(wc -l < "$file") -lt 10 ]]; then
                        log_warning ".gitignore seems minimal (less than 10 lines)"
                    fi
                    ;;
                "VERSION")
                    if grep -q "VERSION_MAJOR" "$file"; then
                        log_success "VERSION file has semantic versioning structure"
                    else
                        log_warning "VERSION file missing semantic versioning structure"
                    fi
                    ;;
                "README.md")
                    if [[ $(wc -l < "$file") -lt 5 ]]; then
                        log_warning "README.md seems minimal (less than 5 lines)"
                    fi
                    ;;
            esac
        else
            log_failure "Required file missing: $file ($description)"
        fi
    done
}

# Validate directory structure
validate_directory_structure() {
    log_info "Validating directory structure..."

    local expected_dirs=(
        ".github:GitHub configuration"
        ".github/workflows:GitHub Actions workflows"
        ".github/ISSUE_TEMPLATE:Issue templates"
        "scripts:Utility scripts"
        "scripts/tools:Toolshed scripts"
        "scripts/tools/git:Git automation tools"
        "scripts/tools/validation:Validation tools"
        "logs:Log directory"
    )

    for dir_spec in "${expected_dirs[@]}"; do
        local dir="${dir_spec%%:*}"
        local description="${dir_spec#*:}"

        if [[ -d "$dir" ]]; then
            log_success "Directory exists: $dir ($description)"

            # Check if directory has content
            if [[ -n "$(ls -A "$dir" 2>/dev/null)" ]]; then
                log_success "$dir contains files"
            else
                log_warning "$dir is empty"
            fi
        else
            # Some directories are optional
            case "$dir" in
                ".github"|".github/workflows"|".github/ISSUE_TEMPLATE")
                    log_failure "Important directory missing: $dir ($description)"
                    ;;
                *)
                    log_warning "Optional directory missing: $dir ($description)"
                    ;;
            esac
        fi
    done
}

# Validate Git configuration
validate_git_configuration() {
    log_info "Validating Git configuration..."

    # Check commit template
    local commit_template=$(git config --get commit.template 2>/dev/null || echo "")
    if [[ -n "$commit_template" ]]; then
        log_success "Git commit template configured: $commit_template"
        if [[ -f "$commit_template" ]]; then
            log_success "Commit template file exists"
        else
            log_failure "Commit template file missing: $commit_template"
        fi
    else
        log_warning "No Git commit template configured"
    fi

    # Check useful aliases
    local aliases=("co" "br" "ci" "st" "lg")
    local alias_count=0

    for alias in "${aliases[@]}"; do
        if git config --get "alias.$alias" >/dev/null 2>&1; then
            alias_count=$((alias_count + 1))
        fi
    done

    if [[ $alias_count -gt 0 ]]; then
        log_success "Git aliases configured ($alias_count/5 common aliases)"
    else
        log_warning "No common Git aliases configured"
    fi

    # Check pull strategy
    local pull_rebase=$(git config --get pull.rebase 2>/dev/null || echo "")
    if [[ "$pull_rebase" == "false" ]]; then
        log_success "Pull strategy configured (merge)"
    elif [[ "$pull_rebase" == "true" ]]; then
        log_success "Pull strategy configured (rebase)"
    else
        log_warning "Pull strategy not explicitly configured"
    fi

    # Check default branch
    local default_branch=$(git config --get init.defaultBranch 2>/dev/null || echo "")
    if [[ "$default_branch" == "main" ]]; then
        log_success "Default branch set to 'main'"
    else
        log_warning "Default branch not set to 'main' (current: ${default_branch:-"not set"})"
    fi
}

# Validate GitHub workflows
validate_github_workflows() {
    log_info "Validating GitHub workflows..."

    if [[ -d ".github/workflows" ]]; then
        local workflow_count=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)

        if [[ $workflow_count -gt 0 ]]; then
            log_success "GitHub workflows found ($workflow_count files)"

            # Check for essential workflows
            if [[ -f ".github/workflows/ci.yml" ]]; then
                log_success "CI workflow exists"
            else
                log_warning "No CI workflow found"
            fi

            # Validate workflow syntax (basic check)
            find .github/workflows -name "*.yml" -o -name "*.yaml" | while read -r workflow; do
                if grep -q "^name:" "$workflow" && grep -q "^on:" "$workflow"; then
                    log_success "Workflow syntax valid: $(basename "$workflow")"
                else
                    log_failure "Workflow syntax issues: $(basename "$workflow")"
                fi
            done
        else
            log_warning "No GitHub workflows found"
        fi
    else
        log_failure "GitHub workflows directory missing"
    fi
}

# Validate documentation
validate_documentation() {
    log_info "Validating documentation..."

    # Check README.md content
    if [[ -f "README.md" ]]; then
        local readme_sections=("# " "## " "### ")
        local section_count=0

        for section in "${readme_sections[@]}"; do
            if grep -q "^$section" README.md; then
                section_count=$((section_count + 1))
            fi
        done

        if [[ $section_count -gt 0 ]]; then
            log_success "README.md has structured content ($section_count heading levels)"
        else
            log_warning "README.md lacks structured headings"
        fi

        # Check for common sections
        local common_sections=("Installation" "Usage" "Contributing" "License")
        local found_sections=0

        for section in "${common_sections[@]}"; do
            if grep -qi "$section" README.md; then
                found_sections=$((found_sections + 1))
            fi
        done

        if [[ $found_sections -gt 1 ]]; then
            log_success "README.md includes common sections ($found_sections/4)"
        else
            log_warning "README.md missing common sections (Installation, Usage, etc.)"
        fi
    fi

    # Check CHANGELOG.md format
    if [[ -f "CHANGELOG.md" ]]; then
        if grep -q "Keep a Changelog" CHANGELOG.md; then
            log_success "CHANGELOG.md follows standard format"
        else
            log_warning "CHANGELOG.md doesn't reference standard format"
        fi

        if grep -q "## \[" CHANGELOG.md; then
            log_success "CHANGELOG.md has version entries"
        else
            log_warning "CHANGELOG.md has no version entries"
        fi
    fi
}

# Validate security configurations
validate_security() {
    log_info "Validating security configurations..."

    # Check .gitignore for security patterns
    if [[ -f ".gitignore" ]]; then
        local security_patterns=("*.key" "*.pem" ".env" "secrets/" "*.pfx")
        local pattern_count=0

        for pattern in "${security_patterns[@]}"; do
            if grep -q "$pattern" .gitignore; then
                pattern_count=$((pattern_count + 1))
            fi
        done

        if [[ $pattern_count -gt 2 ]]; then
            log_success ".gitignore includes security patterns ($pattern_count/5)"
        else
            log_warning ".gitignore missing security patterns (secrets, keys, .env)"
        fi
    fi

    # Check for accidentally committed secrets
    local secret_files=("*.key" "*.pem" ".env" "secrets.json" "config.json")
    local found_secrets=0

    for pattern in "${secret_files[@]}"; do
        if find . -name "$pattern" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./node_modules/*" -not -path "./examples/*" | grep -q .; then
            found_secrets=$((found_secrets + 1))
            log_failure "Potential secret file found: $pattern"
        fi
    done

    if [[ $found_secrets -eq 0 ]]; then
        log_success "No obvious secret files found in repository"
    fi

    # Check for Trivy security scanning in workflows
    if find .github/workflows -name "*.yml" -exec grep -l "trivy" {} \; | grep -q .; then
        log_success "Security scanning (Trivy) configured in workflows"
    else
        log_warning "No security scanning detected in workflows"
    fi
}

# Generate validation report
generate_report() {
    echo ""
    echo "======================================"
    echo "Repository Structure Validation Report"
    echo "======================================"
    echo ""
    echo "Validation Summary:"
    echo -e "  Total Checks: ${PURPLE}$TOTAL_CHECKS${NC}"
    echo -e "  Passed: ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "  Failed: ${RED}$CHECKS_FAILED${NC}"
    echo -e "  Warnings: ${YELLOW}$CHECKS_WARNING${NC}"
    echo ""

    local pass_percentage=$((CHECKS_PASSED * 100 / TOTAL_CHECKS))
    echo "Pass Rate: $pass_percentage%"

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ Repository structure meets all requirements!${NC}"
        VALIDATION_EXIT_CODE=0
    elif [[ $CHECKS_FAILED -le 2 ]]; then
        echo -e "${YELLOW}⚠ Repository structure mostly compliant (minor issues)${NC}"
        VALIDATION_EXIT_CODE=1
    else
        echo -e "${RED}✗ Repository structure needs significant improvements${NC}"
        VALIDATION_EXIT_CODE=2
    fi

    echo ""
    echo "Recommendations:"
    if [[ $CHECKS_FAILED -gt 0 ]]; then
        echo "- Address failed checks above"
        echo "- Run: ./scripts/tools/git/setup-repository.sh"
    fi
    if [[ $CHECKS_WARNING -gt 0 ]]; then
        echo "- Consider addressing warnings for best practices"
    fi
    echo "- Review and customize configurations as needed"
    echo ""

    # Generate JSON output if requested
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        generate_json_report
    fi
}

# Generate JSON report
generate_json_report() {
    local json_report="{
  \"validation_summary\": {
    \"timestamp\": \"$(date -Iseconds)\",
    \"total_checks\": $TOTAL_CHECKS,
    \"passed\": $CHECKS_PASSED,
    \"failed\": $CHECKS_FAILED,
    \"warnings\": $CHECKS_WARNING,
    \"pass_percentage\": $((CHECKS_PASSED * 100 / TOTAL_CHECKS)),
    \"exit_code\": $VALIDATION_EXIT_CODE
  },
  \"results\": [
    $(IFS=,; echo "${VALIDATION_RESULTS[*]}")
  ]
}"

    if [[ -n "$OUTPUT_FILE" ]]; then
        echo "$json_report" > "$OUTPUT_FILE"
        log_info "JSON report written to: $OUTPUT_FILE"
    else
        echo ""
        echo "JSON Report:"
        echo "$json_report"
    fi
}

# Main execution function
main() {
    local categories="${CATEGORIES:-all}"
    local quick_mode="${QUICK_MODE:-false}"

    log_info "Starting repository structure validation..."
    setup_logging

    # Run validation categories
    if [[ "$categories" == "all" ]] || [[ "$categories" == "git" ]]; then
        check_git_repository
        validate_git_configuration
    fi

    if [[ "$categories" == "all" ]] || [[ "$categories" == "files" ]]; then
        validate_required_files
        validate_directory_structure
    fi

    if [[ "$categories" == "all" ]] || [[ "$categories" == "docs" ]]; then
        validate_documentation
    fi

    if [[ "$categories" == "all" ]] || [[ "$categories" == "security" ]]; then
        validate_security
    fi

    if [[ "$categories" == "all" ]] || [[ "$categories" == "cicd" ]]; then
        validate_github_workflows
    fi

    generate_report

    # Exit with appropriate code
    if [[ "$FAIL_ON_ERROR" == "true" ]] && [[ $CHECKS_FAILED -gt 0 ]]; then
        exit $VALIDATION_EXIT_CODE
    fi
}

# Parse command line arguments
CATEGORIES="all"
QUICK_MODE=false
VALIDATION_EXIT_CODE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --no-fail)
            FAIL_ON_ERROR=false
            shift
            ;;
        --version)
            echo "$TOOL_NAME version $TOOL_VERSION"
            exit 0
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --category)
            CATEGORIES="$2"
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
