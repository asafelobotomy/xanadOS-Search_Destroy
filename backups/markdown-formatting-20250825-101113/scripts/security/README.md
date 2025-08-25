# Security Scripts

Scripts for security scanning, RKHunter operations, and vulnerability management.

## Scripts

### rkhunter-update-and-scan.sh

- **Purpose**: Update RKHunter database and perform system scan
- **Usage**: `sudo ./rkhunter-update-and-scan.sh`
- **Prerequisites**: RKHunter installed, sudo access

### rkhunter-wrapper.sh

- **Purpose**: Wrapper for RKHunter operations with logging
- **Usage**: `./rkhunter-wrapper.sh [command]`

### fix_scan_crashes.py

- **Purpose**: Fix and prevent scan-related crashes
- **Usage**: `./fix_scan_crashes.py`
- **Output**: Crash fix report and system patches

## Security Notes

- All security scripts require appropriate system permissions
- Run RKHunter scripts with sudo when needed
- Review scan results and logs regularly
- Keep security tools updated
