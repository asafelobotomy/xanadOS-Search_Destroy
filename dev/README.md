# Development Tools and Scripts

This directory contains development tools, test scripts, and utilities for maintaining the xanadOS-Search_Destroy project.

## Directory Structure

```
dev/
├── debug-scripts/          # Debugging utilities
├── test-scripts/           # Test scripts and utilities
├── *.py                   # Development and testing scripts
└── README.md              # This file
```

## Key Scripts

### Repository Organization
- **`organize_repository_comprehensive.py`** - Complete repository organization tool
- **`repository_status.py`** - Check repository status and statistics
- **`cleanup_repository.py`** - Legacy cleanup script

### Testing Scripts
- **`test_*.py`** - Various testing scripts for specific features
- **`grace_period_demo.py`** - Demonstration of grace period functionality
- **`test_authentication_fix.py`** - Authentication system testing

### Documentation
- **`GRACE_PERIOD_FIX_SUMMARY.md`** - Summary of grace period implementation

## Repository Organization System

### Automated Organization
The repository includes an automated organization system:

1. **Organization Script**: `organize_repository_comprehensive.py`
   - Moves misplaced files to correct locations
   - Removes duplicate files
   - Ensures proper directory structure
   - Updates .gitignore
   - Creates maintenance scripts

2. **Organization Check**: `../scripts/check-organization.py`
   - Validates repository organization
   - Reports misplaced files
   - Checks for missing __init__.py files

3. **Git Hooks**: `../scripts/install-hooks.sh`
   - Installs pre-commit hook
   - Prevents commits with organization issues
   - Automatically checks organization before each commit

### File Placement Rules

| File Type | Location | Examples |
|-----------|----------|----------|
| Application code | `app/` | Core functionality, GUI, utilities |
| Development tools | `dev/` | Test scripts, debugging tools |
| Unit tests | `tests/` | Formal unit tests |
| Documentation | `docs/` | User guides, API docs, implementation notes |
| Configuration | `config/` | Policy files, configuration examples |
| Build scripts | `scripts/` | Build, deployment, maintenance scripts |
| Packaging | `packaging/` | Flatpak, icons, distribution files |

### Running Organization Tools

#### Check organization status:
```bash
python3 scripts/check-organization.py
```

#### Fix organization issues:
```bash
python3 dev/organize_repository_comprehensive.py
```

#### Install git hooks (one-time setup):
```bash
bash scripts/install-hooks.sh
```

### Adding New Files

When adding new files to the repository:

1. **Place files in appropriate directories** according to the rules above
2. **For Python packages**, ensure `__init__.py` files exist
3. **For test scripts**, place in `dev/` or `tests/` depending on purpose
4. **For documentation**, categorize appropriately in `docs/`

The pre-commit hook will automatically check organization before allowing commits.

## Development Workflow

### Before Committing
1. Run tests: `python3 -m pytest tests/` (if tests exist)
2. Check organization: `python3 scripts/check-organization.py`
3. Fix any issues: `python3 dev/organize_repository_comprehensive.py`
4. Commit changes

### Regular Maintenance
- **Weekly**: Run organization check
- **Before releases**: Full organization cleanup
- **When refactoring**: Update organization rules if needed

## Testing Grace Period Feature

The repository includes comprehensive testing for the grace period authentication feature:

```bash
# Test grace period logic
python3 dev/test_grace_period.py

# Test authentication flow
python3 dev/test_authentication_fix.py

# View grace period demo
python3 dev/grace_period_demo.py
```

## Debugging

Debug scripts are located in `debug-scripts/` subdirectory and provide tools for:
- Performance profiling
- Memory usage analysis
- Threading issues
- GUI debugging

## Contributing

When contributing new development tools:

1. **Place scripts in appropriate subdirectories**
2. **Add documentation** explaining the script's purpose
3. **Update this README** if adding new categories
4. **Follow naming conventions**: snake_case for Python files
5. **Include error handling** and helpful output messages

---

For more information about repository organization, see `docs/project/REPOSITORY_ORGANIZATION.md`.

## Usage

### Repository Cleanup
```bash
python dev/cleanup_repository.py
```

### Running Tests
```bash
# Run specific test scripts
python dev/test-scripts/test_[specific_feature].py

# Run all tests
find dev/test-scripts -name "test_*.py" -exec python {} \;
```

### Debug Scripts
Debug scripts are located in `dev/debug-scripts/` and can be used for:
- Authentication testing
- GUI component debugging  
- Firewall functionality testing
- RKHunter integration testing

### Development Workflow

1. **Before making changes**: Run cleanup script to ensure clean environment
2. **During development**: Use debug scripts to test specific components
3. **After changes**: Run relevant test scripts to validate functionality
4. **Before commit**: Ensure all tests pass and run cleanup script

- `demo_strawberry_theme.py` - Demonstrates the dark theme (Strawberry palette)
- `demo_sunrise_theme.py` - Demonstrates the light theme (Sunrise palette)

### `/test-scripts/`

Contains development test scripts used during implementation:

- Various test scripts for bug fixes, UI improvements, and feature testing
- These scripts were used during development to validate specific functionality

## Usage

These resources are primarily for developers working on the application. They are not required for normal application usage.

### Running Demo Scripts

```bash
cd dev/demos
python demo_strawberry_theme.py
python demo_sunrise_theme.py
```

### Test Scripts

The test scripts in `/test-scripts/` are historical development aids and may require modification to run with the current codebase.

## Note

Files in this directory are development resources and are not included in the main application distribution.
