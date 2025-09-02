#!/usr/bin/env bash
# Script Security Validator
# Checks scripts for common security issues

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check for dangerous patterns
check_script_security() {
    local script="$1"
    local issues=0

    echo "Checking: $script"

    # Check for unquoted variables
    if grep -n '\$[A-Za-z_][A-Za-z0-9_]*[^"]' "$script" | grep -v '#' | head -5; then
        log_warning "  Potentially unquoted variables found"
        ((issues++))
    fi

    # Check for rm -rf without proper validation
    if grep -n 'rm -rf' "$script" | grep -v 'echo'; then
        log_warning "  rm -rf found - ensure path validation"
        ((issues++))
    fi

    # Check for eval/exec with variables
    if grep -n 'eval.*\$\|exec.*\$' "$script"; then
        log_error "  Dangerous eval/exec with variables"
        ((issues++))
    fi

    # Check for proper error handling
    if ! grep -q 'set -e' "$script"; then
        log_warning "  Missing error handling (set -e)"
        ((issues++))
    fi

    if [[ $issues -eq 0 ]]; then
        log_success "  No obvious security issues found"
    fi

    return $issues
}

# Main execution
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <script1> [script2] ..."
    exit 1
fi

total_issues=0

for script in "$@"; do
    if [[ -f "$script" ]]; then
        check_script_security "$script"
        total_issues=$((total_issues + $?))
    else
        log_error "Script not found: $script"
        ((total_issues++))
    fi
    echo ""
done

echo "Total security issues found: $total_issues"
exit $total_issues
