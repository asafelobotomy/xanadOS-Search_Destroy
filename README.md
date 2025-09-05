# �️ xanadOS Search & Destroy

[![Security Scanner](https://img.shields.io/badge/Security-A--Grade-green.svg)](docs/project/SECURITY_PERFORMANCE_REPORT.md)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-blue.svg)](https://riverbankcomputing.com/software/pyqt/)
[![ClamAV](https://img.shields.io/badge/Engine-ClamAV-red.svg)](https://www.clamav.net/)

**A comprehensive Linux security scanner and system protection suite with advanced malware
detection, real-time monitoring, and enterprise-grade security hardening.**

_Security Rating: **A- (Excellent)** | Production Ready | Current Version: 2.13.1_

## Start here

- 🛡️ **Main Application**: Run `python -m app.main` to launch the security scanner
- 📖 **Security Guide**: `docs/project/SECURITY_PERFORMANCE_REPORT.md`
- 🚀 **Quick Setup**: `./scripts/tools/git/setup-repository.sh`
- ✅ **Validate Install**: `npm run quick:validate` (requires Node.js)
- 📋 **Feature Guide**: `docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md`

## 🔧 **Development Tools** (AI-Enhanced)

This repository includes development automation tools enhanced with AI assistance:

### **Available Development Tools:**

```bash
# Repository setup and validation
./scripts/tools/git/setup-repository.sh
./scripts/tools/validation/validate-structure.sh

# Code quality and formatting
./scripts/tools/quality/check-quality.sh --fix

# Complete toolshed deployment
./scripts/tools/implement-toolshed.sh
```

**📖 Complete Tool Catalog**: `scripts/tools/README.md` (20+ tools across 6 categories)

**🤖 AI Development Assistance:**

- Chat modes in `.github/chatmodes/` for specialized development tasks
- Prompt templates in `.github/prompts/` for code review and analysis
- Development instructions in `.github/instructions/` for automated guidance

### **🔄 Version Management (Single Source of Truth)**

The project uses automated version management with the `VERSION` file as the single source:

```bash
# Update version across ALL files (package.json, pyproject.toml, README.md, etc.)
echo "2.13.0" > VERSION && npm run version:sync

# Check current version
npm run version:get

# Verify all files are synchronized
npm run version:sync:check
```

**📖 Complete Version Management Guide**: `docs/guides/VERSION-MANAGEMENT.md`

---

## 🛡️ What This Application Does

**xanadOS Search & Destroy** is a comprehensive Linux security suite that provides:

### 🔍 **Core Security Features**

- **Real-time Malware Detection** - ClamAV integration with custom signatures
- **System Integrity Monitoring** - File system and configuration change detection
- **Network Security Analysis** - Traffic monitoring and firewall management
- **Privilege Escalation Protection** - PolicyKit hardening and secure authentication
- **Vulnerability Scanning** - Automated security assessment and reporting

### 🎨 **User Interface & Experience**

- **Modern PyQt6 GUI** - Intuitive interface with professional styling
- **Quick Scan Functionality** - Fast system security assessment
- **Real-time Status Dashboard** - Live monitoring of security components
- **Comprehensive Reporting** - Detailed security analysis and recommendations
- **Settings Management** - Configurable security policies and preferences

### 🚀 **Performance & Reliability**

- **Non-invasive Monitoring** - No authentication loops or system disruption
- **Optimized Scanning** - 58% faster startup with intelligent background processing
- **Memory Efficient** - Advanced optimization for system resource management
- **Multi-threaded Architecture** - Responsive UI with background security operations

---

## 🔧 Installation & Setup

### **System Requirements**

- **Operating System:** Linux (Ubuntu 20.04+, Fedora 35+, Arch Linux)
- **Python:** 3.11 or higher
- **GUI Framework:** PyQt6
- **Security Engine:** ClamAV (for malware detection)
- **Task Scheduler:** Cron daemon (for automated scans and updates)
- **Memory:** 2GB RAM minimum, 4GB recommended

### **Quick Installation**

```bash
# Clone the repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# 🚀 RECOMMENDED: Complete setup with automatic dependency management
make setup

# Alternative: Manual Python dependency installation
pip install -e .

# Install system dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install clamav clamav-daemon cron

# Install system dependencies (Arch Linux)
sudo pacman -S clamav rkhunter cronie

# Install system dependencies (Fedora/RHEL)
sudo dnf install clamav rkhunter cronie

# Update ClamAV signatures
sudo freshclam

# Launch the application
make run  # OR: python -m app.main
```

### **🔍 Verify Installation**

After setup, verify all dependencies are working correctly:

```bash
# Validate all critical dependencies
make validate-deps

# Quick dependency check and auto-fix
./scripts/setup/ensure-deps.sh

# Test application startup
make run
```

### **Development Setup (with AI Enhancement Tools)**

```bash
# Complete development environment with all tools
make setup

# Install Node.js dependencies for validation tools
npm install

# Set up development environment with AI tools
./scripts/tools/git/setup-repository.sh

# Run validation and tests
npm run quick:validate
```

### **🛠️ Setup Options**

- **`make setup`** - Complete development environment (recommended)
- **`make install`** - Runtime dependencies only
- **`make install-dev`** - Development dependencies
- **`make install-advanced`** - Advanced features (ML, analytics, cloud)
- **`make install-all`** - Complete feature set

All critical dependencies (numpy, schedule, aiohttp, inotify, dnspython) are now included by
default! 🎉

---

## 🔒 Security Features & Certifications

### **Security Rating: A- (Excellent)**

Based on comprehensive security analysis
([full report](docs/project/SECURITY_PERFORMANCE_REPORT.md)):

**✅ Security Strengths:**

- **Command Injection Protection** - Multi-layer validation with strict whitelisting
- **Input Validation Framework** - Comprehensive sanitization system
- **Network Security** - SSL/TLS with certificate pinning
- **Privilege Escalation Hardening** - PolicyKit integration with secure validation
- **Dependency Security** - Regular scanning, zero known vulnerabilities

**🛡️ Compliance:**

- ✅ **OWASP Top 10** injection vulnerability protection
- ✅ **CWE-78** (Command Injection) prevention
- ✅ **CWE-22** (Path Traversal) blocking
- ✅ **CWE-200** (Information Disclosure) protection

## 🏗️ Repository Structure

### 📁 Core Application Components

```text
📦 xanadOS-Search_Destroy/
├── 🛡️ app/                       # Main security application
│   ├── 🎮 gui/                   # PyQt6 user interface
│   ├── � core/                  # Security engine components
│   ├── 📊 monitoring/            # Real-time system monitoring
│   └── �️ utils/                # Utility functions and helpers
├── � config/                     # Security policies and configurations
│   ├── 🔐 *.policy               # PolicyKit security rules
│   ├── ⚙️ *.ini                  # Application settings
│   └── �️ security.conf.example # Security configuration template
├── 🧪 tests/                     # Comprehensive test suite
│   ├── � security/              # Security validation tests
│   ├── 🎮 gui/                   # User interface tests
│   └── � integration/           # System integration tests
├── 📚 docs/                      # Security documentation
│   ├── 🛡️ project/              # Security analysis reports
│   ├── 📋 implementation/        # Feature implementation guides
│   └── � releases/              # Version release notes
├── 🤖 .github/                   # AI Development Tools
│   ├── � chatmodes/             # 11 specialized AI interaction modes
│   ├── 🎯 prompts/               # 7 reusable prompt templates
│   ├── 📋 instructions/          # Path-specific development guidance
│   └── ✅ validation/            # Enterprise quality assurance
└── 🛠️ scripts/tools/             # Development automation tools

```

### 🛡️ Security Engine Features

```text
app/core/
├── clamav_wrapper.py             # Malware detection engine
├── privilege_escalation.py       # Secure authentication handling
├── input_validation.py           # Command injection prevention
├── network_security.py           # SSL/TLS certificate validation
├── file_monitor.py               # Real-time file system monitoring
├── firewall_manager.py           # Network security management
├── async_scanner.py              # Multi-threaded scanning engine
└── telemetry.py                  # Security event logging

```

### � User Interface Components

```text
app/gui/
├── main_window.py                # Primary application interface
├── scan_tab.py                   # Security scanning interface
├── settings_dialog.py            # Configuration management
├── security_dashboard.py         # Real-time status display
├── report_viewer.py              # Security report visualization
└── about_dialog.py               # Application information

```

## 🚀 Quick Start

### Security Application Launch

#### Launch GUI Application

```bash
# Clone and setup
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Install dependencies
pip install -r requirements.txt

# Install ClamAV (Ubuntu/Debian)
sudo apt update && sudo apt install clamav clamav-daemon
sudo freshclam

# Launch xanadOS Search & Destroy
python -m app.main
```

#### Development Environment Setup

```bash
# Install Node.js dependencies (for AI development tools)
npm install

# Set up development environment
./scripts/tools/git/setup-repository.sh

# Run validation and quality checks
npm run quick:validate

# Launch with development logging
python -m app.main --debug
```

### 🤖 AI Development Tools

AI development tools are included for development productivity:

- **Chat Modes**: `.github/chatmodes/security.chatmode.md` for security-focused development
- **Prompt Templates**: `.github/prompts/security-review.prompt.md` for code security analysis
- **Quality Tools**: `scripts/tools/quality/check-quality.sh` for automated code review
- **Validation**: `scripts/tools/validation/validate-structure.sh` for repository compliance

---

## 📚 Documentation & Resources

### **🛡️ Security Application Documentation**

- 📋 **[Complete User Guide](docs/implementation/CONSOLIDATED_IMPLEMENTATION_GUIDE.md)** Full
  feature overview and usage instructions
- 🔒 **[Security Analysis Report](docs/project/SECURITY_PERFORMANCE_REPORT.md)** Comprehensive
  security assessment and ratings
- 🚀 **[Performance Benchmarks](docs/project/SECURITY_PERFORMANCE_REPORT.md#performance-analysis)**
  System optimization metrics
- 📈 **[Release Notes](releases/)** - Version history, features, and improvements
- 🔧 **[Development Setup](dev/README.md)** - Developer tools, testing, and contribution guide

### **🔧 Development Tools Documentation**

- 🎯 **[Model Targeting Guide](docs/guides/model-targeting-guide.md)** - AI model selection for
  development
- �️ **[Project Structure Guide](docs/guides/PROJECT_STRUCTURE.md)** - Repository organization
- 🛠️ **[Toolshed Reference](scripts/tools/README.md)** - 20+ automation and quality tools
- 📋 **[Development Instructions](.github/instructions/)** - AI guidance for coding

---

## 🎯 Usage Examples

### **Security Operations**

```bash
# Launch the main application
python -m app.main

# Quick system security scan
# (Use GUI quick scan button or future CLI implementation)

# View security reports
# (Available in GUI Reports tab)

# Update malware signatures
sudo freshclam

# Check application logs
tail -f ~/.local/share/xanadOS/logs/search_destroy.log
```

### **Development with AI Tools**

```bash
# Use security-focused chat mode for code review
# (Available in VS Code with GitHub Copilot)

# Run automated code quality checks
./scripts/tools/quality/check-quality.sh --security

# Comprehensive repository validation
./scripts/tools/validation/validate-structure.sh

# Fix code formatting issues
./scripts/tools/quality/fix-markdown.sh
```

---

## 🏆 Awards & Recognition

- **Security Rating: A- (Excellent)** - Comprehensive security analysis
- **Performance Grade: A (Excellent)** - Advanced optimization techniques
- **Code Quality: A- (Very Good)** - Well-structured, maintainable architecture
- **Industry Standards**: Exceeds typical Linux antivirus security implementations

---

## 🤝 Contributing

We welcome contributions to both the security application and the AI development tools!

### **Security Application Development**

1. Fork the repository
2. Set up development environment: `./scripts/tools/git/setup-repository.sh`
3. Run tests: `python -m pytest tests/`
4. Follow security guidelines: `.github/instructions/security.instructions.md`

### **AI Framework Enhancement**

1. Review framework documentation: `docs/guides/Copilot-INSTRUCTIONS-GUIDE.md`
2. Test with validation tools: `npm run quick:validate`
3. Follow coding standards: `.github/instructions/code-quality.instructions.md`

### **Bug Reports & Feature Requests**

- **Security Issues**: Use private security disclosure process
- **Feature Requests**: Open GitHub issue with enhancement template
- **Bug Reports**: Include system info, logs, and reproduction steps

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Security Disclaimer**: This software is provided as-is for educational and protection purposes.
Always maintain system backups and test in non-production environments first.

---

## 📞 Support & Community

- **Documentation**: Complete guides in `/docs/` directory
- **Issues**: GitHub issue tracker for bug reports and feature requests
- **Security**: Private disclosure for security vulnerabilities
- **Development**: AI-enhanced development tools in `.github/` directory

**xanadOS Search & Destroy** - Comprehensive Linux security with modern development tools. 🛡️

````bash

## Copy to VS Code settings directory

cp .GitHub/Copilot-instructions.md ~/.VS Code/Copilot-instructions.md
```text

2. **Or use VS Code command palette**:
- Open VS Code in this repository
- Press `Ctrl+Shift+P`(or`Cmd+Shift+P` on Mac)
- Type "GitHub Copilot: Add instruction file"
- Select `.GitHub/Copilot-instructions.md`

### Option 3: GitHub Codespaces (Automatic Setup)

- Click the "Open in Codespaces" button above
- Codespaces will automatically configure the GitHub Copilot instructions
- No manual setup required!

### For existing projects (copy essential files only)

```bash

## Copy essential files to current directory

curl -sSL <HTTPS://Git.io/Copilot-setup> | bash -s -- --essential-only

```text

### ✅ **Validate Setup**

```bash

## Quick lint + validation

npm run quick:validate

## Or run structure validator directly

./scripts/validation/validate-structure.sh

```text

Tip:

- In VS Code, run "Tasks: Run Task" → quick:validate
- In Codespaces, validations run fast on the prebuilt container

Tip:

- In VS Code, run “Tasks: Run Task” → quick:validate
- In Codespaces, validations run fast on the prebuilt container

### 🎯 **Start Using Chatmodes**

1. **Open VS Code** to your project directory
2. **Navigate** to `.GitHub/chatmodes/` in the Explorer
3. **Copy content** from any `.chatmode.md` file
4. **Paste into GitHub Copilot Chat** in VS Code
5. **Start developing** with enhanced AI assistance!

### Usage Examples

#### System Architecture (architect.chatmode.md)

```text
Perfect for: API design, database schema, microservices planning

```text

#### Security Analysis (security.chatmode.md)

```text
Perfect for: Vulnerability assessment, secure coding, compliance

```text

#### Code Optimization (elite-engineer.chatmode.md)

```text
Perfect for: Performance tuning, refactoring, advanced algorithms

```text

## 📚 Documentation

- 📖 [Complete Documentation](docs/README.md) — guides and references
- 🚀 [Project Structure Guide](docs/guides/PROJECT_STRUCTURE.md) — repository layout
- 🔧 [Copilot Instructions Guide](docs/guides/Copilot-INSTRUCTIONS-GUIDE.md) — setup
- 🛠️ [Toolshed Reference](docs/guides/TOOLSHED-REFERENCE.md) — tools and utilities
- 🧪 [MCP Examples Index](docs/guides/MCP-EXAMPLES.md) — offline MCP demos
- 📘 [Agent Runbooks](.GitHub/runbooks/) — step-by-step workflows

## 🏆 Enterprise Features

### Code Quality

- ✅ **ShellCheck** validation for all scripts
- ✅ **Prettier** formatting for consistent code style
- ✅ **Markdown linting** for documentation quality
- ✅ **EditorConfig** for cross-platform consistency

### Organization

- ✅ **Professional structure** following GitHub best practices
- ✅ **Archive system** for version management
- ✅ **Implementation reports** with detailed progress tracking
- ✅ **Automated validation** with 21 mandatory checks

### Model Support

- 🤖 **GPT-5** - Latest OpenAI model with advanced reasoning
- 🧠 **Claude Sonnet 4** - Anthropic's most capable model
- ⚡ **Gemini Pro** - Google's enterprise AI solution
- 🔄 **Cross-platform** compatibility

## 📊 Repository Snapshot

- Specialized chatmodes for common engineering scenarios
- Prompt templates for reusable AI interactions
- Instruction sets covering best practices and standards
- Validation and linting with automated checks
- Enterprise-grade docs with categorized reports

## 🤝 Contributing

This framework follows enterprise development standards:

1. **Code Quality**: All contributions must pass validation checks
2. **Documentation**: Updates require corresponding documentation
3. **Testing**: Changes must include appropriate test coverage
4. **Security**: OWASP Top 10 2024/2025 compliance required

## 📄 License

This project is open source and available under standard licensing terms.

---

**🎯 Ready to enhance your GitHub Copilot experience?** Start with the
[Project Structure Guide](docs/guides/PROJECT_STRUCTURE.md) or explore our
[specialized chatmodes](.GitHub/chatmodes/).
````
