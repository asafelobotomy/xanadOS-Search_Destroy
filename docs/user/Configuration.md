# Configuration Guide

This guide covers advanced configuration options for **S&D - Search & Destroy** to customize the application for your specific needs.

## Configuration Files

### Default Configuration

S&D uses a hierarchical configuration system:

```
config/
├── default_config.json     # Default application settings
├── user_config.json        # User-specific overrides
└── security_policy.json    # Security and scanning policies
```

### Environment Variables

Control application behavior with environment variables:

```bash
export XANADOS_SD_CONFIG_PATH="/path/to/config"     # Custom config directory
export XANADOS_SD_LOG_LEVEL="DEBUG"                # Logging verbosity
export XANADOS_SD_QUARANTINE_PATH="/secure/path"   # Quarantine location
export XANADOS_SD_TEMP_PATH="/tmp/sd_temp"         # Temporary files
```

## User Interface Configuration

### Theme Settings

Configure application appearance:

```json
{
  "ui": {
    "theme": "dark",           # Options: "light", "dark", "auto"
    "scale_factor": 1.0,       # UI scaling (0.5 - 2.0)
    "font_family": "system",   # Font selection
    "window_size": {
      "width": 1200,
      "height": 800
    },
    "window_position": "center"
  }
}
```

### Language and Localization

Set interface language:

```json
{
  "localization": {
    "language": "en",          # Language code (en, es, fr, de, etc.)
    "date_format": "YYYY-MM-DD",
    "time_format": "24h",      # Options: "12h", "24h"
    "number_format": "1,234.56"
  }
}
```

## Scanning Configuration

### Default Scan Settings

Configure standard scan behavior:

```json
{
  "scanning": {
    "default_scan_type": "quick",     # Options: "quick", "full", "custom"
    "default_paths": [
      "~/Downloads",
      "~/Documents",
      "~/Desktop"
    ],
    "max_file_size": "100MB",         # Maximum file size to scan
    "max_archive_size": "500MB",      # Maximum archive size to scan
    "scan_depth": 10,                 # Directory traversal depth
    "follow_symlinks": false,         # Follow symbolic links
    "scan_archives": true,            # Scan inside archives
    "scan_email": true,               # Scan email files
    "detect_pua": true                # Detect potentially unwanted applications
  }
}
```

### File Type Filters

Control which files are scanned:

```json
{
  "file_filters": {
    "included_extensions": [
      ".exe", ".dll", ".zip", ".tar", ".pdf", ".doc", ".docx"
    ],
    "excluded_extensions": [
      ".mp3", ".mp4", ".avi", ".mkv", ".iso"
    ],
    "excluded_directories": [
      "/proc", "/sys", "/dev", "node_modules", ".git"
    ],
    "scan_hidden_files": false,       # Scan files starting with '.'
    "scan_system_files": false        # Include system directories
  }
}
```

### Performance Settings

Optimize scanning performance:

```json
{
  "performance": {
    "max_memory_usage": "1GB",        # Memory limit for scanning
    "thread_count": 4,                # Number of scan threads
    "cpu_priority": "normal",         # Options: "low", "normal", "high"
    "background_scanning": true,      # Enable background scans
    "cache_scan_results": true,       # Cache results for performance
    "progress_update_interval": 100   # Progress update frequency (files)
  }
}
```

## Security Configuration

### Quarantine Settings

Configure threat quarantine:

```json
{
  "quarantine": {
    "enabled": true,
    "location": "~/.local/share/xanados-search-destroy/quarantine",
    "max_size": "1GB",                # Maximum quarantine size
    "retention_days": 30,             # Days to keep quarantined files
    "encrypt_quarantine": true,       # Encrypt quarantined files
    "password_protected": false       # Require password for access
  }
}
```

### Automatic Threat Response

Define actions for detected threats:

```json
{
  "threat_response": {
    "default_action": "quarantine",   # Options: "quarantine", "delete", "ignore"
    "auto_quarantine": {
      "viruses": true,
      "trojans": true,
      "adware": false,
      "pua": false
    },
    "notification_level": "all",      # Options: "none", "threats", "all"
    "sound_alerts": true,
    "desktop_notifications": true
  }
}
```

### Privilege Management

Configure authentication requirements:

```json
{
  "security": {
    "require_auth_for_system_scan": true,
    "require_auth_for_quarantine": false,
    "require_auth_for_settings": false,
    "session_timeout": 3600,          # Authentication timeout (seconds)
    "polkit_integration": true        # Use polkit for privilege escalation
  }
}
```

## Real-time Monitoring

### File System Watching

Configure real-time protection:

```json
{
  "real_time_monitoring": {
    "enabled": false,                 # Enable real-time monitoring
    "watched_directories": [
      "~/Downloads",
      "~/Documents"
    ],
    "exclude_patterns": [
      "*.tmp", "*.log", "*~"
    ],
    "scan_on_access": true,           # Scan files when accessed
    "scan_on_modify": true,           # Scan files when modified
    "scan_on_create": true,           # Scan newly created files
    "auto_quarantine_threats": true   # Automatically quarantine threats
  }
}
```

### Event Processing

Configure monitoring behavior:

```json
{
  "event_processing": {
    "event_queue_size": 1000,         # Maximum events in queue
    "batch_processing": true,         # Process events in batches
    "batch_size": 10,                 # Events per batch
    "processing_delay": 1000,         # Delay between processing (ms)
    "ignore_temp_files": true         # Skip temporary files
  }
}
```

## Reporting Configuration

### Report Generation

Configure scan reports:

```json
{
  "reporting": {
    "auto_generate": true,            # Generate reports automatically
    "save_location": "~/Documents/S&D_Reports",
    "report_formats": ["pdf", "json", "csv"],
    "include_clean_files": false,     # Include clean files in reports
    "include_system_info": true,      # Include system information
    "include_performance_data": true, # Include performance metrics
    "report_retention_days": 90       # Days to keep reports
  }
}
```

### Export Settings

Configure report export options:

```json
{
  "export": {
    "pdf_settings": {
      "page_size": "A4",
      "include_charts": true,
      "include_logos": true
    },
    "csv_settings": {
      "delimiter": ",",
      "encoding": "utf-8",
      "include_headers": true
    },
    "json_settings": {
      "pretty_print": true,
      "include_metadata": true
    }
  }
}
```

## Network Configuration

### Update Settings

Configure virus definition updates:

```json
{
  "updates": {
    "auto_update": true,              # Automatic updates
    "update_frequency": "daily",      # Options: "hourly", "daily", "weekly"
    "update_time": "02:00",          # Time for scheduled updates
    "check_on_startup": true,         # Check for updates on launch
    "download_timeout": 300,          # Download timeout (seconds)
    "retry_attempts": 3               # Number of retry attempts
  }
}
```

### Proxy Configuration

Configure network proxy settings:

```json
{
  "network": {
    "proxy": {
      "enabled": false,
      "type": "http",                 # Options: "http", "socks5"
      "host": "proxy.example.com",
      "port": 8080,
      "username": "",
      "password": "",
      "bypass_local": true
    },
    "ssl_verification": true,         # Verify SSL certificates
    "connection_timeout": 30          # Connection timeout (seconds)
  }
}
```

## Logging Configuration

### Log Settings

Configure application logging:

```json
{
  "logging": {
    "level": "INFO",                  # Options: DEBUG, INFO, WARNING, ERROR
    "log_to_file": true,
    "log_file": "data/logs/app.log",
    "max_log_size": "10MB",
    "backup_count": 5,                # Number of log backups to keep
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S"
  }
}
```

### Debug Options

Configure debugging features:

```json
{
  "debug": {
    "enabled": false,                 # Enable debug mode
    "verbose_scanning": false,        # Detailed scan logging
    "performance_profiling": false,   # Profile performance
    "memory_tracking": false,         # Track memory usage
    "save_debug_reports": false       # Save debug information
  }
}
```

## Advanced Configuration

### Custom ClamAV Settings

Override ClamAV configuration:

```json
{
  "clamav": {
    "database_path": "/var/lib/clamav",
    "clamd_socket": "/var/run/clamav/clamd.ctl",
    "max_scan_time": 300,             # Maximum scan time per file (seconds)
    "max_recursion": 16,              # Archive recursion limit
    "max_files": 10000,               # Maximum files per archive
    "pcre_match_limit": 10000,        # PCRE match limit
    "pcre_recmatch_limit": 5000       # PCRE recursion match limit
  }
}
```

### RKHunter Integration

Configure rootkit scanning:

```json
{
  "rkhunter": {
    "enabled": true,
    "config_file": "/etc/rkhunter.conf",
    "database_update": true,          # Update RKHunter database
    "skip_keypress": true,            # Skip keypress prompts
    "check_categories": [
      "system_commands",
      "rootkits",
      "system_integrity",
      "network"
    ]
  }
}
```

## Configuration Management

### Backup and Restore

Backup your configuration:

```bash
# Backup current configuration
cp -r ~/.config/xanados-search-destroy ~/sd-config-backup

# Restore configuration
cp -r ~/sd-config-backup ~/.config/xanados-search-destroy
```

### Reset to Defaults

Reset configuration to defaults:

```bash
# Remove user configuration
rm -rf ~/.config/xanados-search-destroy

# Application will recreate default configuration on next launch
```

### Validation

Validate configuration files:

```bash
# Check configuration syntax
python -m json.tool config/user_config.json

# Test configuration loading
./run.sh --validate-config
```

---

**Next Steps**: See the [Troubleshooting Guide](../../README.md#troubleshooting) for common configuration issues.
