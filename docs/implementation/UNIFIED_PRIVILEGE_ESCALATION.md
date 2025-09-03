# Unified Privilege Escalation Implementation

## Overview

All privilege escalation throughout the application now uses the same standardized GUI sudo method
that RKHunter uses, providing a consistent user experience.

## Changes Made

### 1. ClamAV Virus Definition Updates

**File:** `app/core/clamav_wrapper.py`

- **Before:** Used `pkexec` as first choice for privilege escalation
- **After:** Uses `elevated_run` with GUI sudo (same as RKHunter)
- **Impact:** "Update Definitions" button now shows the same GUI sudo dialog as RKHunter scans

### 2. Process Management Utility

**File:** `app/utils/process_management.py`

- **Before:** `execute_with_privilege()`defaulted to`pkexec`
- **After:** Defaults to `elevated_run` with GUI sudo
- **Impact:** Any utility functions using this now have consistent GUI experience

### 3. Privilege Escalation Manager

**File:** `app/core/privilege_escalation.py`

- **Before:** Fallback used direct `sudo` commands
- **After:** Fallback uses `elevated_run` with GUI sudo
- **Impact:** Policy file installation and other privileged operations use consistent GUI

## Privilege Escalation Priority Order

The `elevated_run` function (used by RKHunter and now all other operations) prioritizes methods in
this order:

1. **🥇 Passwordless sudo** (if configured)

- Fastest and most secure option
- No user interaction required
- Uses `sudo -n` for non-interactive operation

2. **🥈 GUI sudo with askpass helper** (e.g., `ksshaskpass`)

- Provides native desktop integration
- Shows GUI password dialog
- Best user experience when password is required

3. **🥉 pkexec**

- Alternative GUI authentication method
- PolicyKit-based authentication
- System-wide privilege management

4. **🏃 Terminal sudo** (final fallback)

- For terminal environments or when GUI methods fail
- Interactive password prompt in terminal

## User Experience Benefits

### Before Changes

- **RKHunter scans:** Used GUI sudo (ksshaskpass) - ✅ Good experience
- **Update Definitions:** Used pkexec - ❌ Different dialog style
- **Other operations:** Mixed approaches - ❌ Inconsistent

### After Changes

- **RKHunter scans:** Uses GUI sudo (ksshaskpass) - ✅ Consistent
- **Update Definitions:** Uses GUI sudo (ksshaskpass) - ✅ Consistent
- **Other operations:** Uses GUI sudo (ksshaskpass) - ✅ Consistent

## Technical Implementation

### Standard Pattern

````Python
from .elevated_runner import elevated_run

## All privilege escalation now uses this pattern

result = elevated_run(
    command_args,
    timeout=300,
    gui=True  # Enables GUI sudo preference
)

```text

### Key Components

- **elevated_run()**: Centralized privilege escalation function
- **GUI preference**: Always uses `gui=True` for desktop applications
- **Askpass helpers**: Automatically detects and uses available GUI helpers
- **Graceful fallbacks**: Falls back through multiple methods if needed

## Verification

All major privilege escalation points now use the unified approach:

- ✅ ClamAV wrapper (`update_virus_definitions`)
- ✅ Process management (`execute_with_privilege`)
- ✅ Privilege escalation manager (`install_policy_file`)
- ✅ RKHunter wrapper (reference implementation)

## Security Considerations

- **No security reduction**: Same security model as before
- **Improved consistency**: Reduces user confusion
- **Centralized validation**: All privilege escalation goes through `elevated_run`
- **Proper error handling**: Consistent error reporting across all operations

## User Impact

Users will now see the same password dialog style for all operations requiring privileges:

- Virus definition updates
- RKHunter scans
- System configuration changes
- Policy file installations

This provides a more professional and consistent user experience throughout the application.
````
