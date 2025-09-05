# Version Management System

## Overview

The xanadOS Search & Destroy project now uses a **single source of truth** for version
management. The `VERSION` file in the repository root contains the authoritative version
number, and all other files are automatically synchronized to match it.

## Core Concept

**Never edit version numbers manually in any file except `VERSION`**. All version references in:

- `package.json`
- `pyproject.toml`
- `README.md`
- `config/*.toml` files
- Build scripts and documentation

...are automatically updated to match the `VERSION` file when you run the synchronization command.

## Quick Usage

### Update Version Across Entire Project

1. **Edit the VERSION file** (the ONLY place you should manually change version):

   ```bash
   echo "2.14.0" > VERSION
   ```

2. **Sync all files**:

   ```bash
   npm run version:sync
   # or
   make version-sync
   # or
   python scripts/tools/version_manager.py --sync
   ```

3. **Verify synchronization**:

   ```bash
   npm run version:sync:check
   ```

### Check Current Version

```bash
# Get version from VERSION file
npm run version:get
# or
make version-get

# Show comprehensive version info
make version
# or
python scripts/tools/version_manager.py --version-info
```

## Available Commands

### NPM Scripts

```bash
npm run version:get         # Get current version
npm run version:sync        # Sync all files with VERSION
npm run version:sync:check  # Validate all versions match
```

### Makefile Targets

```bash
make version-get    # Get current version
make version-sync   # Sync all files with VERSION
make version-info   # Show detailed version information
make version        # Show project version summary
```

### Direct Python Usage

```bash
python scripts/tools/version_manager.py --get              # Get version
python scripts/tools/version_manager.py --sync             # Sync all files
python scripts/tools/version_manager.py --update-package   # Update package.json only
python scripts/tools/version_manager.py --update-pyproject # Update pyproject.toml only
python scripts/tools/version_manager.py --update-configs   # Update config files only
python scripts/tools/version_manager.py --update-readme    # Update README.md only
python scripts/tools/version_manager.py --version-info     # Show version details
```

## Automatic Integration

### Build Process

Version synchronization is automatically triggered during:

- **Pre-build**: `npm run prebuild` → `npm run version:sync`
- **Quick validation**: `npm run quick:validate` → `npm run version:sync`
- **Release preparation**: `make release` → `make version-sync`

### Pre-commit Hook

Use the included pre-commit hook to automatically sync versions before commits:

```bash
# Install pre-commit hook
cp scripts/tools/git/pre-commit-version-sync.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

This will:

1. Run version sync before each commit
2. Stage any updated files automatically
3. Ensure version consistency in your commits

## File Structure

```text
VERSION                           # Single source of truth
├── package.json                 # Auto-synced: version field
├── pyproject.toml               # Auto-synced: version field
├── README.md                    # Auto-synced: "Current Version: X.Y.Z"
├── config/
│   └── *.toml                   # Auto-synced: version fields
└── scripts/tools/
    └── version_manager.py       # Version management tool
```

## Version Number Format

Use [Semantic Versioning](https://semver.org/) format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:

- `2.13.0` - Minor release with new features
- `2.13.1` - Patch release with bug fixes
- `3.0.0` - Major release with breaking changes

## Benefits

✅ **Single Source of Truth**: Only edit VERSION file
✅ **No Manual Errors**: Eliminates version mismatches
✅ **Automated Workflow**: Integrates with build processes
✅ **Git-Friendly**: Pre-commit hooks ensure consistency
✅ **Build Integration**: Works with npm, Make, and Python
✅ **Validation**: Built-in checks for version consistency

## Migration from Manual Version Management

If upgrading from manual version management:

1. **Identify current version**: Check which version is most current across files
2. **Set VERSION file**: `echo "X.Y.Z" > VERSION` with the correct version
3. **Run initial sync**: `npm run version:sync`
4. **Verify results**: `npm run version:sync:check`
5. **Commit changes**: All files now reference VERSION file as source

## Troubleshooting

### Version Mismatch Detected

```bash
# Fix by syncing with VERSION file
npm run version:sync

# Verify fix
npm run version:sync:check
```

### Build Failures

If builds fail after version changes:

```bash
# Ensure all files are synced
npm run version:sync

# Run full validation
npm run quick:validate
```

### Pre-commit Hook Issues

```bash
# Test pre-commit hook manually
bash scripts/tools/git/pre-commit-version-sync.sh

# Reinstall hook if needed
cp scripts/tools/git/pre-commit-version-sync.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Implementation Details

The version manager (`scripts/tools/version_manager.py`) provides:

- **Version Reading**: Reads from `VERSION` file with error handling
- **File Updates**: Updates JSON, TOML, and Markdown files using regex patterns
- **Validation**: Ensures all updates succeed before declaring success
- **Comprehensive Logging**: Reports all changes made during sync
- **Modular Design**: Individual update functions for different file types

Files are updated using safe patterns that preserve formatting and only change version fields.
