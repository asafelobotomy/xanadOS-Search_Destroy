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

## [2.2.0] - 2025-08-08

### Added

- **Professional 3-Column GUI Layout**: Complete redesign of main window with optimal proportions (25%:37.5%:37.5%)
  - Column 1: Full-length Scan Results section
  - Column 2: Integrated workflow (Scan Progress + Scan Type + Actions)
  - Column 3: Scan Target selection
- **Comprehensive Repository Cleanup Tools**:
  - `dev/cleanup_repository.py` - Automated repository maintenance script
  - `dev/repository_status.py` - Project metrics and status reporting
- **Enhanced Documentation Framework**:
  - `docs/API.md` - Complete API documentation for all modules
  - `docs/CONTRIBUTING.md` - Comprehensive contribution guidelines
  - `docs/CLEANUP_SUMMARY.md` - Repository organization summary
  - Enhanced `dev/README.md` with development workflow guides
- **Organized Development Structure**:
  - `dev/debug-scripts/` directory with 18 organized test/debug files
  - Comprehensive README documentation for all script categories
  - Proper separation of debug tools from main codebase

### Changed

- **GUI Layout Optimization**: Transformed cramped interface into professional 3-column design
- **Scan Results Display**: Extended to full column height for better visibility
- **Progress Section**: Relocated to center column for logical workflow integration
- **Actions Panel**: Moved to center column under Scan Type for better organization
- **File Organization**: Moved 18 test/debug files from root to `dev/debug-scripts/`
- **Repository Structure**: Achieved 100% organization score with all directories properly categorized

### Removed

- **Node.js Artifacts**: Removed node_modules and package-lock.json
- **Python Cache**: Cleaned 207+ cache entries (__pycache__, *.pyc files) across entire project
- **Root Directory Clutter**: Moved all test files to organized structure
- **Unused Development Files**: Archived or removed obsolete scripts and configurations

### Fixed

- **GUI Layout Issues**: Resolved text visibility and cramping problems
- **Project Organization**: Eliminated repository clutter and improved maintainability
- **Documentation Gaps**: Created comprehensive guides for all development aspects
- **Code Quality**: Improved structure and organization across 106 Python files

### Technical Improvements

- **Repository Health**: Achieved 100% organization score with excellent assessment
- **Code Metrics**: 35,785+ lines of code properly structured and documented
- **Test Coverage**: 45 test files organized and accessible
- **Development Workflow**: Complete toolchain for maintenance and quality assurance
- **Documentation Coverage**: 100% with all essential guides and references

## [2.3.0] - 2025-08-09

### Added

- **Enhanced Delete All Reports Functionality**: 
  - Reports tab "Delete All Reports" now removes both ClamAV and RKHunter reports
  - Unified report management across all scan types
  - Proper cleanup of both `~/.local/share/search-and-destroy/scan_reports/` and `~/.local/share/search-and-destroy/rkhunter_reports/`

- **Advanced RKHunter Progress Tracking System**:
  - Real-time progress tracking based on actual scan output parsing
  - Stage-based progress updates with 14 distinct scan phases (5% → 100%)
  - Authentication-aware progress tracking (stays at 0% during password dialogs)
  - Scan start detection with specific indicators to prevent premature updates
  - Sequential progress validation ensuring progress only increases, never decreases

- **Comprehensive RKHunter Output Formatting**:
  - Enhanced visual formatting with color-coded results (green for clean, red for threats, orange for warnings)
  - Emoji-based status indicators with proper character encoding fixes
  - Hierarchical output structure with section headers and summary statistics
  - Improved readability with proper spacing and visual hierarchy
  - Smart filtering to remove noise and display only meaningful information

### Enhanced

- **Scan Tab Layout Optimization**:
  - Improved column proportions for better visual balance
  - Enhanced scan results display area
  - Better integration of progress and target selection components

- **RKHunter Integration Improvements**:
  - Eliminated conflicting progress sources between thread simulation and output parsing
  - Enhanced scan state management with proper initialization and cleanup
  - Improved authentication workflow handling
  - Better coordination between scan thread and main window progress tracking

### Fixed

- **Progress Bar Regression Issues**:
  - Resolved progress jumping backwards (e.g., 40% → 35%) during scan execution
  - Fixed conflicting progress triggers between similar stage names
  - Eliminated duplicate progress updates from multiple sources
  - Corrected authentication-phase progress updates that occurred before password entry

- **RKHunter Output Display Issues**:
  - Fixed missing emoji characters displaying as "�" symbols
  - Resolved poor formatting and hard-to-read scan results
  - Corrected noise filtering for cleaner output display
  - Fixed inconsistent progress tracking throughout scan lifecycle

- **Stage Detection Conflicts**:
  - Implemented specific keyword validation for each scan stage
  - Resolved ambiguous trigger phrases causing incorrect stage detection
  - Fixed early progress conflicts between thread and main window tracking
  - Eliminated cross-contamination between similar stage names

### Technical Improvements

- **Progress Tracking Architecture**:
  - Single authoritative progress source (output-based parsing)
  - Priority-based stage processing (highest progress checked first)
  - Comprehensive stage validation with exact keyword matching
  - Scan state tracking with `_rkhunter_scan_actually_started` flag

- **RKHunter Thread Management**:
  - Removed conflicting progress simulation from `RKHunterScanThread`
  - Enhanced output callback system for real-time progress detection
  - Improved scan start detection with non-conflicting trigger phrases
  - Better error handling and timeout management for authentication

- **UI Responsiveness**:
  - Enhanced real-time output processing with smart filtering
  - Improved status message coordination between components
  - Better visual feedback during authentication and scan phases
  - Optimized progress bar update frequency and accuracy

### Changed

- **Progress Bar Behavior**:
  - Now remains at 0% during authentication dialogs
  - Only advances after successful authentication and actual scan start
  - Provides accurate real-time progress throughout entire scan lifecycle
  - Sequential progression without backwards movement

- **RKHunter Output Processing**:
  - Enhanced filtering system removes common noise and warnings
  - Improved emoji handling with proper character replacement
  - Better section organization with clear visual hierarchy
  - More informative status messages during different scan phases

- **Scan State Management**:
  - Proper state initialization and cleanup for each scan
  - Enhanced coordination between thread and main window components
  - Improved authentication workflow integration
  - Better error handling and recovery mechanisms

## [Unreleased]

### Added

- Placeholder for future features

### Changed

- Placeholder for future changes

### Fixed

- Placeholder for future fixes

## [2.2.0] - 2025-08-08

## [Unreleased]

### Changed

- Code quality improvements: removed unused imports, fixed line lengths, optimized structure

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
