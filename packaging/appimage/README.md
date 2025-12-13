# xanadOS Search & Destroy - AppImage Packaging

This directory contains the configuration and build scripts for creating AppImage packages of xanadOS Search & Destroy.

## ✅ Current Status

**Latest AppImage:** `xanadOS-Search-Destroy-3.0.0-x86_64.AppImage` (320 MB)
- ✅ Fully functional with bundled system Python 3.13
- ✅ All dependencies included (PyQt6, FastAPI, ClamAV integration, etc.)
- ✅ PolicyKit integration for privileged operations
- ✅ Works with FUSE or extraction mode
- ✅ Command-line arguments supported (`--version`, `--help`, `--skip-policy-check`)
- ✅ Tested and verified on Arch Linux

## 📦 What is AppImage?

AppImage is a format for distributing portable software on Linux. An AppImage:
- **Runs everywhere** - Works on most Linux distributions
- **No installation required** - Just download, make executable, and run
- **Self-contained** - Bundles all dependencies
- **No root required** - Runs in userspace (except for privileged operations)

## 🏗️ Building the AppImage

### Prerequisites

- **Linux system** (x86_64 or aarch64)
- **Python 3.13+** installed
- **appimagetool** (automatically downloaded if not present)
- **Development tools**: `gcc`, `make`, `git`
- **Active virtual environment** with project dependencies installed

### Quick Build

Using the Makefile (recommended):

```bash
# Build AppImage
make build-appimage

# The AppImage will be created in: releases/appimage/
```

### Manual Build

```bash
# Run the build script directly
cd packaging/appimage
./build-appimage.sh
```

### Build Process

The build script performs these steps:

1. **Environment Setup** - Creates AppDir structure
2. **Python Installation** - Sets up Python virtual environment
3. **Dependency Installation** - Installs all required packages
4. **Application Bundle** - Copies application code and resources
5. **PolicyKit Integration** - Bundles security policies
6. **AppImage Creation** - Packages everything into a single executable

## 📁 Files

```
packaging/appimage/
├── AppRun                           # Launcher script (executed when AppImage runs)
├── build-appimage.sh                # Main build script
├── requirements.txt                 # Python dependencies
├── xanadOS-Search-Destroy.desktop   # Desktop integration file
├── xanadOS-Search-Destroy.appdata.xml  # AppStream metadata
└── README.md                        # This file
```

## 🚀 Using the AppImage

### Download and Run

```bash
# Make executable
chmod +x xanadOS-Search-Destroy-3.0.0-x86_64.AppImage

# Run the application
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage
```

### First Run

On first run, the AppImage will:
1. Check for PolicyKit policies
2. Offer to install them (requires sudo password once)
3. Launch the application

### Desktop Integration

To integrate with your desktop environment:

```bash
# Extract the desktop file and icon
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract

# Copy to user directories
cp squashfs-root/xanadOS-Search-Destroy.desktop ~/.local/share/applications/
cp squashfs-root/xanadOS-Search-Destroy.png ~/.local/share/icons/hicolor/256x256/apps/

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

### Command Line Options

```bash
# Show version
./xanadOS-Search-Destroy.AppImage --version

# Quick scan mode
./xanadOS-Search-Destroy.AppImage --scan-mode=quick

# Full system scan
./xanadOS-Search-Destroy.AppImage --scan-mode=full

# Update virus definitions
./xanadOS-Search-Destroy.AppImage --update-definitions

# Skip PolicyKit check
./xanadOS-Search-Destroy.AppImage --skip-policy-check
```

## 🔒 Security & Privileges

### How Sudo Operations Work

The AppImage handles privileged operations through **PolicyKit**, not by running as root:

```
User runs AppImage (no sudo)
    ↓
App needs privileged operation (e.g., ClamAV install)
    ↓
App calls pkexec with PolicyKit
    ↓
System prompts for password
    ↓
Operation executes with privileges
```

### PolicyKit Policies

The following policies are included and need to be installed (one-time):

- `io.github.asafelobotomy.searchanddestroy.policy` - Main operations
- `io.github.asafelobotomy.searchanddestroy.hardened.policy` - Hardened mode
- `io.github.asafelobotomy.searchanddestroy.rkhunter.policy` - RKhunter integration

These are automatically offered for installation on first run.

### Manual Policy Installation

```bash
# Extract policies from AppImage
./xanadOS-Search-Destroy.AppImage --appimage-extract

# Copy to system location
sudo cp squashfs-root/usr/share/polkit-1/actions/*.policy /usr/share/polkit-1/actions/
```

## 🛠️ Makefile Targets

```bash
# Build AppImage
make build-appimage

# Clean build artifacts
make clean-appimage

# Install AppImage build tools
make install-appimage-tools

# Test built AppImage
make test-appimage
```

## 📊 AppImage Size

Typical AppImage size: **~200-300 MB**

This includes:
- Python 3.13 runtime
- PyQt6 and Qt libraries
- All Python dependencies
- Application code
- Icons and resources

## 🐛 Troubleshooting

### AppImage Won't Run

```bash
# Check if file is executable
chmod +x xanadOS-Search-Destroy-*.AppImage

# Run with debugging
./xanadOS-Search-Destroy-*.AppImage 2>&1 | tee appimage.log
```

### Missing Libraries

AppImages should be self-contained, but if you encounter missing library errors:

```bash
# Check library dependencies
ldd xanadOS-Search-Destroy-*.AppImage

# Install FUSE if needed (for older systems)
sudo apt install fuse libfuse2  # Debian/Ubuntu
sudo dnf install fuse fuse-libs  # Fedora
```

### PolicyKit Not Working

```bash
# Verify PolicyKit is installed
which pkexec

# Check policies are installed
ls -la /usr/share/polkit-1/actions/ | grep searchanddestroy

# Test PolicyKit manually
pkexec echo "PolicyKit works"
```

### Qt Platform Plugin Issues

If you see "Could not find the Qt platform plugin":

```bash
# Set Qt debug environment variable
QT_DEBUG_PLUGINS=1 ./xanadOS-Search-Destroy-*.AppImage
```

## 🔄 Updating

To update to a new version:

1. Download the new AppImage
2. Make it executable
3. Run it (policies are already installed)
4. Optionally remove the old AppImage

## 📝 Version Information

Current version: **3.0.0**

Check version:
```bash
cat VERSION  # In source tree
./xanadOS-Search-Destroy-*.AppImage --version  # In AppImage
```

## 🤝 Contributing

To contribute to AppImage packaging:

1. Test builds on multiple distributions
2. Report compatibility issues
3. Suggest build optimizations
4. Improve documentation

## 📄 License

Same as main project: GPL-3.0-or-later

## 🔗 Resources

- [AppImage Documentation](https://docs.appimage.org/)
- [AppImageKit GitHub](https://github.com/AppImage/AppImageKit)
- [PolicyKit Documentation](https://www.freedesktop.org/software/polkit/docs/latest/)
- [Main Project Repository](https://github.com/asafelobotomy/xanadOS-Search_Destroy)

## 📧 Support

For issues specific to AppImage packaging:
- Open an issue on GitHub with `[AppImage]` prefix
- Include AppImage version and Linux distribution
- Attach relevant logs
