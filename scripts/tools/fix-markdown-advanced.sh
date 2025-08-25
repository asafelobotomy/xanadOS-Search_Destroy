#!/bin/bash
# Advanced Markdown Linting Fixes
# Addresses specific markdownlint issues found in the repository

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔧 Advanced markdown linting fixes starting..."
echo "📁 Repository root: $REPO_ROOT"

cd "$REPO_ROOT"

# Backup directory for additional fixes
BACKUP_DIR="backups/markdown-advanced-fixes-$(date +%Y%m%d-%H%M%S)"
echo "📦 Creating backup in $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Function to apply advanced markdown fixes
fix_advanced_markdown() {
    local file="$1"
    local relative_path="${file#$REPO_ROOT/}"

    echo "🔧 Advanced fixes for: $relative_path"

    # Create backup
    local backup_file="$BACKUP_DIR/${relative_path}"
    mkdir -p "$(dirname "$backup_file")"
    cp "$file" "$backup_file"

    # Apply advanced fixes using Python
    cat > "/tmp/advanced_markdown_fixer_$$.py" << 'EOF'
import re
import sys

def fix_advanced_markdown(content):
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # MD013: Line length - split long lines at appropriate points
        if len(line) > 100:
            # Don't break URLs, code blocks, or tables
            if not ('http' in line or line.strip().startswith('|') or
                   line.strip().startswith('```') or line.strip().startswith('    ')):
                # Try to break at sentence boundaries or common break points
                if '. ' in line and len(line) > 120:
                    parts = line.split('. ')
                    current_line = parts[0] + '.'
                    for part in parts[1:]:
                        if len(current_line + ' ' + part) > 100:
                            fixed_lines.append(current_line)
                            current_line = part
                        else:
                            current_line += ' ' + part
                    line = current_line
                elif ', ' in line and len(line) > 120:
                    # Break at commas for long lists
                    parts = line.split(', ')
                    current_line = parts[0]
                    for part in parts[1:]:
                        if len(current_line + ', ' + part) > 100:
                            fixed_lines.append(current_line + ',')
                            current_line = part
                        else:
                            current_line += ', ' + part
                    line = current_line

        # MD025: Multiple H1 headings - convert additional H1s to H2s
        if re.match(r'^# ', line) and any(re.match(r'^# ', l) for l in fixed_lines):
            line = re.sub(r'^# ', '## ', line)

        # MD026: Remove trailing punctuation from headings
        if re.match(r'^#+\s+.*[.,:;!?]$', line):
            line = re.sub(r'([.,:;!?])$', '', line)

        # MD031: Ensure blank lines around fenced code blocks
        if line.strip().startswith('```'):
            if fixed_lines and fixed_lines[-1].strip() != '':
                fixed_lines.append('')
            fixed_lines.append(line)
            if i + 1 < len(lines) and lines[i + 1].strip() != '':
                fixed_lines.append('')
            continue

        # MD032: Ensure blank lines around lists
        if re.match(r'^\s*[-*+]\s', line) or re.match(r'^\s*\d+\.\s', line):
            # Check if previous line needs blank line
            if (fixed_lines and fixed_lines[-1].strip() != '' and
                not re.match(r'^\s*[-*+]\s', fixed_lines[-1]) and
                not re.match(r'^\s*\d+\.\s', fixed_lines[-1])):
                fixed_lines.append('')
            fixed_lines.append(line)
            # Check if next line needs blank line
            if (i + 1 < len(lines) and lines[i + 1].strip() != '' and
                not re.match(r'^\s*[-*+]\s', lines[i + 1]) and
                not re.match(r'^\s*\d+\.\s', lines[i + 1])):
                next_needs_blank = True
            else:
                next_needs_blank = False
            continue

        # MD036: Convert emphasis used as headings to proper headings
        if re.match(r'^\*\*[^*]+\*\*$', line.strip()):
            heading_text = re.sub(r'^\*\*([^*]+)\*\*$', r'\1', line.strip())
            if len(heading_text) < 60:  # Reasonable heading length
                # Determine heading level based on context
                line = f'### {heading_text}'
                if fixed_lines and fixed_lines[-1].strip() != '':
                    fixed_lines.append('')
                fixed_lines.append(line)
                if i + 1 < len(lines) and lines[i + 1].strip() != '':
                    fixed_lines.append('')
                continue

        # MD040: Add language specification to fenced code blocks
        if line.strip() == '```':
            # Try to infer language from context
            context = ' '.join(lines[max(0, i-3):i]).lower()
            if 'bash' in context or 'shell' in context or 'command' in context:
                line = '```bash'
            elif 'python' in context or 'pip' in context:
                line = '```python'
            elif 'json' in context:
                line = '```json'
            elif 'yaml' in context or 'yml' in context:
                line = '```yaml'
            elif 'xml' in context or 'html' in context:
                line = '```xml'
            elif 'javascript' in context or 'node' in context:
                line = '```javascript'
            elif 'sql' in context:
                line = '```sql'
            else:
                line = '```text'

        # MD044: Fix common proper name capitalizations
        line = re.sub(r'\bGITHUB\b', 'GitHub', line, flags=re.IGNORECASE)
        line = re.sub(r'\bJAVASCRIPT\b', 'JavaScript', line, flags=re.IGNORECASE)
        line = re.sub(r'\bPYTHON\b', 'Python', line, flags=re.IGNORECASE)

        fixed_lines.append(line)

        # Handle delayed blank line addition for lists
        if 'next_needs_blank' in locals() and next_needs_blank:
            if (i + 1 < len(lines) and lines[i + 1].strip() != '' and
                not re.match(r'^\s*[-*+]\s', lines[i + 1]) and
                not re.match(r'^\s*\d+\.\s', lines[i + 1])):
                fixed_lines.append('')
            next_needs_blank = False

    # Final cleanup - remove excessive blank lines but preserve structure
    cleaned_lines = []
    blank_count = 0
    for line in fixed_lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:  # Allow at most 2 consecutive blank lines
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    # Remove trailing blank lines and ensure single final newline
    while cleaned_lines and cleaned_lines[-1] == '':
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines) + '\n'

if __name__ == '__main__':
    file_path = sys.argv[1]
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content = fix_advanced_markdown(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
EOF

    python3 "/tmp/advanced_markdown_fixer_$$.py" "$file"
    rm -f "/tmp/advanced_markdown_fixer_$$.py"
}

echo "🔍 Finding markdown files with specific issues..."

# Get list of files with issues from markdownlint
npm run lint --silent 2>/dev/null | grep -E '\.md:' | cut -d: -f1 | sort -u | while read -r file; do
    if [[ -f "$file" ]]; then
        fix_advanced_markdown "$file"
    fi
done

echo "✅ Advanced markdown fixes completed!"
echo "📦 Backups saved in: $BACKUP_DIR"

# Test the fixes
echo "🧪 Re-running markdownlint to check improvements..."
if npm run lint --silent > /dev/null 2>&1; then
    echo "✅ All markdown linting issues resolved!"
else
    echo "📊 Remaining issues (if any):"
    npm run lint 2>/dev/null | head -20
    echo "..."
fi

echo "📋 Advanced fixes applied:"
echo "- Fixed line length issues by breaking at sentence boundaries"
echo "- Converted multiple H1 headings to H2"
echo "- Removed trailing punctuation from headings"
echo "- Added proper blank lines around code blocks and lists"
echo "- Converted emphasis headings to proper markdown headings"
echo "- Added language specifications to code blocks"
echo "- Fixed proper name capitalizations"

echo "🎉 Advanced markdown formatting complete!"
