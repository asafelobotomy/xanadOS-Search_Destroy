# Project Architecture

This document describes the architecture and organization of the xanadOS-Search_Destroy project.

## Overview

S&D (Search & Destroy) is a modern GUI application for ClamAV antivirus scanning, built with Python and PyQt6.
The application follows a modular architecture with clear separation of concerns.

## Directory Structure

```text
xanadOS-Search_Destroy/
│
├── app/                           # Main application package
│   ├── **init**.py               # Package initialization
│   ├── main.py                   # Application entry point
│   │
│   ├── core/                     # Core functionality modules
│   │   ├── **init**.py
│   │   ├── file_scanner.py       # File scanning engine
│   │   ├── clamav_wrapper.py     # ClamAV integration
│   │   ├── rkhunter_wrapper.py   # RKHunter integration
│   │   ├── real_time_protection.py # Real-time monitoring
│   │   ├── firewall_detector.py  # Firewall management
│   │   ├── auto_updater.py       # Automatic updates
│   │   └── ...                   # Other core modules
│   │
│   ├── gui/                      # User interface components
│   │   ├── **init**.py
│   │   ├── main_window.py        # Main application window
│   │   ├── theme_manager.py      # Theme and styling
│   │   ├── settings_pages.py     # Settings interface
│   │   ├── themed_widgets.py     # Custom UI components
│   │   └── ...                   # Other GUI modules
│   │
│   ├── monitoring/               # System monitoring
│   │   ├── **init**.py
│   │   └── ...                   # Monitoring modules
│   │
│   └── utils/                    # Utility functions
│       ├── **init**.py
│       ├── config.py             # Configuration management
│       ├── scan_reports.py       # Report generation
│       └── ...                   # Other utilities
│
├── config/                       # Configuration files
│   ├── security.conf.example     # Security configuration template
│   ├── update_config.JSON        # Update configuration
│   └── ...                       # Other config files
│
├── docs/                         # Documentation
│   ├── user/                     # User documentation
│   ├── developer/                # Developer documentation
│   ├── project/                  # Project documentation
│   ├── implementation/           # Implementation details
│   └── releases/                 # Release notes
│
├── packaging/                    # Distribution packaging
│   ├── flatpak/                  # Flatpak packaging
│   └── icons/                    # Application icons
│
├── scripts/                      # Build and utility scripts
│   ├── install-hooks.sh          # Git hooks installation
│   ├── setup-security.sh         # Security setup
│   └── ...                       # Other scripts
│
├── tests/                        # Test suite
│   ├── **init**.py
│   ├── conftest.py               # Test configuration
│   ├── test_gui.py               # GUI tests
│   └── test_monitoring.py        # Monitoring tests
│
├── dev/                          # Development tools
│   ├── debug-scripts/            # Debugging utilities
│   ├── test-scripts/             # Testing utilities
│   └── ...                       # Development utilities
│
├── archive/                      # Archived files
│   ├── old-versions/             # Previous versions
│   ├── deprecated-theme-files/   # Old theme files
│   └── experimental/             # Experimental code
│
├── .GitHub/                      # GitHub configuration
├── .venv/                        # Virtual environment (local)
├── requirements.txt              # Python dependencies
├── package.JSON                  # Node.js dependencies (if any)
├── mypy.ini                      # Type checking configuration
├── pytest.ini                   # Testing configuration
├── .gitignore                    # Git ignore patterns
├── README.md                     # Project overview
├── CHANGELOG.md                  # Change history
├── LICENSE                       # License information
├── VERSION                       # Version number
└── run.sh                        # Quick start script

```text

## Architecture Principles

### 1. Modular Design

- Each module has a single responsibility
- Clear interfaces between modules
- Minimal coupling between components

### 2. Layered Architecture

```text
┌─────────────────────────────┐
│          GUI Layer          │  ← User Interface (PyQt6)
├─────────────────────────────┤
│       Application Layer     │  ← Business Logic
├─────────────────────────────┤
│         Core Layer          │  ← Core Functionality
├─────────────────────────────┤
│        System Layer         │  ← OS Integration
└─────────────────────────────┘

```text

### 3. Configuration Management

- Centralized configuration system
- Environment-specific settings
- User preferences management

### 4. Error Handling

- Comprehensive error handling
- User-friendly error messages
- Logging and debugging support

## Key Components

### Core Engine (`app/core/`)

- **file_scanner.py**: Main scanning engine
- **clamav_wrapper.py**: ClamAV integration and management
- **rkhunter_wrapper.py**: RKHunter rootkit detection
- **real_time_protection.py**: Background monitoring
- **firewall_detector.py**: System firewall management

### User Interface (`app/gui/`)

- **main_window.py**: Primary application interface
- **theme_manager.py**: Dark/Light theme system
- **settings_pages.py**: Configuration interface
- **themed_widgets.py**: Custom UI components

### Utilities (`app/utils/`)

- **config.py**: Configuration management
- **scan_reports.py**: Report generation and storage
- **scan_reports.py**: Threat analysis and reporting

## Data Flow

1. **User Interaction** → GUI Layer
2. **GUI Events** → Application Layer
3. **Business Logic** → Core Layer
4. **System Calls** → System Layer
5. **Results** → Back through layers to GUI

## Security Considerations

- Input validation at all entry points
- Privilege escalation protection
- Secure file handling
- Safe subprocess execution
- Configuration validation

## Testing Strategy

- Unit tests for core functionality
- Integration tests for component interaction
- GUI tests for user interface
- Security tests for vulnerability assessment

## Deployment Architecture

### Development Environment

```bash
Python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Python app/main.py

```text

### Production Distribution

- Flatpak packaging for Linux distributions
- Virtual environment isolation
- Configuration validation
- Security hardening

## Future Architecture Considerations

1. **Plugin System**: Modular extension support
2. **API Layer**: External integration capabilities
3. **Database Layer**: Persistent data storage
4. **Microservices**: Service-oriented architecture
5. **Cloud Integration**: Remote scanning capabilities

## Performance Characteristics

- **Startup Time**: < 3 seconds typical
- **Memory Usage**: 50-100MB base, scales with scan size
- **CPU Usage**: Adaptive based on system resources
- **Storage**: Minimal footprint, configurable cache
- **Network**: Optional cloud features, local by default
