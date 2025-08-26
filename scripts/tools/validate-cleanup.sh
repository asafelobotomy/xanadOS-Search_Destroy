#!/bin/bash
# Repository Cleanup Validation Script
# Validates the cleanup results and checks compliance

echo "🧹 Repository Cleanup Validation Report"
echo "========================================"
echo "Date: $(date)"
echo ""

# Check root directory compliance
echo "📁 Root Directory Compliance Check:"
echo "------------------------------------"
root_files=$(find . -maxdepth 1 -type f | grep -v "^\./\." | wc -l)
echo "Root files count: $root_files"

# List all root files
echo "Root files:"
find . -maxdepth 1 -type f | grep -v "^\./\." | sort | sed 's/^/  - /'

echo ""

# Check directory sizes
echo "📊 Directory Size Analysis:"
echo "----------------------------"
du -sh */ 2>/dev/null | sort -hr

echo ""

# Check for common cleanup issues
echo "🔍 Cleanup Issues Check:"
echo "-------------------------"

# Check for __pycache__ directories
pycache_count=$(find . -type d -name "__pycache__" | wc -l)
echo "Python cache directories: $pycache_count"

# Check for node_modules
node_modules_count=$(find . -type d -name "node_modules" | wc -l)
echo "Node modules directories: $node_modules_count"

# Check for large log files
large_logs=$(find . -name "*.log" -size +10M 2>/dev/null | wc -l)
echo "Large log files (>10MB): $large_logs"

# Check backup directories
backup_dirs=$(find . -type d -name "*backup*" -o -name "*backups*" | wc -l)
echo "Backup directories: $backup_dirs"

echo ""

# File organization compliance
echo "📋 File Organization Compliance:"
echo "---------------------------------"

# Check for misplaced files
misplaced_scripts=$(find . -maxdepth 1 -name "*.sh" -o -name "*.py" | grep -v "^\./\." | wc -l)
echo "Scripts in root directory: $misplaced_scripts"

misplaced_docs=$(find . -maxdepth 1 -name "*.md" | grep -v -E "(README|CONTRIBUTING|CHANGELOG)" | wc -l)
echo "Documentation files in root: $misplaced_docs"

echo ""

# Summary
echo "✅ Cleanup Summary:"
echo "-------------------"
total_size=$(du -sh . | cut -f1)
echo "Total repository size: $total_size"
echo "Root directory compliance: $([ $misplaced_scripts -eq 0 ] && [ $misplaced_docs -eq 0 ] && echo "✅ COMPLIANT" || echo "❌ NON-COMPLIANT")"
echo "Performance optimization: $([ $pycache_count -eq 0 ] && [ $node_modules_count -eq 0 ] && echo "✅ OPTIMIZED" || echo "⚠️ NEEDS ATTENTION")"

echo ""
echo "🎯 Recommendations:"
echo "-------------------"
if [ $pycache_count -gt 0 ]; then
    echo "- Run: find . -type d -name '__pycache__' -exec rm -rf {} +"
fi
if [ $node_modules_count -gt 0 ]; then
    echo "- Run: find . -type d -name 'node_modules' -exec rm -rf {} +"
fi
if [ $large_logs -gt 0 ]; then
    echo "- Archive or compress large log files"
fi
if [ $misplaced_scripts -gt 0 ] || [ $misplaced_docs -gt 0 ]; then
    echo "- Move misplaced files to appropriate directories"
fi

echo ""
echo "📝 Next Steps:"
echo "--------------"
echo "1. Review and organize remaining large directories"
echo "2. Update documentation indexes"
echo "3. Run validation tests"
echo "4. Update .gitignore as needed"
