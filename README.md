# xanadOS Search & Destroy

A comprehensive Linux security scanner and system protection suite with advanced
AI-assisted development framework.

![Dashboard](docs/screenshots/1%20-%20Dashboard.png)

## 🎯 Key Highlights

- 🔍 **Dual-Engine Scanning**: ClamAV signature detection + YARA heuristic analysis
- 🛡️ **Real-Time Protection**: Continuous file system monitoring with adaptive performance
- 📦 **Easy Installation**: Pre-built packages for RPM, DEB, and AUR distributions
- ⚡ **High Performance**: 70-80% faster with intelligent scan caching
- 🎨 **Modern Interface**: Clean PyQt6 GUI with real-time progress visualization
- 🔐 **System Hardening**: Automated security configuration and compliance checking
- 📊 **Comprehensive Reports**: Detailed security analysis with multiple export formats
- 🔄 **Auto-Updates**: Automatic virus definition updates with daemon integration

## ✨ Features

### 🔍 Malware Scanning

![Scan Interface](docs/screenshots/2-%20Scan.png)

Advanced malware detection powered by ClamAV and YARA engines:

- **Real-time file scanning** with live progress display showing file sizes
- **Multi-engine detection** combining ClamAV signature-based and YARA heuristic analysis
- **Smart scan optimization** with result caching for 70-80% performance improvement
- **Concurrent scan prevention** to avoid conflicts between scan types
- **Comprehensive scan types**: Quick Scan, Full System Scan, Custom Directory Scan
- **Quarantine management** for detected threats with secure isolation

### 🛡️ Real-Time Protection

![Real-Time Protection](docs/screenshots/3%20-%20Protection.png)

Advanced real-time file system monitoring and threat prevention:

- **Intelligent file system watching** using modern watchdog library
- **Automatic threat detection** for new and modified files
- **Adaptive performance** with system load monitoring and throttling
- **Background scanning** with 2-8 adaptive worker threads
- **RKHunter integration** for rootkit detection and system integrity checks
- **Automated responses** to detected threats with configurable actions

### 🔐 System Hardening

![System Hardening](docs/screenshots/4%20-%20Hardening.png)

Proactive security configuration and system hardening:

- **Security policy enforcement** with best practice configurations
- **Permission management** for critical system files and directories
- **Service hardening** with systemd security features
- **Firewall integration** with automatic security rule management
- **Compliance checking** against security standards (CIS, NIST)
- **Automated remediation** for common security vulnerabilities

### 📊 Security Reports

![Security Reports](docs/screenshots/5%20-%20Reports.png)

Comprehensive security analysis and reporting:

- **Detailed scan results** with threat categorization and risk assessment
- **Historical tracking** of security events and scan history
- **Performance metrics** showing scan efficiency and resource usage
- **Compliance reports** for security audits and documentation
- **Export capabilities** in multiple formats (PDF, HTML, JSON)
- **Trend analysis** for identifying security patterns over time

### ⚙️ Configuration Management

![Settings](docs/screenshots/6%20-%20Settings.png)

Flexible configuration for customized security policies:

- **Scan scheduling** with cron-like automation for regular security checks
- **Exclusion rules** for trusted files and directories
- **Update management** for virus definitions with daemon integration
- **Performance tuning** to balance security and system resources
- **Notification settings** for security alerts and scan completion
- **Integration options** with external security tools and services

## 💻 System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Fedora 36+, Arch Linux, or compatible)
- **Python**: 3.13 or higher
- **Memory**: 2GB RAM minimum (4GB recommended)
- **Storage**: 500MB for application + space for quarantine
- **Dependencies**: ClamAV, RKHunter, PyQt6
- **Permissions**: sudo access for system-level security operations

## 🚀 Quick Start

### Installation

#### Using Pre-built Packages

**Fedora/RHEL/CentOS:**

```bash
sudo dnf install xanados-search-destroy-*.rpm
```

**Debian/Ubuntu/Mint:**

```bash
sudo apt install ./xanados-search-destroy_*.deb
```

**Arch Linux/Manjaro:**

```bash
# Install from AUR
yay -S xanados-search-destroy
# Or build manually
makepkg -si
```

#### From Source

```bash
# Clone repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# One-command setup (installs everything)
make setup

# Launch application
make run
# Or: python -m app.main
```

### First Run

1. **Update Virus Definitions**: Click "Update Definitions" to download latest malware signatures
2. **Configure Settings**: Review and customize security settings in the Settings tab
3. **Run Initial Scan**: Perform a Quick Scan to establish baseline security status
4. **Enable Real-Time Protection**: Activate continuous monitoring for ongoing protection

For complete documentation, visit our [Documentation Hub](docs/README.md).

### Security Application

- **Launch Guide**: [Complete Implementation Guide](docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md)
- **Security Analysis**: [Security & Performance Report](docs/project/SECURITY_PERFORMANCE_REPORT.md)
- **Setup Instructions**: [Setup Guide](docs/guides/SETUP.md)
- **Packaging Guide**: [Distribution Packages](packaging/PACKAGING_GUIDE.md)

### AI Development Framework

- **Chat Modes**: [AI Interaction Modes](.github/chatmodes/)
- **Development Tools**: [AI Development Instructions](.github/instructions/)
- **Prompt Templates**: [Reusable Prompts](.github/prompts/)

## 📁 Project Structure

```text
├── app/                    # Main application code
├── docs/                   # Complete documentation
├── scripts/                # Build and utility scripts
├── config/                 # Configuration files
├── tests/                  # Test suites
├── packaging/              # Distribution packages
└── examples/               # Examples and templates
```

## 🛠️ Development

```bash
# Setup development environment
./scripts/setup.sh

# Run tests
./scripts/tools/testing/run-tests.sh

# Validate project structure
./scripts/tools/validation/validate-structure.sh
```

## 📖 Documentation

All documentation is organized in the [`docs/`](docs/) directory:

- [User Guides](docs/user/) - End-user documentation
- [Developer Guides](docs/developer/) - Development instructions
- [API Reference](docs/api/) - Technical specifications
- [Security Documentation](docs/security/) - Security practices
- [Implementation Reports](docs/implementation/) - Feature documentation

## 🤝 Contributing

Please read our [Contributing Guide](CONTRIBUTING.md) for development standards and practices.

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
