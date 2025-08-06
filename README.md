# S&D - Search & Destroy

![S&D Logo](icons/org.xanados.SearchAn3. **Install dependencies**

   ```bash
   /home/vm/Documents/xanadOS-Search_Destroy/.venv/bin/python -m pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   ./run.sh
   ```

## Advanced Installation Options

### Option 1: Virtual Environment (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

### Option 2: System-wide Installation

```bash
sudo pip install -r requirements.txt
python app/main.py
```

### Option 3: Development Mode

```bash
./scripts/prepare-build.sh  # Sets up development environment
./scripts/activate.sh       # Activates virtual environment
python app/main.py          # Run in development mode
```roy.png)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](CHANGELOG.md)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/asafelobotomy/xanadOS-Search_Destroy/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13.5-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-40%20passed-brightgreen.svg)](#testing)

> A modern graphical user interface (GUI) for ClamAV antivirus scanning, designed for the xanadOS operating system (WIP).

S&D (Search & Destroy) provides a user-friendly interface to the powerful ClamAV antivirus engine, enabling easy virus scanning, quarantine management, and threat reporting for Linux systems.

## ✨ Features

- 🔍 **Full System Scanning** - Comprehensive file system scanning with ClamAV integration
- 🔄 **Real-time Monitoring** - Automatic file system watching and background scanning
- 📊 **Advanced Reporting** - Detailed scan reports with threat analysis and export options
- 🔒 **Quarantine Management** - Safe isolation and restoration of infected files  
- ⏱️ **Scheduled Scanning** - Automated daily, weekly, and monthly scan scheduling
- 📋 **Multi-format Export** - Reports in JSON, CSV, and HTML formats
- 🔔 **System Tray Integration** - Background operation with notification support
- 🎯 **Smart Priority Scanning** - Event-driven scanning with configurable priorities
- 🛡️ **Security Validation** - Input validation and privilege escalation protection
- 📈 **Performance Monitoring** - Memory optimization and UI responsiveness tracking
- 🌙 **Dark/Light Themes** - Modern UI with theme switching support
- 📦 **Flatpak Distribution** - Secure sandboxed application packaging

## 🚀 Quick Start

```bash
# Build and install
./scripts/prepare-build.sh
make build-flatpak
make install-flatpak
make run-flatpak
```

## 🔧 Getting Started

### Prerequisites

- **Linux-based system** (designed for xanadOS, tested on Ubuntu/Debian)
- **ClamAV antivirus engine** (`sudo apt install clamav clamav-daemon`)
- **Python 3.10+** (tested with Python 3.13.5)
- **PyQt6** for GUI framework (`pip install PyQt6>=6.5.0`)
- **inotify** for real-time file monitoring (`pip install inotify>=0.2.0`)

### Installation from Source

1. Clone the repository

   ```bash
   git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
   cd xanadOS-Search_Destroy
   ```

2. Set up the environment

   ```bash
   ./scripts/prepare-build.sh
   ```

3. Run the application

   ```bash
   ./run.sh
   ```

## 📚 Documentation

- 📖 **[Complete Documentation](docs/README.md)** - Full project overview and features
- 🔨 **[Build Instructions](docs/BUILD.md)** - Detailed build and installation guide
- 📋 **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- 📊 **[Build Status](docs/PRE_BUILD_SUMMARY.md)** - Current build readiness status

## 📂 Project Structure

```text
├── app/              # Main application code (11,030+ lines)
│   ├── core/         # Core functionality (scanning, security, performance)
│   │   ├── file_scanner.py         # Core scanning engine
│   │   ├── clamav_wrapper.py       # ClamAV Python interface
│   │   ├── async_scanner.py        # Async scanning operations
│   │   ├── memory_optimizer.py     # Memory usage optimization
│   │   ├── database_optimizer.py   # Database performance tuning
│   │   ├── ui_responsiveness.py    # UI performance monitoring
│   │   ├── input_validation.py     # Input sanitization
│   │   ├── network_security.py     # Network security measures
│   │   └── privilege_escalation.py # Privilege management
│   ├── gui/          # PyQt6 user interface components
│   │   ├── main_window.py          # Main application window
│   │   ├── scan_dialog.py          # Advanced scan configuration
│   │   ├── scan_thread.py          # Threaded scanning operations
│   │   └── settings_dialog.py      # Application settings
│   ├── monitoring/   # Real-time file system monitoring
│   │   ├── real_time_monitor.py    # Main monitoring coordinator
│   │   ├── file_watcher.py         # inotify-based file watching
│   │   ├── event_processor.py      # Event filtering and processing
│   │   └── background_scanner.py   # Background scanning tasks
│   ├── utils/        # Utility functions and configuration
│   │   ├── config.py               # Configuration management
│   │   └── scan_reports.py         # Report generation and export
│   └── main.py       # Application entry point
├── packaging/        # Distribution and packaging files
│   ├── flatpak/      # Flatpak packaging configuration
│   ├── desktop/      # Desktop integration files
│   └── icons/        # Application icons and branding
├── data/             # Runtime data directories
│   ├── logs/         # Application logs
│   ├── quarantine/   # Quarantine storage
│   ├── reports/      # Generated scan reports
│   └── cache/        # Cache files
├── tests/            # Comprehensive test suite (177 test files)
├── docs/             # Documentation and guides
├── scripts/          # Build and utility scripts
└── config/           # Configuration files and policies
```

## 🛠️ Scripts

- **`run.sh`** - Main application launcher with environment setup
- **`scripts/prepare-build.sh`** - Automated build environment preparation
- **`scripts/verify-build.sh`** - Build verification and dependency checking
- **`scripts/activate.sh`** - Virtual environment activation
- **`scripts/setup-security.sh`** - Security configuration and permissions

## 🔧 Core Components

### Real-time Monitoring System

The application features a sophisticated real-time monitoring system:

- **File System Watcher**: Uses inotify for efficient file system event detection
- **Event Processing**: Intelligent filtering and prioritization of file system events
- **Background Scanner**: Multi-threaded background scanning with priority queues
- **Performance Monitoring**: Real-time tracking of system resources and scan performance

### Security Architecture

- **Input Validation**: Comprehensive path and parameter validation
- **Privilege Management**: Secure privilege escalation with proper containment
- **Network Security**: SSL/TLS configuration and secure communication protocols
- **Sandbox Compatibility**: Full Flatpak sandboxing support for enhanced security

### Performance Optimization

- **Async Operations**: Non-blocking file operations and UI updates
- **Memory Management**: Intelligent garbage collection and memory optimization
- **Database Optimization**: Efficient SQLite operations with proper indexing
- **UI Responsiveness**: Throttled updates and background processing for smooth UX

## 📄 License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0). See the [LICENSE](LICENSE) file for the complete license text.

### Why GPL v3?

- **Copyleft Protection**: Ensures all derivative works remain free and open source
- **Security Software Ethics**: Promotes transparency in security tools
- **Community Contribution**: Encourages collaborative development and improvement
- **Patent Protection**: Provides explicit patent licensing and protection

## 🧪 Testing

The project includes a comprehensive test suite ensuring reliability and performance:

- **Test Coverage**: 177 test files covering all major components
- **Success Rate**: 40 tests passed, 2 skipped (95.2% success rate)  
- **Test Categories**: GUI components, monitoring systems, performance optimization, security validation
- **Continuous Integration**: Automated testing with pytest framework
- **Performance Benchmarks**: Memory usage, scan speed, and UI responsiveness metrics

### Running Tests

```bash
# Run all tests
/home/vm/Documents/xanadOS-Search_Destroy/.venv/bin/python -m pytest tests/ -v

# Run specific test categories
/home/vm/Documents/xanadOS-Search_Destroy/.venv/bin/python -m pytest tests/test_gui.py -v
/home/vm/Documents/xanadOS-Search_Destroy/.venv/bin/python -m pytest tests/test_monitoring.py -v
/home/vm/Documents/xanadOS-Search_Destroy/.venv/bin/python -m pytest tests/test_performance.py -v
```

## 📊 Performance Statistics

Based on current testing and optimization:

- **Scan Performance**: ~1,000-5,000 files/minute (depending on file size and type)
- **Memory Efficiency**: <100MB typical usage, optimized garbage collection
- **Real-time Monitoring**: <1ms file event processing latency
- **Background Scanning**: Multi-threaded with configurable worker pools
- **UI Responsiveness**: <100ms typical UI update intervals
- **Database Operations**: Optimized SQLite with indexing and batching

## ⚙️ Configuration

### Application Settings

The application supports extensive configuration through JSON config files:

```bash
config/
├── default_config.json     # Default application settings
├── user_config.json        # User-specific overrides
└── security_policy.json    # Security and scanning policies
```

### Key Configuration Options

- **Scan Settings**: File type filters, scan depth, timeout values
- **Monitoring**: Real-time monitoring paths and event filters  
- **Performance**: Thread pool sizes, memory limits, cache settings
- **Security**: Quarantine policies, privilege escalation controls
- **UI/UX**: Theme selection, notification preferences, update intervals

### Environment Variables

```bash
export XANADOS_SD_CONFIG_PATH="/path/to/config"     # Custom config directory
export XANADOS_SD_LOG_LEVEL="DEBUG"                # Logging verbosity
export XANADOS_SD_QUARANTINE_PATH="/secure/path"   # Quarantine location
export XANADOS_SD_TEMP_PATH="/tmp/sd_temp"         # Temporary files
```

## 🚀 Usage Guide

### Quick Start Scanning

1. **Launch Application**: `./run.sh` or use the desktop launcher
2. **Select Scan Type**: Quick scan (home directory) or custom path selection
3. **Configure Options**: Choose scan depth, file types, and action on threats
4. **Monitor Progress**: Real-time progress updates and threat detection alerts
5. **Review Results**: Detailed reports with export options and quarantine management

### Real-time Protection

1. **Enable Monitoring**: Activate real-time file system monitoring
2. **Configure Paths**: Set monitored directories (Downloads, Documents, etc.)
3. **Set Policies**: Define automatic actions for different threat levels
4. **Background Operation**: Minimize to system tray for continuous protection

### Advanced Features

- **Scheduled Scans**: Set up daily/weekly/monthly automated scanning
- **Custom Scan Profiles**: Save and reuse specific scan configurations  
- **Report Management**: Export, archive, and analyze historical scan data
- **Integration**: Command-line interface for scripting and automation

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

This project uses GitHub Copilot with custom instructions for consistent development practices. See [`docs/COPILOT_SETUP.md`](docs/COPILOT_SETUP.md) for details on:

- Coding standards and best practices
- Project structure requirements
- How to configure Copilot for this project
- Quick access to development guidelines

**Quick Access**: Run `Ctrl+Shift+P` → "Tasks: Run Task" → "Show Copilot Instructions"

## 🙏 Acknowledgments

- ClamAV team for their excellent antivirus engine
- PyQt6 for providing a powerful UI framework
- xanadOS team for support and integration
