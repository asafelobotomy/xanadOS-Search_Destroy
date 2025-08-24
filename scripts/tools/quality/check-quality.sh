#!/bin/bash

# Tool: check-quality.sh
# Purpose: Comprehensive code quality and standards validation
# Usage: ./check-quality.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="check-quality"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive code quality and standards validation"

# Configuration
LOG_DIR="logs/toolshed"
VERBOSE=false
FIX_ISSUES=false
OUTPUT_FORMAT="console"
REPORT_FILE=""

# Quality metrics
QUALITY_SCORE=0
TOTAL_FILES=0
ISSUES_FOUND=0
ISSUES_FIXED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Quality check results
declare -a QUALITY_RESULTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_DIR/check-quality.log"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$LOG_DIR/check-quality.log"
    QUALITY_RESULTS+=("SUCCESS: $1")
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_DIR/check-quality.log"
    QUALITY_RESULTS+=("WARNING: $1")
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOG_DIR/check-quality.log"
    QUALITY_RESULTS+=("ERROR: $1")
}

log_fix() {
    echo -e "${GREEN}[FIXED]${NC} $1"
    ISSUES_FIXED=$((ISSUES_FIXED + 1))
    [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [FIXED] $1" >> "$LOG_DIR/check-quality.log"
    QUALITY_RESULTS+=("FIXED: $1")
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool checks:
- Markdown formatting and standards
- File naming conventions
- Code documentation quality
- Shell script standards
- JSON/YAML syntax validation
- Security best practices
- Performance patterns

Options:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -f, --fix           Automatically fix issues where possible
    --format FORMAT     Output format: console, json, html
    --report FILE       Write detailed report to file
    --version           Show version information
    --check TYPE        Run specific check type only
                       (markdown|naming|docs|scripts|syntax|security)

Examples:
    $0                  # Full quality check
    $0 --fix            # Check and auto-fix issues
    $0 --format json --report quality-report.json
    $0 --check markdown # Only check Markdown files

EOF
}

# Initialize logging
setup_logging() {
    mkdir -p "$LOG_DIR"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [START] Quality check initiated" >> "$LOG_DIR/check-quality.log"
    fi
}

# Check Markdown formatting
check_markdown_quality() {
    log_info "Checking Markdown file quality..."

    local markdown_files
    mapfile -t markdown_files < <(find . -type f -name "*.md" \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.venv/*" \
        -not -path "./vendor/*" \
        -not -path "./packaging/flatpak/vendor/*")

    if [[ ${#markdown_files[@]} -eq 0 ]]; then
        log_warning "No Markdown files found"
        return
    fi

    TOTAL_FILES=$((TOTAL_FILES + ${#markdown_files[@]}))
    local issues_in_markdown=0

    for file in "${markdown_files[@]}"; do
        log_info "Checking: $file"

        # Check for proper heading structure
        if ! grep -q "^# " "$file"; then
            log_warning "$file: Missing main heading (# )"
            issues_in_markdown=$((issues_in_markdown + 1))
        else
            log_success "$file: Has main heading"
        fi

        # Check for empty lines before headings
        if grep -n "^##" "$file" | while read -r line_info; do
            local line_num="${line_info%%:*}"
            local prev_line=$((line_num - 1))
            if [[ $prev_line -gt 0 ]]; then
                local prev_content
                prev_content=$(sed -n "${prev_line}p" "$file")
                if [[ -n "$prev_content" ]]; then
                    echo "$file:$line_num: Missing empty line before heading"
                fi
            fi
        done | grep -q .; then
            log_warning "$file: Missing empty lines before headings"
            issues_in_markdown=$((issues_in_markdown + 1))

            if [[ "$FIX_ISSUES" == "true" ]]; then
                # Fix missing empty lines before headings
                sed -i '/^##/i\\' "$file"
                log_fix "$file: Added empty lines before headings"
            fi
        fi

        # Check for consistent list formatting
        if grep -q "^-" "$file" && grep -q "^\*" "$file"; then
            log_warning "$file: Inconsistent list markers (- and *)"
            issues_in_markdown=$((issues_in_markdown + 1))

            if [[ "$FIX_ISSUES" == "true" ]]; then
                # Standardize to dash lists
                sed -i 's/^\* /- /g' "$file"
                log_fix "$file: Standardized list markers to dashes"
            fi
        fi

        # Check for trailing spaces
        if grep -q " $" "$file"; then
            log_warning "$file: Contains trailing spaces"
            issues_in_markdown=$((issues_in_markdown + 1))

            if [[ "$FIX_ISSUES" == "true" ]]; then
                sed -i 's/ *$//' "$file"
                log_fix "$file: Removed trailing spaces"
            fi
        fi

        # Check for broken internal links (skip for now due to regex complexity)
        # This could be implemented with a simpler approach if needed

        # Check for code block language specification
        if grep -q '^```$' "$file"; then
            log_warning "$file: Code blocks without language specification"
            issues_in_markdown=$((issues_in_markdown + 1))
        fi
    done

    if [[ $issues_in_markdown -eq 0 ]]; then
        log_success "All Markdown files pass quality checks"
    else
        log_warning "Found $issues_in_markdown issues in Markdown files"
    fi
}

# Check file naming conventions
check_naming_conventions() {
    log_info "Checking file naming conventions..."

    local naming_issues=0

    # Check for spaces in filenames
    find . -type f -name "* *" \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.venv/*" \
        -not -path "./vendor/*" \
        -not -path "./packaging/flatpak/vendor/*" | while read -r file; do
        log_error "Filename contains spaces: $file"
        naming_issues=$((naming_issues + 1))

        if [[ "$FIX_ISSUES" == "true" ]]; then
            local new_name
            new_name=$(echo "$file" | tr ' ' '-')
            mv "$file" "$new_name"
            log_fix "Renamed: $file -> $new_name"
        fi
    done

    # Check for uppercase extensions
    find . -name "*.MD" -o -name "*.TXT" -o -name "*.JSON" -not -path "./.git/*" | while read -r file; do
        log_warning "Uppercase file extension: $file"
        naming_issues=$((naming_issues + 1))

        if [[ "$FIX_ISSUES" == "true" ]]; then
            local new_name
            new_name=$(echo "$file" | tr '[:upper:]' '[:lower:]')
            mv "$file" "$new_name"
            log_fix "Renamed to lowercase: $file -> $new_name"
        fi
    done

    # Check for consistent tool naming in scripts/tools/
    if [[ -d "scripts/tools" ]]; then
        find scripts/tools -name "*.sh" | while read -r script; do
            local basename
            basename=$(basename "$script" .sh)
            if [[ ! "$basename" =~ ^[a-z-]+$ ]]; then
                log_warning "Script name not following kebab-case: $script"
                naming_issues=$((naming_issues + 1))
            fi
        done
    fi

    if [[ $naming_issues -eq 0 ]]; then
        log_success "All files follow naming conventions"
    fi
}

# Check documentation quality
check_documentation_quality() {
    log_info "Checking documentation quality..."

    local doc_files=("README.md" "CHANGELOG.md" "CONTRIBUTING.md" "LICENSE")
    local doc_issues=0

    for doc in "${doc_files[@]}"; do
        if [[ -f "$doc" ]]; then
            case "$doc" in
                "README.md")
                    # Check for essential sections
                    local required_sections=("Installation" "Usage" "Contributing")
                    for section in "${required_sections[@]}"; do
                        if ! grep -qi "$section" "$doc"; then
                            log_warning "$doc: Missing '$section' section"
                            doc_issues=$((doc_issues + 1))
                        fi
                    done

                    # Check for project description
                    if [[ $(head -10 "$doc" | wc -w) -lt 20 ]]; then
                        log_warning "$doc: Project description seems minimal"
                        doc_issues=$((doc_issues + 1))
                    fi
                    ;;
                "CHANGELOG.md")
                    # Check for standard format
                    if ! grep -q "Keep a Changelog" "$doc"; then
                        log_warning "$doc: Not following Keep a Changelog format"
                        doc_issues=$((doc_issues + 1))
                    fi

                    # Check for version entries
                    if ! grep -q "## \[" "$doc"; then
                        log_warning "$doc: No version entries found"
                        doc_issues=$((doc_issues + 1))
                    fi
                    ;;
            esac

            # Check for placeholder text
            if grep -qi "TODO\|FIXME\|XXX" "$doc"; then
                log_warning "$doc: Contains placeholder text (TODO/FIXME/XXX)"
                doc_issues=$((doc_issues + 1))
            fi

            log_success "$doc: Documentation file found"
        else
            case "$doc" in
                "README.md")
                    log_error "Missing critical documentation: $doc"
                    doc_issues=$((doc_issues + 1))
                    ;;
                *)
                    log_warning "Missing documentation: $doc"
                    doc_issues=$((doc_issues + 1))
                    ;;
            esac
        fi
    done

    if [[ $doc_issues -eq 0 ]]; then
        log_success "Documentation quality is good"
    fi
}

# Check shell script quality
check_shell_scripts() {
    log_info "Checking shell script quality..."

    local shell_scripts
    mapfile -t shell_scripts < <(find . -type f -name "*.sh" \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.venv/*" \
        -not -path "./vendor/*" \
        -not -path "./packaging/flatpak/vendor/*")

    if [[ ${#shell_scripts[@]} -eq 0 ]]; then
        log_info "No shell scripts found"
        return
    fi

    TOTAL_FILES=$((TOTAL_FILES + ${#shell_scripts[@]}))
    local script_issues=0

    for script in "${shell_scripts[@]}"; do
        log_info "Checking script: $script"

        # Check for shebang
        if ! head -1 "$script" | grep -q "^#!/"; then
            log_error "$script: Missing shebang line"
            script_issues=$((script_issues + 1))
        else
            log_success "$script: Has shebang"
        fi

        # Check for set -e (exit on error)
        if ! grep -q "set -e" "$script"; then
            log_warning "$script: Not using 'set -e' for error handling"
            script_issues=$((script_issues + 1))
        fi

        # Check for executable permission
        if [[ ! -x "$script" ]]; then
            log_warning "$script: Not executable"
            script_issues=$((script_issues + 1))

            if [[ "$FIX_ISSUES" == "true" ]]; then
                chmod +x "$script"
                log_fix "$script: Made executable"
            fi
        fi

        # Check for function documentation
    local functions
    functions=$(grep -c "^[a-zA-Z_][a-zA-Z0-9_]*() {" "$script" 2>/dev/null || echo "0")
    local documented_functions
    documented_functions=$(grep -c "^# Function:" "$script" 2>/dev/null || echo "0")

        if [[ $functions -gt 0 ]] && [[ $documented_functions -eq 0 ]]; then
            log_warning "$script: Functions not documented"
            script_issues=$((script_issues + 1))
        fi

        # Check for usage function
        if [[ $functions -gt 2 ]] && ! grep -q "show_usage\|usage" "$script"; then
            log_warning "$script: Complex script without usage function"
            script_issues=$((script_issues + 1))
        fi

        # Check for hardcoded paths
        if grep -q "/tmp\|/home\|/Users" "$script"; then
            log_warning "$script: Contains hardcoded paths"
            script_issues=$((script_issues + 1))
        fi
    done

    if [[ $script_issues -eq 0 ]]; then
        log_success "All shell scripts pass quality checks"
    fi
}

# Check JSON/YAML syntax
check_syntax_validation() {
    log_info "Checking JSON/YAML syntax..."

    local syntax_issues=0

    # Check JSON files
    find . -type f -name "*.json" \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.venv/*" \
        -not -path "./vendor/*" \
        -not -path "./packaging/flatpak/vendor/*" | while read -r json_file; do
        if ! python3 -m json.tool "$json_file" >/dev/null 2>&1; then
            log_error "$json_file: Invalid JSON syntax"
            syntax_issues=$((syntax_issues + 1))
        else
            log_success "$json_file: Valid JSON"
        fi
    done

    # Check YAML files
    find . -type f \( -name "*.yml" -o -name "*.yaml" \) \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.venv/*" \
        -not -path "./vendor/*" \
        -not -path "./packaging/flatpak/vendor/*" | while read -r yaml_file; do
        if command -v yamllint >/dev/null 2>&1; then
            if ! yamllint -d relaxed "$yaml_file" >/dev/null 2>&1; then
                log_error "$yaml_file: YAML syntax issues"
                syntax_issues=$((syntax_issues + 1))
            else
                log_success "$yaml_file: Valid YAML"
            fi
        elif python3 -c "import yaml" 2>/dev/null; then
            if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" >/dev/null 2>&1; then
                log_error "$yaml_file: Invalid YAML syntax"
                syntax_issues=$((syntax_issues + 1))
            else
                log_success "$yaml_file: Valid YAML"
            fi
        else
            log_warning "No YAML validator available (install yamllint or PyYAML)"
        fi
    done

    if [[ $syntax_issues -eq 0 ]]; then
        log_success "All syntax checks passed"
    fi
}

# Check security best practices
check_security_practices() {
    log_info "Checking security best practices..."

    local security_issues=0

    # Check for potential secrets in files
    local secret_patterns=(
        "password[[:space:]]*=[[:space:]]*['\"][^'\"]{8,}"
        "api_key[[:space:]]*=[[:space:]]*['\"][^'\"]{20,}"
        "secret[[:space:]]*=[[:space:]]*['\"][^'\"]{16,}"
        "token[[:space:]]*=[[:space:]]*['\"][^'\"]{20,}"
        "-----BEGIN[[:space:]].*PRIVATE KEY-----"
    )

    for pattern in "${secret_patterns[@]}"; do
        if grep -R -I -i \
            --exclude-dir=.git \
            --exclude-dir=node_modules \
            --exclude-dir=.venv \
            --exclude-dir=vendor \
            --exclude-dir=packaging/flatpak/vendor \
            --exclude-dir=examples \
            . -e "$pattern" | grep -v "scripts/tools/quality/check-quality.sh"; then
            log_error "Potential secret found matching pattern: $pattern"
            security_issues=$((security_issues + 1))
        fi
    done

    # Check file permissions
    find . -type f -perm -o+w \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.venv/*" \
        -not -path "./vendor/*" \
        -not -path "./packaging/flatpak/vendor/*" | while read -r world_writable; do
        log_warning "World-writable file: $world_writable"
        security_issues=$((security_issues + 1))

        if [[ "$FIX_ISSUES" == "true" ]]; then
            chmod o-w "$world_writable"
            log_fix "Removed world-write permission: $world_writable"
        fi
    done

    # Check for .env files in repository
    if find . -name ".env*" -not -path "./.git/*" | grep -q .; then
        log_error "Environment files found in repository"
        security_issues=$((security_issues + 1))
    fi

    # Check .gitignore for security patterns
    if [[ -f ".gitignore" ]]; then
        local gitignore_security_patterns=("*.key" "*.pem" ".env" "secrets/" "*.p12")
        local missing_patterns=0

        for pattern in "${gitignore_security_patterns[@]}"; do
            if ! grep -q "$pattern" .gitignore; then
                missing_patterns=$((missing_patterns + 1))
            fi
        done

        if [[ $missing_patterns -gt 0 ]]; then
            log_warning ".gitignore missing $missing_patterns security patterns"
            security_issues=$((security_issues + 1))
        fi
    fi

    if [[ $security_issues -eq 0 ]]; then
        log_success "No security issues detected"
    fi
}

# Calculate quality score
calculate_quality_score() {
    if [[ $TOTAL_FILES -eq 0 ]]; then
        QUALITY_SCORE=100
    else
        local issue_ratio=$((ISSUES_FOUND * 100 / TOTAL_FILES))
        QUALITY_SCORE=$((100 - issue_ratio))
        if [[ $QUALITY_SCORE -lt 0 ]]; then
            QUALITY_SCORE=0
        fi
    fi
}

# Generate quality report
generate_quality_report() {
    calculate_quality_score

    echo ""
    echo "======================================"
    echo "Code Quality Assessment Report"
    echo "======================================"
    echo ""
    echo "Quality Metrics:"
    echo -e "  Files Analyzed: ${PURPLE}$TOTAL_FILES${NC}"
    echo -e "  Issues Found: ${RED}$ISSUES_FOUND${NC}"
    echo -e "  Issues Fixed: ${GREEN}$ISSUES_FIXED${NC}"
    echo -e "  Quality Score: ${BLUE}$QUALITY_SCORE/100${NC}"
    echo ""

    # Quality grade
    if [[ $QUALITY_SCORE -ge 90 ]]; then
        echo -e "Quality Grade: ${GREEN}A (Excellent)${NC}"
    elif [[ $QUALITY_SCORE -ge 80 ]]; then
        echo -e "Quality Grade: ${BLUE}B (Good)${NC}"
    elif [[ $QUALITY_SCORE -ge 70 ]]; then
        echo -e "Quality Grade: ${YELLOW}C (Fair)${NC}"
    else
        echo -e "Quality Grade: ${RED}D (Needs Improvement)${NC}"
    fi

    echo ""
    echo "Summary:"
    if [[ $ISSUES_FOUND -eq 0 ]]; then
        echo -e "${GREEN}✓ Code meets all quality standards!${NC}"
    elif [[ $ISSUES_FIXED -gt 0 ]]; then
        echo -e "${BLUE}✓ Fixed $ISSUES_FIXED issues automatically${NC}"
        echo -e "${YELLOW}! $((ISSUES_FOUND - ISSUES_FIXED)) issues remain${NC}"
    else
        echo -e "${RED}✗ $ISSUES_FOUND quality issues found${NC}"
        echo "Run with --fix to automatically resolve fixable issues"
    fi

    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        generate_json_quality_report
    elif [[ "$OUTPUT_FORMAT" == "html" ]]; then
        generate_html_quality_report
    fi
}

generate_json_quality_report() {
        local json_report
        json_report=$(cat <<'JSON'
{
    "quality_assessment": {
        "timestamp": "__TIMESTAMP__",
        "files_analyzed": __FILES__ ,
        "issues_found": __FOUND__ ,
        "issues_fixed": __FIXED__ ,
        "quality_score": __SCORE__ ,
        "grade": "__GRADE__"
    },
    "results": []
}
JSON
)

        # Fill dynamic fields
        json_report=${json_report/__TIMESTAMP__/$(date -Iseconds)}
        json_report=${json_report/__FILES__/$TOTAL_FILES}
        json_report=${json_report/__FOUND__/$ISSUES_FOUND}
        json_report=${json_report/__FIXED__/$ISSUES_FIXED}
        json_report=${json_report/__SCORE__/$QUALITY_SCORE}
        local grade
        if [[ $QUALITY_SCORE -ge 90 ]]; then grade="A"; elif [[ $QUALITY_SCORE -ge 80 ]]; then grade="B"; elif [[ $QUALITY_SCORE -ge 70 ]]; then grade="C"; else grade="D"; fi
        json_report=${json_report/__GRADE__/$grade}

        if [[ -n "$REPORT_FILE" ]]; then
                echo "$json_report" > "$REPORT_FILE"
                log_info "JSON report written to: $REPORT_FILE"
        else
                echo ""
                echo "JSON Quality Report:"
                echo "$json_report"
        fi
}

# Main execution function
main() {
    local check_type="${CHECK_TYPE:-all}"

    log_info "Starting code quality assessment..."
    setup_logging

    # Run quality checks based on type
    case "$check_type" in
        "all")
            check_markdown_quality
            check_naming_conventions
            check_documentation_quality
            check_shell_scripts
            check_syntax_validation
            check_security_practices
            ;;
        "markdown")
            check_markdown_quality
            ;;
        "naming")
            check_naming_conventions
            ;;
        "docs")
            check_documentation_quality
            ;;
        "scripts")
            check_shell_scripts
            ;;
        "syntax")
            check_syntax_validation
            ;;
        "security")
            check_security_practices
            ;;
        *)
            log_error "Unknown check type: $check_type"
            exit 1
            ;;
    esac

    generate_quality_report

    # Exit with appropriate code based on quality score
    if [[ $QUALITY_SCORE -ge 80 ]]; then
        exit 0
    elif [[ $QUALITY_SCORE -ge 60 ]]; then
        exit 1
    else
        exit 2
    fi
}

# Parse command line arguments
CHECK_TYPE="all"

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
        -f|--fix)
            FIX_ISSUES=true
            shift
            ;;
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --report)
            REPORT_FILE="$2"
            shift 2
            ;;
        --version)
            echo "$TOOL_NAME version $TOOL_VERSION"
            exit 0
            ;;
        --check)
            CHECK_TYPE="$2"
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
