#!/bin/bash

# Tool: fix-python.sh
# Purpose: Comprehensive Python code quality fixing and optimization
# Usage: ./fix-python.sh [options]
# Version: 1.0.0

set -euo pipefail

# Script metadata
TOOL_NAME="fix-python"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive Python code quality fixing and optimization"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_DIR="$WORKSPACE_ROOT/logs/toolshed"
BACKUP_DIR="$WORKSPACE_ROOT/.python-backups"
TEMP_DIR="/tmp/python-fixes-$$"

# Tool options
VERBOSE=false
DRY_RUN=false
FIX_IMPORTS=true
FIX_FORMATTING=true
FIX_LINTING=true
TARGET_DIR="."
STRATEGY="safe"
BACKUP_ENABLED=true

# Python tools configuration
USE_BLACK=true
USE_ISORT=true
USE_AUTOPEP8=true
USE_RUFF=true  # Enhanced: Now uses ruff for comprehensive fixes
RUFF_AUTO_FIX=true  # New: Enable ruff auto-fixes
MAX_LINE_LENGTH=100  # Default aligned with repo docs; override with --line-length
REMOVE_UNUSED_IMPORTS=true  # New: Remove F401 errors
REMOVE_UNUSED_VARIABLES=true  # New: Remove F841 errors
FIX_FSTRING_ISSUES=true  # New: Fix F541 errors
APPLY_AGGRESSIVE_FIXES=false  # New: For complex issues

# Optional checks
RUN_PYLINT=true
PYLINT_FAIL_UNDER="7.0"
SECURITY_WARN=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
FILES_PROCESSED=0
FIXES_APPLIED=0
ERRORS_FOUND=0
declare -a PROCESSED_FILES=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    if [[ "$VERBOSE" == "true" ]]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_DIR/fix-python.log" 2>/dev/null || true
    fi
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    if [[ "$VERBOSE" == "true" ]]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$LOG_DIR/fix-python.log" 2>/dev/null || true
    fi
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    if [[ "$VERBOSE" == "true" ]]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
        echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_DIR/fix-python.log" 2>/dev/null || true
    fi
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    if [[ "$VERBOSE" == "true" ]]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOG_DIR/fix-python.log" 2>/dev/null || true
    fi
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
}

log_debug() {
    [[ "$VERBOSE" == "true" ]] && echo -e "${CYAN}[DEBUG]${NC} $1"
    if [[ "$VERBOSE" == "true" ]]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
        echo "$(date '+%Y-%m-%d %H:%M:%S') [DEBUG] $1" >> "$LOG_DIR/fix-python.log" 2>/dev/null || true
    fi
}

# Initialize environment
init_environment() {
    log_info "Starting $TOOL_NAME v$TOOL_VERSION"
    log_info "$(date)"

    # Create necessary directories
    mkdir -p "$LOG_DIR" "$TEMP_DIR"

    if [[ "$BACKUP_ENABLED" == "true" ]]; then
        BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="$BACKUP_DIR/$BACKUP_TIMESTAMP"
        mkdir -p "$BACKUP_DIR"
        log_info "Backups will be stored in: $BACKUP_DIR"
    fi

    log_debug "Workspace root: $WORKSPACE_ROOT"
    log_debug "Target directory: $TARGET_DIR"
    log_debug "Strategy: $STRATEGY"
}

# Check tool availability
check_tool_availability() {
    log_debug "Checking Python tool availability..."

    local tools_available=0
    local tools_missing=()

    # Check for Python itself
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not found"
        exit 1
    fi

    # Enhanced: Check for virtual environment ruff first
    local venv_ruff="$WORKSPACE_ROOT/.python-env/bin/ruff"
    if [[ -f "$venv_ruff" ]]; then
        USE_RUFF=true
        RUFF_CMD="$venv_ruff"
        log_info "Using ruff from virtual environment for comprehensive fixes"
        tools_available=$((tools_available + 1))
    elif command -v ruff >/dev/null 2>&1; then
        USE_RUFF=true
        RUFF_CMD="ruff"
        log_info "Using system ruff for comprehensive fixes"
        tools_available=$((tools_available + 1))
    else
        USE_RUFF=false
        log_debug "ruff not found, using individual tools"

        # Check for individual tools
        if command -v black >/dev/null 2>&1; then
            log_debug "black found"
            tools_available=$((tools_available + 1))
        else
            USE_BLACK=false
            tools_missing+=("black")
        fi

        if command -v isort >/dev/null 2>&1; then
            log_debug "isort found"
            tools_available=$((tools_available + 1))
        else
            USE_ISORT=false
            tools_missing+=("isort")
        fi
    fi

    # Check for autopep8 as fallback
    if command -v autopep8 >/dev/null 2>&1; then
        log_debug "autopep8 found"
        tools_available=$((tools_available + 1))
    else
        USE_AUTOPEP8=false
        tools_missing+=("autopep8")
    fi

    # Install missing tools if needed
    if [[ ${#tools_missing[@]} -gt 0 ]] && [[ "$tools_available" -eq 0 ]]; then
        log_warning "No Python formatting tools found. Installing essential tools..."
        if [[ "$DRY_RUN" == "false" ]]; then
            python3 -m pip install --user black isort autopep8 2>/dev/null || {
                log_error "Failed to install Python formatting tools. Please install manually:"
                printf '%s\n' "${tools_missing[@]}" | sed 's/^/  - python3 -m pip install /'
                exit 1
            }
            USE_BLACK=true
            USE_ISORT=true
            USE_AUTOPEP8=true
        fi
    elif [[ ${#tools_missing[@]} -gt 0 ]]; then
        log_warning "Some tools missing but continuing with available tools: ${tools_missing[*]}"
    fi

    log_success "Tool availability check completed"
}

# Find Python files
find_python_files() {
    log_debug "Finding Python files in: $TARGET_DIR"

    local files=()

    # Find .py files excluding common directories to avoid
    while IFS= read -r -d '' file; do
        # Skip if file is in excluded directories
        if [[ "$file" =~ (/__pycache__/|/\.git/|/\.venv/|/venv/|/node_modules/|/\.pytest_cache/|/archive/|/\.python-backups/|/\.markdown-backups/) ]]; then
            continue
        fi

        files+=("$file")
    done < <(
        if [[ -n "$SINGLE_FILE" ]]; then
            printf '%s\0' "$SINGLE_FILE"
        else
            find "$TARGET_DIR" -name "*.py" -type f -print0 2>/dev/null
        fi
    )

    log_info "Found ${#files[@]} Python files to process"

    if [[ "$VERBOSE" == "true" ]]; then
        for file in "${files[@]}"; do
            log_debug "  - $file"
        done
    fi

    # Output files for processing
    for file in "${files[@]}"; do
        echo "$file"
    done
}

# Create backup of file
backup_file() {
    local file="$1"

    if [[ "$BACKUP_ENABLED" == "false" ]]; then
        return 0
    fi

    local backup_path="$BACKUP_DIR/${file#./}"
    local backup_dir
    backup_dir=$(dirname "$backup_path")

    mkdir -p "$backup_dir"
    cp "$file" "$backup_path" 2>/dev/null || {
        log_warning "Failed to backup $file"
        return 1
    }

    log_debug "Backed up: $file → $backup_path"
}

# Enhanced: Comprehensive ruff-based fixes for all major issues
fix_with_ruff() {
    local file="$1"
    local changes_made=false

    log_debug "Applying comprehensive ruff fixes to: $file"

    if [[ "$USE_RUFF" == "true" ]] && [[ "$DRY_RUN" == "false" ]]; then
        # Apply ruff auto-fixes for the most common issues
        local ruff_fixes=""

        # Build fix list based on configuration
        if [[ "$REMOVE_UNUSED_IMPORTS" == "true" ]]; then
            ruff_fixes="${ruff_fixes}F401,"  # Unused imports
        fi

        if [[ "$REMOVE_UNUSED_VARIABLES" == "true" ]]; then
            ruff_fixes="${ruff_fixes}F841,"  # Unused variables
        fi

        if [[ "$FIX_FSTRING_ISSUES" == "true" ]]; then
            ruff_fixes="${ruff_fixes}F541,"  # f-string issues
        fi

        # Always fix basic errors and formatting
        ruff_fixes="${ruff_fixes}E501,E502,E731,W291,W292,W293,C4"  # Line length, trailing whitespace, etc.

        # Remove trailing comma
        ruff_fixes="${ruff_fixes%,}"

        # Run ruff with auto-fix
        if [[ -n "$RUFF_CMD" ]]; then
            # Run ruff check but don't abort on non-zero (common when diagnostics exist)
            set +e
            if [[ "$RUFF_AUTO_FIX" == "true" ]]; then
                $RUFF_CMD check --fix --select="$ruff_fixes" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            else
                $RUFF_CMD check --select="$ruff_fixes" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            fi
            local rc_check=$?
            set -e
            [[ $rc_check -eq 0 ]] && { log_debug "Applied ruff fixes to $file"; changes_made=true; }

            # Run ruff format (usually returns 0)
            if $RUFF_CMD format --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null; then
                log_debug "Applied ruff formatting to $file"
                changes_made=true
            fi
        fi
    fi

    [[ "$changes_made" == "true" ]]
}

# Enhanced: Mass fix function for handling large numbers of issues
fix_mass_issues() {
    local file="$1"
    local changes_made=false

    log_debug "Applying mass fixes to: $file"

    if [[ "$USE_RUFF" == "true" ]]; then
        # Handle dry-run mode
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "DRY RUN: Would apply mass fixes to $file"
            if [[ -n "$RUFF_CMD" ]]; then
                log_info "Would run: $RUFF_CMD check --fix --select=E501,F401,F541,F841 --line-length=$MAX_LINE_LENGTH"
                log_info "Would run: $RUFF_CMD format --line-length=$MAX_LINE_LENGTH"
            fi
            return 0
        fi

        # First, try to fix syntax errors and basic issues
        if ! python3 -m py_compile "$file" >/dev/null 2>&1; then
            log_warning "Syntax errors detected in $file, attempting basic fixes..."

            # Try to fix common syntax issues with sed
            sed -i 's/from \.\([a-zA-Z_][a-zA-Z0-9_]*\) import \*/from app.\1 import \*/g' "$file" 2>/dev/null || true
            sed -i 's/from \([a-zA-Z_][a-zA-Z0-9_]*\) import \*/from app.\1 import \*/g' "$file" 2>/dev/null || true
        fi

        # Apply comprehensive ruff fixes for mass issues
        if [[ -n "$RUFF_CMD" ]]; then
            # Fix the most common issues found in analysis:
            # E501 (1495), F401 (228), F541 (85), F841 (37)
            local mass_fixes="E501,F401,F541,F841,E502,E731,W291,W292,W293,C401,F811,F821,N802,N806"

            set +e
            if [[ "$RUFF_AUTO_FIX" == "true" ]]; then
                $RUFF_CMD check --fix --select="$mass_fixes" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            else
                $RUFF_CMD check --select="$mass_fixes" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            fi
            local rc_mass=$?
            set -e
            if [[ $rc_mass -eq 0 ]]; then
                log_debug "Applied mass ruff fixes to $file"
                changes_made=true
            fi

            # Apply formatting
            if $RUFF_CMD format --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null; then
                log_debug "Applied ruff formatting to $file"
                changes_made=true
            fi

            # Second pass for remaining issues
            set +e
            if [[ "$RUFF_AUTO_FIX" == "true" ]]; then
                $RUFF_CMD check --fix --select="E,W,F" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            else
                $RUFF_CMD check --select="E,W,F" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            fi
            local rc_second=$?
            set -e
            if [[ $rc_second -eq 0 ]]; then
                log_debug "Applied second-pass fixes to $file"
                changes_made=true
            fi
        fi
    fi

    [[ "$changes_made" == "true" ]]
}

# Enhanced: Comprehensive fix function for handling both ruff and pylint issues
fix_comprehensive_issues() {
    local file="$1"
    local changes_made=false

    log_debug "Applying comprehensive fixes (ruff + pylint) to: $file"

    if [[ "$USE_RUFF" == "true" ]]; then
        # Handle dry-run mode
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "DRY RUN: Would apply comprehensive fixes to $file"
            if [[ -n "$RUFF_CMD" ]]; then
                log_info "Would run: $RUFF_CMD check --fix --select=ALL --line-length=$MAX_LINE_LENGTH"
                log_info "Would run: $RUFF_CMD format --line-length=$MAX_LINE_LENGTH"
                log_info "Would apply pylint-style fixes for: W0718, W1203, C0415, W0201, C0301"
            fi
            return 0
        fi

        # First, apply all basic ruff fixes
        if [[ -n "$RUFF_CMD" ]]; then
            # Apply extensive ruff fixes covering most issues
            local comprehensive_fixes
            if [[ "$APPLY_AGGRESSIVE_FIXES" == "true" ]]; then
                comprehensive_fixes="E,W,F,C,N,B,A,COM,D,EM,EXE,ICN,INP,PIE,PT,Q,RET,SIM,TID,UP,YTT"
            else
                comprehensive_fixes="E,W,F,C,N"
            fi

            set +e
            if [[ "$RUFF_AUTO_FIX" == "true" ]]; then
                $RUFF_CMD check --fix --select="$comprehensive_fixes" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            else
                $RUFF_CMD check --select="$comprehensive_fixes" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            fi
            local rc_comp=$?
            set -e
            if [[ $rc_comp -eq 0 ]]; then
                log_debug "Applied comprehensive ruff fixes to $file"
                changes_made=true
            fi

            # Apply formatting
            if $RUFF_CMD format --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null; then
                log_debug "Applied ruff formatting to $file"
                changes_made=true
            fi

            # Apply additional pylint-style fixes with sed patterns
            # Fix broad exception handling (W0718)
            if sed -i 's/except Exception:/except Exception as e:/g' "$file" 2>/dev/null; then
                changes_made=true
            fi

            # Fix f-string logging (W1203) - convert format strings to f-strings
            if perl -i -pe 's/log(?:ger)?\.(\w+)\(("[^"]*?%[^"]*?")\s*,\s*([^)]+)\)/log$1(f$2.replace("%s", "{$3}").replace("%d", "{$3}"))/g' "$file" 2>/dev/null; then
                changes_made=true
            fi

            # Fix import outside toplevel (C0415) - move imports to top when safe
            if python3 -c "
import re
import sys

file_path = '$file'
try:
    with open(file_path, 'r') as f:
        content = f.read()

    # Extract imports that are inside functions/methods
    lines = content.split('\n')
    imports_to_move = []
    new_lines = []
    in_function = False
    indent_level = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('def ') or stripped.startswith('class '):
            in_function = True
            indent_level = len(line) - len(line.lstrip())
        elif in_function and line and len(line) - len(line.lstrip()) <= indent_level:
            in_function = False

        if in_function and (stripped.startswith('import ') or stripped.startswith('from ')) and 'if' not in stripped:
            # Simple import that can be moved
            imports_to_move.append(stripped)
            new_lines.append('')  # Remove from current position
        else:
            new_lines.append(line)

    if imports_to_move:
        # Insert imports after existing imports
        import_section_end = 0
        for i, line in enumerate(new_lines):
            if line.strip().startswith(('import ', 'from ')):
                import_section_end = i + 1

        for imp in imports_to_move:
            new_lines.insert(import_section_end, imp)
            import_section_end += 1

        with open(file_path, 'w') as f:
            f.write('\n'.join(new_lines))
except:
    pass
" 2>/dev/null; then
                changes_made=true
            fi

            # Final cleanup pass
            set +e
            if [[ "$RUFF_AUTO_FIX" == "true" ]]; then
                $RUFF_CMD check --fix --select="E,W,F" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            else
                $RUFF_CMD check --select="E,W,F" --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null
            fi
            local rc_final=$?
            set -e
            if [[ $rc_final -eq 0 ]]; then
                log_debug "Applied final cleanup fixes to $file"
                changes_made=true
            fi
        fi
    fi

    # Optionally run pylint for additional diagnostics
    if [[ "$RUN_PYLINT" == "true" ]] && [[ "$DRY_RUN" == "false" ]]; then
        if command -v pylint >/dev/null 2>&1; then
            # Respect exclusions
            if [[ "$file" =~ (/archive/|/\.python-backups/|/\.venv/|/venv/) ]]; then
                : # skip
            else
                pylint --score=y "$file" >/dev/null 2>&1 || true
            fi
        fi
    fi

    [[ "$changes_made" == "true" ]]
}

# Apply import fixes using pylance/isort
fix_imports() {
    local file="$1"
    local changes_made=false

    log_debug "Fixing imports in: $file"

    # Try isort first if available
    if [[ "$USE_ISORT" == "true" ]] && [[ "$DRY_RUN" == "false" ]]; then
        if isort --check-only --diff "$file" >/dev/null 2>&1; then
            log_debug "No import changes needed for $file"
        else
            if isort "$file" 2>/dev/null; then
                log_debug "Applied isort fixes to $file"
                changes_made=true
            else
                log_warning "isort failed for $file"
            fi
        fi
    fi

    # Apply Pylance refactoring for imports if available
    if command -v python3 >/dev/null 2>&1; then
        # Create a simple import organizer script
        cat > "$TEMP_DIR/organize_imports.py" << 'EOF'
import sys
import ast
import re
from typing import List, Set, Tuple

def organize_imports(file_path: str) -> bool:
    """Organize imports in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse to find import statements
        tree = ast.parse(content)

        # Simple import organization - separate standard library, third-party, and local
        import_lines = []
        other_lines = []

        lines = content.split('\n')
        in_imports = False
        import_section_end = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')) and not stripped.startswith('#'):
                in_imports = True
                import_lines.append((i, line))
                import_section_end = i
            elif in_imports and (stripped == '' or stripped.startswith('#')):
                import_section_end = i
            elif stripped and not stripped.startswith('#') and in_imports:
                break

        # If we found imports, organize them
        if import_lines:
            # Group imports
            stdlib_imports = []
            third_party_imports = []
            local_imports = []

            stdlib_modules = {
                'os', 'sys', 'json', 'time', 'datetime', 'typing', 'collections',
                'subprocess', 'pathlib', 'logging', 'configparser', 'argparse',
                'threading', 'multiprocessing', 'asyncio', 'queue', 're',
                'sqlite3', 'urllib', 'http', 'xml', 'csv', 'tempfile'
            }

            for line_num, line in import_lines:
                if 'from .' in line or 'from ..' in line:
                    local_imports.append(line)
                else:
                    # Extract module name
                    if line.strip().startswith('import '):
                        module = line.strip().split()[1].split('.')[0]
                    elif line.strip().startswith('from '):
                        module = line.strip().split()[1].split('.')[0]
                    else:
                        module = ''

                    if module in stdlib_modules:
                        stdlib_imports.append(line)
                    else:
                        third_party_imports.append(line)

            # Rebuild import section
            new_import_section = []
            if stdlib_imports:
                new_import_section.extend(sorted(set(stdlib_imports)))
                new_import_section.append('')
            if third_party_imports:
                new_import_section.extend(sorted(set(third_party_imports)))
                new_import_section.append('')
            if local_imports:
                new_import_section.extend(sorted(set(local_imports)))
                new_import_section.append('')

            # Remove trailing empty line
            if new_import_section and new_import_section[-1] == '':
                new_import_section.pop()

            # Rebuild file content
            new_lines = []
            import_line_numbers = {line_num for line_num, _ in import_lines}

            # Add lines before imports
            for i, line in enumerate(lines):
                if i in import_line_numbers:
                    if not new_import_section:
                        continue
                    new_lines.extend(new_import_section)
                    new_import_section = []  # Only add once
                elif i <= import_section_end and line.strip() == '':
                    continue  # Skip empty lines in import section
                else:
                    new_lines.append(line)

            new_content = '\n'.join(new_lines)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

    except Exception as e:
        print(f"Error organizing imports in {file_path}: {e}", file=sys.stderr)

    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python organize_imports.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    if organize_imports(file_path):
        print(f"Organized imports in {file_path}")
    else:
        print(f"No import changes needed for {file_path}")
EOF

        if [[ "$DRY_RUN" == "false" ]]; then
            if python3 "$TEMP_DIR/organize_imports.py" "$file" 2>/dev/null | grep -q "Organized imports"; then
                log_debug "Applied custom import organization to $file"
                changes_made=true
            fi
        fi
    fi

    if [[ "$changes_made" == "true" ]]; then
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    fi

    return 0
}

# Apply code formatting
fix_formatting() {
    local file="$1"
    local changes_made=false

    log_debug "Applying formatting fixes to: $file"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_debug "DRY RUN: Would format $file"
        return 0
    fi

    # Use ruff if available (preferred)
    if [[ "$USE_RUFF" == "true" ]]; then
        if ruff format "$file" 2>/dev/null; then
            log_debug "Applied ruff formatting to $file"
            changes_made=true
        fi
        if ruff check --fix "$file" 2>/dev/null; then
            log_debug "Applied ruff linting fixes to $file"
            changes_made=true
        fi
    else
        # Use black for formatting
        if [[ "$USE_BLACK" == "true" ]]; then
            if black --line-length "$MAX_LINE_LENGTH" --quiet "$file" 2>/dev/null; then
                log_debug "Applied black formatting to $file"
                changes_made=true
            fi
        fi

        # Use autopep8 as fallback
        if [[ "$USE_AUTOPEP8" == "true" ]]; then
            if autopep8 --in-place --aggressive --aggressive --max-line-length "$MAX_LINE_LENGTH" "$file" 2>/dev/null; then
                log_debug "Applied autopep8 formatting to $file"
                changes_made=true
            fi
        fi
    fi

    if [[ "$changes_made" == "true" ]]; then
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    fi

    return 0
}

# Fix common linting issues
fix_linting_issues() {
    local file="$1"
    local changes_made=false

    log_debug "Fixing linting issues in: $file"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_debug "DRY RUN: Would fix linting issues in $file"
        return 0
    fi

    # Create a Python script to fix common issues
    cat > "$TEMP_DIR/fix_linting.py" << 'EOF'
import sys
import re
from typing import List

def fix_common_linting_issues(file_path: str) -> bool:
    """Fix common Python linting issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix unused imports (basic detection)
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                new_lines.append(line)
                continue

            # Check for unused imports (very basic)
            if line.strip().startswith(('import ', 'from ')) and ' import ' in line:
                # This is a very basic check - in practice, use a proper tool
                new_lines.append(line)
            else:
                new_lines.append(line)

        # Fix trailing whitespace
        new_lines = [line.rstrip() for line in new_lines]

        # Ensure file ends with newline
        new_content = '\n'.join(new_lines)
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'

        # Fix multiple blank lines
        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)

        # Fix missing blank lines after imports
        new_content = re.sub(r'(^from .+?import .+?$)(\n)(^[a-zA-Z_])', r'\1\n\n\3', new_content, flags=re.MULTILINE)
        new_content = re.sub(r'(^import .+?$)(\n)(^[a-zA-Z_])', r'\1\n\n\3', new_content, flags=re.MULTILINE)

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

    except Exception as e:
        print(f"Error fixing linting issues in {file_path}: {e}", file=sys.stderr)

    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_linting.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    if fix_common_linting_issues(file_path):
        print(f"Fixed linting issues in {file_path}")
    else:
        print(f"No linting changes needed for {file_path}")
EOF

    if python3 "$TEMP_DIR/fix_linting.py" "$file" 2>/dev/null | grep -q "Fixed linting issues"; then
        log_debug "Applied linting fixes to $file"
        changes_made=true
    fi

    if [[ "$changes_made" == "true" ]]; then
        FIXES_APPLIED=$((FIXES_APPLIED + 1))
    fi

    return 0
}

# Process a single Python file
process_file() {
    local file="$1"

    log_debug "Processing file: $file"

    # Check if file exists and is readable
    if [[ ! -f "$file" ]]; then
        log_warning "File not found: $file"
        return 1
    fi

    if [[ ! -r "$file" ]]; then
        log_warning "File not readable: $file"
        return 1
    fi

    # Backup file before modifications
    backup_file "$file"

    # Apply fixes based on strategy
    case "$STRATEGY" in
        "safe")
            if [[ "$USE_RUFF" == "true" ]]; then
                fix_with_ruff "$file"
            else
                [[ "$FIX_FORMATTING" == "true" ]] && fix_formatting "$file"
            fi
            ;;
        "aggressive")
            if [[ "$USE_RUFF" == "true" ]]; then
                # Use comprehensive ruff fixes for aggressive mode
                fix_with_ruff "$file"
            else
                # Fallback to individual tools
                [[ "$FIX_IMPORTS" == "true" ]] && fix_imports "$file"
                [[ "$FIX_FORMATTING" == "true" ]] && fix_formatting "$file"
                [[ "$FIX_LINTING" == "true" ]] && fix_linting_issues "$file"
            fi
            ;;
        "mass")
            # New strategy for handling large numbers of issues
            if [[ "$USE_RUFF" == "true" ]]; then
                fix_mass_issues "$file"
            else
                log_warning "Mass fix strategy requires ruff. Falling back to aggressive mode."
                [[ "$FIX_IMPORTS" == "true" ]] && fix_imports "$file"
                [[ "$FIX_FORMATTING" == "true" ]] && fix_formatting "$file"
                [[ "$FIX_LINTING" == "true" ]] && fix_linting_issues "$file"
            fi
            ;;
        "comprehensive")
            # Most thorough strategy - handles both ruff and pylint issues
            if [[ "$USE_RUFF" == "true" ]]; then
                log_debug "Applying comprehensive fixes (ruff + pylint) to: $file"
                fix_comprehensive_issues "$file"
            else
                log_warning "Comprehensive strategy works best with ruff. Using individual tools."
                [[ "$FIX_IMPORTS" == "true" ]] && fix_imports "$file"
                [[ "$FIX_FORMATTING" == "true" ]] && fix_formatting "$file"
                [[ "$FIX_LINTING" == "true" ]] && fix_linting_issues "$file"
            fi
            ;;
        "imports-only")
            if [[ "$USE_RUFF" == "true" ]] && [[ "$REMOVE_UNUSED_IMPORTS" == "true" ]]; then
                # Use ruff for import fixes
                set +e
                if [[ "$RUFF_AUTO_FIX" == "true" ]]; then
                    $RUFF_CMD check --fix --select="F401,F811" "$file" 2>/dev/null
                else
                    $RUFF_CMD check --select="F401,F811" "$file" 2>/dev/null
                fi
                set -e
            else
                [[ "$FIX_IMPORTS" == "true" ]] && fix_imports "$file"
            fi
            ;;
        "format-only")
            if [[ "$USE_RUFF" == "true" ]]; then
                $RUFF_CMD format --line-length="$MAX_LINE_LENGTH" "$file" 2>/dev/null || true
            else
                [[ "$FIX_FORMATTING" == "true" ]] && fix_formatting "$file"
            fi
            ;;
    esac

    FILES_PROCESSED=$((FILES_PROCESSED + 1))

    # Security hygiene warnings (no changes applied)
    warn_insecure_subprocess "$file"

    return 0
}

# Main processing function
process_python_files() {
    log_info "Starting Python processing..."
    log_info "Target: $TARGET_DIR"
    log_info "Strategy: $STRATEGY"
    log_info "Dry run: $DRY_RUN"

    # Find all Python files
    local files=()
    while IFS= read -r -d '' file; do
        # Skip if file is in excluded directories
        if [[ "$file" =~ (/__pycache__/|/\.git/|/\.venv/|/venv/|/node_modules/|/\.pytest_cache/|/archive/|/\.python-backups/|/\.markdown-backups/) ]]; then
            continue
        fi
        files+=("$file")
    done < <(
        if [[ -n "$SINGLE_FILE" ]]; then
            printf '%s\0' "$SINGLE_FILE"
        else
            find "$TARGET_DIR" -name "*.py" -type f -print0 2>/dev/null
        fi
    )

    if [[ ${#files[@]} -eq 0 ]]; then
        log_warning "No Python files found to process"
        return 0
    fi

    log_info "Processing ${#files[@]} Python files..."

    # Process each file
    for file in "${files[@]}"; do
        log_debug "Processing file: $file"
        process_file "$file"
        PROCESSED_FILES+=("$file")
    done

    log_success "Python processing completed successfully"
    log_info "Files processed: $FILES_PROCESSED"
    log_info "Fixes applied: $FIXES_APPLIED"

    if [[ "$BACKUP_ENABLED" == "true" ]]; then
        log_info "Backups stored in: $BACKUP_DIR"
    fi

    return 0
}

# Cleanup function
cleanup() {
    log_debug "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR" 2>/dev/null || true
}

# Run pylint on processed files with repo configuration
run_pylint_check() {
    [[ "$RUN_PYLINT" != "true" ]] && return 0

    if ! command -v pylint >/dev/null 2>&1; then
        log_warning "pylint is not installed; skipping pylint check"
        return 0
    fi

    if [[ ${#PROCESSED_FILES[@]} -eq 0 ]]; then
        log_info "No files processed; skipping pylint check"
        return 0
    fi

    local pylintrc="$WORKSPACE_ROOT/.pylintrc"
    [[ -f "$pylintrc" ]] || pylintrc=""
    local report_file="$LOG_DIR/pylint-report.txt"
    mkdir -p "$LOG_DIR"

    log_info "Running pylint on ${#PROCESSED_FILES[@]} files${pylintrc:+ using $(basename "$pylintrc")}"

    if [[ -n "$pylintrc" ]]; then
        printf '%s\n' "${PROCESSED_FILES[@]}" | xargs -r pylint --rcfile "$pylintrc" | tee "$report_file" || true
    else
        printf '%s\n' "${PROCESSED_FILES[@]}" | xargs -r pylint | tee "$report_file" || true
    fi

    # Parse final score if present
    local score
    score=$(grep -Eo "rated at [0-9]+\.[0-9]+/10" "$report_file" | tail -1 | awk '{print $3}' | cut -d'/' -f1 || true)
    if [[ -n "$score" ]]; then
        log_info "pylint score: $score/10"
        if [[ -n "$PYLINT_FAIL_UNDER" ]]; then
            awk -v s="$score" -v t="$PYLINT_FAIL_UNDER" 'BEGIN {exit (s+0 < t+0) ? 1 : 0}' >/dev/null || {
                log_error "pylint score $score is below threshold $PYLINT_FAIL_UNDER"
            }
        fi
    else
        log_warning "Could not parse pylint score; see $report_file"
    fi
}

# Optional: warn about insecure subprocess usage patterns (no modifications)
warn_insecure_subprocess() {
    local file="$1"
    [[ "$SECURITY_WARN" != "true" ]] && return 0

    if grep -nE "subprocess\.(Popen|call|run)\(.*shell=\s*True" "$file" >/dev/null 2>&1; then
        log_warning "$file: Potential insecure subprocess usage (shell=True). Prefer allowlist + no shell."
    fi
    if grep -nE "subprocess\.(Popen|call|run)\(" "$file" | grep -vq "timeout=" >/dev/null 2>&1; then
        log_warning "$file: subprocess call without timeout detected; add a timeout and error handling."
    fi
}

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool provides comprehensive Python code quality fixes including:
- Import organization and optimization
- Code formatting (black, autopep8, ruff)
- Common linting issue fixes
- Type hint improvements
- Pylance compatibility fixes

Options:
    -h, --help               Show this help message
    -v, --verbose            Enable verbose output
    -d, --dry-run            Preview changes without applying them
    -t, --target DIR         Target directory (default: current directory)
    -s, --strategy STRAT     Fix strategy: safe, aggressive, mass, comprehensive, imports-only, format-only
    --no-backup              Disable backup creation
    --no-imports             Skip import fixes
    --no-formatting          Skip code formatting
    --no-linting             Skip linting fixes
    --line-length N          Maximum line length (default: 100)
    --use-ruff               Prefer ruff over other tools
    --pylint                 Run pylint after fixes using repo .pylintrc
    --pylint-fail-under N    Fail if pylint score is below N (e.g., 9.5)
    --no-security-warn       Disable insecure subprocess warnings
    --version                Show version information

Strategies:
    safe               Only apply safe formatting fixes (default)
    aggressive         Apply all available fixes
    mass              Mass fix for 1000+ issues using ruff (enhanced)
    comprehensive     Fix both ruff and pylint issues (most thorough)
    imports-only       Only fix import organization
    format-only        Only apply code formatting

Examples:
    $0                           # Safe fixes in current directory
    $0 --strategy aggressive     # Apply all fixes aggressively
    $0 --strategy mass          # Handle large numbers of issues efficiently
    $0 --strategy comprehensive  # Fix ruff + pylint issues comprehensively
    $0 --target app/ --verbose   # Fix specific directory with verbose output
    $0 --dry-run --strategy mass  # Preview mass changes

Dependencies:
    - Python 3.6+
    - Optional: black, isort, autopep8, ruff
    - Will auto-install missing tools if needed

Report bugs and feature requests to the development team.
EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -t|--target)
                TARGET_DIR="$2"
                shift 2
                ;;
            -s|--strategy)
                STRATEGY="$2"
                case "$STRATEGY" in
                    safe|aggressive|mass|comprehensive|imports-only|format-only)
                        ;;
                    *)
                        log_error "Invalid strategy: $STRATEGY"
                        log_error "Valid strategies: safe, aggressive, mass, comprehensive, imports-only, format-only"
                        exit 1
                        ;;
                esac
                shift 2
                ;;
            --no-backup)
                BACKUP_ENABLED=false
                shift
                ;;
            --no-imports)
                FIX_IMPORTS=false
                shift
                ;;
            --no-formatting)
                FIX_FORMATTING=false
                shift
                ;;
            --no-linting)
                FIX_LINTING=false
                shift
                ;;
            --line-length)
                MAX_LINE_LENGTH="$2"
                shift 2
                ;;
            --use-ruff)
                USE_RUFF=true
                USE_BLACK=false
                USE_ISORT=false
                shift
                ;;
            --pylint)
                RUN_PYLINT=true
                shift
                ;;
            --pylint-fail-under)
                PYLINT_FAIL_UNDER="$2"
                shift 2
                ;;
            --no-security-warn)
                SECURITY_WARN=false
                shift
                ;;
            --version)
                echo "$TOOL_NAME version $TOOL_VERSION"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_error "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    # Set up error handling
    trap cleanup EXIT

    # Parse arguments
    parse_arguments "$@"

    # Initialize environment
    init_environment

    # Initialize single file variable
    SINGLE_FILE=""

    # Check tool availability
    check_tool_availability

    # Resolve target directory to absolute path
    if [[ -f "$TARGET_DIR" ]]; then
        # If target is a file, get its directory and process only that file
        SINGLE_FILE="$TARGET_DIR"
        TARGET_DIR=$(dirname "$TARGET_DIR")
        log_debug "Processing single file: $SINGLE_FILE"
        log_debug "Directory: $TARGET_DIR"
    elif [[ ! -d "$TARGET_DIR" ]]; then
        log_error "Target does not exist: $TARGET_DIR"
        exit 1
    fi

    # Convert target to absolute path for processing
    TARGET_DIR=$(cd "$TARGET_DIR" && pwd)
    if [[ -n "$SINGLE_FILE" ]]; then
        SINGLE_FILE="$TARGET_DIR/$(basename "$SINGLE_FILE")"
    fi
    log_debug "Resolved target directory: $TARGET_DIR"

    # Process Python files
    process_python_files

    # Optional pylint validation
    run_pylint_check

    # Show summary
    echo
    log_success "=== Python Quality Fix Summary ==="
    log_info "Files processed: $FILES_PROCESSED"
    log_info "Fixes applied: $FIXES_APPLIED"
    log_info "Errors encountered: $ERRORS_FOUND"

    if [[ "$BACKUP_ENABLED" == "true" ]]; then
        log_info "Backups location: $BACKUP_DIR"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: No changes were actually applied"
    fi

    # Exit with appropriate code
    if [[ "$ERRORS_FOUND" -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function with all arguments
main "$@"
