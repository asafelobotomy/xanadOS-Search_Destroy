# 🔍 S&D - Search & Destroy

<div align="center">

![S&D Logo](icons/org.xanados.SearchAndDestroy.png)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](CHANGELOG.md)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/asafelobotomy/xanadOS-Search_Destroy/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13.5-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-40%20passed-brightgreen.svg)](#testing)

**A modern graphical user interface (GUI) for ClamAV antivirus scanning, designed for the xanadOS operating system (WIP).**

S&D (Search & Destroy) provides a user-friendly interface to the powerful ClamAV antivirus engine, enabling easy virus scanning, quarantine management, and threat reporting for Linux systems.

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔍 **Scanning & Detection**
- 🔍 **Full System Scanning** - Comprehensive file system scanning with ClamAV integration
- 🔄 **Real-time Monitoring** - Automatic file system watching and background scanning
- 🎯 **Smart Priority Scanning** - Event-driven scanning with configurable priorities
- ⏱️ **Scheduled Scanning** - Automated daily, weekly, and monthly scan scheduling

</td>
<td width="50%">

### 🛡️ **Security & Management**
- 🔒 **Quarantine Management** - Safe isolation and restoration of infected files
- 🛡️ **Security Validation** - Input validation and privilege escalation protection
- 🔔 **System Tray Integration** - Background operation with notification support
- 📦 **Flatpak Distribution** - Secure sandboxed application packaging

</td>
</tr>
<tr>
<td width="50%">

### 📊 **Reporting & Analysis**
- 📊 **Advanced Reporting** - Detailed scan reports with threat analysis and export options
- 📋 **Multi-format Export** - Reports in JSON, CSV, and HTML formats
- 📈 **Performance Monitoring** - Memory optimization and UI responsiveness tracking

</td>
<td width="50%">

### 🎨 **User Experience**
- 🌙 **Dark/Light Themes** - Modern UI with theme switching support
- 🚀 **Optimized Performance** - Smart memory management and responsive UI
- 📱 **Intuitive Interface** - User-friendly design with advanced features

</td>
</tr>
</table>

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Build and install (Flatpak - Recommended)
./scripts/prepare-build.sh
make build-flatpak
make install-flatpak
make run-flatpak
```

**Or run directly:**
```bash
./run.sh
```

---

## 🔧 Installation

### 📋 Prerequisites

<table>
<tr>
<td width="30%"><strong>System Requirements</strong></td>
<td width="70%">Linux-based system (designed for xanadOS, tested on Ubuntu/Debian)</td>
</tr>
<tr>
<td><strong>ClamAV Engine</strong></td>
<td><code>sudo apt install clamav clamav-daemon</code></td>
</tr>
<tr>
<td><strong>Python Version</strong></td>
<td>Python 3.10+ (tested with Python 3.13.5)</td>
</tr>
<tr>
<td><strong>GUI Framework</strong></td>
<td>PyQt6 for GUI framework (<code>pip install PyQt6>=6.5.0</code>)</td>
</tr>
<tr>
<td><strong>File Monitoring</strong></td>
<td>inotify for real-time file monitoring (<code>pip install inotify>=0.2.0</code>)</td>
</tr>
</table>

### 🛠️ Installation Methods

<details>
<summary><strong>📦 Method 1: Flatpak Installation (Recommended)</strong></summary>

```bash
# Build and install via Flatpak
./scripts/prepare-build.sh
make build-flatpak
make install-flatpak
make run-flatpak
```

**Advantages:**
- ✅ Sandboxed security
- ✅ Automatic dependency management
- ✅ System integration
- ✅ Easy updates

</details>

<details>
<summary><strong>🐍 Method 2: Virtual Environment (Development)</strong></summary>

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and run
pip install -r requirements.txt
python app/main.py
```

**Advantages:**
- ✅ Isolated environment
- ✅ Development-friendly
- ✅ Easy dependency management

</details>

<details>
<summary><strong>⚡ Method 3: Quick Setup Script</strong></summary>

```bash
# Clone repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Automated setup
./scripts/prepare-build.sh

# Install dependencies
/home/vm/Documents/xanadOS-Search_Destroy/.venv/bin/python -m pip install -r requirements.txt

# Run application
./run.sh
```

</details>

<details>
<summary><strong>🌐 Method 4: System-wide Installation</strong></summary>

```bash
# System-wide installation (not recommended for production)
sudo pip install -r requirements.txt
python app/main.py
```

**⚠️ Note:** Only recommended for testing environments.

</details>

<details>
<summary><strong>🔧 Method 5: Development Mode</strong></summary>

```bash
./scripts/prepare-build.sh  # Sets up development environment
./scripts/activate.sh       # Activates virtual environment
python app/main.py          # Run in development mode
```

**Advantages:**
- ✅ Development tools enabled
- ✅ Debug logging
- ✅ Hot reloading

</details>

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| 📖 **[Complete Documentation](docs/README.md)** | Full project overview and features |
| 🔨 **[Build Instructions](docs/BUILD.md)** | Detailed build and installation guide |
| 📋 **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** | Technical implementation details |
| 📊 **[Build Status](docs/PRE_BUILD_SUMMARY.md)** | Current build readiness status |

---

## 📂 Project Structure

```text
📁 xanadOS-Search_Destroy/
├── 📂 app/              # Main application code (11,030+ lines)
│   ├── 📂 core/         # Core functionality (scanning, security, performance)
│   │   ├── 🔍 file_scanner.py         # Core scanning engine
│   │   ├── 🛡️ clamav_wrapper.py       # ClamAV Python interface
│   │   ├── ⚡ async_scanner.py        # Async scanning operations
│   │   ├── 💾 memory_optimizer.py     # Memory usage optimization
│   │   ├── 📊 database_optimizer.py   # Database performance tuning
│   │   ├── 🎯 ui_responsiveness.py    # UI performance monitoring
│   │   ├── 🔒 input_validation.py     # Input sanitization
│   │   ├── 🌐 network_security.py     # Network security measures
│   │   └── 🔐 privilege_escalation.py # Privilege management
│   ├── 📂 gui/          # PyQt6 user interface components
│   │   ├── 🖥️ main_window.py          # Main application window
│   │   ├── ⚙️ scan_dialog.py          # Advanced scan configuration
│   │   ├── 🔄 scan_thread.py          # Threaded scanning operations
│   │   └── 🛠️ settings_dialog.py      # Application settings
│   ├── 📂 monitoring/   # Real-time file system monitoring
│   │   ├── 👁️ real_time_monitor.py    # Main monitoring coordinator
│   │   ├── 📁 file_watcher.py         # inotify-based file watching
│   │   ├── ⚡ event_processor.py      # Event filtering and processing
│   │   └── 🔄 background_scanner.py   # Background scanning tasks
│   ├── 📂 utils/        # Utility functions and configuration
│   │   ├── ⚙️ config.py               # Configuration management
│   │   └── 📄 scan_reports.py         # Report generation and export
│   └── 🚀 main.py       # Application entry point
├── 📦 packaging/        # Distribution and packaging files
├── 📊 data/             # Runtime data directories
├── 🧪 tests/            # Comprehensive test suite (177 test files)
├── 📚 docs/             # Documentation and guides
├── 🔧 scripts/          # Build and utility scripts
└── ⚙️ config/           # Configuration files and policies
```

---

## 🛠️ Development Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| 🚀 `run.sh` | Main application launcher | `./run.sh` |
| 🔧 `scripts/prepare-build.sh` | Build environment setup | `./scripts/prepare-build.sh` |
| ✅ `scripts/verify-build.sh` | Build verification | `./scripts/verify-build.sh` |
| 🐍 `scripts/activate.sh` | Virtual environment activation | `./scripts/activate.sh` |
| 🔒 `scripts/setup-security.sh` | Security configuration | `./scripts/setup-security.sh` |

---

## 🏗️ Core Architecture

### 🔄 Real-time Monitoring System
- **File System Watcher**: Uses inotify for efficient file system event detection
- **Event Processing**: Intelligent filtering and prioritization of file system events
- **Background Scanner**: Multi-threaded background scanning with priority queues
- **Performance Monitoring**: Real-time tracking of system resources and scan performance

### 🛡️ Security Architecture
- **Input Validation**: Comprehensive path and parameter validation
- **Privilege Management**: Secure privilege escalation with proper containment
- **Network Security**: SSL/TLS configuration and secure communication protocols
- **Sandbox Compatibility**: Full Flatpak sandboxing support for enhanced security

### ⚡ Performance Optimization
- **Async Operations**: Non-blocking file operations and UI updates
- **Memory Management**: Intelligent garbage collection and memory optimization
- **Database Optimization**: Efficient SQLite operations with proper indexing
- **UI Responsiveness**: Throttled updates and background processing for smooth UX

---

## 🧪 Testing

<div align="center">

**📊 Test Statistics**
```
177 Test Files | 40 Tests Passed | 2 Skipped | 95.2% Success Rate
```

</div>

### Test Categories
- 🖥️ **GUI Components** - Interface and user interaction testing
- 👁️ **Monitoring Systems** - Real-time file system monitoring
- ⚡ **Performance** - Memory usage, scan speed, UI responsiveness
- 🔒 **Security** - Input validation, privilege management

### Running Tests

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run specific categories
.venv/bin/python -m pytest tests/test_gui.py -v
.venv/bin/python -m pytest tests/test_monitoring.py -v
.venv/bin/python -m pytest tests/test_performance.py -v
```

---

## 📊 Performance Metrics

<table>
<tr>
<td width="50%">

### 🚀 **Speed & Efficiency**
- **Scan Rate**: 1,000-5,000 files/minute
- **Memory Usage**: <100MB typical
- **Event Processing**: <1ms latency
- **UI Updates**: <100ms intervals

</td>
<td width="50%">

### 🔧 **Optimization Features**
- **Multi-threading**: Configurable worker pools
- **Memory Management**: Optimized garbage collection
- **Database**: Indexed SQLite operations
- **Background Tasks**: Priority-based queuing

</td>
</tr>
</table>

---

## ⚙️ Configuration

### 📁 Configuration Files
```bash
config/
├── 🔧 default_config.json     # Default application settings
├── 👤 user_config.json        # User-specific overrides
└── 🔒 security_policy.json    # Security and scanning policies
```

### 🌐 Environment Variables
```bash
export XANADOS_SD_CONFIG_PATH="/path/to/config"     # Custom config directory
export XANADOS_SD_LOG_LEVEL="DEBUG"                # Logging verbosity
export XANADOS_SD_QUARANTINE_PATH="/secure/path"   # Quarantine location
export XANADOS_SD_TEMP_PATH="/tmp/sd_temp"         # Temporary files
```

---

## 🚀 Usage Guide

### 🔍 Quick Scanning
1. **🚀 Launch**: `./run.sh` or desktop launcher
2. **📁 Select**: Quick scan or custom path
3. **⚙️ Configure**: Scan depth, file types, threat actions
4. **👁️ Monitor**: Real-time progress and alerts
5. **📊 Review**: Detailed reports and quarantine management

### 🛡️ Real-time Protection
1. **🔄 Enable**: Activate file system monitoring
2. **📁 Configure**: Set monitored directories
3. **🛠️ Policies**: Define automatic threat responses
4. **🔔 Background**: Minimize to system tray

---

## 📄 License

<div align="center">

**GNU General Public License v3.0 (GPL-3.0)**

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

*Ensuring security software remains free and transparent*

</div>

### 🔍 Why GPL v3?
- **🔒 Copyleft Protection** - All derivatives remain open source
- **🛡️ Security Ethics** - Transparency in security tools
- **🤝 Community Development** - Collaborative improvement
- **⚖️ Patent Protection** - Explicit licensing and protection

---

## 🤝 Contributing

<div align="center">

**We welcome contributions!** 🎉

</div>

### 🚀 Getting Started
1. **🍴 Fork** the repository
2. **🌟 Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **💾 Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **📤 Push** to branch (`git push origin feature/amazing-feature`)
5. **📋 Open** a Pull Request

### 📝 Development Guidelines
This project uses **GitHub Copilot** with custom instructions for consistent development practices.

**📚 Quick Access**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Show Copilot Instructions"

See [`docs/COPILOT_SETUP.md`](docs/COPILOT_SETUP.md) for detailed guidelines.

---

## 🙏 Acknowledgments

<div align="center">

**Special thanks to:**

🦠 **ClamAV Team** - Excellent antivirus engine  
🖥️ **PyQt6** - Powerful UI framework  
🏢 **xanadOS Team** - Support and integration  

</div>

---

<div align="center">

**Made with ❤️ for the xanadOS community**

[![⭐ Star this project](https://img.shields.io/github/stars/asafelobotomy/xanadOS-Search_Destroy?style=social)](https://github.com/asafelobotomy/xanadOS-Search_Destroy)

</div>
