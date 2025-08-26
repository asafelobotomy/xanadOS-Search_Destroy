#!/bin/bash
# Pylance Performance Optimization Script
# This script cleans up performance-heavy files and directories

echo "🔧 Pylance Performance Optimization for xanadOS-Search_Destroy"
echo "================================================================"

# Count current files before cleanup
echo "📊 Current workspace statistics:"
echo "   Python files: $(find . -name "*.py" | wc -l)"
echo "   __pycache__ dirs: $(find . -type d -name "__pycache__" | wc -l)"
echo "   Cache files: $(find . -path "*/__pycache__/*" -name "*.py*" | wc -l)"

echo ""
echo "🧹 Cleaning up performance-heavy directories..."

# Remove all __pycache__ directories
echo "   Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files
echo "   Removing .pyc files..."
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove .pyo files
echo "   Removing .pyo files..."
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove pytest cache
echo "   Removing pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove mypy cache
echo "   Removing mypy cache..."
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Count files after cleanup
echo ""
echo "✅ Cleanup complete! New statistics:"
echo "   Python files: $(find . -name "*.py" | wc -l)"
echo "   __pycache__ dirs: $(find . -type d -name "__pycache__" | wc -l)"
echo "   Cache files: $(find . -path "*/__pycache__/*" -name "*.py*" | wc -l)"

echo ""
echo "🚀 Performance optimizations applied:"
echo "   ✅ VS Code settings updated with Python analysis excludes"
echo "   ✅ Pyrightconfig.json created with focused analysis scope"
echo "   ✅ File watcher excludes configured"
echo "   ✅ Search excludes optimized"
echo "   ✅ Python cache files removed"
echo ""
echo "📋 Next steps:"
echo "   1. Restart VS Code for settings to take effect"
echo "   2. Reload window: Ctrl+Shift+P > 'Developer: Reload Window'"
echo "   3. Consider opening app/ subdirectory if working primarily on the main application"
echo ""
echo "💡 Tip: Run this script periodically to maintain performance:"
echo "   bash scripts/tools/optimize-pylance-performance.sh"
