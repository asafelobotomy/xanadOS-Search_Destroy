# xanadOS Search & Destroy - AI Agent Instructions

## Project Overview

A comprehensive Linux security scanner and protection suite combining ClamAV signature-based detection, YARA heuristic analysis, real-time file system monitoring, and automated system hardening. Built with Python 3.13+, PyQt6 GUI, FastAPI REST API/WebSocket backend, and enterprise-grade security frameworks.

**Technology Stack**: Python 3.13+, PyQt6, FastAPI/uvicorn, aiohttp, watchdog, Redis, SQLAlchemy, YARA, ClamAV, PolicyKit, systemd

## Core Architecture

### Security-First Design Philosophy

This is a **security application** - every operation must be validated and sanitized:

- **Input Validation**: ALL user inputs MUST be validated using `app/core/input_validation.py` patterns
  - File paths: Use `validate_file_path()`, `is_safe_path()`, `check_path_traversal()`
  - Check against `FORBIDDEN_PATHS`: `/proc`, `/sys`, `/dev`, `/boot`, `/etc/shadow`, etc.
  - Maximum limits enforced: `MAX_FILE_SIZE` (100MB), `MAX_SCAN_DEPTH` (10), `MAX_FILES_PER_SCAN` (10K)

- **Privilege Escalation**: Use `app/core/security_integration.py` framework - NEVER raw `sudo`
  ```python
  # ✅ CORRECT: Use security framework
  from app.core.security_integration import elevate_privileges
  result = elevate_privileges(command=["systemctl", "restart", "clamav-daemon"])

  # ❌ WRONG: Direct execution (security vulnerability)
  subprocess.run(["sudo", user_input])  # NEVER DO THIS - shell injection risk
  ```

- **PolicyKit Integration**: All privileged operations require policies in `config/*.policy`
  - Example: `io.github.asafelobotomy.searchanddestroy.policy`
  - Actions must be declared before use: `org.freedesktop.policykit.exec`

- **Command Validation**: Use `app/utils/process_management.py::execute_with_privilege()`
  - Validates command structure before execution
  - Prevents shell injection via command whitelist
  - Logs all privileged operations for audit

### Scanner Architecture (Hybrid Multi-Engine)

**Primary Components**:

1. **UnifiedScannerEngine** (`app/core/unified_scanner_engine.py`):
   - Main orchestrator coordinating ClamAV + YARA engines
   - **Result Caching**: 70-80% performance gain via SHA256 hash + mtime cache
     - Cache location: `~/.cache/search-and-destroy/scan_cache.db`
     - Cache key format: `f"{file_hash}:{file_mtime}"`
     - NEVER bypass cache without explicit reason (performance regression)
   - Quarantine management with secure 0700 permissions
   - Progress callbacks via `add_progress_callback(callback)`
   - **Concurrent Scan Prevention**: Only ONE scan type active at a time

2. **ClamAV Integration** (`app/core/clamav_wrapper.py`):
   - Signature-based malware detection
   - Daemon detection and fallback to direct scanning
   - Automatic definition updates via `freshclam`
   - Returns `ScanResult` with threat_level, description, engine info

3. **YARA Scanner** (`app/core/yara_scanner.py`):
   - Heuristic/behavioral malware detection
   - Rules in `config/yara_rules/*.yar`
   - Custom rule compilation with metadata extraction
   - Returns `YaraScanResult` with matched rules and severity

4. **Hybrid Scanner** (`app/core/hybrid_scanner.py`):
   - Combines ClamAV + YARA results
   - Weighted threat scoring algorithm
   - Returns `HybridScanResult` with aggregated confidence

### Threading & Concurrency Architecture

**UnifiedThreadingManager** (`app/core/unified_threading_manager.py`):
- Consolidates 9 threading/async modules (4,291 lines → 1 unified system)
- **Resource Management**:
  - Adaptive thread pool sizing (2-8 threads based on CPU cores)
  - Resource semaphores: `max_file_operations=50`, `max_ml_operations=5`, `max_scan_operations=20`
  - Deadlock prevention via timeout enforcement

- **Thread Types**:
  - `IO_BOUND`: File operations, network requests (use ThreadPoolExecutor)
  - `CPU_BOUND`: Hashing, encryption, ML inference (use ProcessPoolExecutor)
  - `GUI`: Qt operations (MUST run on main thread)

- **Async Patterns**:
  ```python
  # Async file operations
  from app.core.unified_threading_manager import async_scan_directory
  results = await async_scan_directory(scanner, "/path", recursive=True)

  # GUI scan thread (cooperative cancellation)
  thread = manager.create_scan_thread(
      scan_func=scanner.scan_directory,
      scan_args=("/path",),
      priority=TaskPriority.HIGH
  )
  thread.finished.connect(on_scan_complete)
  thread.start()
  ```

- **Cooperative Cancellation**: Threads check `self._cancel_requested` flag regularly
  - GUI threads emit `finished` signal even when cancelled
  - Use `CooperativeCancellationMixin` for custom threads

### Real-Time Monitoring (`app/monitoring/file_watcher.py`)

**Multi-Backend Architecture** (performance-ordered):
1. **fanotify** (Linux kernel-level, requires root) - BEST performance, requires `FANOTIFY_AVAILABLE=True`
2. **watchdog** (cross-platform, inotify on Linux) - RECOMMENDED, `WATCHDOG_AVAILABLE=True`
3. **Polling fallback** (universal, no dependencies) - Last resort

**Features**:
- Event debouncing and throttling to prevent scan storms
- Configurable exclusions (`.git/`, `node_modules/`, `__pycache__/`)
- Async mode via `enable_async_mode()` for async generators
- Event types: `FILE_CREATED`, `FILE_MODIFIED`, `FILE_DELETED`, `FILE_MOVED`

**Usage Pattern**:
```python
from app.monitoring.file_watcher import FileSystemWatcher, WatchEventType

watcher = FileSystemWatcher()
watcher.watch_directory("/home/user", recursive=True)

async for event in watcher.async_events():
    if event.event_type == WatchEventType.FILE_CREATED:
        await scanner.scan_file_async(event.file_path)
```

### Component Organization (Strict Separation)

```
app/
├── core/          # Business logic, NO GUI dependencies (PyQt6 imports forbidden)
│   ├── unified_scanner_engine.py      # Main scanner orchestrator
│   ├── security_integration.py        # Security operations coordinator
│   ├── input_validation.py            # Security validation patterns
│   ├── unified_threading_manager.py   # Thread/async management
│   ├── clamav_wrapper.py              # ClamAV integration
│   ├── yara_scanner.py                # YARA integration
│   └── hybrid_scanner.py              # Multi-engine coordination
│
├── gui/           # PyQt6 interface (imports core/, never vice versa)
│   ├── main_window.py                 # Main window with tab management
│   ├── system_hardening_tab.py        # Security hardening UI
│   ├── security_dashboard.py          # Real-time monitoring dashboard
│   └── setup_wizard.py                # First-time setup wizard
│
├── api/           # FastAPI REST/WebSocket endpoints
│   ├── web_dashboard.py               # Web-based security dashboard
│   └── client_sdk.py                  # Python SDK for API clients
│
├── monitoring/    # Real-time file watching
│   └── file_watcher.py                # Multi-backend file monitoring
│
├── utils/         # Utilities (config, logging, process management)
│   ├── config.py                      # XDG-compliant config management
│   ├── process_management.py          # Safe command execution
│   └── permission_manager.py          # Permission handling
│
├── gpu/           # GPU-accelerated scanning (optional)
│   └── acceleration.py                # CUDA/OpenCL hash computation
│
└── ml/            # Machine learning threat detection (optional)
    └── threat_detector.py             # ML-based heuristic analysis
```

**Import Rules**:
- `core/` → Cannot import from `gui/`, `api/`
- `gui/` → Can import from `core/`, `utils/`
- `api/` → Can import from `core/`, `utils/`
- Tests mirror `app/` structure: `tests/test_core/`, `tests/test_gui/`

## Development Workflow

### Setup & Dependencies

**One-Command Setup** (handles everything):
```bash
make setup           # Installs uv, Python deps, system deps, pre-commit hooks
```

**Manual Steps**:
```bash
make setup-python-env    # Create .venv with uv or python3
make install-deps        # Install dependencies (uv sync --all-extras OR pip install -e .)
make validate            # Run validation (npm run quick:validate)
```

**Package Manager Preference**:
- Use `uv` (modern, fast Rust-based package manager) over `pip`
- `uv sync --all-extras` installs dependencies from `pyproject.toml`
- Optional dependency groups: `[security]`, `[malware-analysis]`, `[advanced]`, `[dev]`

**System Dependencies** (Debian/Ubuntu):
```bash
sudo apt install clamav clamav-daemon freshclam yara python3-dev build-essential
```

### Testing

```bash
python -m pytest tests/              # All tests
python -m pytest tests/test_core/    # Core logic only
python -m pytest tests/test_gui.py -v  # GUI tests (mocked PyQt6)
python -m pytest -k test_scanner     # Specific test pattern
python -m pytest --cov=app           # With coverage
```

**Test Fixtures** (`tests/conftest.py`):
- `mock_pyqt`: Auto-mocks all PyQt6 modules for headless testing
- `temp_workspace`: Provides temporary directory (auto-cleanup)
- `mock_file_system`: Creates common directory structure
- All fixtures have session/function scope management

**Test Structure Rules**:
- Mirror `app/` structure: `app/core/scanner.py` → `tests/test_core/test_scanner.py`
- Use descriptive test names: `test_scanner_detects_malware_with_clamav()`
- Mock external dependencies (ClamAV, network, filesystem)

### Running the Application

```bash
make run                    # Preferred (handles environment setup)
python -m app.main          # Alternative (direct Python execution)
python -m app.main --skip-policy-check  # Skip PolicyKit verification
```

**Entry Point Details** (`app/main.py`):
1. **Single-Instance Guard**: Uses Unix socket in `/tmp/` to prevent multiple instances
2. **Splash Screen**: `ModernSplashScreen` with progressive loading phases
3. **Setup Wizard**: First-time setup for PolicyKit policies and ClamAV
4. **Progressive Loading**: 5 phases (UI init, cache, system check, dashboard, finalization)
5. **Wayland Compatibility**: Sets `QT_WAYLAND_DISABLE_WINDOWDECORATION=1` automatically

## Critical Conventions

### Configuration Management (XDG-Compliant)

**Directory Structure**:
- Config: `~/.config/search-and-destroy/config.json`
- Data: `~/.local/share/search-and-destroy/` (logs, quarantine, reports)
- Cache: `~/.cache/search-and-destroy/` (scan cache, temporary files)

**Loading Configuration**:
```python
from app.utils.config import load_config, save_config, CONFIG_DIR, DATA_DIR, CACHE_DIR

config = load_config()  # Returns dict, auto-creates dirs with 0700 perms
# Modify config
config["scan_settings"]["max_depth"] = 15
save_config(config)  # Explicit save required - NO auto-save
```

**CRITICAL**: Config is **NEVER** auto-saved:
- Prevents corruption from crashes mid-write
- Explicit `save_config()` call required
- Atomic write via temp file + rename for safety

### Security Patterns (Critical for Security Application)

**Path Validation** (ALWAYS required):
```python
from app.core.input_validation import (
    validate_file_path,
    is_safe_path,
    check_path_traversal,
    FORBIDDEN_PATHS
)

# Example: Validate user-provided scan path
user_path = "/home/user/Downloads"

# Step 1: Basic validation
validate_file_path(user_path)  # Raises SecurityValidationError if invalid

# Step 2: Safety check
if not is_safe_path(user_path):
    raise SecurityError(f"Path {user_path} is in forbidden locations")

# Step 3: Path traversal check
if check_path_traversal(user_path, base_dir="/home/user"):
    raise SecurityError("Path traversal detected")

# Now safe to scan
result = scanner.scan_directory(user_path)
```

**Privilege Escalation** (Use security framework):
```python
from app.core.security_integration import SecurityIntegrationCoordinator

security = SecurityIntegrationCoordinator()

# Example: Restart ClamAV daemon (requires root)
result = security.elevate_privileges(
    command=["systemctl", "restart", "clamav-daemon"],
    reason="Update virus definitions"
)

if result.success:
    logger.info("ClamAV daemon restarted successfully")
else:
    logger.error(f"Failed: {result.error_message}")
```

**Command Execution** (Safe subprocess usage):
```python
from app.utils.process_management import execute_with_privilege

# Validated command execution with timeout
result = execute_with_privilege(
    command=["freshclam", "--quiet"],
    timeout=300,  # 5 minutes
    method="pkexec"  # Uses PolicyKit
)

if result.returncode == 0:
    logger.info("Definitions updated")
```

### Threading & Async Patterns

**GUI Thread Safety** (PyQt6 requirement):
```python
from PyQt6.QtCore import QTimer

# ✅ CORRECT: Schedule GUI update on main thread
QTimer.singleShot(0, lambda: self.update_progress_bar(value))

# ❌ WRONG: Direct GUI update from worker thread (crashes)
self.progress_bar.setValue(value)  # NEVER from worker thread
```

**Scanner Thread Creation**:
```python
from app.core.unified_threading_manager import UnifiedThreadingManager, TaskPriority

manager = UnifiedThreadingManager()

# Create scan thread with automatic resource management
thread = manager.create_scan_thread(
    scan_func=self.scanner.scan_directory,
    scan_args=("/home/user/Downloads",),
    priority=TaskPriority.HIGH,
    callback=self.on_scan_complete
)

# Connect signals
thread.progress_updated.connect(self.update_progress)
thread.result_ready.connect(self.handle_result)
thread.error_occurred.connect(self.handle_error)
thread.finished.connect(self.cleanup)

# Start scanning
thread.start()

# Cancel if needed (cooperative)
thread.request_cancel()
```

**Async File Operations**:
```python
import aiofiles
from pathlib import Path

async def scan_files_async(file_paths: list[Path]):
    results = []
    async for path in file_paths:
        async with aiofiles.open(path, 'rb') as f:
            content = await f.read()
            result = await scanner.scan_bytes_async(content)
            results.append(result)
    return results
```

### Type Hints & Modern Python (3.13+)

**Use Modern Syntax**:
```python
# ✅ CORRECT: Python 3.13 union syntax
def scan_file(path: str | Path) -> ScanResult | None:
    results: list[dict[str, Any]] = []

# ❌ WRONG: Old typing module syntax
from typing import Optional, List, Dict, Any
def scan_file(path: Union[str, Path]) -> Optional[ScanResult]:
    results: List[Dict[str, Any]] = []
```

**Dataclasses** (Preferred over dicts):
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ScanProgress:
    current_file: str
    files_scanned: int
    total_files: int
    threats_found: int
    start_time: datetime = field(default_factory=datetime.utcnow)

    @property
    def completion_percentage(self) -> float:
        return (self.files_scanned / self.total_files) * 100
```

**Type Checking**:
- `mypy` enforced via pre-commit hooks
- Config: `config/mypy.ini`
- Strict mode enabled: `strict = true`

## Advanced Topics

### API Development (FastAPI/WebSocket)

**Web Dashboard** (`app/api/web_dashboard.py`):
- FastAPI app with CORS middleware
- WebSocket support for real-time updates
- REST endpoints: `/api/health`, `/api/scan`, `/api/threats`
- Serves dashboard at `http://localhost:8000/`

**Client SDK** (`app/api/client_sdk.py`):
- Python client library for programmatic API access
- Handles authentication, rate limiting, retries
- Example usage:
  ```python
  from app.api.client_sdk import SecurityClient

  client = SecurityClient("http://localhost:8000")
  scan_result = await client.scan_file("/path/to/file")
  ```

### YARA Rule Development

**Rule Location**: `config/yara_rules/*.yar`

**Example Rule Structure**:
```yara
rule Suspicious_ELF_Binary {
    meta:
        description = "Detects suspicious ELF binaries"
        author = "xanadOS Security"
        severity = "medium"

    strings:
        $elf_magic = { 7F 45 4C 46 }
        $execve = "execve"
        $chmod = "chmod"

    condition:
        $elf_magic at 0 and 2 of ($execve, $chmod)
}
```

**Testing YARA Rules**:
```bash
# Test rule compilation
yara -C config/yara_rules/malware_detection.yar

# Test against sample file
yara config/yara_rules/malware_detection.yar /path/to/test/file
```

### GPU Acceleration (`app/gpu/acceleration.py`)

**Optional CUDA/OpenCL Support**:
- Accelerates SHA256 hashing for large files
- Requires NVIDIA GPU with CUDA or OpenCL runtime
- Fallback to CPU if GPU unavailable
- 5-10x speedup for hash computation

**Usage**:
```python
from app.gpu.acceleration import gpu_hash_file

# Automatic GPU/CPU selection
file_hash = gpu_hash_file("/path/to/large/file.iso")
```

### Machine Learning Threat Detection (`app/ml/`)

**Optional ML-based Heuristics**:
- Behavioral analysis using scikit-learn models
- Trained on benign/malware samples
- Complements signature-based detection
- Requires `[malware-analysis]` dependencies

### Packaging & Distribution

**Supported Formats**:
- **Debian/Ubuntu**: `.deb` packages (`packaging/debian/`)
- **Fedora/RHEL**: `.rpm` packages (`packaging/rpm/`)
- **Arch Linux**: AUR package (`packaging/aur/`)
- **AppImage**: Portable Linux binary (`build/appimage/`)

**Build Commands**:
```bash
# Debian package
cd packaging/debian && dpkg-buildpackage -us -uc

# RPM package
cd packaging/rpm && rpmbuild -ba xanados-search-destroy.spec

# AppImage (requires appimagetool)
bash build/appimage/build-appimage.sh
```

**Release Process**:
1. Update `VERSION` file and `CHANGELOG.md`
2. Tag release: `git tag -a v2.10.0 -m "Release 2.10.0"`
3. Build packages for all distributions
4. Upload to GitHub releases
5. Submit to distribution repositories

## Common Tasks

### Adding a New Scanner Feature

1. **Implement Core Logic** (`app/core/`):
   ```python
   # app/core/custom_scanner.py
   from dataclasses import dataclass

   @dataclass
   class CustomScanResult:
       file_path: str
       is_threat: bool
       confidence: float

   class CustomScanner:
       def scan_file(self, path: str) -> CustomScanResult:
           # Implementation
           pass
   ```

2. **Integrate with UnifiedScannerEngine**:
   ```python
   # app/core/unified_scanner_engine.py
   from .custom_scanner import CustomScanner

   class UnifiedScannerEngine:
       def __init__(self):
           self.custom_scanner = CustomScanner()

       async def scan_file_async(self, path):
           custom_result = self.custom_scanner.scan_file(path)
           # Combine with existing results
   ```

3. **Add GUI Integration** (`app/gui/`):
   ```python
   # app/gui/scan_tab.py
   def on_custom_scan_clicked(self):
       thread = self.manager.create_scan_thread(
           scan_func=self.scanner.custom_scanner.scan_file,
           scan_args=(self.path_input.text(),)
       )
       thread.start()
   ```

4. **Write Tests** (`tests/test_core/test_custom_scanner.py`):
   ```python
   def test_custom_scanner_detects_threat(tmp_path):
       scanner = CustomScanner()
       test_file = tmp_path / "malware.exe"
       test_file.write_bytes(b"malicious content")

       result = scanner.scan_file(str(test_file))
       assert result.is_threat
       assert result.confidence > 0.8
   ```

5. **Update Documentation**:
   - Add entry to `CHANGELOG.md` under "Added" section
   - Update `docs/developer/scanner_architecture.md`

### Adding Security Validation Rules

1. **Define Validation** (`app/core/input_validation.py`):
   ```python
   def validate_network_url(url: str) -> None:
       """Validate URL for security (prevent SSRF)."""
       if not url.startswith(("http://", "https://")):
           raise SecurityValidationError("Invalid URL protocol")

       # Block internal IPs
       parsed = urlparse(url)
       if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
           raise SecurityValidationError("Internal IP blocked")
   ```

2. **Add PolicyKit Policy** (if privilege needed):
   ```xml
   <!-- config/io.github.asafelobotomy.searchanddestroy.network.policy -->
   <policyconfig>
     <action id="org.freedesktop.policykit.network.scan">
       <description>Perform network security scan</description>
       <message>Authentication required for network scan</message>
       <defaults>
         <allow_any>no</allow_any>
         <allow_inactive>no</allow_inactive>
         <allow_active>auth_admin</allow_active>
       </defaults>
     </action>
   </policyconfig>
   ```

3. **Use SecurityIntegrationCoordinator**:
   ```python
   from app.core.security_integration import SecurityIntegrationCoordinator

   security = SecurityIntegrationCoordinator()
   response = security.process_security_request(
       SecurityRequest(
           user_id="current_user",
           resource=url,
           action="network_scan",
           context={"url": url}
       )
   )
   ```

4. **Test Edge Cases**:
   ```python
   def test_network_url_validation():
       # Test path traversal
       with pytest.raises(SecurityValidationError):
           validate_network_url("http://localhost/../../etc/passwd")

       # Test SSRF prevention
       with pytest.raises(SecurityValidationError):
           validate_network_url("http://127.0.0.1/admin")

       # Test valid URL
       validate_network_url("https://example.com/api/scan")
   ```

### Debugging Common Issues

**ClamAV Not Detecting**:
```bash
# Check daemon status
systemctl status clamav-daemon

# Update definitions manually
sudo freshclam

# Check logs
tail -f ~/.local/share/search-and-destroy/logs/scanner.log
```

**Qt GUI Crashes**:
```bash
# Enable Qt debugging
export QT_DEBUG_PLUGINS=1
python -m app.main

# Check for thread safety violations (GUI updates from worker threads)
```

**Scanner Performance Issues**:
```bash
# Check cache status
sqlite3 ~/.cache/search-and-destroy/scan_cache.db "SELECT COUNT(*) FROM cache;"

# Clear cache if corrupted
rm ~/.cache/search-and-destroy/scan_cache.db

# Monitor resource usage
htop -p $(pgrep -f "python.*app.main")
```

**Test Failures**:
```bash
# Run with verbose output
python -m pytest -vv tests/test_core/test_scanner.py

# Debug specific test
python -m pytest --pdb tests/test_core/test_scanner.py::test_scan_file

# Check for mocking issues (PyQt6 not properly mocked)
python -m pytest --tb=short tests/test_gui.py
```

## Anti-Patterns (Critical - What NOT to Do)

❌ **Temp files in project root** → Use `archive/` or `tempfile.mkdtemp()`
❌ **GUI code in `app/core/`** → Strict separation enforced (breaks headless mode)
❌ **Raw shell execution** → Use `app.utils.process_management.execute_with_privilege()`
❌ **Auto-save config** → Explicit `save_config()` only (prevents corruption)
❌ **Custom threading** → Use `UnifiedThreadingManager` (resource limits + deadlock prevention)
❌ **Bypass scanner cache** → 70-80% performance loss without good reason
❌ **Hardcoded paths** → Use XDG variables: `CONFIG_DIR`, `DATA_DIR`, `CACHE_DIR`
❌ **Importing `typing.Optional`** → Use `str | None` (Python 3.13 syntax)
❌ **Direct `subprocess.run()`** → Validate commands with `input_validation.py`
❌ **GUI updates from threads** → Use `QTimer.singleShot()` or signals

## Key Files Reference

### Core Scanner Files
- `app/core/unified_scanner_engine.py` - Main scanner orchestrator (1,076 lines)
- `app/core/unified_threading_manager.py` - Thread/async management (1,059 lines)
- `app/core/security_integration.py` - Security coordinator (830 lines)
- `app/core/input_validation.py` - Security validation patterns (405 lines)

### Integration Files
- `app/core/clamav_wrapper.py` - ClamAV signature detection
- `app/core/yara_scanner.py` - YARA heuristic analysis
- `app/core/hybrid_scanner.py` - Multi-engine result aggregation
- `app/monitoring/file_watcher.py` - Real-time file monitoring (831 lines)

### GUI Files
- `app/gui/main_window.py` - Main window with tab management
- `app/gui/security_dashboard.py` - Real-time monitoring dashboard
- `app/gui/system_hardening_tab.py` - Security hardening interface

### Configuration & Utils
- `app/utils/config.py` - XDG-compliant config management (720 lines)
- `app/utils/process_management.py` - Safe command execution
- `tests/conftest.py` - Test fixtures and PyQt6 mocking (308 lines)

### Build & Packaging
- `pyproject.toml` - Dependencies, entry points, build config (1,008 lines)
- `Makefile` - Development commands (289 lines)
- `packaging/debian/` - Debian/Ubuntu packaging
- `packaging/rpm/` - Fedora/RHEL packaging

### Configuration Files
- `config/*.policy` - PolicyKit security policies
- `config/yara_rules/*.yar` - YARA malware detection rules
- `config/security_config.toml` - Security framework configuration

## Documentation Structure

- **User Guides**: `docs/user/` - Installation, usage, troubleshooting
- **Developer Docs**: `docs/developer/` - Architecture, API reference
- **Implementation**: `docs/implementation/` - Implementation reports, decisions
- **Project Docs**: `docs/project/` - Roadmap, structure, governance
- **Architecture**: `docs/PROJECT_STRUCTURE.md`, `CONTRIBUTING.md`
- **Changelog**: `CHANGELOG.md` - Version history with semantic versioning
