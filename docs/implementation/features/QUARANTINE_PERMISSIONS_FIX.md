# Quarantine Directory Permissions Fix

## Issue Identified

During application startup, users were seeing this warning:

```text
Startup self-check warnings:
Weak permissions on quarantine (0o755); expected 0o700

```text

## Root Cause Analysis

The quarantine directory was being created with default permissions (0o755) instead of secure permissions (0o700), which posed a potential security risk.

### Security Concern

- **0o755 permissions**: `drwxr-xr-x` - Owner, group, and others can read and execute
- **0o700 permissions**: `drwx------` - Only owner can read, write, and execute

The quarantine directory should be accessible only by the application owner since it may contain potentially malicious files that have been isolated.

## Technical Details

### Original Problem

In `/app/utils/config.py`, the quarantine directory was created without explicit permissions:

```Python

## Create subdirectories

SCAN_REPORTS_DIR.mkdir(exist_ok=True)
QUARANTINE_DIR.mkdir(exist_ok=True)  # Used default permissions (0o755)
LOG_DIR.mkdir(exist_ok=True)

```text

### Security Check Logic

In `/app/gui/main_window.py`, the startup self-check validates directory permissions:

```Python
if name in ("config", "quarantine") and mode not in (0o700, 0o750):
    issues.append(f"Weak permissions on {name} ({oct(mode)}); expected 0o700")

```text

## Solution Implemented

### 1. Enhanced Directory Creation (config.py)

```Python

## Create subdirectories 2

SCAN_REPORTS_DIR.mkdir(exist_ok=True)

## Create quarantine directory with secure permissions (0o700)

QUARANTINE_DIR.mkdir(exist_ok=True)
if os.name == "posix":  # Unix-like systems
    try:
        QUARANTINE_DIR.chmod(0o700)  # Only owner can read/write/execute
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not set secure permissions on quarantine directory: {e}")

LOG_DIR.mkdir(exist_ok=True)

```text

### 2. Enhanced Startup Self-Check (main_window.py)

```Python
if name in ("config", "quarantine") and mode not in (0o700, 0o750):

## Try to fix quarantine permissions automatically

    if name == "quarantine":
        try:
            d.chmod(0o700)
            print(f"✅ Fixed quarantine directory permissions: {oct(mode)} → 0o700")
            continue  # Skip adding to issues since we fixed it
        except (OSError, PermissionError) as e:
            issues.append(f"Weak permissions on {name} ({oct(mode)}); expected 0o700 - Failed to fix: {e}")
            continue
    issues.append(f"Weak permissions on {name} ({oct(mode)}); expected 0o700")

```text

## Fix Benefits

### 1. Security Enhancement

- **Improved isolation**: Quarantine directory accessible only by application owner
- **Reduced attack surface**: Prevents unauthorized access to quarantined files
- **Compliance**: Follows security best practices for sensitive directories

### 2. User Experience

- **Silent fix**: Permissions corrected automatically during startup
- **No manual intervention**: Users don't need to manually fix permissions
- **Clear feedback**: When permissions are fixed, users see confirmation message

### 3. Robustness

- **Cross-platform compatibility**: Only applies on POSIX systems (Unix/Linux/macOS)
- **Error handling**: Graceful fallback if permission changes fail
- **Dual protection**: Both creation-time and runtime permission fixes

## Files Modified

### app/utils/config.py

- **Enhanced quarantine directory creation**: Added explicit chmod(0o700) after mkdir
- **Added OS detection**: Only applies secure permissions on POSIX systems
- **Added error handling**: Graceful handling of permission change failures

### app/gui/main_window.py

- **Enhanced startup self-check**: Added automatic permission fix attempt
- **Improved feedback**: Clear success/failure messages for permission fixes
- **Fallback behavior**: Still warns if automatic fix fails

## Testing Results

### Before Fix

```bash
$ ls -la ~/.local/share/search-and-destroy/ | grep quarantine
drwxr-xr-x 1 vm vm  26 Aug  5 11:49 quarantine

## App startup showed

## Startup self-check warnings

## Weak permissions on quarantine (0o755); expected 0o700

```text

### After Fix

```bash
$ ls -la ~/.local/share/search-and-destroy/ | grep quarantine
drwx------ 1 vm vm  26 Aug  5 11:49 quarantine

## App startup shows no permission warnings

```text

## Compatibility

### Platform Support

- ✅ **Linux**: Full support with chmod() functionality
- ✅ **macOS**: Full support with chmod() functionality
- ✅ **Windows**: Graceful fallback (permissions concept differs)
- ✅ **Other POSIX**: Full support on Unix-like systems

### Backwards Compatibility

- ✅ **Existing installations**: Automatically fixes permissions on next startup
- ✅ **New installations**: Creates quarantine directory with secure permissions
- ✅ **Permission failures**: Graceful degradation with warning messages

## Security Validation

### Permission Verification

```bash

## Verify secure permissions

$ stat -c '%a %n' ~/.local/share/search-and-destroy/quarantine
700 /home/vm/.local/share/search-and-destroy/quarantine

## Verify access control

$ ls -la ~/.local/share/search-and-destroy/quarantine
drwx------ 1 vm vm 26 Aug  5 11:49 .

```text

### Attack Vector Mitigation

- **Prevents unauthorized file access**: Other users cannot read quarantined files
- **Prevents information disclosure**: Directory listing not available to other users
- **Prevents tampering**: Other users cannot modify or delete quarantined files

## Future Considerations

### Potential Enhancements

- **Encrypted quarantine**: Add file-level encryption for quarantined items
- **Audit logging**: Log all quarantine directory access attempts
- **Permission monitoring**: Detect and alert on unauthorized permission changes

### Maintenance

- **Regular checks**: Periodic verification of quarantine directory permissions
- **Update handling**: Ensure permissions preserved during application updates
- **Recovery procedures**: Automated recovery from permission corruption

Date: August 11, 2025
Status: ✅ COMPLETED AND TESTED
Security Impact: HIGH (Improved isolation of potentially malicious files)
User Impact: LOW (Silent fix, no user action required)
