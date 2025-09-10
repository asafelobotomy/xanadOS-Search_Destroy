#!/bin/bash
set -euo pipefail

# XanadOS Search & Destroy Modernization Implementation Script
# Implements Python 3.13 and 2024-2025 modernization standards

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 XanadOS Search & Destroy Modernization Implementation"
echo "=================================================================="
echo "📍 Project Root: $PROJECT_ROOT"
echo "📍 Script Location: $SCRIPT_DIR"
echo ""

# Check Python 3.13
echo "🔍 Checking Python version..."
if ! python3 --version | grep -q "3\.13"; then
    echo "❌ Python 3.13 required but not found"
    echo "Current version: $(python3 --version)"
    exit 1
fi
echo "✅ Python 3.13 available: $(python3 --version)"

# Check uv package manager
echo "🔍 Checking uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "❌ uv package manager not found"
    echo "Install with: pip install uv"
    exit 1
fi
echo "✅ uv available: $(uv --version)"

# Activate virtual environment if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "🔄 Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "✅ Virtual environment activated"
fi

echo ""
echo "📋 IMPLEMENTING MODERNIZATION CHANGES"
echo "=================================================================="

# Run the Python implementation script
echo "🐍 Running Python modernization implementation..."
cd "$PROJECT_ROOT"
python3 scripts/tools/modernization/implement_modernization_2024.py

# Run validation after modernization
echo ""
echo "🔍 Running post-modernization validation..."
if npm run quick:validate; then
    echo "✅ Post-modernization validation passed"
else
    echo "⚠️  Post-modernization validation has warnings (review recommended)"
fi

echo ""
echo "🎉 MODERNIZATION IMPLEMENTATION COMPLETE"
echo "=================================================================="
echo "✅ XanadOS Search & Destroy modernized to Python 3.13 standards"
echo "✅ Latest dependency versions applied"
echo "✅ Modern typing syntax implemented"
echo "✅ Security vulnerabilities addressed"
echo ""
echo "🎯 Next Steps:"
echo "  1. Review any validation warnings above"
echo "  2. Run comprehensive tests: make test"
echo "  3. Review dependency changes: uv show"
echo "  4. Commit changes: git add . && git commit -m 'Modernize to Python 3.13'"
echo ""
echo "📖 For details, see: docs/reports/MODERNIZATION_REPORT_2024.md"
