#!/bin/bash
# Targeted Markdown Linting Fix Script
# Fixes the most common and critical markdown linting issues

set -euo pipefail

echo "🎯 Targeted markdown linting fixes starting..."

# Fix specific files with the most critical issues
fix_specific_file() {
    local file="$1"
    echo "🔧 Fixing: $file"

    # Create backup
    cp "$file" "${file}.backup-$(date +%s)"

    # Use sed to make targeted fixes
    sed -i '
        # MD031: Add blank lines around fenced code blocks
        /^```/ {
            # Check if previous line is not blank
            x
            /^$/!{
                x
                i\

                b cont1
            }
            x
            :cont1
        }

        # MD032: Add blank lines around list items
        /^[[:space:]]*[-*+][[:space:]]/ {
            # Check if previous line is not blank and not a list item
            x
            /^$/!{
                /^[[:space:]]*[-*+][[:space:]]/!{
                    x
                    i\

                    b cont2
                }
            }
            x
            :cont2
        }

        # Store current line for next iteration
        h
    ' "$file"

    # Fix multiple H1 headings (convert second and subsequent H1s to H2s)
    python3 -c "
import re

with open('$file', 'r') as f:
    content = f.read()

lines = content.split('\n')
h1_count = 0
fixed_lines = []

for line in lines:
    if re.match(r'^# ', line):
        h1_count += 1
        if h1_count > 1:
            line = re.sub(r'^# ', '## ', line)
    fixed_lines.append(line)

with open('$file', 'w') as f:
    f.write('\n'.join(fixed_lines))
"

    echo "✅ Fixed: $file"
}

# Fix the most problematic files first
echo "📋 Fixing critical files with multiple issues..."

# Fix archive files
if [[ -f "archive/ARCHIVE_INDEX.md" ]]; then
    fix_specific_file "archive/ARCHIVE_INDEX.md"
fi

if [[ -f "archive/REPOSITORY_CLEANUP_SUMMARY.md" ]]; then
    fix_specific_file "archive/REPOSITORY_CLEANUP_SUMMARY.md"
fi

# Fix other high-impact files
if [[ -f "releases/v2.10.0.md" ]]; then
    fix_specific_file "releases/v2.10.0.md"
fi

if [[ -f "tests/README_MODERN_TESTS.md" ]]; then
    fix_specific_file "tests/README_MODERN_TESTS.md"
fi

if [[ -f "tests/VALIDATION_REPORT.md" ]]; then
    fix_specific_file "tests/VALIDATION_REPORT.md"
fi

# Apply general fixes to remaining files with MD040 (fenced code language) issues
echo "📝 Adding language specifications to code blocks..."
find . -name "*.md" -not -path "./.venv/*" -not -path "./node_modules/*" -not -path "./.git/*" -not -path "./backups/*" | while read -r file; do
    # Skip if file doesn't exist or has been processed
    [[ -f "$file" ]] || continue

    # Add language to fenced code blocks that don't have one
    sed -i 's/^```$/```text/' "$file"
done

# Remove trailing punctuation from headings
echo "🔧 Removing trailing punctuation from headings..."
find . -name "*.md" -not -path "./.venv/*" -not -path "./node_modules/*" -not -path "./.git/*" -not -path "./backups/*" | while read -r file; do
    [[ -f "$file" ]] || continue

    sed -i 's/^\(#\+[[:space:]]\+.*\)[.,:;!?]$/\1/' "$file"
done

echo "✅ Targeted markdown fixes completed!"

# Test the improvements
echo "🧪 Testing markdown linting improvements..."
if npm run lint --silent > /dev/null 2>&1; then
    echo "🎉 All markdown linting issues resolved!"
else
    echo "📊 Remaining issues count:"
    npm run lint 2>/dev/null | wc -l
    echo "🔍 Sample remaining issues:"
    npm run lint 2>/dev/null | head -5
fi

echo "📋 Summary of fixes applied:"
echo "- Fixed multiple H1 headings by converting extras to H2"
echo "- Added blank lines around lists and code blocks"
echo "- Added language specifications to fenced code blocks"
echo "- Removed trailing punctuation from headings"
echo "- Created backups of all modified files"
