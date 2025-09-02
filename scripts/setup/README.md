# Setup Scripts

Installation and configuration scripts for development and production environments.

## Quick Start

For new developers or when setting up a fresh environment:

```bash
# 1. Complete development environment setup
./scripts/setup-dev-environment.sh

# 2. Verify all dependencies are working (recommended)
./scripts/setup/ensure-deps.sh

# 3. Start the application
make run
```

## Scripts

### ensure-deps.sh ⭐ **NEW**

- **Purpose**: Verify and auto-install all critical dependencies
- **Usage**: `./ensure-deps.sh`
- **Features**:
  - Validates numpy, schedule, aiohttp, inotify, dnspython
  - Auto-creates virtual environment if missing
  - Tests application startup
  - Updates UV lock file

### install-hooks.sh

- **Purpose**: Install Git hooks for automated checks
- **Usage**: `./install-hooks.sh`

### install-security-hardening.sh

- **Purpose**: Install security hardening measures
- **Usage**: `sudo ./install-security-hardening.sh`

### setup-security.sh

- **Purpose**: Configure security settings and permissions
- **Usage**: `sudo ./setup-security.sh`

### activate.sh

- **Purpose**: Activate virtual environment
- **Usage**: `source ./activate.sh`

## Setup Process

1. Run `../setup-dev-environment.sh` for complete setup
2. Run `ensure-deps.sh` to verify dependencies
3. Run `install-hooks.sh` to set up Git hooks
4. Run `install-security-hardening.sh` for security setup
5. Run `setup-security.sh` to configure security settings
4. Use `activate.sh` to activate development environment

## Requirements

- Bash shell
- Git (for hooks)
- Sudo access (for security scripts)
- Python virtual environment
