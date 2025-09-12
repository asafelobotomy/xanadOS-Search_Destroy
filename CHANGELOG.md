# Changelog
<!-- markdownlint-disable MD024 -->

All notable changes to xanadOS Search & Destroy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Development environment improvements and automation scripts
- Enhanced repository maintenance tools

### Changed

- Continued modernization of build and development workflows

## [2.14.0] - 2025-09-12

### Added

- **Complete Development Environment Setup Script**
  - Automated installation of modern package managers (uv, pnpm, fnm)
  - Python virtual environment setup with dependency management
  - Node.js environment configuration with npm integration
  - System security tools installation (ClamAV, RKHunter) based on detected OS
  - Comprehensive validation checks and detailed setup reports
  - Multi-OS support (Ubuntu, Fedora, Arch Linux)
  - Shell environment configuration and path management

- **Enhanced Makefile Development Targets**
  - Added `run`, `run-debug`, `dev`, `clean`, `lint`, and `format` targets
  - Improved development workflow automation with better error handling
  - Enhanced integration with modern package managers
  - Streamlined development task execution

- **Comprehensive Validation and Testing Framework**
  - `validate-setup.sh` for environment health checking and validation
  - `unified-test-runner.sh` for consolidated testing across multiple frameworks
  - Enhanced logging and result tracking for better visibility
  - Automated dependency conflict resolution with `resolve-dependency-conflicts.sh`
  - Support for unit, integration, security, quality, GUI, and Docker tests

### Fixed

- **Package Manager Standardization and Security**
  - Enforced pnpm usage with `.npmrc` configuration to prevent package-lock conflicts
  - Removed package-lock.json to eliminate dependency management conflicts
  - Standardized dependency management across the entire project
  - Enhanced npm dependency security and vulnerability management

- **Code Quality and Security Improvements**
  - Fixed 234 code quality issues in `scripts/tools/` directory
  - Enhanced subprocess security across all core modules
  - Improved temporary file handling and security patterns
  - Resolved unused variable assignments and import organization
  - Enhanced ruff checks and auto-fixes for remaining quality issues

- **Development Environment Optimization**
  - Resolved Python environment detection and setup issues
  - Fixed Node.js version management and compatibility
  - Enhanced virtual environment creation and validation
  - Improved dependency installation reliability and error recovery

### Changed

- **Repository Maintenance and Organization**
  - Updated `.gitignore` with modern patterns and comprehensive coverage
  - Cleaned up Python cache directories and temporary files
  - Enhanced file organization compliance with enterprise standards
  - Improved archive management and backup systems

- **Build System Modernization**
  - Enhanced pyproject.toml with modern dependency specifications
  - Improved requirements management with fixed dependency versions
  - Updated package.json with enhanced script automation
  - Better integration between Python and Node.js build systems

## [2.13.2] - 2025-09-07

### Added

- **Enhanced VS Code File Restoration Prevention**
  - Comprehensive prevention system for deprecated file recreation
  - Enhanced git hooks to allow deletions while blocking additions
  - Improved VS Code workspace configuration management
  - Complete solution for editor-based file restoration issues

- **Modernized Flatpak Distribution Support**
  - Updated ClamAV to latest version 1.4.3 with enhanced security features
  - Added Rust SDK extension for modern ClamAV build requirements
  - Enhanced build system with cmake-ninja for improved performance
  - Simplified Python dependencies installation process
  - Updated to current app version v2.13.1 with latest fixes

### Fixed

- **VS Code Integration Issues**
  - Resolved VS Code workspace file restoration that recreated empty deprecated files
  - Enhanced .gitignore, VS Code settings, and git hook integration
  - Fixed file watch patterns to prevent unwanted file recreation
  - Improved workspace stability and file management

- **Repository Cleanup and Maintenance**
  - Moved misplaced Flatpak package to proper location
  - Removed empty temporary files from root directory
  - Fixed npm dependencies and resolved security vulnerabilities
  - Enhanced repository compliance with file organization policies

### Changed

- **Flatpak Build System Improvements**
  - Modernized build approach based on proven ClamTk and Kapitano implementations
  - Enhanced dependency management for better compatibility
  - Improved build performance and reliability
  - Updated manifest structure for better maintainability

## [2.13.1] - 2025-09-05

### Fixed

- **First Time Setup Dialog**: Resolved issue where setup dialog appeared on every launch
  - Added missing `first_time_setup_completed` configuration flag
  - Enhanced `needs_setup()` function with auto-recovery logic
  - Automatically detects existing package installations and marks setup complete
  - Prevents future occurrences even if config file is corrupted or reset

### Security

- **Setup Wizard Security**: Replaced direct `subprocess.run` calls with secure alternatives
  - Updated package detection commands to use `run_secure()`
  - Enhanced post-installation command execution security
  - Improved Python package installation security in setup wizard

### Documentation

- **Implementation Reports**: Added comprehensive fix documentation
  - `docs/implementation-reports/first-time-setup-dialog-fix.md`
  - Detailed root cause analysis and solution documentation
  - Prevention strategies for future similar issues

## [2.12.0] - 2025-09-05

### Added

- **SSH Security Hardening**: Complete SSH daemon security configuration
  - PermitRootLogin disabled for enhanced security
  - SSH Protocol v2 enforcement (blocking insecure v1)
  - Authentication limits with MaxAuthTries: 3
  - X11 and TCP forwarding disabled for network security
  - ClientAlive settings for session management

- **RKHunter Optimization Scripts**: Automated false positive reduction
  - `scripts/security/rkhunter_optimize.sh` - Configuration optimization
  - `scripts/security/ssh_hardening.sh` - SSH security automation
  - `scripts/security/fixes_applied_report.sh` - Comprehensive status reporting
  - `scripts/security/rkhunter_config_fix.sh` - Configuration error resolution

- **Enhanced Security Configuration**:
  - Secure temporary directory for RKHunter operations
  - Comprehensive whitelist for legitimate system files
  - Enhanced detection modes without false positive prone tests
  - Automated scanning configuration for GUI integration

### Fixed

- **RKHunter Scan Accuracy**: Dramatically improved scan reliability
  - Reduced false positives by 79% (29 warnings → 6 warnings)
  - Fixed invalid UNHIDE_TESTS configuration error
  - Enhanced GUI integration with proper scan functionality
  - Scan accuracy improved from 10.3% to 85%+

- **SSH Security Gaps**: Complete system hardening implementation
  - Root SSH access completely disabled
  - Secure authentication protocols enforced
  - Network forwarding vulnerabilities eliminated
  - Session timeout and connection limits applied

### Changed

- **Repository Modernization**: Enhanced development and deployment
  - Docker support with containerization
  - Enhanced build processes and validation frameworks
  - Updated configuration management with TOML and enhanced JSON
  - Improved monitoring and performance configuration templates

- **Security Architecture**: Comprehensive security posture improvement
  - System security significantly enhanced with industry standards
  - False positive detection rate reduced from 90% to minimal levels
  - Enhanced privilege escalation controls and access management

## [2.11.2] - 2025-08-25

### Added

- **Python Validation Tooling**
  - Python validation script: `scripts/tools/quality/check-python.sh`
  - Runs ruff/black/flake8; optional mypy and pytest with `--strict`
  - NPM scripts: `validate:python`, `validate:python:strict`, and `quick:validate:all`
  - Extends quick validation with Python checks (non-destructive)

### Changed

- **Markdown Tooling Consolidation**
  - Archived legacy Markdown fixer wrapper scripts in favor of canonical
    `scripts/tools/quality/fix-markdown.sh`
  - Archived files: `fix-markdown-formatting.sh`, `fix-markdown-targeted.sh`,
    `fix-markdown-advanced.sh`, `fix-markdown-final.sh`

### Fixed

- **Flathub Distribution**
  - Updated Flatpak manifest to reference v2.11.1 tag and correct commit hash
  - Added v2.11.1 release entry to AppStream metadata
  - Synchronized all Flathub submission files with latest release

### Documentation

- Updated metainfo.xml with comprehensive v2.11.1 release notes

## [2.11.1] - 2025-08-25

### Added

- **Flathub Submission Automation**
  - Comprehensive Flathub submission automation script
  - Complete Flathub submission documentation and guides
  - Automated submission process with fork detection and branch management
  - Enhanced submission validation and error handling

### Fixed

- **Version Management**
  - VERSION file format simplified for Flathub compatibility
  - Flatpak manifest commit hash synchronization
  - Submission script robustness with better error recovery

### Documentation

- **Submission Documentation**
  - Added Flathub submission ready report with complete verification
  - Created step-by-step submission guides for various scenarios
  - Enhanced submission process documentation

## [2.11.0] - 2025-08-24

### Added

- **Enterprise-Grade Repository Organization**
  - AI development tools and comprehensive framework
  - 11 specialized chat modes for different development scenarios
  - 7 reusable prompt templates for common development tasks
  - Path-specific instructions for security, testing, and debugging
  - MCP (Model Context Protocol) integration for enhanced capabilities
  - Comprehensive validation system with 20+ quality checks
  - Automated quality assurance and compliance checking
  - Professional documentation and README structure
  - Complete Flathub compliance verification and submission readiness
  - Repository cleanup and organization tools
  - YAML validation support (yamllint + PyYAML)

### Changed

- **Application Identity Migration**
  - Migrated App ID from org.xanados.* to io.GitHub.asafelobotomy.SearchAndDestroy
  - Improved file organization following strict directory policies
  - Enhanced quality assessment pipeline with comprehensive validation
  - Archived legacy PolicyKit policies with proper metadata
  - Repository structure reorganized for enterprise standards
  - All scripts categorized and moved to proper directories
  - Reports and analysis moved to structured reporting system
  - Backup files archived for clean repository maintenance

### Fixed

- **Repository Compliance**
  - Root directory policy compliance violations
  - Markdown formatting inconsistencies across documentation
  - YAML validation warnings in quality checker
  - File placement violations in repository structure
  - Enterprise deployment and automation scripts
  - Repository organization and file structure standardization
  - Quality metrics maintained at 98.9% during reorganization

## [1.0.0] - 2024-12-19

### Added

- **Initial Release**
  - Initial AI development tools
  - Core instruction system for GitHub Copilot optimization
  - Basic validation and quality assurance tools
  - Security-focused instructions for code review and development
  - Secure coding practices integrated into chat modes
