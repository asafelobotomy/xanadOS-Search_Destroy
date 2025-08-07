# Changelog

All notable changes to the xanadOS-Search_Destroy project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-08-07

### Added

- Enhanced dashboard Last Scan card with proper timestamp and scan type display
- Clickable Last Scan card functionality that opens the Scan tab
- Improved date/time formatting with 12-hour time and full date display
- Debug logging for dashboard card updates
- Automatic reports refresh after scan completion regardless of active tab

### Fixed

- Dashboard card showing "Recently" instead of actual scan details
- Reports not appearing in Reports tab after scan completion
- Duplicate Quick Scan reports generation
- Incorrect scan type labeling (showing "custom" instead of "quick")
- Race condition in report refresh timing after scan completion
- JSON structure mismatch in dashboard card data reading

### Changed

- Reduced Quick Scan file limit from 1000 to 50 files for better performance
- Updated dashboard card text size from 20px to 16px for better layout
- Modified scan type detection logic to properly pass ScanType enum
- Enhanced report saving mechanism to prevent duplicates while ensuring reliability
- Improved dashboard card description to indicate clickability

### Technical Improvements

- Refactored `update_dashboard_cards()` method to read correct JSON structure
- Added proper scan type cleanup (removing "ScanType." prefix)
- Implemented delayed refresh mechanism with error handling
- Enhanced scan completion workflow with proper status tracking

## [Unreleased]

### Added

- GitHub Copilot instructions setup for consistent development practices
- `.copilot-instructions.md` file with comprehensive coding standards and best practices
- VS Code workspace configuration for Copilot integration
- Task automation for quick access to development guidelines
- Documentation in `docs/COPILOT_SETUP.md` explaining the Copilot instruction system

### Changed

- Updated README.md to include development guidelines section
- Enhanced VS Code settings for better Copilot integration
- Streamlined tasks.json with single instruction access task
- Reorganized project structure for better maintainability
- Consolidated packaging files into `packaging/` directory
- Moved implementation summaries to `docs/implementation-history/`

### Removed

- Legacy instruction files and references
- Duplicate `src/` directory structure
- Redundant test files in root directory
- Obsolete `archive/` and `gui_improvements/` directories
- Temporary build artifacts and cache files
- Duplicate `flatpak/` and `icons/` directories
- Outdated file associations and task configurations

## [1.0.0] - 2025-01-XX

### Added

- Initial release of S&D (Search & Destroy)
- PyQt6-based GUI interface
- ClamAV integration for virus scanning
- System tray functionality
- Scan reporting and export features
- Quarantine management
- Scheduled scanning capabilities
- Flatpak packaging support

### Fixed

- Import system conflicts resolved
- Settings dialog crashes fixed
- Report display errors corrected
- Virus definition update functionality

### Changed

- Project structure reorganized
- Documentation improved
- Git configuration optimized
