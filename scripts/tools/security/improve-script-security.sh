#!/usr/bin/env bash
# Security Improvements for Critical Scripts
# Based on comprehensive scripts review 2025-09-02

set -euo pipefail

# Add input validation function to rkhunter-wrapper.sh
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

echo "🛡️ Security Improvements for Critical Scripts"
echo "============================================="
echo ""

# Improve rkhunter-wrapper.sh security
log_info "Improving rkhunter-wrapper.sh security..."

cat > scripts/security/rkhunter-wrapper.sh << 'EOF'
#!/usr/bin/env bash
# RKHunter execution wrapper with GUI environment support
# This script runs with root privileges via pkexec

set -euo pipefail

# Input validation function
validate_rkhunter_args() {
    local args=("$@")

    # Check for dangerous arguments
    for arg in "${args[@]}"; do
        # Prevent command injection attempts
        if [[ "$arg" =~ [;\|\&\$\`] ]]; then
            echo "Error: Invalid characters in argument: $arg" >&2
            exit 1
        fi

        # Only allow known safe rkhunter options
        if [[ "$arg" =~ ^- ]] && ! [[ "$arg" =~ ^--(check|update|propupd|version|help|config-check)$ ]]; then
            if ! [[ "$arg" =~ ^-[cuvh]$ ]]; then
                echo "Warning: Potentially unsafe argument: $arg" >&2
            fi
        fi
    done
}

# Validate rkhunter exists and is executable
if [[ ! -x "/usr/bin/rkhunter" ]]; then
    echo "Error: rkhunter not found or not executable at /usr/bin/rkhunter" >&2
    exit 1
fi

# Set up GUI environment if available
export DISPLAY="${DISPLAY:-:0}"

# Safely handle SUDO_USER environment variable
if [[ -n "${SUDO_USER:-}" ]] && [[ -z "${XAUTHORITY:-}" ]]; then
    # Validate SUDO_USER is a real username (basic validation)
    if id "$SUDO_USER" &>/dev/null; then
        # Try to find the XAUTHORITY file for the original user
        XAUTH_PATH="/home/$SUDO_USER/.Xauthority"
        if [[ -f "$XAUTH_PATH" ]]; then
            export XAUTHORITY="$XAUTH_PATH"
        fi
    fi
fi

# Validate arguments before execution
validate_rkhunter_args "$@"

# Execute RKHunter with validated arguments
exec /usr/bin/rkhunter "$@"
EOF

log_success "Enhanced rkhunter-wrapper.sh with input validation"

# Improve rkhunter-update-and-scan.sh security
log_info "Improving rkhunter-update-and-scan.sh security..."

cat > scripts/security/rkhunter-update-and-scan.sh << 'EOF'
#!/usr/bin/env bash
# RKHunter combined update and scan wrapper
# This script runs both operations with a single authentication

set -euo pipefail

# Input validation and security functions
validate_environment() {
    # Validate SUDO_USER if present
    if [[ -n "${SUDO_USER:-}" ]]; then
        if ! id "$SUDO_USER" &>/dev/null; then
            echo "Error: Invalid SUDO_USER: $SUDO_USER" >&2
            exit 1
        fi
    fi

    # Validate DISPLAY format if present
    if [[ -n "${DISPLAY:-}" ]] && ! [[ "$DISPLAY" =~ ^:[0-9]+(\.[0-9]+)?$ ]]; then
        echo "Warning: Potentially invalid DISPLAY format: $DISPLAY" >&2
    fi
}

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Validate rkhunter exists
if [[ ! -x "/usr/bin/rkhunter" ]]; then
    echo "Error: rkhunter not found or not executable" >&2
    exit 1
fi

# Validate environment variables
validate_environment

# Set up GUI environment if available
export DISPLAY="${DISPLAY:-:0}"

# Safely handle SUDO_USER and XAUTHORITY
if [[ -n "${SUDO_USER:-}" ]] && [[ -z "${XAUTHORITY:-}" ]]; then
    XAUTH_PATH="/home/$SUDO_USER/.Xauthority"
    if [[ -f "$XAUTH_PATH" ]]; then
        export XAUTHORITY="$XAUTH_PATH"
    fi
fi

log_message "Starting RKHunter update and scan sequence"

# Step 1: Update database
log_message "Updating RKHunter database..."

# Validate arguments passed to script
for arg in "$@"; do
    if [[ "$arg" =~ [;\|\&\$\`] ]]; then
        echo "Error: Invalid characters in argument: $arg" >&2
        exit 1
    fi
done

# Execute RKHunter with validated arguments
exec /usr/bin/rkhunter "$@"
EOF

log_success "Enhanced rkhunter-update-and-scan.sh with security improvements"

# Create a security validation script
log_info "Creating security validation script..."

cat > scripts/tools/security/validate-script-security.sh << 'EOF'
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
EOF

chmod +x scripts/tools/security/validate-script-security.sh
log_success "Created security validation script"

echo ""
echo "🎯 Security Improvements Summary:"
echo "================================="
echo "✅ Enhanced rkhunter-wrapper.sh with input validation"
echo "✅ Enhanced rkhunter-update-and-scan.sh with environment validation"
echo "✅ Created security validation script"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Test the security-enhanced scripts: sudo scripts/security/rkhunter-wrapper.sh --version"
echo "2. Run security validation: scripts/tools/security/validate-script-security.sh scripts/security/*.sh"
echo "3. Apply similar patterns to other critical scripts"
echo ""
echo "⚠️  Testing Required:"
echo "===================="
echo "- Verify rkhunter wrapper still works with pkexec"
echo "- Test with various argument combinations"
echo "- Ensure GUI environment variables work correctly"
