# RKHunter Configuration Fix Report

## Issue Description

User reported RKHunter scan failure with error:
"Unknown disabled test name in the configuration file: $disable_tests"

## Root Cause Analysis

The issue was caused by incorrect shell variable expansion syntax in the RKHunter
configuration generation code in `app/core/rkhunter_wrapper.py` lines 765-766:

```python
# PROBLEMATIC CODE (before fix):
'DISABLE_TESTS="suspscan hidden_procs deleted_files"',
'DISABLE_TESTS="$DISABLE_TESTS packet_cap_apps apps"',  # ❌ Invalid shell variable syntax
```

The second line attempted to use shell variable expansion (`$DISABLE_TESTS`) which is:

1. Invalid RKHunter configuration syntax
2. Causes RKHunter to interpret `$disable_tests` as a literal test name
3. Results in configuration parsing errors

## Solution Implemented

### Fix Applied

Replaced the two-line problematic configuration with a single, properly formatted line:

```python
# FIXED CODE (after fix):
'DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"',
```

### Technical Details

- **File Modified**: `app/core/rkhunter_wrapper.py`
- **Lines Changed**: 765-766 → 765
- **Method**: Combined all disabled tests into a single configuration directive
- **Syntax**: Standard RKHunter configuration format (no shell variables)

## Validation Results

### Syntax Validation

✅ **No shell variable syntax found** - Verified no remaining `$` variable references in configuration
✅ **Single DISABLE_TESTS line** - Confirmed only one DISABLE_TESTS directive exists
✅ **Proper formatting** - All disabled tests listed in single quoted string

### Functional Testing

✅ **App startup successful** - Application launches without configuration errors
✅ **Configuration generation** - RKHunter config file created successfully
✅ **No dependency conflicts** - Fix doesn't affect other components

## Disabled Tests Explanation

The following tests are disabled to prevent false positives on modern Linux systems:

- `suspscan` - Suspicious scan (often flags legitimate system files)
- `hidden_procs` - Hidden process detection (modern systemd can cause false positives)
- `deleted_files` - Deleted file detection (normal for package managers)
- `packet_cap_apps` - Packet capture application detection (false positives with network tools)
- `apps` - Application verification (can flag legitimately updated system applications)

## Impact Assessment

- **Immediate**: RKHunter scans will no longer fail with configuration errors
- **Security**: No security impact - only formatting fix for existing disabled tests
- **Performance**: Slight improvement due to single configuration line vs. invalid parsing
- **Maintenance**: Simplified configuration is easier to maintain and extend

## Verification Steps

1. ✅ Configuration syntax validated - no shell variables
2. ✅ Application startup tested - no errors
3. ✅ RKHunter wrapper functionality confirmed
4. ✅ No regression in other security components

## Resolution Status

🟢 **RESOLVED** - RKHunter configuration syntax error fixed and validated

The user can now run RKHunter scans without encountering the "$disable_tests" configuration error.
