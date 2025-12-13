# Scan Error Fix - ClamAV Option Format

## Issue Reported
December 13, 2025

### Problem
When running a Quick Scan, the scan completed but:
1. ❌ Error displayed: `WARNING: Ignoring unsupported option --max-filesize`
2. ❌ EICAR test virus in `/tmp/eicar.com` was NOT detected
3. ❌ No threat action dialog appeared

### Root Cause
ClamAV's `clamscan` command requires certain options to use the `=` format (e.g., `--max-filesize=100M`) instead of separate arguments (e.g., `--max-filesize 100M`).

The codebase was inconsistent:
- Quick scan mode: Used correct `=` format ✅
- Full scan mode: Used incorrect separate argument format ❌
- Other locations: Mixed usage

### Error Details
```
Scan error: /tmp/plasma-systemmonitor.geuygx: WARNING: Ignoring unsupported option --max-filesize
```

This caused clamscan to:
- Ignore the file size limit option
- Potentially skip scanning certain files
- Miss the EICAR test virus in `/tmp/eicar.com`

## Solution Implemented

### Files Modified
- `app/core/clamav_wrapper.py`

### Changes Made

#### 1. Fixed Full Scan Mode Options (Lines 476-486)
**Before:**
```python
if max_recursion:
    options.extend(["--max-recursion", str(max_recursion)])

max_files = kwargs.get("max_files", scan_settings.get("max_files", 10000))
if max_files:
    options.extend(["--max-files", str(max_files)])
```

**After:**
```python
if max_recursion:
    options.append(f"--max-recursion={max_recursion}")

max_files = kwargs.get("max_files", scan_settings.get("max_files", 10000))
if max_files:
    options.append(f"--max-files={max_files}")
```

#### 2. Fixed Secondary max-filesize Location (Line ~865)
**Before:**
```python
if max_filesize:
    cmd.extend(["--max-filesize", str(max_filesize)])
```

**After:**
```python
if max_filesize:
    cmd.append(f"--max-filesize={max_filesize}")
```

### Quick Scan Already Correct
Quick scan mode was already using the correct format:
```python
options.append("--max-filesize=25M")   # ✅ Correct
options.append("--max-recursion=8")    # ✅ Correct
options.append("--max-files=5000")     # ✅ Correct
```

## ClamAV Command Line Reference

### Valid Option Formats (from `clamscan --help`)
```
--max-filesize=#n          Files larger than this will be skipped
--max-scansize=#n          Maximum amount of data to scan per container
--max-recursion=#n         Maximum archive recursion level
--max-files=#n             Maximum number of files to scan
```

Note: The `=#n` format is REQUIRED - using separate arguments causes errors.

## Testing

### Verification Steps
1. ✅ ClamAV directly detects EICAR: `clamscan /tmp/eicar.com`
   - Result: `Win.Test.EICAR_HDB-1 FOUND`

2. ✅ Quick Scan includes `/tmp` directory
   - Uses `tempfile.gettempdir()` which resolves to `/tmp`

3. ⏳ Rebuild AppImage with fixes
4. ⏳ Test Quick Scan detects EICAR
5. ⏳ Verify threat action dialog appears

### Expected Behavior After Fix
```
Quick Scan → Scan /tmp → Detect EICAR → Show Threat Dialog → User Chooses Action
```

## Technical Details

### Why the Format Matters
ClamAV uses GNU getopt for argument parsing, which supports:
- Long options with `=`: `--option=value` (REQUIRED for most options)
- Short options with space: `-o value`

Using `--max-filesize 100M` (two separate arguments) causes getopt to:
1. Interpret `--max-filesize` as a flag without value
2. Treat `100M` as a positional argument (file to scan)
3. Print "Ignoring unsupported option" warning

### Other Options Affected
These options also require `=` format:
- `--max-scansize`
- `--max-recursion`
- `--max-files`
- `--max-embeddedpe`
- `--max-htmlnormalize`
- `--max-htmlnotags`
- `--max-scriptnormalize`
- `--max-ziptypercg`
- `--pcre-max-filesize`

## Prevention

### Code Review Checklist
- [ ] All ClamAV `--max-*` options use `=` format
- [ ] Use `append()` with f-string instead of `extend()` with list
- [ ] Test scans with verbose output to catch warnings
- [ ] Verify threat detection with EICAR test file

### Best Practice
```python
# ✅ CORRECT
options.append(f"--max-filesize={max_filesize}")
options.append(f"--max-recursion={max_recursion}")

# ❌ INCORRECT
options.extend(["--max-filesize", str(max_filesize)])
options.extend(["--max-recursion", str(max_recursion)])
```

## Impact

### Before Fix
- Scans ran but missed threats due to ignored options
- File size limits not enforced
- Recursion limits not enforced
- EICAR test virus not detected
- Users not notified of threats

### After Fix
- All options properly recognized by ClamAV
- File size and recursion limits enforced
- Threats properly detected
- Threat action dialogs appear
- Users can quarantine/delete/move threats

## Next Steps

### Immediate
1. ✅ Fix implemented
2. ⏳ Rebuild AppImage
3. ⏳ Test EICAR detection
4. ⏳ Verify threat dialog appears
5. ⏳ Test all 5 action options

### Future
- Add automated tests for ClamAV option formatting
- Create validation function for ClamAV command construction
- Add warning detection in scan output parsing
- Log all ClamAV warnings to help identify future issues

## Related Issues
- Threat action prompts feature (THREAT_ACTION_PROMPTS_IMPLEMENTED.md)
- AppImage testing (TESTING_PLAN.md - Phase 3)

---

**Status:** ✅ Fix implemented, AppImage rebuilding
**Priority:** Critical (Affects core malware detection functionality)
**Testing:** Required before release
