# Archive Directory

This directory contains archived files from the xanadOS Search & Destroy project to prevent accidental loss of code during refactoring and cleanup operations.

## Directory Structure

### `/cleanup-stubs/`
Contains stub files that were created during aggressive cleanup operations. These files replaced working implementations and caused functionality loss.

**Contents:**
- `scan_dialog_stub.py` - Minimal stub that replaced scan dialog functionality (28 lines)
- `settings_dialog_stub.py` - Minimal stub that replaced settings dialog functionality (28 lines)

**Note:** These stubs were created during the comprehensive cleanup that broke the application. They serve as examples of what NOT to do during cleanup operations.

### `/unused-components/`
For components that are no longer actively used but may contain valuable code or concepts for future reference.

### `/old-versions/`
Contains backup versions and previous implementations of files.

**Contents:**

- `main_window_corrupted_backup.py.txt` - Corrupted backup of main_window.py from cleanup operation (renamed to .txt to avoid syntax checking)
- `rkhunter_components_backup.py` - Backup of rkhunter_components.py

### `/experimental/`
For experimental features and proof-of-concept implementations that aren't ready for main codebase.

## Archive Guidelines

### When to Archive Files:
1. **Before Major Refactoring**: Always create backups before significant changes
2. **Unused Components**: When removing features that might be useful later
3. **Failed Implementations**: Code that didn't work but contains valuable learning
4. **Superseded Versions**: When replacing files with better implementations

### Naming Conventions:
- Use descriptive names indicating the reason for archiving
- Include date stamps for time-sensitive archives: `filename_YYYYMMDD.py`
- Add suffixes like `_stub`, `_backup`, `_experimental`, `_deprecated`

### File Documentation:
Each archived file should include a header comment explaining:
- Why it was archived
- Date of archiving
- What replaced it (if applicable)
- Any important notes about the implementation

## Recovery Process

To restore archived files:
1. Copy the file from archive to appropriate location
2. Review and test the restored functionality
3. Update imports and dependencies as needed
4. Document the restoration in git commit message

## Examples

### Archiving a File:
```bash
# Before deleting/replacing a file
cp app/gui/old_component.py archive/old-versions/old_component_$(date +%Y%m%d).py

# Add explanation header to archived file
echo "# ARCHIVED $(date): Replaced by new_component.py due to performance issues" | cat - archive/old-versions/old_component_*.py > temp && mv temp archive/old-versions/old_component_*.py
```

### Restoring a File:
```bash
# Copy back from archive
cp archive/old-versions/old_component_20250807.py app/gui/old_component.py

# Test and adjust as needed
```

## Lessons Learned

The creation of this archive system was prompted by an incident where comprehensive cleanup operations replaced working implementations with minimal stubs, breaking core application functionality. Key lessons:

1. **Always preserve working code** before attempting "cleanup"
2. **Test functionality** after any refactoring operation
3. **Use version control** but also maintain local archives for safety
4. **Incremental changes** are safer than comprehensive overhauls

## Maintenance

- Review archived files quarterly to determine if they can be permanently deleted
- Keep documentation updated with archival reasons
- Ensure archive doesn't grow indefinitely
- Regular cleanup of truly obsolete archived files (>1 year old and confirmed unnecessary)
