# RPM Spec file for xanadOS Search & Destroy
# Compatible with Fedora, RHEL, CentOS, openSUSE, etc.

%global app_name xanados-search-destroy
%global app_id io.github.asafelobotomy.SearchAndDestroy
%global python_version 3.13

Name:           %{app_name}
Version:        0.3.0
Release:        1%{?dist}
Summary:        Comprehensive Linux security scanner and system protection suite

License:        GPL-3.0-or-later
URL:            https://github.com/asafelobotomy/xanadOS-Search_Destroy
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

# Build dependencies
BuildRequires:  python%{python_version}
BuildRequires:  python%{python_version}-devel
BuildRequires:  python%{python_version}-pip
BuildRequires:  python%{python_version}-setuptools
BuildRequires:  python%{python_version}-wheel
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

# Runtime dependencies - Core
Requires:       python%{python_version}
Requires:       python%{python_version}-pyqt6 >= 6.9.1
Requires:       python%{python_version}-requests >= 2.32.0
Requires:       python%{python_version}-psutil >= 6.1.0
Requires:       python%{python_version}-cryptography >= 44.0.0
Requires:       python%{python_version}-pyyaml >= 6.0.2
Requires:       python%{python_version}-click >= 8.1.7
Requires:       python%{python_version}-rich >= 13.9.4
Requires:       python%{python_version}-colorama >= 0.4.6
Requires:       python%{python_version}-tabulate >= 0.9.0
Requires:       python%{python_version}-numpy >= 2.2.0
Requires:       python%{python_version}-schedule >= 1.2.2
Requires:       python%{python_version}-aiohttp >= 3.11.0
Requires:       python%{python_version}-watchdog >= 6.0.0
Requires:       python%{python_version}-dnspython >= 2.8.0
Requires:       python%{python_version}-dotenv >= 1.0.1

# Security scanning tools
Requires:       clamav >= 0.103.0
Requires:       clamav-update
Requires:       rkhunter >= 1.4.6

# System utilities
Requires:       inotify-tools
Requires:       sudo
Requires:       polkit

# Optional but recommended
Recommends:     chkrootkit
Recommends:     lynis
Recommends:     aide

%description
xanadOS Search & Destroy is a comprehensive security scanner and system
protection suite for Linux. It provides:

- ClamAV virus and malware scanning with modern GUI
- Real-time file system monitoring and protection
- RKHunter rootkit detection integration
- System integrity monitoring
- Scheduled security scans
- Quarantine management for threats
- Comprehensive security reporting
- Modern PyQt6 graphical interface

Designed for both desktop users and system administrators who need
powerful security tools with an intuitive interface.

%prep
%autosetup -n %{name}-%{version}

%build
# Build Python package
%py3_build

%install
# Install Python package
%py3_install

# Install desktop file
install -D -m 0644 packaging/desktop/%{app_id}.desktop \
    %{buildroot}%{_datadir}/applications/%{app_id}.desktop

# Install icons
for size in 16 32 48 64 128; do
    install -D -m 0644 packaging/icons/%{app_id}-${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{app_id}.png
done

# Install SVG icon
install -D -m 0644 packaging/icons/%{app_id}.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{app_id}.svg

# Install AppStream metadata
install -D -m 0644 packaging/appdata/%{app_id}.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/%{app_id}.metainfo.xml

# Install polkit policy
install -D -m 0644 config/%{app_id}.policy \
    %{buildroot}%{_datadir}/polkit-1/actions/%{app_id}.policy

# Install configuration files
install -D -m 0644 config/security_config.toml \
    %{buildroot}%{_sysconfdir}/%{app_name}/security_config.toml

install -D -m 0644 config/monitoring_config.toml \
    %{buildroot}%{_sysconfdir}/%{app_name}/monitoring_config.toml

install -D -m 0644 config/gui_config.toml \
    %{buildroot}%{_sysconfdir}/%{app_name}/gui_config.toml

# Install YARA rules
install -D -m 0644 config/yara_rules/malware_detection.yar \
    %{buildroot}%{_datadir}/%{app_name}/yara_rules/malware_detection.yar

# Install systemd service (optional for real-time protection)
install -D -m 0644 packaging/systemd/%{app_name}-monitor.service \
    %{buildroot}%{_unitdir}/%{app_name}-monitor.service

# Install documentation
install -D -m 0644 README.md %{buildroot}%{_docdir}/%{app_name}/README.md
install -D -m 0644 LICENSE %{buildroot}%{_docdir}/%{app_name}/LICENSE
install -D -m 0644 CHANGELOG.md %{buildroot}%{_docdir}/%{app_name}/CHANGELOG.md

%check
# Validate desktop file
desktop-file-validate %{buildroot}%{_datadir}/applications/%{app_id}.desktop

# Validate AppStream metadata
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/%{app_id}.metainfo.xml

# Run basic import test
%{__python3} -c "import app; print('Version:', app.__version__)"

%post
# Update icon cache
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

# Update desktop database
/usr/bin/update-desktop-database &> /dev/null || :

# Create application data directories
mkdir -p %{_localstatedir}/lib/%{app_name}/quarantine
mkdir -p %{_localstatedir}/log/%{app_name}
mkdir -p %{_sharedstatedir}/%{app_name}/scan_reports

# Set proper permissions
chmod 755 %{_localstatedir}/lib/%{app_name}
chmod 700 %{_localstatedir}/lib/%{app_name}/quarantine
chmod 755 %{_localstatedir}/log/%{app_name}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ xanadOS Search & Destroy installed successfully!"
echo ""
echo "Quick Start:"
echo "  1. Update ClamAV definitions: sudo freshclam"
echo "  2. Launch application: %{app_name}"
echo "  3. Or from menu: Applications → Security → Search & Destroy"
echo ""
echo "For real-time protection:"
echo "  sudo systemctl enable --now %{app_name}-monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

%postun
# Update icon cache
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

# Update desktop database
/usr/bin/update-desktop-database &> /dev/null || :

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%license LICENSE
%doc README.md CHANGELOG.md

# Python package
%{python3_sitelib}/app/
%{python3_sitelib}/%{name}-%{version}-py%{python3_version}.egg-info/

# Desktop integration
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/icons/hicolor/*/apps/%{app_id}.*
%{_datadir}/metainfo/%{app_id}.metainfo.xml

# Polkit policy
%{_datadir}/polkit-1/actions/%{app_id}.policy

# Configuration
%dir %{_sysconfdir}/%{app_name}
%config(noreplace) %{_sysconfdir}/%{app_name}/*.toml

# YARA rules
%{_datadir}/%{app_name}/yara_rules/

# Systemd service
%{_unitdir}/%{app_name}-monitor.service

# Runtime directories (created in %post)
%dir %{_localstatedir}/lib/%{app_name}
%dir %{_localstatedir}/log/%{app_name}
%dir %{_sharedstatedir}/%{app_name}

%changelog
* Sun Dec 15 2024 xanadOS Team <dev@xanados.org> - 0.3.0-1
- Update to version 0.3.0-beta
- Add Real-Time Protection optimizations (Phases 1-4)
- Implement scan result caching (70-80% performance improvement)
- Add smart file prioritization and pre-processing
- Integrate YARA heuristic detection engine
- Add hybrid multi-engine scanner (ClamAV + YARA)
- Implement system load monitoring and adaptive throttling
- Add adaptive worker thread scaling (2-8 workers)
- Implement comprehensive performance metrics tracking
- Add scan safety features (prevent concurrent scans)
- Display real-time file sizes during scanning
- Fix Update Definitions button for ClamAV freshclam daemon
- Improve GUI responsiveness and user experience

* Mon Nov 01 2024 xanadOS Team <dev@xanados.org> - 0.2.0-1
- Initial RPM release
- Modern PyQt6 GUI for ClamAV scanning
- RKHunter integration
- Real-time file monitoring
- Comprehensive security features
