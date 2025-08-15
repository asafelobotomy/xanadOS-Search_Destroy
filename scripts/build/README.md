# Build Scripts

This directory contains scripts for building, packaging, and releasing the xanadOS Search & Destroy application.

## Scripts

### prepare-build.sh
- **Purpose**: Prepares the build environment and dependencies
- **Usage**: `./prepare-build.sh`
- **Prerequisites**: Python 3.10+, required system packages

### verify-build.sh
- **Purpose**: Verifies the build integrity and tests
- **Usage**: `./verify-build.sh`
- **Output**: Build verification report

### release.sh
- **Purpose**: Creates official releases with versioning and packaging
- **Usage**: `./release.sh [version]`
- **Output**: Release packages and artifacts

### test-flatpak-build.sh
- **Purpose**: Tests Flatpak package building process
- **Usage**: `./test-flatpak-build.sh`
- **Prerequisites**: Flatpak development tools

## Build Process

1. Run `prepare-build.sh` to set up environment
2. Run `verify-build.sh` to test build integrity
3. Run `test-flatpak-build.sh` to test packaging
4. Run `release.sh` to create release

## Dependencies

- Python 3.10+
- Flatpak development tools
- Git (for versioning)
- Required system packages (see main README)
