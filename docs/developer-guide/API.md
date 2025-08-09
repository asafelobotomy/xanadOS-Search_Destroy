# # API Documentation

This document provides API documentation for the xanadOS-Search_Destroy application.

## Core Modules

### app.core.file_scanner

#### FileScanner Class

The main scanning engine for file-based threat detection.

```python
class FileScanner:
    def __init__(self, config: Dict[str, Any])
    def scan_file(self, file_path: str) -> ScanResult
    def scan_directory(self, directory_path: str) -> List[ScanResult]
```

**Methods:**
- `scan_file(file_path)`: Scan a single file for threats
- `scan_directory(directory_path)`: Recursively scan a directory

### app.core.async_scanner

#### AsyncScanner Class

Asynchronous scanning implementation for improved performance.

```python
class AsyncScanner:
    async def scan_async(self, paths: List[str]) -> AsyncGenerator[ScanResult]
    async def batch_scan(self, paths: List[str], batch_size: int = 10)
```

### app.core.clamav_wrapper

#### ClamAVWrapper Class

Integration with ClamAV antivirus engine.

```python
class ClamAVWrapper:
    def is_available(self) -> bool
    def update_database(self) -> bool
    def scan_file_with_clamav(self, file_path: str) -> ScanResult
```

## GUI Modules

### app.gui.main_window

#### MainWindow Class

Main application window and user interface controller.

```python
class MainWindow(QMainWindow):
    def __init__(self)
    def start_scan(self)
    def stop_scan(self)
    def update_progress(self, progress: int)
```

### app.gui.scan_dialog

#### ScanDialog Class

Dialog for configuring scan parameters.

```python
class ScanDialog(QDialog):
    def get_scan_settings(self) -> Dict[str, Any]
    def set_default_settings(self, settings: Dict[str, Any])
```

## Monitoring Modules

### app.monitoring.real_time_monitor

#### RealTimeMonitor Class

Real-time file system monitoring for threat detection.

```python
class RealTimeMonitor:
    def start_monitoring(self, paths: List[str])
    def stop_monitoring(self)
    def add_exclusion(self, path: str)
```

### app.monitoring.file_watcher

#### FileWatcher Class

File system event watcher implementation.

```python
class FileWatcher:
    def watch_directory(self, path: str, callback: Callable)
    def stop_watching(self)
```

## Utility Modules

### app.utils.config

#### Configuration Management

```python
def load_config() -> Dict[str, Any]
def save_config(config: Dict[str, Any]) -> bool
def get_default_config() -> Dict[str, Any]
```

### app.utils.scan_reports

#### Report Generation

```python
class ScanReportGenerator:
    def generate_report(self, results: List[ScanResult]) -> str
    def save_report(self, report: str, filename: str) -> bool
    def export_json(self, results: List[ScanResult]) -> str
```

## Data Models

### ScanResult

```python
@dataclass
class ScanResult:
    file_path: str
    threat_detected: bool
    threat_type: Optional[str]
    confidence: float
    scan_time: datetime
    engine_used: str
    metadata: Dict[str, Any]
```

### ScanSettings

```python
@dataclass  
class ScanSettings:
    scan_type: ScanType
    target_paths: List[str]
    exclude_paths: List[str]
    deep_scan: bool
    follow_symlinks: bool
    max_file_size: int
```

## Events and Callbacks

### Scan Events

The scanning system emits various events that can be handled by the GUI:

```python
# Progress callback
def on_scan_progress(progress: int, current_file: str):
    pass

# Result callback  
def on_scan_result(result: ScanResult):
    pass

# Completion callback
def on_scan_complete(results: List[ScanResult]):
    pass

# Error callback
def on_scan_error(error: Exception):
    pass
```

### Real-time Monitoring Events

```python
# Threat detection callback
def on_threat_detected(file_path: str, threat_info: Dict[str, Any]):
    pass

# File system event callback
def on_file_event(event_type: str, file_path: str):
    pass
```

## Security Features

### Privilege Escalation

```python
def run_with_privileges(command: List[str]) -> subprocess.CompletedProcess
def check_privileges() -> bool
def request_privileges() -> bool
```

### Network Security

```python
class NetworkSecurityManager:
    def enable_firewall(self) -> bool
    def disable_firewall(self) -> bool
    def get_firewall_status(self) -> Dict[str, Any]
    def block_ip(self, ip_address: str) -> bool
```

## Error Handling

All API functions use custom exception types:

```python
class ScannerError(Exception):
    pass

class ConfigurationError(Exception):
    pass

class PermissionError(Exception):
    pass

class NetworkError(Exception):
    pass
```

## Usage Examples

### Basic File Scanning

```python
from app.core.file_scanner import FileScanner

scanner = FileScanner(config)
result = scanner.scan_file("/path/to/file")

if result.threat_detected:
    print(f"Threat detected: {result.threat_type}")
```

### Asynchronous Directory Scanning

```python
import asyncio
from app.core.async_scanner import AsyncScanner

async def scan_directory():
    scanner = AsyncScanner()
    async for result in scanner.scan_async(["/path/to/dir"]):
        print(f"Scanned: {result.file_path}")

asyncio.run(scan_directory())
```

### Real-time Monitoring

```python
from app.monitoring.real_time_monitor import RealTimeMonitor

def threat_callback(file_path, threat_info):
    print(f"Threat detected in {file_path}")

monitor = RealTimeMonitor()
monitor.set_threat_callback(threat_callback)
monitor.start_monitoring(["/home", "/tmp"])
```

## Configuration

### Default Configuration Structure

```json
{
  "scanning": {
    "engines": ["clamav", "custom"],
    "max_file_size": 104857600,
    "follow_symlinks": false,
    "scan_archives": true
  },
  "monitoring": {
    "enabled": true,
    "watch_paths": ["/home"],
    "exclude_paths": ["/proc", "/sys"]
  },
  "security": {
    "require_privileges": true,
    "firewall_integration": true
  }
}
```

For more detailed information, see the source code and inline documentation.
