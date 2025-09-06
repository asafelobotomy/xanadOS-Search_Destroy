#!/bin/bash
# prevent-file-restoration.sh - Prevent deprecated files from being recreated by VS Code
# Usage: ./scripts/utils/prevent-file-restoration.sh

set -euo pipefail

# Define deprecated test files that should not be recreated
DEPRECATED_TEST_FILES=(
    "test_config_fix.py"
    "test_cron_integration.py"
    "test_improved_status.py"
    "test_optimization_direct.py"
    "test_optimization_fixes.py"
    "test_rkhunter_fix.py"
    "test_rkhunter_fixes.py"
    "test_rkhunter_status.py"
)

# Define deprecated summary/config files that should not be recreated
DEPRECATED_CONFIG_FILES=(
    "CRON_INTEGRATION_SUMMARY.md"
    "MODERN_SETUP_SUMMARY.md"
    "RKHUNTER_FIX_SUMMARY.md"
    ".envrc"
    "Makefile.modern"
    "fix_setup_config.py"
)

# Define additional empty files restored by VS Code
DEPRECATED_EMPTY_FILES=(
    "docs/guides/MODERN_DEVELOPMENT_SETUP.md"
    "releases/v2.13.1.md"
    "scripts/tools/test_firewall_optimization_integration.py"
    "scripts/tools/validate_firewall_detection_fix.py"
    "scripts/tools/version_manager.py"
    "scripts/tools/version_manager_new.py"
    "app/core/elevated_runner_simple.py"
)

# Combine all deprecated files
ALL_DEPRECATED_FILES=("${DEPRECATED_TEST_FILES[@]}" "${DEPRECATED_CONFIG_FILES[@]}" "${DEPRECATED_EMPTY_FILES[@]}")

echo "🛡️ Checking for deprecated files..."

FOUND_FILES=0
for file in "${ALL_DEPRECATED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "⚠️  Found deprecated file: $file"
        rm -f "$file"
        echo "🗑️  Removed: $file"
        ((FOUND_FILES++))
    fi
done

if [[ $FOUND_FILES -eq 0 ]]; then
    echo "✅ No deprecated files found"
else
    echo "🧹 Cleaned up $FOUND_FILES deprecated files"

    # Stage the removal if we're in a git repository
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "📝 Staging file removals in git..."
        for file in "${ALL_DEPRECATED_FILES[@]}"; do
            if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
                git rm --cached "$file" 2>/dev/null || true
            fi
        done
    fi
fi

echo "🚀 Prevention mechanism active - VS Code file restoration blocked"
