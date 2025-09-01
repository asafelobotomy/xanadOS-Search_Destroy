# Repository Cleanup Plan

**Date:** August 26, 2025
**Objective:** Trim, clean, and organize the xanadOS-Search_Destroy repository

## 🎯 **Cleanup Analysis Summary**

### **Root Directory Issues (CRITICAL)**

- ❌ `check_versions.py` - Should be in `scripts/tools/`
- ❌ `test_settings_fix.py` - Should be in `scripts/tools/` or `dev/`
- ❌ `version_manager.py` - Should be in `scripts/tools/`
- ❌ `PYLANCE-FIX.md` - Should be in `docs/development/`
- ❌ `markdown-fixes.log` - Should be in `logs/` or deleted
- ❌ `run.sh` - Should be in `scripts/`

### **Large Directory Issues**

- 🗂️ `node_modules/` (37MB) - Should be in `.gitignore`, needs cleanup
- 🗂️ `dev/` (17MB) - Needs organization review
- 🗂️ `backups/` (6.4MB) - Should be in `archive/backups/`
- 🗂️ `logs/` (1.2MB) - Review if needed, move to `.gitignore`

### **Directory Organization Review Needed**

- `packaging/` (1.9MB) - Review contents and organization
- `archive/` (1.5MB) - Verify proper archival structure
- `examples/` (340KB) - Consolidate and organize

## 📋 **Cleanup Plan by Priority**

### **Phase 1: Root Directory Cleanup (IMMEDIATE)**

1. Move development scripts to proper locations
2. Move documentation to proper locations
3. Remove temporary/log files
4. Clean up node_modules

### **Phase 2: Directory Organization (HIGH PRIORITY)**

1. Reorganize `dev/` directory
2. Move `backups/` to `archive/backups/`
3. Review and clean `packaging/`
4. Consolidate `examples/`

### **Phase 3: Archive and Optimize (MEDIUM PRIORITY)**

1. Review `archive/` structure
2. Optimize `logs/` handling
3. Review `config/` organization
4. Clean up unused files

### **Phase 4: Final Validation (LOW PRIORITY)**

1. Update `.gitignore` patterns
2. Validate file organization compliance
3. Update documentation indexes
4. Run final validation tests

## 🎯 **Expected Outcomes**

- Reduced repository size by ~50MB
- 100% compliance with file organization policy
- Improved navigation and maintainability
- Clear separation of active vs archived content
