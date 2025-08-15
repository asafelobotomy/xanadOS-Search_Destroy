# Setup Scripts

Installation and configuration scripts for development and production environments.

## Scripts

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

1. Run `install-hooks.sh` to set up Git hooks
2. Run `install-security-hardening.sh` for security setup
3. Run `setup-security.sh` to configure security settings
4. Use `activate.sh` to activate development environment

## Requirements

- Bash shell
- Git (for hooks)
- Sudo access (for security scripts)
- Python virtual environment
