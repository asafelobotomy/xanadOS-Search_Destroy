# xanadOS Search & Destroy - AppImage

## Quick Start

1. **Download** the AppImage:
   - `xanadOS-Search-Destroy-3.0.0-x86_64.AppImage`

2. **Make it executable**:
   ```bash
   chmod +x xanadOS-Search-Destroy-3.0.0-x86_64.AppImage
   ```

3. **Run the application**:
   ```bash
   ./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage
   ```

## First Run

On first run, the application will offer to install PolicyKit policies for privileged operations:
- ClamAV installation
- RKhunter scans
- Quarantine management

These policies allow the application to perform security scans without requiring you to run the entire application as root.

## System Requirements

- **Linux** (any modern distribution)
- **x86_64** architecture
- **FUSE** (recommended but not required)
- **X11 or Wayland** display server
- **PolicyKit** for privileged operations

## Without FUSE

If you don't have FUSE installed or get FUSE errors, you can run the AppImage in extraction mode:

```bash
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract-and-run
```

## Features

✅ **Malware Scanning** - ClamAV integration for virus detection
✅ **Rootkit Detection** - RKhunter for rootkit scanning
✅ **Quarantine Management** - Isolate suspicious files
✅ **System Monitoring** - Real-time security monitoring
✅ **Scheduled Scans** - Automated security checks
✅ **Beautiful GUI** - Modern PyQt6 interface

## Size Information

- **AppImage Size**: 320 MB
- **Installed Size**: ~1.0 GB (when running)
- **Memory Usage**: ~200-300 MB RAM

## Troubleshooting

### "Permission denied"
Make sure the AppImage is executable:
```bash
chmod +x xanadOS-Search-Destroy-3.0.0-x86_64.AppImage
```

### "FUSE error"
Install FUSE2 or use extraction mode:
```bash
# Arch Linux
sudo pacman -S fuse2

# Ubuntu/Debian
sudo apt install fuse

# Or use extraction mode
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract-and-run
```

### PolicyKit policies not installing
Manually copy the policies:
```bash
./xanadOS-Search-Destroy-3.0.0-x86_64.AppImage --appimage-extract
sudo cp squashfs-root/usr/share/polkit-1/actions/*.policy /usr/share/polkit-1/actions/
```

## Support

- **Issues**: https://github.com/asafelobotomy/xanadOS-Search_Destroy/issues
- **Documentation**: See the main project README

## License

This software is distributed under the same license as the main project.
