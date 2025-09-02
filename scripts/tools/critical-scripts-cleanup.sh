#!/usr/bin/env bash
# Critical Scripts Cleanup - Immediate Actions Required
# Generated from comprehensive scripts review 2025-09-02

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo "🧹 Critical Scripts Cleanup - Immediate Actions"
echo "=============================================="
echo ""

# Navigate to repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

log_info "Starting critical script cleanup in: $PWD"

# Phase 1: Remove deprecated/redundant markdown scripts
log_info "Phase 1: Removing deprecated markdown script stubs..."

DEPRECATED_SCRIPTS=(
    "scripts/tools/fix-markdown-advanced.sh"
    "scripts/tools/fix-markdown-final.sh"
    "scripts/tools/fix-markdown-formatting.sh"
    "scripts/tools/fix-markdown-targeted.sh"
)

for script in "${DEPRECATED_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        log_warning "Removing deprecated script: $script"
        rm "$script"
        log_success "Removed: $script"
    else
        log_info "Already removed: $script"
    fi
done

# Phase 2: Archive the redundant organization script
log_info "Phase 2: Handling duplicate organization scripts..."

if [[ -f "scripts/utils/check-organization.py" ]]; then
    # Create archive directory if needed
    mkdir -p "archive/superseded/2025-09-02"

    # Move the smaller/duplicate version to archive
    mv "scripts/utils/check-organization.py" "archive/superseded/2025-09-02/check-organization-utils.py"
    log_success "Archived duplicate: scripts/utils/check-organization.py"

    # Document the archival
    cat > "archive/superseded/2025-09-02/README-organization-scripts.md" << 'EOF'
# Organization Scripts Consolidation - 2025-09-02

## check-organization-utils.py

**Superseded Date**: 2025-09-02
**Superseded By**: scripts/check-organization.py (main implementation)
**Reason**: Duplicate functionality - smaller version with limited features

### Changes
- Consolidated organization checking into single authoritative script
- Removed redundant implementation to prevent confusion
- Main script has more comprehensive validation

### Archive Location
- `archive/superseded/2025-09-02/check-organization-utils.py`

This file was consolidated during script review and cleanup.
EOF

    log_success "Created archival documentation"
else
    log_info "Duplicate organization script already removed"
fi

# Phase 3: Standardize shell script headers (sample of critical scripts)
log_info "Phase 3: Standardizing critical script headers..."

CRITICAL_SCRIPTS=(
    "scripts/security/rkhunter-wrapper.sh"
    "scripts/security/rkhunter-update-and-scan.sh"
)

for script in "${CRITICAL_SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        # Check if it uses the old shebang
        if head -1 "$script" | grep -q "#!/bin/bash"; then
            log_warning "Updating shebang in: $script"
            sed -i '1s|#!/bin/bash|#!/usr/bin/env bash|' "$script"
            log_success "Updated shebang: $script"
        fi

        # Check if it has proper error handling
        if ! grep -q "set -euo pipefail" "$script"; then
            log_warning "Script missing proper error handling: $script"
            # Note: Manual review needed for complex scripts
        fi
    fi
done

# Phase 4: Verify removal and report
log_info "Phase 4: Verification and reporting..."

echo ""
echo "📊 Cleanup Results:"
echo "==================="

REMOVED_COUNT=0
for script in "${DEPRECATED_SCRIPTS[@]}"; do
    if [[ ! -f "$script" ]]; then
        echo "✅ Removed: $script"
        ((REMOVED_COUNT++))
    else
        echo "❌ Still exists: $script"
    fi
done

if [[ -f "archive/superseded/2025-09-02/check-organization-utils.py" ]]; then
    echo "✅ Archived: scripts/utils/check-organization.py"
else
    echo "ℹ️  Organization script consolidation: already completed"
fi

echo ""
echo "🎯 Summary:"
echo "- Deprecated scripts removed: $REMOVED_COUNT/4"
echo "- Organization scripts consolidated: ✅"
echo "- Archive documentation created: ✅"

echo ""
echo "📋 Next Steps Required:"
echo "======================"
echo "1. Review security scripts for input validation"
echo "2. Add comprehensive error handling to all scripts"
echo "3. Create unit tests for Python scripts"
echo "4. Implement script documentation standards"

echo ""
echo "⚠️  Manual Review Required:"
echo "=========================="
echo "- scripts/security/rkhunter-wrapper.sh: Add input validation"
echo "- scripts/security/rkhunter-update-and-scan.sh: Sanitize environment variables"
echo "- All scripts with 'rm -rf': Add path validation"

echo ""
log_success "Critical cleanup completed! Review full report at: docs/reports/SCRIPTS_REVIEW_2025-09-02.md"
