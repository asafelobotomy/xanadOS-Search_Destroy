#!/usr/bin/env bash

# Final validation warning fixes - September 2025
# This script addresses the remaining validation warnings for 100% success rate

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
echo "🔧 Addressing validation warnings for XanadOS Search & Destroy"
echo "📍 Project Root: $PROJECT_ROOT"

# Fix 1: Ensure fnm is properly available in all environments
echo ""
echo "🔍 ISSUE 1: fnm Node Version Manager Detection"
echo "----------------------------------------------------------------"

if [[ -f "$HOME/.bashrc" ]] && grep -q "fnm" "$HOME/.bashrc"; then
    echo "✅ fnm configuration found in ~/.bashrc"

    # Add fnm to current PATH if not already there
    if ! command -v fnm >/dev/null 2>&1; then
        export PATH="$HOME/.local/share/fnm:$PATH"
        echo "✅ Added fnm to current PATH"
    fi

    # Verify fnm works
    if command -v fnm >/dev/null 2>&1; then
        echo "✅ fnm is now available: $(fnm --version)"
    else
        echo "❌ fnm still not available after PATH fix"
    fi
else
    echo "⚠️  fnm not found in ~/.bashrc - may need reinstallation"
fi

# Fix 2: Verify Python code quality is actually clean
echo ""
echo "🔍 ISSUE 2: Python Code Quality Status"
echo "----------------------------------------------------------------"

cd "$PROJECT_ROOT"

# Check Python code quality with ruff
if command -v python >/dev/null 2>&1; then
    echo "🐍 Running Python code quality check..."

    if python -m ruff check app/ >/dev/null 2>&1; then
        echo "✅ Python code quality: CLEAN (no issues found)"
    else
        echo "⚠️  Python code quality: Found some issues"
        echo "🔧 Running automatic fixes..."
        python -m ruff check app/ --fix >/dev/null 2>&1 || true
        echo "✅ Automatic fixes applied"
    fi
else
    echo "❌ Python not available"
fi

# Fix 3: Create a summary validation status
echo ""
echo "📊 CURRENT VALIDATION STATUS"
echo "=================================================================="

# Test each component
FNMSTATUS="❌"
if command -v fnm >/dev/null 2>&1; then
    FNMSTATUS="✅"
fi

PYTHON_STATUS="❌"
if python -m ruff check app/ >/dev/null 2>&1; then
    PYTHON_STATUS="✅"
fi

echo "Modern Node Manager (fnm): $FNMSTATUS"
echo "Python Code Quality: $PYTHON_STATUS"

# Count successful checks
PASSED=0
if [[ "$FNMSTATUS" == "✅" ]]; then
    ((PASSED++))
fi
if [[ "$PYTHON_STATUS" == "✅" ]]; then
    ((PASSED++))
fi

echo ""
echo "🎯 RESOLUTION STATUS: $PASSED/2 issues resolved"

if [[ $PASSED -eq 2 ]]; then
    echo ""
    echo "🎉 SUCCESS: All validation warnings have been addressed!"
    echo "🏆 Your repository should now achieve 100% validation success"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Run: npm run quick:validate"
    echo "  2. Verify 22/22 (100%) validation success"
    echo "  3. Enjoy your fully modernized and validated codebase!"
else
    echo ""
    echo "⚠️  Some issues may need manual attention"
    echo "📋 Please check the output above for specific details"
fi

echo ""
echo "✅ Validation warning resolution complete!"
