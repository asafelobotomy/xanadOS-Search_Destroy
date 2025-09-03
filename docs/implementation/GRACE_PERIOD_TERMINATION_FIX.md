## RKHunter Grace Period Termination Fix

### Problem Solved

The issue was that when stopping an RKHunter scan within the 30-second grace period, the system was
still prompting for sudo/pkexec authentication even though the scan was successfully stopping.

### Root Cause

1. RKHunter scans run with elevated privileges (pkexec)

2.

When stopping within the grace period, the direct kill commands fail due to permission denied
(expected)

3. The old logic would then fall back to pkexec, causing the unnecessary authentication prompt
4. However, the scan was actually stopping naturally due to the cancellation flag

### Solution Implemented

1.

**Enhanced Grace Period Logic**: Within the 30-second grace period, if direct kill fails (indicating
an elevated process), the system now:

- Attempts direct kill first (as expected)
- If it fails due to permissions, logs it as info rather than warning
- Returns `False`from`_terminate_with_privilege_escalation` but doesn't attempt pkexec
- The calling method (`terminate_current_scan`) recognizes this as acceptable within grace period
- Reports overall success since the process will terminate naturally

2.

**Improved Error Messages**: Changed warning messages to info messages for expected permission
denied scenarios within grace period

3.

**Intelligent Fallback**: Only attempts pkexec authentication outside the grace period or when
specifically needed

### Key Code Changes

## In `terminate_current_scan()` method

- Added grace period check before calling privileged termination
- Within grace period: accepts failure gracefully and returns True
- Outside grace period: continues with normal pkexec fallback

## In `_terminate_with_privilege_escalation()` method

- Within grace period: attempts direct kill but returns False (not True) if it fails
- Doesn't fall through to pkexec code within grace period for elevated processes
- Improved logging to be less alarming for expected scenarios

### Result

- ✅ No sudo/pkexec authentication prompts within 30-second grace period
- ✅ Scans stop successfully and naturally
- ✅ Maintains security by still requiring authentication outside grace period
- ✅ Improved user experience with no unnecessary password prompts

### Testing

Comprehensive tests confirm:

- Direct kill attempts are made (as they should be)
- No pkexec calls within grace period for elevated processes
- Overall termination reported as successful
- Process stops naturally without user intervention
