# Packaging Guide for xanadOS Search & Destroy

Complete guide for building and distributing xanadOS Search & Destroy across different Linux distributions.

## 📦 Package Formats Supported

- **RPM** - Fedora, RHEL, CentOS, openSUSE, Mageia
- **DEB** - Debian, Ubuntu, Linux Mint, Pop!_OS, elementary OS
- **AUR** - Arch Linux, Manjaro, EndeavourOS, Garuda Linux

## 🚀 Quick Build

### Build All Packages

```bash
# Build for all supported formats
make build-all-packages

# Or build individually:
./packaging/rpm/build-rpm.sh      # RPM package
./packaging/debian/build-deb.sh   # DEB package
./packaging/aur/build-aur.sh      # AUR package
```

## 📋 Prerequisites

### For RPM Building (Fedora/RHEL)

```bash
# Fedora
sudo dnf install rpm-build rpmdevtools desktop-file-utils libappstream-glib

# RHEL/CentOS
sudo yum install rpm-build rpmdevtools desktop-file-utils libappstream-glib
```

### For DEB Building (Debian/Ubuntu)

```bash
sudo apt-get install build-essential debhelper devscripts dh-python \
    python3-all python3-setuptools python3-pip desktop-file-utils appstream
```

### For AUR Building (Arch Linux)

```bash
sudo pacman -S base-devel git
```

## 🔧 Building RPM Packages

### Automatic Build

```bash
cd /home/solon/Documents/xanadOS-Search_Destroy
./packaging/rpm/build-rpm.sh
```

### Manual Build

```bash
# Setup RPM build environment
rpmdev-setuptree

# Get version
VERSION=$(cat VERSION | tr -d '\n')

# Create source tarball
git archive --format=tar.gz --prefix="xanados-search-destroy-${VERSION}/" \
    HEAD > ~/rpmbuild/SOURCES/xanados-search-destroy-${VERSION}.tar.gz

# Copy spec file
cp packaging/rpm/xanados-search-destroy.spec ~/rpmbuild/SPECS/

# Build
cd ~/rpmbuild/SPECS
rpmbuild -ba xanados-search-destroy.spec
```

### Install RPM

```bash
# With DNF (Fedora)
sudo dnf install ~/rpmbuild/RPMS/noarch/xanados-search-destroy-*.rpm

# With YUM (RHEL/CentOS)
sudo yum localinstall ~/rpmbuild/RPMS/noarch/xanados-search-destroy-*.rpm

# With Zypper (openSUSE)
sudo zypper install ~/rpmbuild/RPMS/noarch/xanados-search-destroy-*.rpm

# Direct RPM
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/xanados-search-destroy-*.rpm
```

## 📦 Building DEB Packages

### Automatic Build

```bash
cd /home/solon/Documents/xanadOS-Search_Destroy
./packaging/debian/build-deb.sh
```

### Manual Build

```bash
# Create build directory
VERSION=$(cat VERSION | tr -d '\n')
BUILD_DIR="/tmp/xanados-search-destroy-${VERSION}"
mkdir -p "${BUILD_DIR}"

# Copy source
git archive HEAD | tar -x -C "${BUILD_DIR}"

# Copy debian directory
cp -r packaging/debian "${BUILD_DIR}/"

# Build
cd "${BUILD_DIR}"
dpkg-buildpackage -us -uc -b
```

### Install DEB

```bash
# With APT (recommended)
sudo apt install /tmp/xanados-search-destroy_*.deb

# With dpkg
sudo dpkg -i /tmp/xanados-search-destroy_*.deb
sudo apt-get install -f  # Fix dependencies if needed

# With GDebi (GUI)
sudo gdebi /tmp/xanados-search-destroy_*.deb
```

## 🏔️ Building AUR Packages

### Automatic Build

```bash
cd /home/solon/Documents/xanadOS-Search_Destroy
./packaging/aur/build-aur.sh
```

### Manual Build

```bash
# Copy PKGBUILD to build directory
mkdir -p /tmp/xanados-aur
cp packaging/aur/PKGBUILD /tmp/xanados-aur/
cd /tmp/xanados-aur

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Build package
makepkg -sf --noconfirm
```

### Install AUR Package

```bash
# With pacman
sudo pacman -U xanados-search-destroy-*.pkg.tar.zst

# Or build and install in one step
makepkg -si
```

### Publishing to AUR

1. **Create AUR Account**: https://aur.archlinux.org/register
2. **Setup SSH Key**: Add your SSH key to AUR account
3. **Clone AUR Repository**:
   ```bash
   git clone ssh://aur@aur.archlinux.org/xanados-search-destroy.git
   cd xanados-search-destroy
   ```
4. **Copy Files**:
   ```bash
   cp ../packaging/aur/PKGBUILD .
   cp ../packaging/aur/.SRCINFO .
   ```
5. **Update Checksums**:
   ```bash
   updpkgsums
   makepkg --printsrcinfo > .SRCINFO
   ```
6. **Test Build**:
   ```bash
   makepkg -si
   ```
7. **Commit and Push**:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version X.Y.Z"
   git push
   ```

## 📝 Package Contents

All packages include:

### Binaries & Libraries
- Python package installed to site-packages
- Main executable: `xanados-search-destroy`

### Desktop Integration
- Desktop file: `/usr/share/applications/io.github.asafelobotomy.SearchAndDestroy.desktop`
- Icons: `/usr/share/icons/hicolor/*/apps/` (16, 32, 48, 64, 128, SVG)
- AppStream metadata: `/usr/share/metainfo/io.github.asafelobotomy.SearchAndDestroy.metainfo.xml`

### System Integration
- Polkit policy: `/usr/share/polkit-1/actions/`
- Systemd service: `/usr/lib/systemd/system/xanados-search-destroy-monitor.service`

### Configuration
- `/etc/xanados-search-destroy/security_config.toml`
- `/etc/xanados-search-destroy/monitoring_config.toml`
- `/etc/xanados-search-destroy/gui_config.toml`

### YARA Rules
- `/usr/share/xanados-search-destroy/yara_rules/malware_detection.yar`

### Runtime Directories
- `/var/lib/xanados-search-destroy/` - Application data
- `/var/lib/xanados-search-destroy/quarantine/` - Quarantined files
- `/var/log/xanados-search-destroy/` - Log files

### Documentation
- `/usr/share/doc/xanados-search-destroy/`
- `/usr/share/licenses/xanados-search-destroy/` (or `/usr/share/doc/` on Debian)

## 🔍 Validation

### Test Desktop File

```bash
desktop-file-validate /usr/share/applications/io.github.asafelobotomy.SearchAndDestroy.desktop
```

### Test AppStream Metadata

```bash
# Fedora/RHEL
appstream-util validate-relax /usr/share/metainfo/*.metainfo.xml

# Debian/Ubuntu
appstreamcli validate /usr/share/metainfo/*.metainfo.xml
```

### Test Package Installation

```bash
# Import test
python3 -c "import app; print('Version:', app.__version__)"

# Launch test
xanados-search-destroy --version
```

## 🚀 Post-Installation

After installing any package:

```bash
# 1. Update ClamAV definitions
sudo freshclam

# 2. Enable real-time protection (optional)
sudo systemctl enable --now xanados-search-destroy-monitor

# 3. Launch application
xanados-search-destroy

# Or from application menu:
# Applications → Security → xanadOS Search & Destroy
```

## 📊 Package Metadata

### RPM Package Info

```bash
rpm -qi xanados-search-destroy
rpm -ql xanados-search-destroy  # List files
rpm -qR xanados-search-destroy  # List dependencies
```

### DEB Package Info

```bash
dpkg -l xanados-search-destroy
dpkg -L xanados-search-destroy  # List files
apt-cache show xanados-search-destroy  # Show details
```

### AUR Package Info

```bash
pacman -Qi xanados-search-destroy
pacman -Ql xanados-search-destroy  # List files
pacman -Si xanados-search-destroy  # Show details
```

## 🔧 Troubleshooting

### RPM Build Issues

**Problem**: Missing dependencies
```bash
# Install build dependencies
sudo dnf builddep packaging/rpm/xanados-search-destroy.spec
```

**Problem**: Signature verification fails
```bash
# Build without signature
rpmbuild -ba --define '_gpg_name %{nil}' xanados-search-destroy.spec
```

### DEB Build Issues

**Problem**: Missing build dependencies
```bash
# Install dependencies from control file
sudo apt-get build-dep .
```

**Problem**: Lintian warnings
```bash
# Check package for issues
lintian -i xanados-search-destroy_*.deb
```

### AUR Build Issues

**Problem**: Checksum mismatch
```bash
# Update checksums
updpkgsums
```

**Problem**: Missing dependencies
```bash
# Install dependencies
makepkg -s
```

## 🎯 Distribution-Specific Notes

### Fedora
- Uses DNF package manager
- Requires `python3-pyqt6` from repositories

### Ubuntu/Debian
- Uses APT package manager
- May need to enable universe repository for some dependencies

### Arch Linux
- Uses Pacman package manager
- Most Python packages available in repositories
- Some may need AUR helpers like `yay` or `paru`

## 📚 Additional Resources

- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)
- [Debian Packaging Tutorial](https://www.debian.org/doc/manuals/maint-guide/)
- [Arch Package Guidelines](https://wiki.archlinux.org/title/PKGBUILD)
- [AppStream Documentation](https://www.freedesktop.org/software/appstream/docs/)

## 🤝 Contributing Packages

To contribute packaging improvements:

1. Test on your distribution
2. Update packaging files as needed
3. Submit pull request with:
   - Updated packaging files
   - Build test results
   - Distribution version tested

## 📞 Support

- **Issues**: https://github.com/asafelobotomy/xanadOS-Search_Destroy/issues
- **Discussions**: https://github.com/asafelobotomy/xanadOS-Search_Destroy/discussions
- **Wiki**: https://github.com/asafelobotomy/xanadOS-Search_Destroy/wiki
