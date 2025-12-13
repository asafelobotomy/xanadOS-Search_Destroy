# Bug Report Template

Use this template to document any bugs found during AppImage testing.

---

## Bug #1: [Title]

**Reported Date**: YYYY-MM-DD
**Reporter**: [Your Name]
**Severity**: ☐ Critical  ☐ High  ☐ Medium  ☐ Low
**Status**: ☐ Open  ☐ In Progress  ☐ Fixed  ☐ Won't Fix  ☐ Cannot Reproduce

**Test Phase**: [e.g., Phase 3: Core Security Features]
**Test Number**: [e.g., Test 3.4]

### Description
[Clear and concise description of the bug]

### Steps to Reproduce
1.
2.
3.

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### System Information
- **OS**:
- **Kernel**:
- **Desktop Environment**:
- **Display Server**:
- **AppImage Version**: 3.0.0
- **AppImage Size**: 320 MB
- **Python Version** (bundled): 3.13

### Error Messages/Logs
```
[Paste any error messages or relevant log excerpts]
```

### Screenshots
[Attach screenshots if applicable]

### Workaround
[If you found a temporary solution, describe it here]

### Additional Context
[Any other relevant information]

---

## Bug #2: [Title]

**Reported Date**: YYYY-MM-DD
**Reporter**: [Your Name]
**Severity**: ☐ Critical  ☐ High  ☐ Medium  ☐ Low
**Status**: ☐ Open  ☐ In Progress  ☐ Fixed  ☐ Won't Fix  ☐ Cannot Reproduce

**Test Phase**: [e.g., Phase 2: PolicyKit Integration]
**Test Number**: [e.g., Test 2.5]

### Description
[Clear and concise description of the bug]

### Steps to Reproduce
1.
2.
3.

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### System Information
- **OS**:
- **Kernel**:
- **Desktop Environment**:
- **Display Server**:
- **AppImage Version**: 3.0.0
- **AppImage Size**: 320 MB
- **Python Version** (bundled): 3.13

### Error Messages/Logs
```
[Paste any error messages or relevant log excerpts]
```

### Screenshots
[Attach screenshots if applicable]

### Workaround
[If you found a temporary solution, describe it here]

### Additional Context
[Any other relevant information]

---

## Severity Definitions

### Critical
- Application crashes on launch
- Data loss or corruption
- Security vulnerabilities
- Complete feature failure (e.g., cannot scan at all)
- Affects all users on all systems

### High
- Major feature not working
- Frequent crashes in specific scenarios
- PolicyKit integration completely broken
- Performance severely degraded
- Affects most users

### Medium
- Minor feature not working
- Occasional crashes
- UI rendering issues
- Performance issues under specific conditions
- Affects some users

### Low
- Cosmetic issues
- Typos or grammatical errors
- Minor UI inconsistencies
- Feature requests
- Edge case issues
- Affects few users

---

## Status Definitions

- **Open**: Bug reported, not yet addressed
- **In Progress**: Being actively worked on
- **Fixed**: Fix implemented and tested
- **Won't Fix**: Decided not to fix (document reason)
- **Cannot Reproduce**: Unable to reproduce the issue (needs more info)

---

## Bug Tracking Summary

| Bug # | Title | Severity | Status | Assigned To | Fixed In |
|-------|-------|----------|--------|-------------|----------|
| 1     |       |          |        |             |          |
| 2     |       |          |        |             |          |
| 3     |       |          |        |             |          |
| 4     |       |          |        |             |          |
| 5     |       |          |        |             |          |

---

## Notes

- Update this file as you discover and fix bugs
- Link to GitHub issues if using issue tracker
- Include steps to verify the fix
- Document any regression testing needed
