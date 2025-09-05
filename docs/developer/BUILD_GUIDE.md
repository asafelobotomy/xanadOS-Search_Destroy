# Build and Development Guide

## Overview

xanadOS Search & Destroy uses a modern, automated build system with comprehensive tooling for
development, testing, and deployment. This guide covers all aspects of building and developing
the application.

## Quick Start

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.0.0 or higher (for development tools)
- **Operating System**: Linux (Ubuntu 20.04+, Fedora 35+, Arch Linux)
- **System Dependencies**: ClamAV, RKHunter (installed via setup)

### One-Command Setup

```bash
# Clone and setup everything
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy
make setup
```

## Build System Architecture

### Core Build Tools

1. **Makefile**: Primary build automation system
2. **package.json**: Node.js tooling and validation scripts
3. **pyproject.toml**: Python packaging and dependencies
4. **Docker**: Containerization and deployment

### Modern Package Managers (Preferred)

- **uv**: Lightning-fast Python package management (10-100x faster than pip)
- **pnpm**: Efficient Node.js package management (70% less disk space)
- **fnm**: Ultra-fast Node.js version management

### Legacy Fallbacks

- **pip**: Python package management
- **npm**: Node.js package management

## Available Commands

### Core Commands

```bash
# Setup and installation
make setup              # Complete development environment (recommended)
make setup-full         # Full setup with all optional components
make install-deps       # Install dependencies only

# Development
make run                # Launch the application
make dev                # Start development environment
make dev-gui            # Start GUI development environment

# Quality assurance
make validate          # Comprehensive validation
make test              # Run all tests
make lint              # Run linting tools
make format            # Format code
make type-check        # Run type checking
make audit             # Security audit
```

### NPM Scripts

```bash
# Validation and quality
npm run quick:validate        # Enhanced quick validation
npm run validate:all         # Comprehensive validation
npm run lint                 # Markdown linting
npm run spell:check:main     # Spell checking

# Version management
npm run version:sync         # Synchronize version across all files
npm run version:get          # Get current version
npm run version:sync:check   # Verify version consistency

# Security
npm run security:check       # Security scanning
npm run security:privilege-check  # Privilege escalation audit

# Python validation
npm run validate:python      # Python code validation
npm run validate:python:strict    # Strict Python validation
```

## Development Workflows

### Daily Development

```bash
# 1. Setup environment (first time)
make setup

# 2. Start development
make dev-gui

# 3. Before committing changes
npm run quick:validate
make test

# 4. Format and lint code
make format
make lint
```

### Adding New Features

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Install any new dependencies
make install-deps

# 3. Develop and test
make run
make test

# 4. Validate code quality
npm run validate:all
make audit

# 5. Commit with proper format
git commit -m "feat: your feature description"
```

### Release Process

```bash
# 1. Update version
echo "2.13.2" > VERSION
npm run version:sync

# 2. Update CHANGELOG.md

# 3. Validate everything
npm run validate:all
make test

# 4. Build and test
make setup
make run

# 5. Commit and tag
git commit -m "release: Version 2.13.2"
git tag v2.13.2
```

## System Dependencies

### Required System Packages

#### Ubuntu/Debian

```bash
sudo apt update && sudo apt install \
    clamav clamav-daemon \
    rkhunter \
    cron \
    python3-dev \
    python3-pip \
    build-essential
```

#### Arch Linux

```bash
sudo pacman -S \
    clamav \
    rkhunter \
    cronie \
    python \
    python-pip \
    base-devel
```

#### Fedora/RHEL

```bash
sudo dnf install \
    clamav clamav-update \
    rkhunter \
    cronie \
    python3-devel \
    python3-pip \
    gcc
```

### Python Dependencies

#### Core Runtime Dependencies

- PyQt6 (GUI framework)
- requests (HTTP library)
- psutil (system monitoring)
- cryptography (security)
- numpy (numerical operations)
- aiohttp (async HTTP)

#### Development Dependencies

- pytest (testing framework)
- ruff (linting and formatting)
- mypy (type checking)
- bandit (security scanning)

#### Optional Dependencies

- Advanced security tools (YARA, Volatility3)
- Machine learning libraries (pandas, scikit-learn)
- Cloud integration (boto3)

## Container Build

### Docker Development

```bash
# Build development container
docker build -t xanados-search-destroy:dev .

# Run in container
docker-compose up dev

# Interactive development
docker-compose run --rm dev bash
```

### Docker Production

```bash
# Build production image
docker build --target runtime -t xanados-search-destroy:latest .

# Run production container
docker run -d --name xanados xanados-search-destroy:latest
```

## Validation and Testing

### Validation Levels

1. **Quick Validation**: `npm run quick:validate`
   - Markdown linting
   - Spell checking
   - Version synchronization
   - Basic structure validation

2. **Comprehensive Validation**: `npm run validate:all`
   - All quick validation checks
   - Python code quality
   - Security scanning
   - Structure validation

3. **Full Testing**: `make test`
   - Unit tests
   - Integration tests
   - GUI tests
   - Performance benchmarks

### Continuous Integration

The project includes pre-commit hooks and validation that run:

- On every commit (version sync)
- On pull request (full validation)
- On release (comprehensive testing)

## Troubleshooting

### Common Issues

#### Setup Dialog Appears Repeatedly

This issue was fixed in v2.13.1. If you still encounter it:

```bash
# Run the auto-fix
python -c "
from app.utils.config import load_config, save_config
from datetime import datetime
config = load_config()
if 'setup' not in config: config['setup'] = {}
config['setup']['first_time_setup_completed'] = True
config['setup']['last_setup_check'] = datetime.now().isoformat()
save_config(config)
print('Setup completion flag added successfully')
"
```

#### Missing Dependencies

```bash
# Reinstall all dependencies
make setup

# Check for missing system packages
./scripts/setup/ensure-deps.sh
```

#### Build Failures

```bash
# Clean and rebuild
make clean
make setup

# Check system compatibility
npm run validate:all
```

## Performance

### Build Performance

- **Modern tools setup**: ~6x faster than legacy
- **uv vs pip**: 10-100x faster Python package installation
- **pnpm vs npm**: 70% less disk space, faster installs
- **Parallel validation**: Multiple quality checks run simultaneously

### Runtime Performance

- **Startup time**: 58% faster with optimized loading
- **Memory usage**: Optimized for systems with 2GB+ RAM
- **Scan performance**: Multi-threaded scanning engine

## Recent Changes (v2.13.1)

### Bug Fixes

- Fixed recurring "First Time Setup" dialog
- Enhanced setup wizard with auto-recovery logic
- Improved configuration persistence

### Security Improvements

- Replaced `subprocess.run` with `run_secure()` in setup wizard
- Enhanced privilege escalation protection
- Improved input validation

### Build System Enhancements

- Updated version management system
- Enhanced validation tooling
- Improved error handling and reporting

---

For additional help, see:

- `CONTRIBUTING.md` - Contribution guidelines
- `docs/developer/CONTRIBUTING.md` - Detailed developer guide
- `scripts/tools/README.md` - Available development tools
- `Makefile` - Complete list of build commands
