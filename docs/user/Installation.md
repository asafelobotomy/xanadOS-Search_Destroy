# Installation Guide

This guide covers installation methods for **S&D - Search & Destroy** on Linux systems.

## System Requirements

### Hardware Requirements

- **Processor**: 64-bit x86/x64 processor
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 500 MB free disk space for application, additional space for virus definitions
- **Network**: Internet connection for virus definition updates

### Software Requirements

| Component | Requirement | Installation Command |
|-----------|-------------|---------------------|
| **Operating System** | Linux (tested on Ubuntu/Debian, designed for xanadOS) | N/A |
| **Python** | Python 3.10 or higher | `sudo apt install python3 python3-pip` |
| **ClamAV Engine** | ClamAV antivirus engine | `sudo apt install clamav clamav-daemon` |
| **GUI Framework** | PyQt6 | `pip install PyQt6>=6.5.0` |
| **RKHunter** | Rootkit scanner (optional) | `sudo apt install rkhunter` |

## Installation Methods

### Method 1: Flatpak Installation (Recommended)

Flatpak provides the most secure and isolated installation method.

```bash
# Install Flatpak if not present
sudo apt install flatpak

# Clone repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Build and install
./scripts/prepare-build.sh
make build-flatpak
make install-flatpak

# Run the application
make run-flatpak
```

### Method 2: Python Virtual Environment

For development or custom installations.

```bash
# Clone repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Automated setup
./scripts/prepare-build.sh

# Install dependencies
$(pwd)/.venv/bin/python -m pip install -r requirements.txt  # uses current directory

# Run application
./run.sh
```

### Method 3: Direct Python Installation

For testing environments only.

```bash
# Clone repository
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy

# Install dependencies
pip install -r requirements.txt

# Run application
python app/main.py
```

## Post-Installation Setup

### 1. Update Virus Definitions

```bash
# Update ClamAV virus definitions
sudo freshclam

# Update RKHunter definitions (if installed)
sudo rkhunter --update
```

### 2. Configure Security Policies

The application includes security policies for privileged operations:

```bash
# Install security policies (optional)
./scripts/setup-security.sh
```

### 3. Verify Installation

```bash
# Check ClamAV installation
clamscan --version

# Check RKHunter installation (optional)
rkhunter --version

# Test application launch
./run.sh
```

## Troubleshooting Installation

### Common Issues

#### ClamAV Not Found

```bash
# Install ClamAV
sudo apt update
sudo apt install clamav clamav-daemon

# Start ClamAV service
sudo systemctl enable clamav-freshclam
sudo systemctl start clamav-freshclam
```

#### Permission Denied Errors

```bash
# Check file permissions
ls -la ./run.sh

# Make scripts executable
chmod +x ./run.sh
chmod +x ./scripts/*.sh
```

#### Python Dependencies Missing

```bash
# Install Python development headers
sudo apt install python3-dev python3-venv

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### Flatpak Build Failures

```bash
# Install flatpak-builder
sudo apt install flatpak-builder

# Verify all dependencies
./scripts/verify-build.sh

# Clean and rebuild
make clean-flatpak
make build-flatpak
```

### Getting Help

If you encounter issues during installation:

1. **Check the [Troubleshooting Guide](../../README.md#troubleshooting)**
2. **Review system logs**: `/var/log/syslog` for system-level issues
3. **Check application logs**: `data/logs/` for application-specific errors
4. **Report issues**: [GitHub Issues](https://github.com/asafelobotomy/xanadOS-Search_Destroy/issues)

## Uninstallation

### Flatpak Uninstall

```bash
# Remove Flatpak application
flatpak uninstall org.xanados.SearchAndDestroy

# Remove user data (optional)
rm -rf ~/.local/share/xanados-search-destroy
rm -rf ~/.config/xanados-search-destroy
```

### Manual Uninstall

```bash
# Remove application files
rm -rf /path/to/xanadOS-Search_Destroy

# Remove user data (optional)
rm -rf ~/.local/share/xanados-search-destroy
rm -rf ~/.config/xanados-search-destroy

# Remove virtual environment
rm -rf .venv
```

---

**Next Steps**: After installation, see the [User Manual](User_Manual.md) for usage instructions.
