# Scripts Directory

Organized collection of build, deployment, maintenance, and utility scripts for xanadOS Search & Destroy.

## Directory Structure

```text
scripts/
├── build/              # Build and release scripts
│   ├── prepare-build.sh
│   ├── verify-build.sh
│   ├── release.sh
│   └── test-flatpak-build.sh
├── setup/              # Installation and configuration
│   ├── install-hooks.sh
│   ├── install-security-hardening.sh
│   ├── setup-security.sh
│   └── activate.sh
├── maintenance/        # Repository maintenance
│   ├── cleanup.sh
│   ├── cleanup-repository.sh
│   ├── archive.sh
│   ├── restore.sh
│   ├── organize_repository.py
│   ├── organize_repository_comprehensive.py
│   ├── cleanup_repository.py
│   └── verify_cleanup.py
├── security/           # Security and scanning
│   ├── rkhunter-update-and-scan.sh
│   ├── rkhunter-wrapper.sh
│   └── fix_scan_crashes.py
├── flathub/            # Flathub packaging
│   ├── prepare-flathub.sh
│   └── flathub-submission-assistant.sh
└── utils/              # Utilities and tools
    ├── check-organization.py
    ├── organize_documentation.py
    ├── repository_status.py
    └── extended-grace-period-summary.sh
```

## Quick Reference

### Common Tasks

```bash
# Development setup
./scripts/setup/install-hooks.sh
source ./scripts/setup/activate.sh

# Build and test
./scripts/build/prepare-build.sh
./scripts/build/test-flatpak-build.sh

# Maintenance
./scripts/maintenance/cleanup.sh
./scripts/maintenance/organize_repository_comprehensive.py

# Security
sudo ./scripts/security/rkhunter-update-and-scan.sh
```

### Script Categories

- **build/**: Build, package, and release automation
- **setup/**: Environment setup and configuration
- **maintenance/**: Repository cleanup and organization
- **security/**: Security scanning and hardening
- **flathub/**: Flatpak packaging for Flathub
- **utils/**: General utilities and tools

## Usage Guidelines

1. **Permissions**: All scripts are executable (`chmod +x`)
2. **Documentation**: Each directory has its own README
3. **Dependencies**: Check individual script requirements
4. **Testing**: Test scripts in development environment first

## Integration

These scripts integrate with:
- **Makefile**: Main automation (run `make help`)
- **GitHub Actions**: CI/CD workflows
- **Development**: Use with `dev/` directory tools
