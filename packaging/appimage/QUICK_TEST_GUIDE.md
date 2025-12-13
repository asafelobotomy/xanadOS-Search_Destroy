# Quick Testing Guide

## 🚀 Getting Started

Welcome to the xanadOS Search & Destroy AppImage testing! This guide will help you quickly get started with testing.

## Step 1: Run Automated Tests (5 minutes)

Start with the automated test script to verify basic functionality:

```bash
cd /home/solon/Documents/xanadOS-Search_Destroy
./packaging/appimage/test-appimage-basic.sh
```

**Expected Result**: All 15 automated tests should pass (100%)

---

## Step 2: Manual GUI Testing (15-30 minutes)

### Quick Launch Test
```bash
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --skip-policy-check
```

### What to Check:
1. ✅ **Splash screen** appears with progress
2. ✅ **Main window** opens within 5 seconds
3. ✅ **All tabs** are accessible (Dashboard, Scan, Quarantine, Reports, Settings)
4. ✅ **Window operations** work (resize, minimize, maximize, close)

---

## Step 3: Test Core Features (30-60 minutes)

### A. ClamAV Quick Scan
```bash
# Launch the app
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage

# In the app:
# 1. Go to Scan tab
# 2. Select "Quick Scan"
# 3. Choose /tmp directory
# 4. Start scan
# 5. Verify results display
```

### B. EICAR Test Virus Detection
```bash
# Create test virus
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.com

# Scan /tmp in the app
# Expected: ClamAV detects "Eicar-Test-Signature"
```

### C. Quarantine Test
```bash
# In the app:
# 1. After EICAR detection, click "Quarantine"
# 2. Go to Quarantine tab
# 3. Verify file appears
# 4. Test "Restore" and "Delete" buttons
```

---

## Step 4: PolicyKit Testing (10-20 minutes)

### First Run (with PolicyKit)
```bash
# Run WITHOUT --skip-policy-check
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage

# Expected:
# - PolicyKit installation prompt appears
# - Option to install policies
# - Can proceed with or without installation
```

### Verify Policies
```bash
# After accepting policy installation:
ls -la /usr/share/polkit-1/actions/io.github.asafelobotomy.searchanddestroy*.policy

# Should show 3 policy files
```

---

## Step 5: Settings & Persistence (10 minutes)

### Test Configuration
```bash
# In the app:
# 1. Go to Settings tab
# 2. Change some settings (scan depth, exclusions, etc.)
# 3. Close the app
# 4. Relaunch the app
# 5. Verify settings persisted

# Check config files:
find ~/.config -name "*search*destroy*" -o -name "*xanad*"
find ~/.local/share -name "*search*destroy*" -o -name "*xanad*"
```

---

## Checklist Summary

Use this quick checklist to track your testing progress:

### Basic Tests (Automated)
- [ ] Automated test script passes 100%

### GUI Tests
- [ ] Application launches
- [ ] Splash screen displays
- [ ] Main window opens
- [ ] All tabs accessible
- [ ] Window operations work
- [ ] Application closes cleanly

### Core Features
- [ ] ClamAV scan works
- [ ] EICAR test virus detected
- [ ] Quarantine file works
- [ ] Restore from quarantine works
- [ ] Delete from quarantine works

### PolicyKit
- [ ] Installation prompt appears
- [ ] Policies install correctly
- [ ] Can skip installation and still use app

### Persistence
- [ ] Settings save
- [ ] Settings load after restart
- [ ] Config files created

### Performance
- [ ] Startup time < 5 seconds
- [ ] Memory usage reasonable
- [ ] UI responsive during scan

---

## Common Issues & Solutions

### Issue: "Permission denied"
**Solution**: Make AppImage executable
```bash
chmod +x releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage
```

### Issue: "FUSE error"
**Solution**: Install FUSE2 or use extraction mode
```bash
sudo pacman -S fuse2  # Arch Linux
# OR
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract-and-run
```

### Issue: App won't launch
**Solution**: Check terminal for errors
```bash
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --skip-policy-check 2>&1 | tee error.log
```

### Issue: ClamAV not installed
**Solution**: App should offer to install it
- Follow in-app prompts
- Or manually: `sudo pacman -S clamav`

---

## Reporting Issues

If you find bugs, document them in `packaging/appimage/BUG_REPORTS.md` using the template provided.

Include:
- Steps to reproduce
- Expected vs actual behavior
- System information
- Error messages/logs
- Screenshots

---

## Quick Commands Reference

```bash
# Launch app
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage

# Skip PolicyKit check
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --skip-policy-check

# Show version
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --version

# Show help
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --help

# Extract AppImage
./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract

# Run automated tests
./packaging/appimage/test-appimage-basic.sh

# Check test results
cat test-results-*.txt
```

---

## Full Testing Plan

For comprehensive testing, see `packaging/appimage/TESTING_PLAN.md` which includes:
- 8 testing phases
- 80+ individual tests
- Cross-distribution testing
- Performance benchmarks
- Edge case testing

---

## Time Estimates

- **Quick validation**: 20-30 minutes (automated + basic GUI)
- **Standard testing**: 2-3 hours (Phases 1-5)
- **Comprehensive testing**: 8-14 hours (all phases)

---

## Need Help?

- **Documentation**: See `packaging/appimage/README.md`
- **Testing Plan**: See `packaging/appimage/TESTING_PLAN.md`
- **Bug Reports**: See `packaging/appimage/BUG_REPORTS.md`
- **Implementation**: See `packaging/appimage/IMPLEMENTATION_SUMMARY.md`

---

**Happy Testing! 🚀**
