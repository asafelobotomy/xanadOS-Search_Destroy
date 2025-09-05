# Archive index

This index tracks deprecated, legacy, and superseded content per the archive policy.

- Category: deprecated — historical docs/releases referencing org.xanados.* kept for context
- Category: legacy-versions — older release notes kept under docs/releases

For policy and structure, see `archive/README.md`.

## Archive Index 2

## Overview

This document provides a comprehensive index of all archived content in the repository,
organized by category and chronology for easy discovery and reference.

## 📊 Archive Statistics

- **Total Archived Items**: 24
- **Deprecated Items**: 3
- **Legacy Versions**: 0
- **Superseded Items**: 12
- **Performance/Monitoring Data**: 6
- **Temporary Testing Files**: 2
- **Development Files**: 1
- **Last Updated**: 2025-08-28

## 🗂️ Archive Categories

### Deprecated Content

- `tests/test_implementation.py` — Archived 2025-08-25 (umbrella legacy test superseded by focused pytest suites)
- `app/core/elevated_runner_simple.py` — Archived 2025-08-25 (deprecated simple elevated runner; use `app/core/elevated_runner.py`)
- `app/core/elevated_runner_simple.py` — Archived 2025-08-26 (deprecated simple elevated runner; replacement `app/core/elevated_runner.py`)
- `scripts/tools/fix-markdown-formatting.sh` — Archived 2025-08-27 (deprecated wrapper; use `scripts/tools/quality/fix-markdown.sh`)
- `scripts/tools/fix-markdown-targeted.sh` — Archived 2025-08-27 (deprecated wrapper; use `scripts/tools/quality/fix-markdown.sh`)
- `scripts/tools/fix-markdown-advanced.sh` — Archived 2025-08-27 (deprecated wrapper; use `scripts/tools/quality/fix-markdown.sh`)
- `scripts/tools/fix-markdown-final.sh` — Archived 2025-08-27 (deprecated wrapper; use `scripts/tools/quality/fix-markdown.sh`)

### Legacy Versions

No legacy versions currently archived.

### Superseded Content

**Recent Archives (2025-08-28)**:

- `.flake8` - Legacy linting config superseded by `[tool.ruff.lint]` in `pyproject.toml`

**Previous Archives (2025-08-26)**:

- `.flake8` - Legacy linting config superseded by `[tool.ruff.lint]` in `pyproject.toml`
- `.pylintrc` - Legacy pylint config superseded by `[tool.ruff.lint]` in `pyproject.toml`
- `.ruff.toml` - Standalone Ruff config superseded by `[tool.ruff]` in `pyproject.toml`

**Previous Archives (2025-08-24)**:

- `PROFESSIONAL_PLAN_90_PERCENT_QUALITY.md` - Planning document superseded by completion
- `PROFESSIONAL_SUCCESS_REPORT.md` - Intermediate success report superseded by completion
- `STAGE_1_COMPLETION_REPORT.md` - Intermediate stage report superseded by final completion
- `STAGE_4_COMPLETION_REPORT.md` - Stage report superseded by mission accomplished
- `STAGE_4_COMPREHENSIVE_REVIEW.md` - Review superseded by final achievement
- `BUG_REPORT_2025-08-23.md` - Date-specific report superseded by completion
- `COMPREHENSIVE_FIX_REPORT_2025-08-23.md` - Date-specific report superseded by completion
- `version-control-validation-2025-08-23.md` - Date-specific validation superseded by completion
- `config/org.xanados.searchanddestroy.policy`- Superseded by`config/io.GitHub.asafelobotomy.searchanddestroy.policy`
- `config/org.xanados.searchanddestroy.hardened.policy`- Superseded by`config/io.GitHub.asafelobotomy.searchanddestroy.hardened.policy`
- `config/org.xanados.searchanddestroy.rkhunter.policy`- Superseded by`config/io.GitHub.asafelobotomy.searchanddestroy.rkhunter.policy`

### Performance and Monitoring Data

**Recent Archives (2025-08-25)**:

- `performance-monitoring/` - Performance monitoring data from security assessment
- `logs/` - Application logs from development and testing
- `latest_monitoring_dir.txt` - Outdated monitoring directory reference

### Temporary Testing Files

**Recent Archives (2025-08-28)**:

- `test_installation.py` - Test file for setup wizard validation (archived after successful testing)

**Previous Archives (2025-08-27)**:

- `test_black_formatting.py` - Temporary test file for Black formatter
    verification (archived after successful testing)

### Development Files

**Recent Archives (2025-08-28)**:

- `dev/` - Development directory containing testing scripts, analysis tools, and demos
  - `coverage.xml` - Test coverage report file
  - Various debugging and testing scripts

## 📅 Chronological Index

### 2025

**August 28, 2025** - Repository organization cleanup:

- Archived `test_installation.py` test file
- Archived `.flake8` legacy configuration file
- Archived `coverage.xml` test coverage report
- Archived `dev/` directory with development tools and scripts
- Removed empty `clamav_db/` directory

**August 25, 2025** - Repository organization cleanup:

- Archived performance monitoring data
- Archived application logs
- Moved security and performance reports to docs/reports/

**August 24, 2025** - Major archival of superseded reports:

- Archived planning documents completed successfully
- Archived intermediate stage reports superseded by final completion
- Archived date-specific quality reports superseded by achievement

**Previous Archives** - Various implementation reports and development files

## 🔍 Search Index

### By File Type

- **Documentation**: 8 files
- **Configuration**: 0 files
- **Templates**: 0 files
- **Scripts**: 0 files

### By Archive Reason

- **Technology Evolution**: 0 files
- **Security Updates**: 0 files
- **Standards Changes**: 0 files
- **Performance Improvements**: 0 files
- **Project Completion**: 8 files (planning superseded by completion)

## 📋 Archive Entry Template

When adding new archived content, use this template:

```Markdown

### [File Name] - [Archive Date]

- **Type**: deprecated|legacy-version|superseded
- **Original Location**: `path/to/original/file`

- **Archive Location**: `archive/category/date/filename`
- **Archive Reason**: Brief reason for archiving
- **Replacement**: Link to replacement or "None"
- **Retention Until**: Date or "Permanent"
- **Dependencies**: List of dependent files or "None"
- **Migration Notes**: Brief migration guidance or "N/A"

---

```Markdown

## 🔄 Maintenance Schedule

### Monthly Updates

- [ ] Review new archives
- [ ] Update statistics
- [ ] Validate archive organization
- [ ] Check retention schedules

### Quarterly Reviews

- [ ] Comprehensive archive audit
- [ ] Update search indices
- [ ] Review retention policies
- [ ] Archive optimization

## 📞 Archive Support

For questions about archived content:

1. **Location**: Check this index for current location
2. **Context**: Review archive metadata for background
3. **Alternatives**: Follow replacement links when available
4. **Support**: Contact project maintainers for assistance

## 🏷️ Tags and Metadata

### Content Tags

- `deprecated`
- `legacy`
- `superseded`
- `compliance`
- `migration`

### Archive Status

- `active-archive` - Recently archived, may still have references
- `stable-archive` - Fully archived, no active references
- `retention-review` - Subject to retention policy review
- `permanent-archive` - Permanent retention required

---

**This index is automatically maintained and updated during archive operations. Manual
edits should be avoided to maintain data integrity.**

## Pre-Modernization Archive (2025-09-05)

**Location**: `archive/pre-modernization-20250905/`  
**Reason**: Files replaced by modern development environment setup  
**Status**: Archived after successful modernization validation  

### Archived Components
- Legacy setup scripts superseded by modern-dev-setup.sh
- Deprecated configuration files replaced by modern tooling
- Redundant documentation replaced by comprehensive guides
- Old dependency management replaced by modern package managers

### Modern Replacements
- Setup: `scripts/setup/modern-dev-setup.sh`
- Commands: `Makefile.modern`
- Environment: `.envrc` with direnv automation
- Documentation: `docs/guides/MODERNIZATION_COMPLETE_SUMMARY.md`


## Makefile Consolidation (2025-09-05)

**Location**: `archive/legacy-makefile-20250905/`  
**Reason**: Consolidated legacy and modern Makefiles for solo development  
**Status**: Legacy Makefile replaced with enhanced modern version  

### Changes
- Replaced legacy Python-focused Makefile with modern multi-language version
- Enhanced with modern development tools integration
- Improved command organization and help system
- Added support for modern package managers and automation

### Benefits
- 6x faster development environment setup
- Automatic environment activation
- Cross-platform compatibility
- Better developer experience


## Final Cleanup - 2025-09-05

**Archive Location**: `archive/final-cleanup-20250905/`

### Deprecated Content
- `org.xanados.searchanddestroy.hardened.policy` — Archived 2025-09-05 (deprecated PolicyKit superseded by io.github.asafelobotomy.* policies)
- `org.xanados.searchanddestroy.policy` — Archived 2025-09-05 (deprecated PolicyKit superseded by io.github.asafelobotomy.* policies)
- `org.xanados.searchanddestroy.rkhunter.policy` — Archived 2025-09-05 (deprecated PolicyKit superseded by io.github.asafelobotomy.* policies)

### Test Files  
- `test_gui_fix.py` — Archived 2025-09-05 (root directory organization compliance)

### Legacy Tests
- `tests/test_implementation.py` — Archived 2025-09-05 (umbrella test superseded by focused suites)

**Status**: Repository modernization and cleanup COMPLETE
**Next Action**: Regular maintenance using modern development workflow
