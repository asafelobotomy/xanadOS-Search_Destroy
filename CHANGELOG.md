# Changelog

All notable changes to this GitHub Copilot Enhancement Framework will be documented in this file.

The format is based on [Keep a Changelog](HTTPS://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](HTTPS://semver.org/spec/v2.0.0.HTML).

## [Unreleased]

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

## [2.11.2] - 2025-08-25

### Fixed

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
- Comprehensive GitHub Copilot enhancement framework
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

- Initial GitHub Copilot Enhancement Framework
- Core instruction system for GitHub Copilot optimization
- Basic validation and quality assurance tools

### Security

- Security-focused instructions for code review and development
- Secure coding practices integrated into chat modes
