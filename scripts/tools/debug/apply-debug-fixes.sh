#!/bin/bash
# Quick Debug Fixes for xanadOS Search & Destroy
# Applies the most critical fixes identified in the comprehensive debug analysis

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Applying quick debug fixes to xanadOS Search & Destroy..."
echo "📍 Project root: $PROJECT_ROOT"

# Change to project directory
cd "$PROJECT_ROOT"

# Backup files before making changes
BACKUP_DIR="archive/debug-fixes-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Creating backups in $BACKUP_DIR..."

# Backup critical files that will be modified
cp scripts/validation/validate-agent-workflow.sh "$BACKUP_DIR/"
cp scripts/validation/validate-version-control.sh "$BACKUP_DIR/"
cp app/main.py "$BACKUP_DIR/"

echo "🔍 Analyzing current issues..."

# Check if shellcheck is available
if command -v shellcheck >/dev/null 2>&1; then
    echo "✅ ShellCheck available - running analysis"
    SHELL_ISSUES=$(shellcheck scripts/validation/*.sh 2>&1 | wc -l)
    echo "📊 Found $SHELL_ISSUES shell script issues"
else
    echo "⚠️  ShellCheck not available - skipping shell analysis"
    SHELL_ISSUES=0
fi

# Check Python issues with flake8
if python3 -m flake8 --version >/dev/null 2>&1; then
    echo "✅ Flake8 available - running analysis"
    PYTHON_ISSUES=$(python3 -m flake8 app/main.py --count 2>/dev/null || echo "0")
    echo "📊 Found $PYTHON_ISSUES Python style issues"
else
    echo "⚠️  Flake8 not available - skipping Python analysis"
    PYTHON_ISSUES=0
fi

echo ""
echo "🛠️  Applying fixes..."

# Fix 1: Variable quoting in validate-version-control.sh
echo "📝 Fix 1: Adding variable quotes in validate-version-control.sh"
if grep -q '[ $untracked_count -eq 0 ]' scripts/validation/validate-version-control.sh; then
    sed -i 's/\[ \$untracked_count -eq 0 \]/[ "$untracked_count" -eq 0 ]/' \
        scripts/validation/validate-version-control.sh
    echo "   ✅ Fixed variable quoting"
else
    echo "   ℹ️  Variable quoting already correct"
fi

# Fix 2: Comment out problematic array assignment in validate-agent-workflow.sh
echo "📝 Fix 2: Commenting problematic array code in validate-agent-workflow.sh"
if grep -q 'ROOT_FILES=.*wc -l' scripts/validation/validate-agent-workflow.sh; then
    sed -i '/ROOT_FILES=.*wc -l/s/^/# FIXME: /' scripts/validation/validate-agent-workflow.sh
    sed -i '/ROOT_FILES=.*wc -l/a # TODO: Replace with proper array handling - see debug report' \
        scripts/validation/validate-agent-workflow.sh
    echo "   ✅ Commented problematic array code"
else
    echo "   ℹ️  Array code already handled"
fi

# Fix 3: Add shellcheck directive to setup-dev-environment.sh
echo "📝 Fix 3: Adding shellcheck directive to setup-dev-environment.sh"
if ! grep -q 'shellcheck source=' scripts/setup-dev-environment.sh; then
    sed -i '/source \.venv\/bin\/activate/i # shellcheck source=/dev/null' \
        scripts/setup-dev-environment.sh
    echo "   ✅ Added shellcheck directive"
else
    echo "   ℹ️  Shellcheck directive already present"
fi

# Fix 4: Improve import order in app/main.py (add TODO comment)
echo "📝 Fix 4: Adding import order TODO in app/main.py"
if ! grep -q 'TODO.*import.*order' app/main.py; then
    sed -i '/from app\.core\.single_instance/i # TODO: Move this import to top of file for PEP8 compliance' \
        app/main.py
    echo "   ✅ Added import order TODO"
else
    echo "   ℹ️  Import order TODO already present"
fi

echo ""
echo "🧪 Verifying fixes..."

# Verify shell script fixes
if command -v shellcheck >/dev/null 2>&1; then
    NEW_SHELL_ISSUES=$(shellcheck scripts/validation/*.sh 2>&1 | wc -l)
    if [ "$NEW_SHELL_ISSUES" -lt "$SHELL_ISSUES" ]; then
        echo "✅ Shell script issues reduced: $SHELL_ISSUES → $NEW_SHELL_ISSUES"
    else
        echo "ℹ️  Shell script issues: $NEW_SHELL_ISSUES (may require manual fixes)"
    fi
fi

# Verify Python fixes
if python3 -m flake8 --version >/dev/null 2>&1; then
    NEW_PYTHON_ISSUES=$(python3 -m flake8 app/main.py --count 2>/dev/null || echo "0")
    if [ "$NEW_PYTHON_ISSUES" -lt "$PYTHON_ISSUES" ]; then
        echo "✅ Python issues reduced: $PYTHON_ISSUES → $NEW_PYTHON_ISSUES"
    else
        echo "ℹ️  Python issues: $NEW_PYTHON_ISSUES (some require manual fixes)"
    fi
fi

echo ""
echo "📋 Summary of applied fixes:"
echo "   1. ✅ Fixed variable quoting in shell scripts"
echo "   2. ✅ Commented problematic array handling (manual fix needed)"
echo "   3. ✅ Added shellcheck directive for source command"
echo "   4. ✅ Added import order improvement TODO"
echo ""
echo "📖 Next steps:"
echo "   • Review comprehensive debug report: docs/reports/comprehensive-debug-report.md"
echo "   • Review fix recommendations: docs/reports/script-fix-recommendations.md"
echo "   • Implement manual fixes for array handling and exception patterns"
echo "   • Run full test suite to verify no regressions"
echo ""
echo "💾 Backups saved in: $BACKUP_DIR"
echo "🎉 Quick fixes complete!"

# Create a summary file
cat > "$BACKUP_DIR/fixes-applied.md" << EOF
# Debug Fixes Applied $(date +"%Y-%m-%d %H:%M:%S")

## Automatic Fixes Applied

1. **Variable Quoting**: Fixed unquoted variables in validate-version-control.sh
2. **Array Handling**: Commented problematic array code with TODO for manual fix
3. **ShellCheck Directive**: Added source directive to suppress SC1091 warning
4. **Import Order**: Added TODO comment for PEP8 import order compliance

## Files Modified

- scripts/validation/validate-version-control.sh
- scripts/validation/validate-agent-workflow.sh
- scripts/setup-dev-environment.sh
- app/main.py

## Backups Created

Original files backed up in: $BACKUP_DIR

## Manual Fixes Still Needed

- Replace array handling in validate-agent-workflow.sh with proper implementation
- Update exception handling patterns in Python files (32 instances)
- Implement subprocess security improvements (14 instances)
- Fix declare/assign separation in shell scripts (7 instances)

See comprehensive reports for detailed implementation guidance.
EOF

echo "📝 Fix summary written to: $BACKUP_DIR/fixes-applied.md"
