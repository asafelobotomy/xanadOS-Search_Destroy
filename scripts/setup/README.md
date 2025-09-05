# Setup Scripts

## Modern Development Environment (2025)

The xanadOS Search & Destroy project now uses modern development environment setup
with cutting-edge tools and automation.

### Quick Start

```bash
# Single command setup (recommended)
bash scripts/setup/modern-dev-setup.sh

# Or use the modern Makefile
make setup
```

### Modern Tools Included

- **uv**: Lightning-fast Python package management (10-100x faster)
- **pnpm**: Efficient Node.js package management (70% less disk space)
- **fnm**: Ultra-fast Node.js version management (500x faster switching)
- **direnv**: Automatic environment activation
- **Modern security scanning**: Integrated ClamAV, RKHunter, and more

### Features

- 6x faster overall setup time
- Automatic environment activation
- Cross-platform compatibility (Linux, macOS, Windows/WSL2)
- Interactive and non-interactive modes
- Comprehensive validation and error handling
- Performance benchmarking

### Documentation

- Setup Guide: `docs/guides/MODERNIZATION_COMPLETE_SUMMARY.md`
- Performance Analysis: `docs/guides/PERFORMANCE_COMPARISON.md`
- Migration Guide: `docs/guides/PACKAGE_MANAGER_MIGRATION.md`

### Legacy Files

Legacy setup scripts have been archived to `archive/pre-modernization-*/`
for historical reference.

