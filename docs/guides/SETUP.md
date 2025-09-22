# 🚀 xanadOS Search & Destroy - Simplified Setup

## One-Command Setup

This repository now features a **revolutionary one-command setup** that installs and configures everything you need for development:

```bash
# THE ONLY COMMAND YOU NEED TO RUN:
make setup
```

That's it! This single command will:

✅ **Install modern package managers** (uv, pnpm, fnm)
✅ **Create Python virtual environment** with all dependencies
✅ **Install Node.js and JavaScript dependencies**
✅ **Install security tools** (ClamAV, RKHunter)
✅ **Configure your shell environment** for auto-activation
✅ **Validate everything works** properly
✅ **Generate a detailed setup report**

## Alternative Setup Options

```bash
# Force reinstallation of everything
make setup-force

# Minimal setup (essential dependencies only)
make setup-minimal

# Direct script execution with options
bash scripts/setup.sh --help
```

## What Gets Installed

### 🚀 Modern Package Managers
- **uv**: 10-100x faster Python package management
- **pnpm**: 70% less disk space for Node.js packages
- **fnm**: 500x faster Node.js version switching

### 🛡️ Security Tools
- **ClamAV**: Antivirus scanning
- **RKHunter**: Rootkit detection
- **System monitoring tools**

### 🔧 Development Environment
- **Python virtual environment** with all project dependencies
- **Node.js environment** with all JavaScript dependencies
- **Shell auto-activation** (automatically activates when you enter the directory)
- **Development tools** and validation scripts

## After Setup

Once setup completes, you can immediately:

```bash
# Start development
make dev

# Run the application
python -m app.main

# Run tests
make test

# Use modern package managers
uv add package-name     # Add Python packages (10-100x faster)
pnpm add package-name   # Add Node.js packages (70% less disk space)
fnm use 18             # Switch Node.js versions (500x faster)
```

## Troubleshooting

If you encounter any issues:

1. **Check the detailed log:**
   ```bash
   cat setup.log
   ```

2. **View the setup report:**
   ```bash
   cat SETUP_REPORT.md
   ```

3. **Force reinstall everything:**
   ```bash
   make setup-force
   ```

4. **Get help:**
   ```bash
   bash scripts/setup.sh --help
   ```

## What's Different About This Setup

### ❌ **Before (Old Way)**
- Multiple fragmented scripts
- Manual environment activation
- Complex dependency management
- Inconsistent tool detection
- Platform-specific issues
- No validation
- No progress indicators

### ✅ **After (New Way)**
- **Single command does everything**
- **Automatic environment activation**
- **Modern, fast package managers**
- **Cross-platform compatibility**
- **Comprehensive validation**
- **Real-time progress indicators**
- **Detailed setup reports**
- **Error handling and recovery**

## System Compatibility

This setup script works on:
- ✅ **Arch Linux** (pacman)
- ✅ **Ubuntu/Debian** (apt)
- ✅ **Fedora/RHEL** (dnf)
- ✅ **macOS** (brew)

## Support

- **Setup Issues**: Check `setup.log` and `SETUP_REPORT.md`
- **Development Help**: See `docs/` directory
- **Tool Documentation**: Run `make help`

---

**🎯 Goal**: Zero-friction development environment setup in one command!
