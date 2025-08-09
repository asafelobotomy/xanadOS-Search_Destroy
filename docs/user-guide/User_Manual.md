# User Manual

This manual provides comprehensive instructions for using **S&D - Search & Destroy** to protect your system from malware and security threats.

## Getting Started

### First Launch

1. **Launch S&D**: Use the desktop launcher or run `./run.sh` from the terminal
2. **Interface Overview**: Familiarize yourself with the main interface
3. **Update Definitions**: Ensure virus definitions are up-to-date

### Main Interface

The S&D interface consists of several key sections:

- **Dashboard Tab**: Overview of system status and recent scans
- **Scan Tab**: Configure and execute security scans
- **Reports Tab**: View detailed scan results and history
- **Settings Tab**: Configure application preferences

## Scanning for Threats

### Quick Scan

For basic threat detection:

1. **Open the Scan Tab**
2. **Select "Quick Scan"** from scan type options
3. **Choose scan path** or use default (user home directory)
4. **Click "Start Scan"** to begin

### Full System Scan

For comprehensive system analysis:

1. **Select "Full Scan"** from scan type options
2. **Configure scan depth** and file type filters
3. **Enable "Include System Directories"** for complete coverage
4. **Start the scan** and monitor progress

### Custom Scan

For targeted scanning:

1. **Choose "Custom Scan"** option
2. **Select specific directories** to scan
3. **Configure advanced options**:
   - File size limits
   - File type filters
   - Scan depth restrictions
4. **Execute the custom scan**

### RKHunter Rootkit Scanning

**New in Version 2.3.0**: Enhanced rootkit detection with RKHunter integration.

For advanced rootkit and system security scanning:

1. **Select "RKHunter Scan"** from available scan types
2. **Authentication Required**: 
   - A secure password dialog will appear (pkexec systems)
   - Or enter password in terminal when prompted
   - This is normal - rootkit scanning requires elevated privileges
3. **Monitor Real-time Progress**:
   - Progress bar shows accurate scan progression
   - Stage-based updates with clear descriptions
   - Color-coded results with status indicators
4. **Scan Phases Include**:
   - System command validation
   - Shared library analysis  
   - File properties verification
   - Known rootkit detection
   - Additional security checks
   - Malware scanning
   - Network security analysis
   - System configuration review

**Enhanced Features**:
- ✅ **Real-time Progress**: Accurate progression from 0% to 100%
- ✅ **Visual Feedback**: Color-coded results (green=clean, red=threat, orange=warning)
- ✅ **Detailed Reporting**: Comprehensive scan results with emoji indicators
- ✅ **Authentication Aware**: Progress only advances after successful login

### Real-time Protection

Enable continuous monitoring:

1. **Go to Settings Tab**
2. **Enable "Real-time Monitoring"**
3. **Configure monitored directories**
4. **Set automatic threat responses**

## Managing Scan Results

### Viewing Results

- **Scan Progress**: Monitor real-time scan progress
- **Threat Detection**: View detected threats with details
- **Clean Files**: See count of clean files processed
- **Performance Metrics**: Monitor scan speed and resource usage

### Threat Actions

When threats are detected:

1. **Quarantine**: Safely isolate threats (recommended)
2. **Delete**: Permanently remove threats (use with caution)
3. **Ignore**: Mark as false positive (expert users only)

### Quarantine Management

Access quarantined files:

1. **Open Reports Tab**
2. **Select "Quarantine" section**
3. **View quarantined items** with details
4. **Restore or delete** quarantined files as needed

### Enhanced Report Management

**New in Version 2.3.0**: Unified report management for all scan types.

Managing scan history and reports:

1. **Access Reports Tab** to view all scan results
2. **View Different Report Types**:
   - ClamAV virus scan reports
   - RKHunter rootkit scan reports
   - System scan summaries
3. **Delete All Reports** (Enhanced):
   - Single button removes ALL scan reports
   - Clears both ClamAV and RKHunter history
   - Provides clean slate for new scanning
4. **Export Options**:
   - Save reports in multiple formats
   - Archive important scan results
   - Share reports for analysis

**Report Features**:
- ✅ **Unified Management**: Single interface for all report types
- ✅ **Complete Cleanup**: One action removes all scan history
- ✅ **Multiple Formats**: CSV, JSON, and text exports available
- ✅ **Detailed Information**: Timestamps, scan types, and results

## Advanced Features

### Scheduled Scanning

Set up automatic scans:

1. **Go to Scan Tab**
2. **Expand "Schedule" section**
3. **Configure scan frequency**:
   - Daily, Weekly, or Monthly
   - Specific times and days
4. **Save schedule settings**

### RKHunter Integration

**Updated in Version 2.3.0**: Enhanced rootkit detection with improved user experience.

Advanced rootkit and system security scanning:

1. **Authentication Handling**:
   - Automatic privilege escalation with secure dialogs
   - Clear progress indication during authentication
   - No progress updates until scan actually begins
2. **Enhanced Scan Categories**:
   - System Commands & Binaries
   - Known Rootkit Detection
   - Additional Security Checks
   - Malware Scanning
   - Network Security Analysis
   - System Configuration Review
   - File System Integrity
3. **Real-time Visual Feedback**:
   - Stage-based progress tracking (14 distinct phases)
   - Color-coded results with emoji indicators
   - Enhanced output formatting for better readability
   - Professional scan result presentation

**Key Improvements**:
- ✅ **Authentication Aware**: Progress tracking respects password dialogs
- ✅ **Accurate Progress**: Real-time updates based on actual scan phases  
- ✅ **Enhanced Output**: Color-coded, emoji-rich results display
- ✅ **Error Resilience**: Better handling of authentication and scan errors

### Performance Tuning

Optimize scan performance:

- **Memory Usage**: Adjust memory limits for large scans
- **CPU Priority**: Set scan thread priority
- **Scan Depth**: Limit directory traversal depth
- **File Filters**: Exclude unnecessary file types

## Reports and Analysis

### Scan Reports

Generate detailed reports:

1. **Complete a scan**
2. **Go to Reports Tab**
3. **View scan summary** with statistics
4. **Export reports** in multiple formats:
   - PDF for sharing
   - JSON for analysis
   - CSV for spreadsheet import

### Report Contents

Each report includes:

- **Scan Summary**: Overview of scan results
- **Threat Details**: Information about detected threats
- **System Information**: Hardware and software details
- **Performance Metrics**: Scan speed and resource usage
- **Recommendations**: Suggested actions and improvements

### Historical Analysis

Track security trends:

- **Scan History**: View previous scan results
- **Threat Trends**: Monitor threat detection patterns
- **Performance Tracking**: Analyze scan performance over time

## Configuration and Settings

### General Settings

- **Theme Selection**: Choose light or dark theme
- **Language**: Select interface language
- **Notifications**: Configure alert preferences
- **Auto-updates**: Enable automatic virus definition updates

### Scan Configuration

- **Default Scan Paths**: Set standard scan locations
- **File Type Filters**: Configure which files to scan
- **Exclusion Lists**: Add directories or files to ignore
- **Threat Responses**: Set automatic actions for detected threats

### Security Settings

- **Quarantine Location**: Configure secure quarantine directory
- **Password Protection**: Secure settings and quarantine access
- **Privilege Management**: Configure authentication requirements

## Best Practices

### Regular Scanning

- **Daily Quick Scans**: For routine threat detection
- **Weekly Full Scans**: For comprehensive system analysis
- **Monthly Deep Scans**: Include system directories and archives

### Threat Response

1. **Don't Panic**: False positives can occur
2. **Verify Threats**: Research unknown detections
3. **Quarantine First**: Don't delete immediately
4. **Regular Backups**: Maintain system backups
5. **Update Definitions**: Keep virus definitions current

### System Maintenance

- **Regular Updates**: Keep S&D updated to latest version
- **Definition Updates**: Ensure virus definitions are current
- **Log Review**: Periodically check application logs
- **Performance Monitoring**: Watch for unusual resource usage

## Troubleshooting

### Common Issues

#### Slow Scan Performance

- **Reduce scan depth** to limit directory traversal
- **Exclude large media files** from scans
- **Increase memory limits** for better performance
- **Close other applications** during intensive scans

#### False Positive Detections

- **Research the detection** using online databases
- **Add to exclusion list** if confirmed safe
- **Report false positives** to ClamAV project
- **Restore from quarantine** if necessary

#### Permission Errors

- **Check file permissions** on scan directories
- **Run with appropriate privileges** for system scans
- **Configure polkit policies** for GUI authentication
- **Use "Skip inaccessible files"** option

### Getting Help

For additional support:

- **Built-in Help**: Check application tooltips and help text
- **Documentation**: Review complete documentation set
- **Community**: Join project discussions on GitHub
- **Bug Reports**: Submit issues with detailed information

---

**Next Steps**: Explore [Configuration Guide](Configuration.md) for advanced customization options.
