# API Documentation

This document provides comprehensive API documentation for the xanadOS-Search_Destroy application (S&D - Search & Destroy).

**Version**: 2.7.0
**Updated**: August 19, 2025

## Core Modules

### app.core.clamav_wrapper

#### ClamAVWrapper Class

Enhanced ClamAV integration with full feature support and performance optimizations.

```Python
class ClamAVWrapper:
    def **init**(self, config: Optional[Dict[str, Any]] = None)
    def scan_file(self, file_path: str, use_daemon: bool = True, **kwargs) -> ScanFileResult
    def scan_directory(self, directory_path: str, **kwargs) -> List[ScanFileResult]
    def should_scan_file(self, file_path: str, quick_scan: bool = False) -> bool
    def update_virus_definitions(self) -> bool
    def start_daemon(self) -> bool
    def apply_2025_security_hardening(self) -> Dict[str, bool]
    def get_2025_performance_settings(self) -> Dict[str, Any]
    def implement_multithreaded_scanning(self, file_list: List[str], max_workers: int = None) -> List[Dict[str, Any]]
```

## Key Features

- Daemon-based scanning for 3-10x performance improvement
- Smart file filtering with risk-based analysis
- Security hardening with 2025 best practices
- Multi-threaded parallel scanning support

### app.core.file_scanner

#### FileScanner Class

The main scanning engine with quarantine management and scheduling.

```Python
class FileScanner:
    def **init**(self, clamav_wrapper: Optional[ClamAVWrapper] = None)
    def scan_file(self, file_path: str, scan_id: Optional[str] = None, **kwargs) -> ScanFileResult
    def scan_directory(self, directory_path: str, **kwargs) -> List[ScanFileResult]
    def validate_scan_directory(self, directory_path: str) -> dict
    def update_virus_definitions(self) -> bool
    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None
    def set_detailed_progress_callback(self, callback: Callable[[dict], None]) -> None
    def set_result_callback(self, callback: Callable[[ScanFileResult], None]) -> None
```

## Advanced Features

- Rate limiting and memory optimization
- Quarantine management with secure isolation
- Scheduled scanning capabilities
- Real-time progress tracking

### app.core.rkhunter_wrapper

#### RKHunterWrapper Class

RKHunter rootkit detection integration with optimization support.

```Python
class RKHunterWrapper:
    def **init**(self, config: Optional[Dict[str, Any]] = None)
    def run_scan(self, categories: List[str] = None, **kwargs) -> RKHunterScanResult
    def update_database(self) -> bool
    def get_available_tests(self) -> List[str]
    def check_system_integrity(self) -> Dict[str, Any]
```

## GUI Modules

### app.gui.main_window

#### MainWindow Class

Main application window and user interface controller with modern PyQt6 interface.

```Python
class MainWindow(QMainWindow):
    def **init**(self)
    def start_scan(self)
    def stop_scan(self)
    def update_progress(self, progress: int)
    def switch_theme(self, theme_name: str)
    def show_scan_results(self, results: List[ScanFileResult])
```

### app.gui.scan_dialog

#### ScanDialog Class

Dialog for configuring advanced scan parameters.

```Python
class ScanDialog(QDialog):
    def get_scan_settings(self) -> Dict[str, Any]
    def set_default_settings(self, settings: Dict[str, Any])
    def configure_scan_options(self) -> ScanConfiguration
```

### app.gui.rkhunter_components

#### RKHunterScanDialog Class

Specialized dialog for RKHunter rootkit scan configuration.

```Python
class RKHunterScanDialog(QDialog):
    def **init**(self, parent=None)
    def get_selected_categories(self) -> List[str]
    def apply_theme(self, theme_name: str)
```

#### RKHunterScanThread Class

Non-blocking thread for RKHunter scan execution.

```Python
class RKHunterScanThread(QThread):
    progress_updated = pyqtSignal(str, int)
    scan_completed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
```

## Utility Modules

### app.utils.config

#### Configuration Management

Centralized configuration system with validation and defaults.

```Python
def load_config() -> Dict[str, Any]
def save_config(config: Dict[str, Any]) -> bool
def get_default_config() -> Dict[str, Any]
def validate_config(config: Dict[str, Any]) -> bool
def setup_logging() -> logging.Logger
```

### app.utils.scan_reports

#### ScanReportManager Class

Advanced report generation and export system.

```Python
class ScanReportManager:
    def **init**(self, config: Dict[str, Any])
    def generate_report(self, results: List[ScanResult], format: str = "JSON") -> str
    def save_report(self, report_data: Dict[str, Any], filename: str) -> bool
    def export_to_html(self, results: List[ScanResult]) -> str
    def export_to_csv(self, results: List[ScanResult]) -> str
    def get_recent_reports(self, days: int = 7) -> List[Dict[str, Any]]
```

## Data Types and Enums

### Core Data Types

```Python
@dataclass
class ScanFileResult:
    file_path: str
    result: ScanResult
    threat_name: Optional[str] = None
    threat_type: Optional[str] = None
    file_size: int = 0
    scan_time: float = 0.0
    error_message: Optional[str] = None

class ScanResult(Enum):
    CLEAN = "clean"
    INFECTED = "infected"
    SUSPICIOUS = "suspicious"
    ERROR = "error"
    SKIPPED = "skipped"

class ScanType(Enum):
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    RKHUNTER = "rkhunter"

@dataclass
class MonitorConfig:
    paths_to_watch: List[str]
    excluded_paths: List[str]
    excluded_extensions: List[str]
    scan_new_files: bool = True
    scan_modified_files: bool = True
    max_file_size: int = 100 _1024_ 1024  # 100MB
```

### Event Types

```Python
class WatchEventType(Enum):
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    DIRECTORY_CREATED = "directory_created"
    DIRECTORY_DELETED = "directory_deleted"

@dataclass
class WatchEvent:
    event_type: WatchEventType
    file_path: str
    timestamp: float
    size: int = 0
    is_directory: bool = False
```

## Security and Performance Features

### Security Enhancements

- **Input Validation**: All paths and parameters validated through `PathValidator`
- **Privilege Management**: Secure elevation using `pkexec` and modern authentication
- **Sandboxing**: Full Flatpak compatibility with restricted permissions
- **Rate Limiting**: Protection against resource exhaustion attacks

### Performance Optimizations

- **ClamAV Daemon**: 3-10x faster scanning with memory-resident database
- **Smart Filtering**: Risk-based file selection reduces scanning overhead by 50-80%
- **Async Operations**: Non-blocking UI with background processing
- **Memory Management**: Intelligent garbage collection and resource monitoring

### Modern Python Features

- **Type Hints**: Comprehensive type annotations throughout
- **Dataclasses**: Modern data structures with automatic methods
- **Async/Await**: Asynchronous operations where beneficial
- **Context Managers**: Proper resource management and cleanup
- **Pathlib**: Modern path handling with `Path` objects

---

**Note**: This API documentation covers the core public interfaces.
For detailed implementation examples and usage patterns, see the comprehensive implementation documentation in the `docs/implementation/` directory.

## Additional Resources

- **User Manual**: See `docs/user/User_Manual.md` for end-user documentation
- **Development Guide**: See `docs/developer/DEVELOPMENT.md` for setup instructions
- **Implementation Docs**: See `docs/implementation/` for detailed technical documentation
- **ClamAV Integration**: See `docs/developer/ClamAV_Implementation_Summary.md` for ClamAV-specific details

---

**Last updated:**August 19, 2025 |**Version:** 2.7.0
