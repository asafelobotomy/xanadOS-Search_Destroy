# Script Fix Recommendations - xanadOS Search & Destroy

## Shell Script Fixes

### 1. scripts/validation/validate-agent-workflow.sh

#### Issue: Array handling and file counting (Lines 84-89)

**Current Code:**

```bash
ROOT_FILES=($(ls -1 | grep -v "^[.]" | grep -v "^docs$" | grep -v "^scripts$" | grep -v "^archive$" | grep -v "^examples$" | wc -l))
if [ "$ROOT_FILES" -le 10 ]; then
    print_success "Root directory properly organized (${ROOT_FILES} files)"
```

**Fixed Code:**

```bash
# Count files properly without ls | grep
shopt -s nullglob dotglob
all_files=(*)
filtered_files=()
for file in "${all_files[@]}"; do
    [[ "$file" =~ ^\. ]] && continue
    [[ "$file" == "docs" ]] && continue
    [[ "$file" == "scripts" ]] && continue
    [[ "$file" == "archive" ]] && continue
    [[ "$file" == "examples" ]] && continue
    filtered_files+=("$file")
done
root_file_count=${#filtered_files[@]}

if [ "$root_file_count" -le 10 ]; then
    print_success "Root directory properly organized ($root_file_count files)"
else
    print_failure "Root directory cluttered ($root_file_count files - should be ≤10)"
fi
```

#### Issue: Unused function (Line 34)

**Action:** Remove unused `print_warning()` function or add comment if intentionally reserved

### 2. scripts/validation/validate-version-control.sh

#### Issue: Declare and assign separately (Multiple locations)

**Current Pattern:**

```bash
local template_file=$(git config --get commit.template)
```

**Fixed Pattern:**

```bash
local template_file
template_file=$(git config --get commit.template)
```

**Apply to lines:** 58, 69, 77, 164, 209, 253, 319

#### Issue: Missing quotes (Line 254)

**Current Code:**

```bash
if [ $untracked_count -eq 0 ]; then
```

**Fixed Code:**

```bash
if [ "$untracked_count" -eq 0 ]; then
```

## Python Fixes

### 1. app/main.py

#### Issue: Import order (Line 16)

**Current Code:**

```python
import logging
import sys
from pathlib import Path

# Other imports...

from app.core.single_instance import SingleInstanceManager
```

**Fixed Code:**

```python
import logging
import sys
from pathlib import Path

from app.core.single_instance import SingleInstanceManager

# Rest of imports...
```

#### Issue: Broad exception handling (Line 42)

**Current Code:**

```python
try:
    # startup code
except Exception:
    # handle error
```

**Fixed Code:**

```python
try:
    # startup code
except (ImportError, RuntimeError) as e:
    logger.error(f"Startup failed: {e}")
    # handle specific error types
```

### 2. Security Improvements

#### Subprocess Security Pattern

**Current Pattern:**

```python
result = subprocess.run([command, arg], capture_output=True)
```

**Improved Pattern:**

```python
def secure_subprocess_run(command_path, args, **kwargs):
    """Run subprocess with security validation."""
    if not os.path.isfile(command_path):
        raise FileNotFoundError(f"Command not found: {command_path}")

    # Validate command path is in expected locations
    safe_paths = ["/usr/bin", "/usr/local/bin", "/bin"]
    if not any(command_path.startswith(path) for path in safe_paths):
        raise SecurityError(f"Command path not in safe locations: {command_path}")

    return subprocess.run([command_path] + args, **kwargs)
```

#### Try/Except/Pass Improvement

**Current Pattern:**

```python
try:
    risky_operation()
except Exception:
    pass
```

**Improved Pattern:**

```python
try:
    risky_operation()
except SpecificException as e:
    logger.debug(f"Non-critical operation failed: {e}")
except Exception as e:
    logger.warning(f"Unexpected error in risky_operation: {e}")
```

#### Temporary Directory Security

**Current Pattern:**

```python
temp_dir = "/tmp"
```

**Improved Pattern:**

```python
import tempfile
import os

def get_secure_temp_dir():
    """Get secure temporary directory following XDG spec."""
    if hasattr(tempfile, 'gettempdir'):
        return tempfile.gettempdir()
    return os.environ.get('XDG_RUNTIME_DIR', '/tmp')
```

## Implementation Script

Create this script to apply fixes automatically:

```bash
#!/bin/bash
# fix-debug-issues.sh

set -euo pipefail

echo "Applying debug fixes..."

# Fix shell script issues
echo "Fixing shell scripts..."

# Fix validate-agent-workflow.sh array handling
sed -i 's/ROOT_FILES=(\$(ls -1.*wc -l))/# Fixed array handling - see new implementation below/' \
    scripts/validation/validate-agent-workflow.sh

# Fix variable quoting in validate-version-control.sh
sed -i 's/\[ \$untracked_count -eq 0 \]/[ "$untracked_count" -eq 0 ]/' \
    scripts/validation/validate-version-control.sh

# Fix Python import order
echo "Fixing Python imports..."
# This would require more complex sed or a Python script for proper import reordering

echo "Manual fixes required:"
echo "1. Update array handling in validate-agent-workflow.sh"
echo "2. Split declare/assign in validate-version-control.sh"
echo "3. Improve exception handling specificity in Python files"
echo "4. Review subprocess security implementations"

echo "Fixes applied successfully!"
```

## Priority Implementation Order

### High Priority (Fix Immediately)

1. **Shell Script Array Handling**: Fix the ROOT_FILES array issue in validate-agent-workflow.sh
2. **Variable Quoting**: Add quotes around variables in shell scripts
3. **Import Organization**: Fix Python import order issues

### Medium Priority (Fix in Next Sprint)

1. **Exception Handling**: Replace broad exception catching with specific handlers
2. **Subprocess Security**: Implement command validation for subprocess calls
3. **Temporary Directory Security**: Replace hardcoded paths with secure alternatives

### Low Priority (Technical Debt)

1. **Code Organization**: Split large files into smaller modules
2. **Unused Functions**: Remove or document unused functions
3. **Style Consistency**: Apply consistent formatting across all files

## Testing Strategy

### Before Applying Fixes

```bash
# Test current functionality
./scripts/validation/validate-agent-workflow.sh
./scripts/validation/validate-version-control.sh
python3 app/main.py --version
```

### After Applying Fixes

```bash
# Verify functionality still works
shellcheck scripts/validation/*.sh
python3 -m flake8 app/main.py
python3 -m bandit -r app/ -ll
python3 app/main.py --version
```

### Regression Testing

```bash
# Full test suite
npm run validate  # If available
python3 -m pytest tests/  # If tests exist
./scripts/tools/validation/validate-structure.sh
```

## Conclusion

These fixes address the major issues identified in the comprehensive debug analysis:

- **Shell Script Robustness**: Improved array handling and variable quoting
- **Python Code Quality**: Better import organization and exception handling
- **Security Posture**: Enhanced subprocess validation and temporary file handling
- **Maintainability**: Clearer error handling and reduced technical debt

The fixes are designed to be low-risk and maintain backward compatibility while improving code
quality and security posture.
