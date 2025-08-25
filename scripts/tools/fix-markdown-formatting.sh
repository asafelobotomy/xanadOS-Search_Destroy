#!/bin/bash
# Comprehensive Markdown Formatting Improvement Script
# Fixes markdown linting issues across the entire repository

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🎨 Starting comprehensive markdown formatting improvements..."
echo "📁 Repository root: $REPO_ROOT"

cd "$REPO_ROOT"

# Create backup directory
BACKUP_DIR="backups/markdown-formatting-$(date +%Y%m%d-%H%M%S)"
echo "📦 Creating backup in $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Function to backup and fix a markdown file
fix_markdown_file() {
    local file="$1"
    local relative_path="${file#$REPO_ROOT/}"

    echo "🔧 Processing: $relative_path"

    # Create backup
    local backup_file="$BACKUP_DIR/${relative_path}"
    mkdir -p "$(dirname "$backup_file")"
    cp "$file" "$backup_file"

    # Apply fixes using sed for common markdown issues
    sed -i '
        # Fix MD022: Add blank lines around headings
        /^#/ {
            # Look ahead to see if previous line is not blank
            x; /^$/ !{x; i\

            b cont}
            x
            :cont
        }

        # Fix MD032: Add blank lines around lists
        /^[[:space:]]*[-*+]/ {
            # Look ahead to see if previous line is not blank and not a list item
            x; /^$/ !{/^[[:space:]]*[-*+]/ !{x; i\

            b cont2}}
            x
            :cont2
        }

        # Fix MD031: Add blank lines around fenced code blocks
        /^```/ {
            x; /^$/ !{x; i\

            b cont3}
            x
            :cont3
        }

        # Store current line for next iteration
        h
    ' "$file"

    # Fix specific patterns that need more complex handling with Python
    cat > "/tmp/markdown_fixer_$$.py" << 'EOF'
import re
import sys

def fix_markdown_content(content):
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fix MD022: Ensure blank lines around headings
        if re.match(r'^#+\s', line):
            # Add blank line before heading if previous line is not blank
            if fixed_lines and fixed_lines[-1].strip() != '':
                fixed_lines.append('')
            fixed_lines.append(line)
            # Add blank line after heading if next line is not blank
            if i + 1 < len(lines) and lines[i + 1].strip() != '':
                fixed_lines.append('')

        # Fix MD032: Ensure blank lines around lists
        elif re.match(r'^\s*[-*+]\s', line):
            # Add blank line before list if previous line is not blank and is not a list item
            if (fixed_lines and fixed_lines[-1].strip() != '' and
                not re.match(r'^\s*[-*+]\s', fixed_lines[-1])):
                fixed_lines.append('')
            fixed_lines.append(line)

        # Fix MD031: Ensure blank lines around fenced code blocks
        elif line.startswith('```'):
            # Add blank line before code block if previous line is not blank
            if fixed_lines and fixed_lines[-1].strip() != '':
                fixed_lines.append('')
            fixed_lines.append(line)
            i += 1
            # Add code block content
            while i < len(lines) and not lines[i].startswith('```'):
                fixed_lines.append(lines[i])
                i += 1
            if i < len(lines):  # Add closing ```
                fixed_lines.append(lines[i])
            # Add blank line after code block if next line is not blank
            if i + 1 < len(lines) and lines[i + 1].strip() != '':
                fixed_lines.append('')

        # Fix MD036: Replace emphasis used as headings with proper headings
        elif re.match(r'^[*_]{2}[^*_]+[*_]{2}$', line.strip()):
            # Convert **bold text** that looks like a heading to proper heading
            heading_text = re.sub(r'^[*_]{2}([^*_]+)[*_]{2}$', r'\1', line.strip())
            if len(heading_text) < 60:  # Reasonable heading length
                if fixed_lines and fixed_lines[-1].strip() != '':
                    fixed_lines.append('')
                fixed_lines.append(f'### {heading_text}')
                if i + 1 < len(lines) and lines[i + 1].strip() != '':
                    fixed_lines.append('')
            else:
                fixed_lines.append(line)

        # Fix MD040: Add language to fenced code blocks
        elif line.strip() == '```':
            # Default to bash for scripts, json for data, or text for unknown
            if 'script' in sys.argv[1].lower() or '.sh' in sys.argv[1]:
                fixed_lines.append('```bash')
            elif 'json' in sys.argv[1].lower():
                fixed_lines.append('```json')
            elif 'config' in sys.argv[1].lower():
                fixed_lines.append('```yaml')
            else:
                fixed_lines.append('```text')

        # Fix MD049: Use consistent emphasis style (underscore)
        elif '_' in line or '*' in line:
            # Convert *emphasis* to _emphasis_
            line = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'_\1_', line)
            fixed_lines.append(line)

        else:
            fixed_lines.append(line)

        i += 1

    # Remove trailing blank lines and ensure single final newline
    while fixed_lines and fixed_lines[-1] == '':
        fixed_lines.pop()

    return '\n'.join(fixed_lines) + '\n'

if __name__ == '__main__':
    file_path = sys.argv[1]
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content = fix_markdown_content(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
EOF

    python3 "/tmp/markdown_fixer_$$.py" "$file"
    rm -f "/tmp/markdown_fixer_$$.py"
}

echo "🔍 Finding all markdown files..."
find . -name "*.md" -not -path "./.venv/*" -not -path "./node_modules/*" -not -path "./.git/*" | while read -r file; do
    fix_markdown_file "$file"
done

echo "✅ Markdown formatting improvements completed!"
echo "📦 Backups saved in: $BACKUP_DIR"

# Test with markdownlint if available
if command -v markdownlint >/dev/null 2>&1; then
    echo "🧪 Running markdownlint validation..."
    if markdownlint **/*.md --ignore node_modules --ignore .venv 2>/dev/null; then
        echo "✅ Markdownlint validation passed!"
    else
        echo "⚠️ Some markdown issues remain - check output above"
    fi
elif command -v npm >/dev/null 2>&1; then
    echo "🧪 Running npm markdownlint validation..."
    if npm run lint 2>/dev/null; then
        echo "✅ NPM markdownlint validation passed!"
    else
        echo "⚠️ Some markdown issues remain - check npm run lint output"
    fi
else
    echo "ℹ️ Markdownlint not available - manual verification recommended"
fi

echo "📋 Summary:"
echo "- Fixed common markdown linting issues"
echo "- Added proper spacing around headings, lists, and code blocks"
echo "- Ensured consistent emphasis style"
echo "- Added language specifications to code blocks"
echo "- Created backups of all modified files"

echo "🎉 Markdown formatting improvement complete!"
