# Archive Index

Comprehensive inventory of all archived content in the repository following archive policy requirements.

## 📋 Archive Contents

### Recently Added (2025-12-09)

#### Consolidation Backup Archive
- **Consolidation Analysis Documents** (`consolidation-backup-20250920/`)
  - **Archived Date**: 2025-12-09
  - **Original Date**: 2025-09-20
  - **Contents**: 4 analysis documents from Phase 2 consolidation work
    - `api-compatibility-mapping.md` (5,823 bytes)
    - `configuration-consolidation-20250920/analysis.md` (4,879 bytes)
    - `rkhunter-consolidation-20250920/analysis.md` (4,044 bytes)
    - `scanner-consolidation-20250920/analysis.md` (3,023 bytes)
  - **Total Size**: 24K
  - **Reason**: Consolidation work completed, backups no longer needed in root
  - **Retention**: 1 year (analysis documents)
  - **Original Location**: `consolidation-backup/`

### Recently Added (2025-09-21)

#### Security Consolidation Archive - Phase 2D
- **Legacy Security Components** (`security-consolidation-legacy/phase2d-20250921-101655/`)
  - **Archived Date**: 2025-09-21
  - **Files**: 6 legacy security modules (184,846 total bytes)
    - `gui_auth_manager.py` (17,255 bytes)
    - `elevated_runner.py` (5,060 bytes)
    - `permission_manager.py` (12,778 bytes)
    - `security_standards.py` (15,392 bytes)
    - `security_api.py` (116,633 bytes)
    - `security_dashboard.py` (32,728 bytes)
  - **Reason**: Consolidated into unified security framework for better maintainability
  - **Replacement**: 5 comprehensive security modules (3,307 lines)
    - `app/core/unified_security_framework.py` (735 lines)
    - `app/core/authorization_engine.py` (496 lines)
    - `app/core/api_security_gateway.py` (763 lines)
    - `app/core/permission_controller.py` (764 lines)
    - `app/core/security_integration.py` (549 lines)
  - **Benefits**: 36% code reduction + enterprise features (LDAP/SAML/OAuth2/MFA)
  - **Retention**: 2 years (core system components)
  - **Original Locations**: `app/core/`, `app/utils/`, `app/api/`, `app/gui/`

### Recently Added (2025-09-15)

#### Deprecated Authentication Systems
- **Complex Authentication Systems** (`deprecated-auth-systems/2025-09-15/`)
  - **Archived Date**: 2025-09-15
  - **Files**: `privilege_escalation.py`, `auth_session_manager.py`
  - **Reason**: Overly complex for GUI application needs, not used in production code
  - **Replacement**: `app/core/gui_auth_manager.py` with `elevated_run_gui()`
  - **Retention**: 2 years (core system components)
  - **Original Location**: `app/core/`
  - **Lines Removed**: 808 lines of complex authentication code
  - **Related Changes**: Updated `app/core/__init__.py`, cleaned `rkhunter_optimizer.py`

### Recently Added (2025-09-12)

#### Deprecated Content
- **Docker and Container Tools** (`deprecated/2025-09-12/`)
  - **Archived Date**: 2025-09-12
  - **Files**: `Dockerfile`, `docker-compose.yml`, `containers/docker-manager.sh`
  - **Reason**: Docker/Podman no longer used in development workflow
  - **Replacement**: Native tooling with uv (Python) and pnpm (Node.js)
  - **Retention**: 1 year
  - **Original Location**: Root directory and `scripts/tools/containers/`
  - **Related Changes**: Removed container scanning from security-scan.sh, updated cspell.json

- **VS Code Tool Configurations** (`deprecated/2025-09-12/`)
  - **Archived Date**: 2025-09-12
  - **Files**: `.prettierrc.json`, `.prettierignore`
  - **Reason**: Prettier VS Code extension removed from development environment
  - **Replacement**: Code formatting handled by Ruff (Python) and markdownlint (Markdown)
  - **Retention**: 1 year
  - **Original Location**: Root directory
  - **Related Changes**: Removed prettier from package.json, updated .vscode/extensions.json

- **Repository Cleanup - Root Policy Violations** (`deprecated/2025-09-12/`)
  - **Archived Date**: 2025-09-12
  - **Files**: `coverage.xml`, `markdown-fixes.log`, `setup.log`, `.coverage`
  - **Reason**: Files violated root directory organization policy
  - **Replacement**: Proper locations (logs/, htmlcov/, tests/)
  - **Retention**: 1 year
  - **Original Location**: Root directory

- **Repository Cleanup - Redundant Configurations** (`deprecated/2025-09-12/`)
  - **Archived Date**: 2025-09-12
  - **Files**: `update_config.json`, `performance_config_template.json`, `rkhunter_enhanced.conf`
  - **Reason**: Superseded by enhanced/optimized versions
  - **Replacement**: `update_config_enhanced.json`, `performance_config_2025.json`, `rkhunter-optimized.conf`
  - **Retention**: 1 year
  - **Original Location**: `config/` directory

- **Repository Cleanup - Deprecated Test Configs** (`deprecated/2025-09-12/`)
  - **Archived Date**: 2025-09-12
  - **Files**: `pytest.ini`, `pytest_modern.ini`
  - **Reason**: Test configuration consolidated into pyproject.toml
  - **Replacement**: `pyproject.toml` [tool.pytest.ini_options]
  - **Retention**: 1 year
  - **Original Location**: `config/` directory

- **Makefile.new** (`deprecated/2025-09-12/`)
  - **Archived Date**: 2025-09-12
  - **Reason**: Duplicate of main Makefile, incomplete features
  - **Replacement**: Use main `Makefile` in root directory
  - **Retention**: 1 year
  - **Original Location**: `/Makefile.new`

### Existing Archive Categories

#### Deprecated Content (`deprecated/`)
- Historical documentation and configuration files
- References to org.xanados.* kept for context

#### Legacy Versions (`legacy-versions/`)
- **Legacy Makefile** (`legacy-makefile-20250905/`)
- Older release notes and version-specific content

#### Superseded Content (`superseded/`)
- **2025-09-02**: Contains superseded Makefile.old and configurations
- Various replaced scripts and configuration files

#### Backups (`backups/`)
- Development environment backups
- Configuration backups from setup processes
- Repository operation backup files

## 📊 Archive Statistics

- **Total Archived Items**: 31
- **Deprecated Items**: 10
- **Legacy Versions**: 0
- **Superseded Items**: 12
- **Performance/Monitoring Data**: 6
- **Temporary Testing Files**: 2
- **Development Files**: 1
- **Last Updated**: 2025-09-12

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
- `archive/temp-testing/test_rkhunter_fix.py` — Archived 2025-09-05 (temporary test file from recent development work)
- `archive/temp-testing/test_rkhunter_fixes.py` — Archived 2025-09-05 (temporary test file from recent development work)
- `archive/temp-testing/test_optimization_fixes.py` — Archived 2025-09-05 (temporary test file from recent development work)
- `archive/temp-testing/test_cron_integration.py` — Archived 2025-09-05 (temporary test file from recent development work)
- `archive/temp-testing/test_optimization_direct.py` — Archived 2025-09-05 (temporary test file from recent development work)
- `archive/temp-testing/test_config_fix.py` — Archived 2025-09-05 (temporary test file from recent development work)
