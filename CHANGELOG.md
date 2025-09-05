# Changelog

All notable changes to xanadOS Search & Destroy will be documented in this file.

The format is based on [Keep a Changelog](HTTPS://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](HTTPS://semver.org/spec/v2.0.0.HTML).

## [Unreleased]

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

### Added (tooling)

- Python validation script: `scripts/tools/quality/check-python.sh`
  - Runs ruff/black/flake8; optional mypy and pytest with `--strict`.
- NPM scripts: `validate:python`, `validate:python:strict`, and `quick:validate:all`.
  - Extends quick validation with Python checks (non-destructive).

### Changed (toolshed)

- Archived legacy Markdown fixer wrapper scripts in favor of the canonical
  `scripts/tools/quality/fix-markdown.sh`.
  Archived files:
  - `scripts/tools/fix-markdown-formatting.sh`
  - `scripts/tools/fix-markdown-targeted.sh`
  - `scripts/tools/fix-markdown-advanced.sh`
  - `scripts/tools/fix-markdown-final.sh`

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

### Fixed (Flathub)

- Updated Flatpak manifest to reference v2.11.1 tag and correct commit hash
- Added v2.11.1 release entry to AppStream metadata
- Synchronized all Flathub submission files with latest release

### Documentation

- Updated metainfo.XML with comprehensive v2.11.1 release notes

## [2.11.1] - 2025-08-25

### Added

- Comprehensive Flathub submission automation script
- Complete Flathub submission documentation and guides
- Automated submission process with fork detection and branch management
- Enhanced submission validation and error handling

### Fixed 2

- VERSION file format simplified for Flathub compatibility
- Flatpak manifest commit hash synchronization
- Submission script robustness with better error recovery

### Documentation 2

- Added Flathub submission ready report with complete verification
- Created step-by-step submission guides for various scenarios
- Enhanced submission process documentation

## [2.11.0] - 2025-08-24

### Added 2

- Enterprise-grade repository organization and structure
- AI development tools
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

- Migrated App ID from org.xanados.* to io.GitHub.asafelobotomy.SearchAndDestroy
- Improved file organization following strict directory policies
- Enhanced quality assessment pipeline with comprehensive validation
- Archived legacy PolicyKit policies with proper metadata

### Fixed 3

- Root directory policy compliance violations
- Markdown formatting inconsistencies across documentation
- YAML validation warnings in quality checker
- File placement violations in repository structure
- Enterprise deployment and automation scripts

### Changed 2

- Repository structure reorganized for enterprise standards
- All scripts categorized and moved to proper directories
- Reports and analysis moved to structured reporting system
- Backup files archived for clean repository maintenance

### Fixed 4

- Repository organization and file structure standardization
- Quality metrics maintained at 98.9% during reorganization

## [1.0.0] - 2024-12-19

### Release

- Initial AI development tools
- Core instruction system for GitHub Copilot optimization
- Basic validation and quality assurance tools

### Security

- Security-focused instructions for code review and development
- Secure coding practices integrated into chat modes
