# Packaging Directory

This directory contains all packaging files for distributing xanadOS Search & Destroy across different Linux distributions.

## 📦 Supported Package Formats

| Format | Distributions | Build Script | Status |
|--------|--------------|--------------|--------|
| **RPM** | Fedora, RHEL, CentOS, openSUSE, Mageia | `rpm/build-rpm.sh` | ✅ Ready |
| **DEB** | Debian, Ubuntu, Mint, Pop!_OS, elementary | `debian/build-deb.sh` | ✅ Ready |
| **AUR** | Arch, Manjaro, EndeavourOS, Garuda | `aur/build-aur.sh` | ✅ Ready |

## 🚀 Quick Start

### Build All Packages

```bash
# From project root
./packaging/rpm/build-rpm.sh      # Build RPM
./packaging/debian/build-deb.sh   # Build DEB
./packaging/aur/build-aur.sh      # Build AUR
```

### Install Built Packages

```bash
# RPM (Fedora/RHEL)
sudo dnf install ~/rpmbuild/RPMS/noarch/xanados-search-destroy-*.rpm

# DEB (Debian/Ubuntu)
sudo apt install /tmp/xanados-search-destroy_*.deb

# AUR (Arch Linux)
sudo pacman -U /tmp/xanados-search-destroy-aur/*.pkg.tar.zst
```

## 📁 Directory Structure

```
packaging/
├── rpm/                    # RPM packaging
│   ├── xanados-search-destroy.spec
│   └── build-rpm.sh
├── debian/                 # DEB packaging
│   ├── control
│   ├── rules
│   ├── changelog
│   ├── copyright
│   ├── compat
│   └── build-deb.sh
├── aur/                    # AUR packaging
│   ├── PKGBUILD
│   └── build-aur.sh
├── desktop/                # Desktop integration
│   └── io.github.asafelobotomy.SearchAndDestroy.desktop
├── appdata/                # AppStream metadata
│   └── io.github.asafelobotomy.SearchAndDestroy.metainfo.xml
├── systemd/                # Systemd services
│   └── xanados-search-destroy-monitor.service
├── icons/                  # Application icons (multiple sizes)
└── PACKAGING_GUIDE.md      # Complete packaging documentation
```

## 📚 Documentation

- **[PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)** - Complete packaging guide with:
  - Prerequisites for each distribution
  - Detailed build instructions
  - Manual build processes
  - Troubleshooting guide
  - Distribution-specific notes
  - Publishing guidelines

## ✨ Features

All packages include:

- ✅ **Desktop Integration**: Menu entries, icons, desktop actions
- ✅ **System Integration**: Polkit policies, systemd services
- ✅ **AppStream Metadata**: Software center compatibility
- ✅ **Complete Dependencies**: All required runtime dependencies
- ✅ **Configuration Management**: Preserved user settings
- ✅ **Post-Install Hooks**: Proper setup and cleanup
- ✅ **Security Hardening**: Proper permissions and policies

## 🔍 Package Contents

### Application Files
- Python package in site-packages
- Main executable: `xanados-search-destroy`
- Desktop launcher with quick actions

### Configuration
- `/etc/xanados-search-destroy/*.toml` - Configuration files
- `/usr/share/xanados-search-destroy/yara_rules/` - YARA detection rules

### Runtime Directories
- `/var/lib/xanados-search-destroy/` - Application data
- `/var/lib/xanados-search-destroy/quarantine/` - Quarantine (secure)
- `/var/log/xanados-search-destroy/` - Log files

### System Integration
- Desktop file with actions (Quick Scan, Update, Real-Time)
- Icons in multiple sizes (16, 32, 48, 64, 128, SVG)
- Polkit policy for privilege elevation
- Systemd service for real-time monitoring
- AppStream metadata for software centers

## 🎯 Quick Reference

### Version Information
Version is automatically read from `VERSION` file in project root.

### Build Requirements

**RPM:**
- rpm-build, rpmdevtools, desktop-file-utils, libappstream-glib

**DEB:**
- build-essential, debhelper, devscripts, dh-python, appstream

**AUR:**
- base-devel, git

### Testing Packages

```bash
# Validate desktop file
desktop-file-validate *.desktop

# Validate AppStream metadata
appstream-util validate *.metainfo.xml

# Test Python import
python3 -c "import app; print(app.__version__)"
```

## 🤝 Contributing

When updating packaging:

1. Update version in `VERSION` file
2. Update changelogs:
   - RPM: In spec file `%changelog` section
   - DEB: `debian/changelog`
   - AUR: Increment `pkgrel` in PKGBUILD
3. Test build on target distribution
4. Validate with distribution tools
5. Submit PR with test results

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/asafelobotomy/xanadOS-Search_Destroy/issues)
- **Guide**: See [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)
- **Discussions**: [GitHub Discussions](https://github.com/asafelobotomy/xanadOS-Search_Destroy/discussions)

## 📜 License

All packaging files are licensed under GPL-3.0-or-later, same as the main project.
