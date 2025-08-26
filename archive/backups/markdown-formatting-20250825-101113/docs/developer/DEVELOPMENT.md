# Development Setup & Guide

## Quick Start

### Virtual Environment Setup

This project uses a Python virtual environment for dependency management:

```bash

## Clone and navigate to project

Git clone <HTTPS://GitHub.com/asafelobotomy/xanadOS-Search_Destroy.Git>
cd xanadOS-Search_Destroy

## Automated setup (recommended)

./scripts/prepare-build.sh

## Manual setup alternative

Python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt

## Run the application

./run.sh

## or manually: Python app/main.py

## Run tests

Python -m pytest tests/ -v
```

## Modern Development Features

### GitHub Copilot Integration

This project includes comprehensive GitHub Copilot instructions for consistent development:

- **Access Instructions**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Show Copilot Instructions"
- **Coding Standards**: Automated code formatting with Black and Flake8
- **Type Hints**: Modern Python type annotations throughout
- **Documentation**: Comprehensive docstrings and API documentation

### Build System

The project uses a modern Makefile with industry standards:

```bash

## View all available targets

make help

## Development setup

make dev-setup

## Quality assurance

make quality

## Build Flatpak

make build-flatpak

## Install and run

make install-flatpak
make run-flatpak
```

## Project Architecture

### Core Components

- **`app/core/`** - Core security functionality (11,030+ lines)
- `clamav_wrapper.py` - Enhanced ClamAV integration with daemon support
- `file_scanner.py` - Advanced scanning engine with quarantine management
- `rkhunter_wrapper.py` - RKHunter rootkit detection integration
- `firewall_detector.py` - Multi-platform firewall management
- **`app/gui/`** - PyQt6 user interface components
- `main_window.py` - Main application window with tabbed interface
- `scan_thread.py` - Non-blocking scan operations
- `settings_dialog.py` - Comprehensive settings management
- **`app/monitoring/`** - Real-time protection system
- `real_time_monitor.py` - File system monitoring coordinator
- `file_watcher.py` - inotify-based file watching
- `background_scanner.py` - Background threat scanning

### Modern Features

#### Performance Optimizations

- **ClamAV Daemon Integration**: 3-10x faster scanning
- **Smart File Filtering**: Risk-based scanning reduces overhead by 50-80%
- **Async Operations**: Non-blocking UI with background processing
- **Memory Management**: Intelligent garbage collection and optimization

#### Security Enhancements

- **Input Validation**: Comprehensive path and parameter validation
- **Privilege Management**: Secure privilege escalation with containment
- **Sandboxing**: Full Flatpak compatibility for enhanced security
- **Authentication**: Modern pkexec/ksshaskpass integration

#### Real-time Protection

- **File System Monitoring**: inotify-based event detection
- **Priority Scanning**: Event-driven scanning with priority queues
- **Background Processing**: Multi-threaded background operations
- **Performance Monitoring**: Resource usage tracking and optimization

## Directory Structure

- `app/` - Main application source code
- `tests/` - Test suite
- `docs/` - Documentation (empty, ready for future docs)
- `config/` - Configuration files (local.JSON is ignored)
- `data/logs/` - Application log files (ignored)
- `data/reports/` - Generated scan reports (ignored)
- `data/quarantine/` - Quarantined files (ignored)
- `.venv/` - Python virtual environment (ignored)
