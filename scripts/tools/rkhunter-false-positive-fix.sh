#!/bin/bash
# RKHunter False Positive Quick Fix Script
# This script applies common optimizations to reduce RKHunter false positives

set -euo pipefail

# Configuration
RKHUNTER_CONF="/etc/rkhunter.conf"
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
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
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."

    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi

    if ! command -v rkhunter &> /dev/null; then
        log_error "RKHunter is not installed"
        exit 1
    fi

    if [[ ! -f "$RKHUNTER_CONF" ]]; then
        log_error "RKHunter configuration file not found: $RKHUNTER_CONF"
        exit 1
    fi

    log_success "Requirements check passed"
}

backup_config() {
    log_info "Creating backup of current configuration..."

    local backup_file="${RKHUNTER_CONF}.backup.${BACKUP_SUFFIX}"
    cp "$RKHUNTER_CONF" "$backup_file"

    log_success "Configuration backed up to: $backup_file"
}

apply_optimizations() {
    log_info "Applying RKHunter optimizations..."

    # Create temporary optimization file
    local temp_config=$(mktemp)

    cat >> "$temp_config" << 'EOF'

# === RKHunter False Positive Optimizations ===
# Added by rkhunter-false-positive-fix.sh

# Common false positive directories
ALLOWHIDDENDIR="/dev/.udev"
ALLOWHIDDENDIR="/dev/.static"
ALLOWHIDDENDIR="/dev/.initramfs"
ALLOWHIDDENDIR="/sys/kernel/security"
ALLOWHIDDENDIR="/sys/kernel/debug"

# Common system processes that may trigger warnings
ALLOWHIDDENPROC="/sbin/udevd"
ALLOWHIDDENPROC="/usr/sbin/sshd"

# Network and process allowances
ALLOWPROCS="/usr/sbin/NetworkManager"

# Performance optimizations
HASH_FUNC="SHA256"

# Disable high false-positive tests (uncomment as needed)
# DISABLE_TESTS="suspscan"
# DISABLE_TESTS="hidden_procs"
# DISABLE_TESTS="deleted_files"
# DISABLE_TESTS="apps"

# Mail configuration (disable during tuning)
# MAIL-ON-WARNING=""

EOF

    # Append optimizations to config file
    cat "$temp_config" >> "$RKHUNTER_CONF"
    rm "$temp_config"

    log_success "Optimizations applied to configuration"
}

update_database() {
    log_info "Updating RKHunter database..."

    if rkhunter --update --quiet; then
        log_success "Database updated successfully"
    else
        log_warning "Database update had warnings (this is normal)"
    fi
}

update_file_properties() {
    log_info "Updating file properties database..."

    if rkhunter --propupd --quiet; then
        log_success "File properties updated successfully"
    else
        log_warning "Property update had warnings"
    fi
}

run_test_scan() {
    log_info "Running test scan to verify optimizations..."

    local test_log=$(mktemp)

    if rkhunter --check --skip-keypress --report-warnings-only --logfile "$test_log"; then
        log_success "Test scan completed with no warnings"
    else
        log_info "Test scan completed with warnings. Review log for remaining issues:"
        echo "Test log location: $test_log"

        # Show summary of warnings
        local warning_count=$(grep -c "Warning:" "$test_log" 2>/dev/null || echo "0")
        log_info "Total warnings found: $warning_count"

        if [[ $warning_count -gt 0 ]]; then
            echo
            log_info "Sample warnings (first 5):"
            grep "Warning:" "$test_log" | head -5 || true
        fi
    fi
}

analyze_remaining_warnings() {
    log_info "Analyzing remaining warnings for additional optimizations..."

    local log_file="/var/log/rkhunter.log"

    if [[ -f "$log_file" ]]; then
        log_info "Common remaining warning patterns:"

        # Application version warnings
        local app_warnings=$(grep -c "application version" "$log_file" 2>/dev/null || echo "0")
        if [[ $app_warnings -gt 0 ]]; then
            echo "  - Application version mismatches: $app_warnings"
            echo "    Consider adding: DISABLE_TESTS=\"apps\""
        fi

        # Hidden process warnings
        local proc_warnings=$(grep -c "hidden process" "$log_file" 2>/dev/null || echo "0")
        if [[ $proc_warnings -gt 0 ]]; then
            echo "  - Hidden process warnings: $proc_warnings"
            echo "    Consider adding specific ALLOWHIDDENPROC entries"
        fi

        # File property warnings
        local prop_warnings=$(grep -c "file properties" "$log_file" 2>/dev/null || echo "0")
        if [[ $prop_warnings -gt 0 ]]; then
            echo "  - File property warnings: $prop_warnings"
            echo "    Run: sudo rkhunter --propupd"
        fi
    fi
}

generate_maintenance_script() {
    local maintenance_script="/usr/local/bin/rkhunter-maintenance.sh"

    log_info "Creating maintenance script..."

    cat > "$maintenance_script" << 'EOF'
#!/bin/bash
# RKHunter Maintenance Script
# Run this after system updates to prevent false positives

echo "RKHunter Maintenance - $(date)"

# Update RKHunter database
echo "Updating RKHunter database..."
rkhunter --update --quiet

# Update file properties after system changes
echo "Updating file properties..."
rkhunter --propupd --quiet

echo "Maintenance completed"
EOF

    chmod +x "$maintenance_script"
    log_success "Maintenance script created: $maintenance_script"
}

show_recommendations() {
    cat << 'EOF'

=== RKHunter False Positive Optimization Complete ===

NEXT STEPS:
1. Review the test scan results above
2. For remaining warnings, consider:
   - Adding specific files/processes to whitelist
   - Disabling problematic tests if warnings are legitimate
   - Running property update after system changes

MAINTENANCE:
- Run after system updates: sudo rkhunter --propupd
- Use maintenance script: sudo /usr/local/bin/rkhunter-maintenance.sh
- Schedule regular scans: add to crontab

COMMON ADDITIONAL OPTIMIZATIONS:
- Disable app version checking: DISABLE_TESTS="apps"
- Disable deleted files check: DISABLE_TESTS="deleted_files"
- Add more hidden directories as needed
- Whitelist legitimate processes causing warnings

SECURITY NOTE:
Only whitelist items you have verified as legitimate.
Review configurations regularly for security drift.

EOF
}

main() {
    echo "RKHunter False Positive Optimization Tool"
    echo "========================================"
    echo

    check_requirements
    backup_config
    apply_optimizations
    update_database
    update_file_properties
    run_test_scan
    analyze_remaining_warnings
    generate_maintenance_script
    show_recommendations

    log_success "RKHunter optimization completed successfully!"
}

# Run main function
main "$@"
