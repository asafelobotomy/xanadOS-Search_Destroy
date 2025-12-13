# AppImage Testing Plan

## 📋 Overview

This document outlines a comprehensive testing plan for the xanadOS Search & Destroy AppImage. The plan is divided into phases, with each phase building on the previous one to ensure systematic validation.

## 🎯 Testing Objectives

1. **Verify AppImage functionality** - Ensure the AppImage runs correctly on target systems
2. **Validate core features** - Test all security scanning and malware detection features
3. **Confirm PolicyKit integration** - Verify privilege escalation works correctly
4. **Test portability** - Ensure it works across different Linux distributions
5. **Assess performance** - Measure startup time, memory usage, and responsiveness
6. **Validate user experience** - Ensure GUI is usable and intuitive

---

## Phase 1: Basic Functionality Tests 🔍

**Goal:** Verify the AppImage launches and basic operations work

### Test 1.1: AppImage Execution
- [ ] **Test**: Run `./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage`
- [ ] **Expected**: Application launches without errors
- [ ] **Command**: `./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --skip-policy-check`
- [ ] **Duration**: 30 seconds
- [ ] **Result**: ___________

### Test 1.2: GUI Launch & Splash Screen
- [ ] **Test**: Observe splash screen and startup sequence
- [ ] **Expected**: Splash screen appears, progress indicators work, main window opens
- [ ] **Check**: All 5 startup phases complete (UI init, cache, system check, dashboard, finalization)
- [ ] **Duration**: 10-15 seconds
- [ ] **Result**: ___________

### Test 1.3: Main Window Display
- [ ] **Test**: Verify main window renders correctly
- [ ] **Expected**:
  - Window title: "S&D - Search & Destroy"
  - All toolbar buttons visible
  - Menu bar accessible
  - Status bar shows information
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 1.4: Tab Navigation
- [ ] **Test**: Click through all tabs/panels in the application
- [ ] **Expected**: All tabs load without errors:
  - Dashboard
  - Scan tab
  - Quarantine
  - Reports
  - Settings
  - Any other tabs
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 1.5: Window Operations
- [ ] **Test**: Resize, minimize, maximize, restore window
- [ ] **Expected**: Window responds correctly to all operations
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 1.6: Application Exit
- [ ] **Test**: Close application via X button and File → Exit
- [ ] **Expected**: Application closes cleanly without errors or hangs
- [ ] **Duration**: 30 seconds
- [ ] **Result**: ___________

**Phase 1 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 2: PolicyKit Integration Tests 🔐

**Goal:** Verify privilege escalation works correctly

### Test 2.1: First Run Policy Prompt
- [ ] **Test**: Run AppImage for the first time (without --skip-policy-check)
- [ ] **Expected**: PolicyKit installation prompt appears
- [ ] **Command**: `./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage`
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 2.2: Policy Installation - Accept
- [ ] **Test**: Accept the PolicyKit policy installation prompt
- [ ] **Expected**: Policies installed to `/usr/share/polkit-1/actions/`
- [ ] **Verify**: Check policies exist:
  ```bash
  ls -la /usr/share/polkit-1/actions/io.github.asafelobotomy.searchanddestroy*.policy
  ```
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 2.3: Policy Installation - Decline
- [ ] **Test**: Run fresh AppImage, decline policy installation
- [ ] **Expected**: Application continues but privileged operations may require manual auth
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 2.4: Manual Policy Installation
- [ ] **Test**: Extract AppImage and manually copy policies
- [ ] **Command**:
  ```bash
  ./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract
  sudo cp squashfs-root/usr/share/polkit-1/actions/*.policy /usr/share/polkit-1/actions/
  ```
- [ ] **Expected**: Policies installed successfully
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 2.5: ClamAV Installation Privilege
- [ ] **Test**: Trigger ClamAV installation (if not installed)
- [ ] **Expected**: PolicyKit authentication dialog appears, installation succeeds
- [ ] **Duration**: 5 minutes
- [ ] **Result**: ___________

### Test 2.6: RKhunter Scan Privilege
- [ ] **Test**: Run RKhunter scan
- [ ] **Expected**: PolicyKit authentication dialog appears (or automatic if policy allows)
- [ ] **Duration**: 3 minutes
- [ ] **Result**: ___________

### Test 2.7: Quarantine Operation Privilege
- [ ] **Test**: Move a file to quarantine
- [ ] **Expected**: PolicyKit authentication dialog appears, file quarantined successfully
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

**Phase 2 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 3: Core Security Features Tests 🛡️

**Goal:** Validate all security scanning and detection features

### Test 3.1: ClamAV Quick Scan
- [ ] **Test**: Run a quick scan on `/tmp` directory
- [ ] **Expected**: Scan completes, results displayed
- [ ] **Duration**: 2-5 minutes
- [ ] **Result**: ___________

### Test 3.2: ClamAV Full Scan
- [ ] **Test**: Run a full system scan (or large directory)
- [ ] **Expected**: Scan progresses with real-time updates, completes successfully
- [ ] **Duration**: 10-30 minutes (can cancel early if working)
- [ ] **Result**: ___________

### Test 3.3: ClamAV Signature Update
- [ ] **Test**: Update ClamAV virus signatures
- [ ] **Expected**: Signatures download and update successfully
- [ ] **Duration**: 2-5 minutes
- [ ] **Result**: ___________

### Test 3.4: EICAR Test File Detection
- [ ] **Test**: Create EICAR test virus and scan
- [ ] **Command**:
  ```bash
  echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.com
  ```
- [ ] **Expected**: ClamAV detects and reports the test virus
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 3.5: RKhunter System Check
- [ ] **Test**: Run RKhunter rootkit scan
- [ ] **Expected**: Scan completes, reports any findings
- [ ] **Duration**: 5-10 minutes
- [ ] **Result**: ___________

### Test 3.6: Quarantine File
- [ ] **Test**: Quarantine the EICAR test file
- [ ] **Expected**: File moved to quarantine directory, accessible in Quarantine tab
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 3.7: Restore from Quarantine
- [ ] **Test**: Restore a quarantined file
- [ ] **Expected**: File restored to original location or chosen directory
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 3.8: Delete from Quarantine
- [ ] **Test**: Permanently delete a quarantined file
- [ ] **Expected**: File removed completely
- [ ] **Duration**: 30 seconds
- [ ] **Result**: ___________

### Test 3.9: Custom Scan Path
- [ ] **Test**: Select a custom directory to scan
- [ ] **Expected**: File picker opens, selected directory scans correctly
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 3.10: Scheduled Scan Creation
- [ ] **Test**: Create a scheduled scan task
- [ ] **Expected**: Schedule saved, appears in scheduled tasks list
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

**Phase 3 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 4: Configuration & Data Persistence Tests 💾

**Goal:** Verify settings save/load and data persists correctly

### Test 4.1: Configuration File Creation
- [ ] **Test**: Check if config files are created in correct location
- [ ] **Expected**: Config files exist in `~/.config/xanadOS-Search-Destroy/` or similar
- [ ] **Command**: `find ~/.config -name "*search*destroy*" -o -name "*xanad*"`
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 4.2: Settings Modification
- [ ] **Test**: Change various settings in Settings tab
- [ ] **Expected**: Settings save and persist after relaunch
- [ ] **Settings to test**:
  - Scan depth
  - Exclusion paths
  - Update frequency
  - Theme/appearance
- [ ] **Duration**: 3 minutes
- [ ] **Result**: ___________

### Test 4.3: Database Files
- [ ] **Test**: Verify database files are accessible
- [ ] **Expected**: SQLite database created and accessible
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 4.4: Log Files
- [ ] **Test**: Check if log files are being written
- [ ] **Expected**: Log files created and contain scan/activity logs
- [ ] **Location**: Check `~/.local/share/xanadOS-Search-Destroy/logs/` or similar
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 4.5: Scan History
- [ ] **Test**: View scan history in Reports tab
- [ ] **Expected**: Previous scans listed with details
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 4.6: Export Reports
- [ ] **Test**: Export a scan report to file
- [ ] **Expected**: Report saved in chosen format (PDF, CSV, JSON, etc.)
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

**Phase 4 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 5: Performance & Stability Tests ⚡

**Goal:** Measure performance and identify any stability issues

### Test 5.1: Startup Time
- [ ] **Test**: Measure time from launch to main window
- [ ] **Expected**: < 5 seconds on modern hardware
- [ ] **Command**: `time ./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --skip-policy-check`
- [ ] **Duration**: 5 attempts
- [ ] **Results**:
  - Attempt 1: _____s
  - Attempt 2: _____s
  - Attempt 3: _____s
  - Attempt 4: _____s
  - Attempt 5: _____s
  - **Average**: _____s

### Test 5.2: Memory Usage (Idle)
- [ ] **Test**: Monitor memory usage while application is idle
- [ ] **Expected**: < 500 MB RAM
- [ ] **Command**: `ps aux | grep -i search.*destroy | grep -v grep`
- [ ] **Duration**: 5 minutes
- [ ] **Result**: _____ MB

### Test 5.3: Memory Usage (Scanning)
- [ ] **Test**: Monitor memory during active scan
- [ ] **Expected**: < 1 GB RAM
- [ ] **Duration**: During a full scan
- [ ] **Result**: _____ MB

### Test 5.4: CPU Usage (Idle)
- [ ] **Test**: Monitor CPU usage while idle
- [ ] **Expected**: < 5% CPU
- [ ] **Command**: `top -b -n 1 | grep -i search`
- [ ] **Duration**: 2 minutes
- [ ] **Result**: _____% CPU

### Test 5.5: CPU Usage (Scanning)
- [ ] **Test**: Monitor CPU during scan
- [ ] **Expected**: Variable, but responsive UI
- [ ] **Duration**: During scan
- [ ] **Result**: _____% CPU

### Test 5.6: Multiple Launches
- [ ] **Test**: Try to launch AppImage multiple times
- [ ] **Expected**: Single instance guard activates, existing window comes to front
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 5.7: Long Session Stability
- [ ] **Test**: Keep application running for extended period
- [ ] **Expected**: No memory leaks, crashes, or freezes
- [ ] **Duration**: 1-2 hours
- [ ] **Result**: ___________

### Test 5.8: UI Responsiveness
- [ ] **Test**: Interact with UI during intensive scan
- [ ] **Expected**: UI remains responsive, buttons/menus work
- [ ] **Duration**: During scan
- [ ] **Result**: ___________

**Phase 5 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 6: Cross-Distribution Testing 🐧

**Goal:** Verify portability across different Linux distributions

### Test 6.1: Arch Linux (Development System)
- [ ] **Distribution**: Arch Linux (current system)
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ✅ Passed (development system)
- [ ] **Notes**: ___________

### Test 6.2: Ubuntu 24.04 LTS
- [ ] **Distribution**: Ubuntu 24.04 LTS
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ⏳ Not Tested
- [ ] **Notes**: ___________

### Test 6.3: Ubuntu 22.04 LTS
- [ ] **Distribution**: Ubuntu 22.04 LTS
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ⏳ Not Tested
- [ ] **Notes**: ___________

### Test 6.4: Fedora 40+
- [ ] **Distribution**: Fedora ___
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ⏳ Not Tested
- [ ] **Notes**: ___________

### Test 6.5: Debian 12 (Bookworm)
- [ ] **Distribution**: Debian 12
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ⏳ Not Tested
- [ ] **Notes**: ___________

### Test 6.6: Linux Mint
- [ ] **Distribution**: Linux Mint ___
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ⏳ Not Tested
- [ ] **Notes**: ___________

### Test 6.7: openSUSE Tumbleweed/Leap
- [ ] **Distribution**: openSUSE ___
- [ ] **Kernel**: _____________
- [ ] **Desktop Environment**: _____________
- [ ] **Test Date**: _____________
- [ ] **Status**: ⏳ Not Tested
- [ ] **Notes**: ___________

**Phase 6 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 7: Edge Cases & Error Handling Tests 🔍

**Goal:** Test unusual scenarios and error recovery

### Test 7.1: No Internet Connection
- [ ] **Test**: Launch and use app without internet
- [ ] **Expected**: App works, shows appropriate messages for features requiring internet
- [ ] **Duration**: 5 minutes
- [ ] **Result**: ___________

### Test 7.2: Insufficient Permissions
- [ ] **Test**: Try to scan protected system directories without PolicyKit
- [ ] **Expected**: Appropriate error message, graceful handling
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 7.3: Disk Space Full
- [ ] **Test**: Simulate low disk space during scan
- [ ] **Expected**: Error message, scan stops gracefully
- [ ] **Duration**: 3 minutes
- [ ] **Result**: ___________

### Test 7.4: Corrupted Configuration
- [ ] **Test**: Manually corrupt config file and launch
- [ ] **Expected**: App detects corruption, recreates default config
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 7.5: Missing Dependencies (System)
- [ ] **Test**: Test on system without ClamAV/RKhunter
- [ ] **Expected**: App offers to install or shows instructions
- [ ] **Duration**: 5 minutes
- [ ] **Result**: ___________

### Test 7.6: Cancel Scan Mid-Operation
- [ ] **Test**: Start a scan and cancel halfway through
- [ ] **Expected**: Scan stops cleanly, partial results shown
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

### Test 7.7: Large File Scan
- [ ] **Test**: Scan a very large file (> 1 GB)
- [ ] **Expected**: Progress updates, completes without crash
- [ ] **Duration**: 5 minutes
- [ ] **Result**: ___________

### Test 7.8: Special Characters in Paths
- [ ] **Test**: Scan directory with spaces, unicode, special chars in name
- [ ] **Expected**: Handles paths correctly
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

**Phase 7 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Phase 8: Desktop Integration Tests 🖥️

**Goal:** Verify system integration features

### Test 8.1: Desktop File Installation
- [ ] **Test**: Extract AppImage and check desktop file
- [ ] **Command**:
  ```bash
  ./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract
  cat squashfs-root/xanadOS-Search-Destroy.desktop
  ```
- [ ] **Expected**: Valid desktop file with correct paths
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 8.2: Icon Display
- [ ] **Test**: Check if icon files are present
- [ ] **Expected**: PNG icons at various sizes (128px, 256px, etc.)
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 8.3: AppStream Metadata
- [ ] **Test**: Verify appdata.xml is present and valid
- [ ] **Command**: `cat squashfs-root/*.appdata.xml`
- [ ] **Expected**: Valid AppStream metadata
- [ ] **Duration**: 1 minute
- [ ] **Result**: ___________

### Test 8.4: File Associations (if applicable)
- [ ] **Test**: Check if any file associations are registered
- [ ] **Expected**: Scan results files open in app
- [ ] **Duration**: 2 minutes
- [ ] **Result**: ___________

**Phase 8 Status**: ⏳ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

---

## Testing Environment Setup 🛠️

### Required Tools
```bash
# Install testing dependencies (if needed)
sudo pacman -S fuse2 htop time stress-ng  # Arch Linux

# For cross-distribution testing, consider:
# - Virtual machines (QEMU/KVM, VirtualBox)
# - Docker/Podman containers
# - Live USB systems
```

### Test System Information Template
```
OS: ____________________
Kernel: ________________
Desktop Environment: ____
Display Server: _________
FUSE Version: __________
PolicyKit Version: ______
Python Version: ________
Qt Version: ____________
Memory (Total): ________
CPU: ___________________
GPU: ___________________
```

---

## Automated Testing Script 🤖

Create a quick automated test script for basic checks:

```bash
#!/bin/bash
# save as: test-appimage-basic.sh

set -e
APPIMAGE="./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage"

echo "=== Basic AppImage Tests ==="
echo ""

# Test 1: File exists
echo "[1/6] Checking if AppImage exists..."
test -f "$APPIMAGE" && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Executable
echo "[2/6] Checking if executable..."
test -x "$APPIMAGE" && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Version flag
echo "[3/6] Testing --version flag..."
"$APPIMAGE" --version 2>&1 | grep -q "3.0.0" && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: Help flag
echo "[4/6] Testing --help flag..."
"$APPIMAGE" --help 2>&1 | grep -q "Advanced malware" && echo "✅ PASS" || echo "❌ FAIL"

# Test 5: Extraction
echo "[5/6] Testing extraction..."
rm -rf /tmp/test-extract
mkdir -p /tmp/test-extract
cd /tmp/test-extract
"$OLDPWD/$APPIMAGE" --appimage-extract >/dev/null 2>&1
test -f squashfs-root/AppRun && echo "✅ PASS" || echo "❌ FAIL"
cd "$OLDPWD"
rm -rf /tmp/test-extract

# Test 6: Size check
echo "[6/6] Checking size..."
SIZE=$(stat -c %s "$APPIMAGE")
if [ "$SIZE" -gt 300000000 ] && [ "$SIZE" -lt 400000000 ]; then
    echo "✅ PASS ($(numfmt --to=iec-i --suffix=B "$SIZE"))"
else
    echo "❌ FAIL (unexpected size: $(numfmt --to=iec-i --suffix=B "$SIZE"))"
fi

echo ""
echo "=== Basic tests complete ==="
```

---

## Bug Tracking Template 🐛

When issues are found, document them using this template:

```markdown
### Bug #X: [Brief Description]

**Severity**: Critical / High / Medium / Low
**Phase**: [Which test phase]
**Test**: [Specific test number]

**Description**:
[Detailed description of the issue]

**Steps to Reproduce**:
1.
2.
3.

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**System Information**:
- OS:
- Kernel:
- Desktop:
- AppImage Version:

**Logs/Screenshots**:
[Attach relevant logs or screenshots]

**Workaround** (if any):
[Temporary solution]

**Status**: Open / In Progress / Fixed / Won't Fix
```

---

## Success Criteria ✅

The AppImage is considered **production-ready** when:

- [ ] **Phase 1**: All basic functionality tests pass (6/6)
- [ ] **Phase 2**: PolicyKit integration works (5/7 minimum)
- [ ] **Phase 3**: Core security features functional (8/10 minimum)
- [ ] **Phase 4**: Data persistence works correctly (5/6 minimum)
- [ ] **Phase 5**: Performance meets targets (all tests)
- [ ] **Phase 6**: Tested on at least 3 distributions (3/7 minimum)
- [ ] **Phase 7**: Error handling is acceptable (6/8 minimum)
- [ ] **Phase 8**: Desktop integration complete (3/4 minimum)
- [ ] **No critical bugs**
- [ ] **No more than 2 high-severity bugs**

---

## Timeline Estimate ⏱️

- **Phase 1**: 15-30 minutes
- **Phase 2**: 30-60 minutes
- **Phase 3**: 1-2 hours
- **Phase 4**: 20-40 minutes
- **Phase 5**: 2-3 hours
- **Phase 6**: 3-6 hours (depending on VM setup)
- **Phase 7**: 30-60 minutes
- **Phase 8**: 15-30 minutes

**Total**: 8-14 hours for complete testing

**Recommended**: Start with Phases 1-5 on current system (4-6 hours), then expand to cross-distribution testing if time permits.

---

## Next Steps 🚀

1. **Start with Phase 1** - Basic functionality (quickest validation)
2. **Move to Phase 3** - Core features (most important for security app)
3. **Test Phase 2** - PolicyKit (critical for privileged operations)
4. **Continue with remaining phases** as time permits
5. **Document all findings** in TESTING.md
6. **Fix critical bugs** before considering Phase 6
7. **Cross-platform testing** last (most time-consuming)

---

**Testing Started**: __________
**Testing Completed**: __________
**Tester**: __________
**Overall Status**: ⏳ Not Started
