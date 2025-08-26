# 🗂️ Project Structure

## Overview

This document describes the organization structure of the xanadOS Search & Destroy project.

## 📁 Directory Structure

```text
xanadOS-Search_Destroy/
├── app/                          # 🎯 Main application code
│   ├── **init**.py
│   ├── main.py                   # Application entry point
│   ├── core/                     # Core functionality
│   │   ├── **init**.py
│   │   ├── async_scanner.py      # Asynchronous scanning engine
│   │   ├── clamav_wrapper.py     # ClamAV integration
│   │   ├── file_scanner.py       # File scanning logic
│   │   ├── system_hardening.py   # Security hardening assessment
│   │   └── ...
│   ├── gui/                      # User interface components
│   │   ├── **init**.py
│   │   ├── main_window.py        # Main application window
│   │   ├── system_hardening_tab.py # Security hardening interface
│   │   └── ...
│   ├── monitoring/               # System monitoring
│   │   ├── **init**.py
│   │   └── ...
│   └── utils/                    # Utility functions
│       ├── **init**.py
│       └── ...
├── archive/                      # 📦 Archived/deprecated code
│   ├── README.md
│   ├── cleanup-stubs/
│   ├── configs/
│   ├── development/
│   ├── old-versions/
│   └── temp-docs/
├── config/                       # ⚙️ Configuration files
│   ├── *.rules                   # Security rules
│   ├── *.policy                  # PolicyKit policies
│   ├── *.conf.example           # Configuration templates
│   └── *.JSON                    # JSON configurations
├── dev/                          # 🔧 Development tools and utilities
│   ├── analysis/                 # Code analysis tools
│   ├── debug/                    # Debugging utilities
│   ├── demos/                    # Demonstration scripts
│   │   └── enhanced_hardening_demo.py
│   ├── performance-analysis/     # Performance testing
│   ├── reports/                  # Development reports
│   │   ├── dangerous_parameter_removal_report.py
│   │   └── security_fix_summary.py
│   ├── security-tools/           # Security testing tools
│   │   ├── fix_security_issues.py
│   │   ├── simple_security_fix.py
│   │   ├── validate_removal.py
│   │   └── verify_security_fixes.py
│   ├── test-scripts/             # Test automation
│   ├── testing/                  # Testing utilities
│   │   └── test_enhanced_hardening.py
│   └── ...
├── docs/                         # 📚 Documentation
│   ├── deployment/               # Deployment guides
│   ├── developer/                # Developer documentation
│   ├── implementation/           # Implementation details
│   ├── maintenance/              # Maintenance guides
│   ├── project/                  # Project documentation
│   ├── releases/                 # Release notes
│   ├── reports/                  # Generated reports
│   │   └── ENHANCED_HARDENING_REPORT.md
│   ├── screenshots/              # Application screenshots
│   ├── user/                     # User documentation
│   └── PROJECT_STRUCTURE.md     # This file
├── packaging/                    # 📦 Packaging files
│   ├── flatpak/                  # Flatpak packaging
│   └── icons/                    # Application icons
├── scripts/                      # 🔧 Utility scripts
│   ├── build/                    # Build scripts
│   ├── maintenance/              # Maintenance scripts
│   ├── security/                 # Security scripts
│   ├── setup/                    # Setup scripts
│   ├── utils/                    # Utility scripts
│   ├── check-organization.py     # Repository organization checker
│   └── ...
├── tests/                        # 🧪 Unit and integration tests
│   ├── **init**.py
│   ├── conftest.py               # Test configuration
│   ├── test_gui.py               # GUI tests
│   ├── test_implementation.py    # Implementation tests
│   └── test_monitoring.py        # Monitoring tests
├── tools/                        # 🛠️ External tools
│   └── flatpak-pip-generator     # Flatpak dependency generator
├── .GitHub/                      # 🔄 GitHub workflows
├── .venv/                        # 🐍 Python virtual environment
├── CHANGELOG.md                  # 📝 Change log
├── LICENSE                       # 📄 License file
├── Makefile                      # 🔨 Build automation
├── README.md                     # 📖 Main documentation
├── requirements.txt              # 📋 Production dependencies
├── requirements-dev.txt          # 📋 Development dependencies
├── run.sh                        # 🚀 Application launcher
└── VERSION                       # 🏷️ Version file
```

## 🎯 Organization Principles

### Core Application (`app/`)

- **Purpose**: Production application code only
- **Structure**: Modular organization by functionality
- **Rules**: No temporary files, demos, or development tools

### Development (`dev/`)

- **Purpose**: Development tools, utilities, and experimental code
- **Structure**: Organized by tool type and purpose
- **Rules**: All development scripts and tools go here

### Documentation (`docs/`)

- **Purpose**: All project documentation
- **Structure**: Organized by audience and document type
- **Rules**: Generated reports and documentation only

### Configuration (`config/`)

- **Purpose**: Configuration files and templates
- **Structure**: Files organized by type and usage
- **Rules**: Production configuration only

### Testing (`tests/`)

- **Purpose**: Formal unit and integration tests
- **Structure**: Mirror the `app/` structure
- **Rules**: Only pytest-compatible test files

## 🚫 Anti-Patterns (What NOT to do)

- ❌ Don't put temporary files in the root directory
- ❌ Don't mix development tools with production code
- ❌ Don't put test files in the root directory
- ❌ Don't create nested demo/script directories in `app/`
- ❌ Don't put configuration files in random locations

## ✅ Best Practices

- ✅ Use descriptive directory names
- ✅ Keep related files together
- ✅ Separate production code from development tools
- ✅ Use clear file naming conventions
- ✅ Add `**init**.py` files to Python packages
- ✅ Document the purpose of each directory

## 🔧 Maintenance

Run the organization checker regularly:

```bash
Python scripts/check-organization.py
```

This will identify any organizational issues and suggest fixes.
