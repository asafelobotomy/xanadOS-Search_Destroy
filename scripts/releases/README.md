# Release Management Scripts

This directory contains scripts for managing releases, version updates, and deployment automation.

## Scripts

### Planned Scripts

- **create-release.sh** - Automated release creation with GitHub API
- **update-version.sh** - Version number update across project files
- **prepare-release-notes.sh** - Generate release notes from commits
- **validate-release.sh** - Pre-release validation and testing

### Release Process Integration

These scripts support the release workflow documented in `docs/releases/`.

## Usage

Scripts in this directory should be run from the project root:

```bash

## Example usage (when scripts are implemented)

./scripts/releases/create-release.sh v2.9.1
./scripts/releases/update-version.sh 2.9.1

```text

## Dependencies

- Git with proper authentication
- GitHub CLI (gh) for GitHub API operations
- Python 3.x for version parsing and file updates

---

_This directory is part of the repository organization initiative._
