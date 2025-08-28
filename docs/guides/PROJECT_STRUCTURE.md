# Project Structure

This document outlines the organized repository structure for xanadOS Search & Destroy
with integrated AI development tools.

## 📁 Repository Organization

```text
xanadOS-Search_Destroy/
├── �️ app/                       # Main security application
│   ├── � __init__.py            # Package initialization
│   ├── � main.py                # Application entry point
│   ├── � core/                  # Security engine components
│   │   ├── 📄 clamav_wrapper.py  # Malware detection engine
│   │   ├── � privilege_escalation.py # Secure authentication
│   │   ├── 📄 input_validation.py # Command injection prevention
│   │   ├── � network_security.py # SSL/TLS certificate validation
│   │   ├── 📄 file_monitor.py    # Real-time file monitoring
│   │   └── 📄 ...                # Additional security modules
│   ├── 🎮 gui/                   # PyQt6 user interface
│   │   ├── 📄 main_window.py     # Primary application interface
│   │   ├── � scan_tab.py        # Security scanning interface
│   │   ├── 📄 settings_dialog.py # Configuration management
│   │   └── 📄 ...                # Additional GUI components
│   ├── � monitoring/            # Real-time system monitoring
│   └── �️ utils/                # Utility functions and helpers
├── � config/                    # Security policies and configurations
│   ├── � *.policy              # PolicyKit security rules
│   ├── ⚙️ *.ini                 # Application configuration files
│   └── �️ security.conf.example # Security configuration template
├── 🧪 tests/                    # Comprehensive test suite
│   ├── � security/             # Security validation tests
│   ├── 🎮 gui/                  # User interface tests
│   └── � integration/          # System integration tests
├── � docs/                     # Documentation system
│   ├── 📄 README.md             # Documentation index
│   ├── �️ project/             # Security application documentation
│   │   └── 📄 SECURITY_PERFORMANCE_REPORT.md # Security analysis
│   ├── � implementation/       # Feature implementation guides
│   │   ├── � CONSOLIDATED_IMPLEMENTATION_GUIDE.md # Complete overview
│   │   └── � SECURITY_IMPROVEMENTS.md # Enhancement reports
│   ├── � releases/            # Version release notes
│   └── � guides/              # AI development framework guides
│       ├── 📄 Copilot-INSTRUCTIONS-GUIDE.md # AI framework guide
│       ├── 📄 PROJECT_STRUCTURE.md # This document
│       └── 📄 TOOLSHED-REFERENCE.md # Development tools
├── 📄 .gitignore                 # Git ignore patterns
├── 📄 CONTRIBUTING.md             # Contribution guidelines
├── 📄 IMPLEMENTATION_SUMMARY.md   # Executive implementation summary
├── 🤖 .github/                   # AI Development Tools
│   ├── 💬 chatmodes/             # 11 specialized AI interaction modes
│   ├── 🎯 prompts/               # 7 reusable prompt templates
│   ├── � instructions/          # Path-specific development guidance
│   ├── ✅ validation/            # Enterprise quality assurance
│   ├── 🔧 workflows/             # GitHub Actions CI/CD
│   └── �📄 copilot-instructions.md # Main AI development guidance
├── 🛠️ scripts/                  # Development automation tools
│   └── 🔧 tools/                # Comprehensive toolshed (20+ tools)
│       ├── 🔍 validation/       # Repository validation scripts
│       ├── 🎨 quality/          # Code quality and formatting tools
│       ├── 📚 documentation/    # Documentation generation
│       └── 🔐 git/              # Git workflow automation
├── 📦 packaging/                # Application packaging and distribution
│   ├── 📦 flatpak/             # Flatpak packaging configuration
│   └── 🎨 icons/               # Application icons and assets
├── 📈 releases/                 # Version release documentation
├── 🗄️ archive/                  # Historical files and backups
├── 💻 dev/                      # Development tools and testing
├── 🧪 examples/                 # Usage examples and templates
├── 📄 README.md                 # Main project documentation
├── 📄 package.json              # Node.js dependencies (for dev tools)
├── 📄 pyproject.toml            # Python project configuration
├── 📄 requirements.txt          # Python dependencies
└── 📄 VERSION                   # Current application version
```

## 🎯 Directory Purposes

### 🛡️ Security Application Core

- **`app/`** - Main security application with PyQt6 GUI and security engines
- **`config/`** - Security policies, PolicyKit rules, and application settings
- **`tests/`** - Comprehensive security and functionality testing suite
- **`packaging/`** - Distribution packages (Flatpak, icons, etc.)

### 🤖 AI Development Framework

- **`.github/`** - Complete GitHub Copilot enhancement system
- **`scripts/tools/`** - 20+ automation tools for development workflow
- **`docs/guides/`** - AI framework documentation and guides

### 📚 Documentation Structure

- **`docs/project/`** - Security application analysis and performance reports
- **`docs/implementation/`** - Feature implementation guides and security improvements
- **`docs/releases/`** - Version history and release notes
- **`docs/guides/`** - AI development framework documentation

## 📋 File Naming Conventions

### Security Application Files

- **Python Modules**: `snake_case.py` (e.g., `clamav_wrapper.py`)
- **GUI Components**: `descriptive_name.py` (e.g., `main_window.py`)
- **Config Files**: `descriptive.extension` (e.g., `security.conf.example`)
- **Policy Files**: `*.policy` (e.g., `io.github.asafelobotomy.searchanddestroy.policy`)

### AI Framework Files

- **Chat Modes**: `*.chatmode.md` (e.g., `security.chatmode.md`)
- **Prompts**: `*.prompt.md` (e.g., `security-review.prompt.md`)
- **Instructions**: `*.instructions.md` (e.g., `security.instructions.md`)

### Documentation Files

- **Security Reports**: `SECURITY_*.md` (e.g., `SECURITY_PERFORMANCE_REPORT.md`)
- **Implementation Guides**: `*_GUIDE.md` (e.g., `CONSOLIDATED_IMPLEMENTATION_GUIDE.md`)
- **Release Notes**: `v*.md` or `RELEASE_*.md`

## 🔧 Configuration Files

### Python Application

- **`pyproject.toml`** - Modern Python project configuration
- **`requirements.txt`** - Production dependencies
- **`requirements-dev.txt`** - Development dependencies
- **`VERSION`** - Current application version

### Development Tools

- **`package.json`** - Node.js dependencies for development tools
- **`.editorconfig`** - Cross-editor consistency
- **`.gitattributes`** - Git behavior configuration
- **`.gitignore`** - Version control exclusions

## 🚀 Development Workflow

### Security Application Development

1. **Main Application**: Modify files in `app/` directory
2. **Testing**: Run tests from `tests/` directory
3. **Configuration**: Update policies in `config/` directory
4. **Documentation**: Update security docs in `docs/project/`

### AI-Enhanced Development

1. **Chat Modes**: Use `.github/chatmodes/security.chatmode.md` for security development
2. **Quality Tools**: Run `scripts/tools/quality/check-quality.sh` for code review
3. **Validation**: Use `scripts/tools/validation/validate-structure.sh` for compliance
4. **Documentation**: Auto-generate docs with `scripts/tools/documentation/generate-docs.sh`

## 📖 Navigation Guide

| Need | Location | Key Files |
|------|----------|-----------|
| **Launch App** | `app/main.py` | Main application entry point |
| **Security Guide** | `docs/project/` | `SECURITY_PERFORMANCE_REPORT.md` |
| **Implementation** | `docs/implementation/` | `CONSOLIDATED_IMPLEMENTATION_GUIDE.md` |
| **AI Tools** | `.github/chatmodes/` | `security.chatmode.md`, `testing.chatmode.md` |
| **Development** | `scripts/tools/` | Quality, validation, and automation tools |
| **Configuration** | `config/` | Security policies and application settings |

## 🎨 Benefits of This Organization

### Security Application Benefits

- ✅ Clear separation of security components
- ✅ Comprehensive security policy organization
- ✅ Professional GUI and core module structure
- ✅ Extensive testing and validation framework

### AI Development Benefits

- ✅ Sophisticated development assistance with specialized chat modes
- ✅ Automated quality assurance and validation tools
- ✅ Comprehensive documentation generation and maintenance
- ✅ Enterprise-grade development workflow enhancement

### Overall Maintainability

- ✅ Dual-purpose design: security application + development framework
- ✅ Professional organization following GitHub conventions
- ✅ Scalable architecture for both security features and development tools
- ✅ Comprehensive documentation for both end users and developers

This structure supports both a production-ready security application and
advanced AI-assisted development workflow, making it an exemplary
repository for modern software development practices.
