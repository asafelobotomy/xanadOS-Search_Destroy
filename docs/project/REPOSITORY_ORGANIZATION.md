# Repository Organization Report

**Generated:** 2025-08-10 02:52:00

## Directory Structure

```text
xanadOS-Search_Destroy/
├── app/                    # Main application code
│   ├── core/              # Core functionality
│   ├── gui/               # User interface
│   ├── monitoring/        # Real-time monitoring
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── dev/                   # Development tools and tests
├── docs/                  # Documentation
│   ├── developer/         # Developer documentation
│   ├── implementation/    # Implementation details
│   ├── project/          # Project documentation
│   ├── releases/         # Release notes
│   └── user/             # User documentation
├── packaging/             # Packaging files
├── scripts/              # Build and utility scripts
├── tests/                # Unit tests
└── archive/              # Archived files

```text

## Organization Rules

### File Placement

- **Python application code**: `app/` directory
- **Development scripts**: `dev/` directory
- **Test files**: `dev/`or`tests/` directory
- **Documentation**: `docs/` directory (categorized by type)
- **Configuration**: `config/` directory
- **Build scripts**: `scripts/` directory

### Naming Conventions

- **Python files**: snake_case
- **Documentation**: SCREAMING_SNAKE_CASE for major docs, PascalCase for others
- **Scripts**: kebab-case with appropriate extension

## Maintenance

### Automated Checks

- Run `scripts/check-organization.py` to verify organization
- Install Git hooks with `scripts/install-hooks.sh`
- Pre-commit hook prevents commits with organization issues

### Manual Maintenance

- Use `dev/organize_repository.py` to fix organization issues
- Review and categorize new files regularly
- Update this documentation when structure changes

## Recent Changes

### Files Moved

- `test_grace_period.py`→`dev/test_grace_period.py`
- `verify_cleanup.py`→`dev/verify_cleanup.py`
- `REPOSITORY_CLEANUP_SUMMARY.md`→`docs/project/REPOSITORY_CLEANUP_SUMMARY.md`

No organization issues found.

## Statistics

- **Total Python files**: 5351
- **Documentation files**: 50
- **Configuration files**: 6

---

_This report is automatically generated. Do not edit manually._
