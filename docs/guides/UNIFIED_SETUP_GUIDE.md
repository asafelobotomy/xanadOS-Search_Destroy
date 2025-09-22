# xanadOS Search & Destroy - Unified Setup Guide

## Overview

The xanadOS Search & Destroy project now features a **single, comprehensive setup command** that handles everything needed to get the application running, from dependency installation to validation.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# ONE COMMAND - Complete setup
make setup

# Launch the application
make run
```

## What the Unified Setup Does

The `make setup` command is a comprehensive process that includes all of these phases:

### Phase 1: Modern Development Environment Setup
- Installs modern package managers (uv, pnpm, fnm)
- Sets up automatic environment activation with direnv
- Configures optimal development tools

### Phase 2: Dependencies Installation
- Python dependencies via uv (10-100x faster than pip)
- JavaScript dependencies via pnpm (70% less disk space)
- System dependencies detection and installation

### Phase 3: Comprehensive Validation
- Markdown linting
- Spell checking
- Version synchronization
- Template validation

### Phase 4: Test Suite Verification
- Runs complete test suite to verify functionality
- Validates security components
- Checks GUI and monitoring systems

## System Requirements

- **Operating System:** Linux (Ubuntu 20.04+, Fedora 35+, Arch Linux)
- **Python:** 3.11 or higher
- **Memory:** 2GB RAM minimum, 4GB recommended
- **Disk Space:** 1GB free space for dependencies

## Automatic System Detection

The setup process automatically detects your Linux distribution and installs appropriate packages:

- **Ubuntu/Debian:** `apt install clamav clamav-daemon cron rkhunter`
- **Fedora/RHEL:** `dnf install clamav rkhunter cronie`
- **Arch Linux:** `pacman -S clamav rkhunter cronie`

## Success Indicators

After running `make setup`, you should see:

```
🎉 SETUP COMPLETE! All systems ready for development
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next steps:
  • Run make run to start the application
  • Run make dev for development mode
  • Run make help to see all available commands
```

## Troubleshooting

### If Setup Fails

1. **Check System Requirements**: Ensure you have Python 3.11+ and sufficient disk space
2. **Update Package Managers**: Run `sudo apt update` (Ubuntu) or equivalent for your system
3. **Check Permissions**: Ensure you have sudo access for system dependency installation
4. **View Logs**: Check the setup log file in `logs/setup-YYYYMMDD-HHMMSS.log`

### Common Issues

#### "Command not found: make"
```bash
# Ubuntu/Debian
sudo apt install build-essential

# Fedora/RHEL
sudo dnf groupinstall "Development Tools"

# Arch Linux
sudo pacman -S base-devel
```

#### "Python version too old"
The application requires Python 3.11+. Use your system's package manager to upgrade Python.

#### "Permission denied" during system package installation
The setup process requires sudo access to install system packages like ClamAV and rkhunter.

## Validation

After setup completes, you can verify everything is working:

```bash
# Re-run validation (already included in setup)
make validate

# Check specific components
make test

# Verify application launches correctly
make run
```

## Development Features

The unified setup also provides a complete development environment:

- **Modern Package Managers**: uv (Python), pnpm (JavaScript), fnm (Node.js)
- **Code Quality Tools**: Black, ruff, flake8, pytest
- **Security Tools**: ClamAV, rkhunter, comprehensive monitoring
- **Validation Suite**: Markdown linting, spell checking, test automation
- **AI Enhancement Tools**: GitHub Copilot integration, development prompts

## Available Commands

After setup, these commands are available:

| Command | Description |
|---------|-------------|
| `make run` | Launch the security scanner application |
| `make dev` | Start development environment |
| `make test` | Run complete test suite |
| `make validate` | Run comprehensive validation |
| `make help` | Show all available commands |

## Next Steps

1. **Launch Application**: `make run`
2. **Read Security Guide**: `docs/project/SECURITY_PERFORMANCE_REPORT.md`
3. **Explore Features**: `docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md`
4. **Development**: See `docs/developer/` for contribution guidelines

## Benefits of Unified Setup

- **Single Command**: No need to remember multiple setup steps
- **Comprehensive**: Handles everything from environment to validation
- **Fast**: Modern package managers provide 6x faster setup
- **Reliable**: Automatic error detection and recovery
- **Cross-Platform**: Works on all major Linux distributions
- **Development Ready**: Complete environment for contributors

The unified setup process eliminates the complexity of managing multiple setup commands and ensures everyone gets a consistent, working environment with a single `make setup` command.
