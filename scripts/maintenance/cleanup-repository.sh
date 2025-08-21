#!/bin/bash
# Repository Cleanup Script for xanadOS-Search_Destroy
# Removes temporary files, cache files, and organizes development files

echo "🧹 Starting repository cleanup..."

# Remove Python cache files (excluding .venv)
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
find . -name "*.pyo" -not -path "./.venv/*" -delete 2>/dev/null || true
find . -name "*.pyd" -not -path "./.venv/*" -delete 2>/dev/null || true

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.backup" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name ".#*" -delete 2>/dev/null || true
find . -name "#*#" -delete 2>/dev/null || true

# Remove build artifacts
echo "Removing build artifacts..."
rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

# Remove log files (but keep .gitkeep)
echo "Cleaning log directories..."
find data/logs/ -type f -not -name ".gitkeep" -delete 2>/dev/null || true

# Clean quarantine directory (but keep .gitkeep)
echo "Cleaning quarantine directory..."
find data/quarantine/ -type f -not -name ".gitkeep" -delete 2>/dev/null || true

# Clean cache directory (but keep .gitkeep)
echo "Cleaning cache directory..."
find data/cache/ -type f -not -name ".gitkeep" -delete 2>/dev/null || true

# Move any test files from root to dev/debug-scripts/
echo "Organizing test files..."
if ls test_*.py verify_*.py 2>/dev/null; then
    mv test_*.py verify_*.py dev/debug/ 2>/dev/null || true
    echo "Moved test files to dev/debug/"
fi

# Move any implementation docs from root to docs/implementation/
echo "Organizing documentation..."
mkdir -p docs/implementation/
if ls *_IMPLEMENTATION.md *_TEST.md *_FIXES.md 2>/dev/null; then
    mv *_IMPLEMENTATION.md *_TEST.md *_FIXES.md docs/implementation/ 2>/dev/null || true
    echo "Moved implementation docs to docs/implementation/"
fi

# Report final state
echo ""
echo "✅ Repository cleanup completed!"
echo ""
echo "📊 Repository Statistics:"
echo "Python files: $(find . -name "*.py" -not -path "./.venv/*" | wc -l)"
echo "Documentation files: $(find docs/ -name "*.md" | wc -l)"
echo "Test files: $(find dev/debug/ dev/testing/ tests/ -name "*.py" | wc -l)"
echo "Cache files remaining: $(find . -name "__pycache__" -not -path "./.venv/*" | wc -l)"
echo ""
echo "🎯 Repository is now clean and organized for v2.8.0 release!"
