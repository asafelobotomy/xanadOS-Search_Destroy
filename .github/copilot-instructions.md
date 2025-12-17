# xanadOS Search & Destroy - AI Agent Instructions

## Project Overview

A comprehensive Linux security scanner and protection suite combining ClamAV signature-based detection, YARA heuristic analysis, real-time file system monitoring, and automated system hardening. Built with Python 3.13+, PyQt6 GUI, FastAPI REST API/WebSocket backend, and enterprise-grade security frameworks.

**Current Version**: 0.3.0-beta
**Technology Stack**: Python 3.13+, PyQt6, FastAPI/uvicorn, aiohttp, watchdog, Redis, SQLAlchemy, YARA, ClamAV, PolicyKit, systemd
**Package Management**: `uv` (Python), `pnpm` (Node.js), `fnm` (Node version management)

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
make validate            # Run validation via npm run quick:validate
```

**CRITICAL**: There is **NO package.json** in this project. Validation runs via bash scripts:
- `make validate` → executes bash validation scripts via Make targets
- Validation scripts are in `scripts/tools/validation/`
- Do NOT expect `npm install` or Node.js dependencies (legacy documentation artifact)

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

### Validation & Quality Assurance

**Validation System** (bash-based, NO package.json):
```bash
make validate                       # Primary validation command
# Internally calls: bash scripts/tools/validation/enhanced-quick-validate.sh

# Alternative invocation (equivalent)
bash scripts/tools/validation/enhanced-quick-validate.sh
```

**Validation Phases** (from `scripts/tools/validation/enhanced-quick-validate.sh`):
1. **Development Tools**: Checks for `uv`, `pnpm`, `fnm` availability
2. **Core Infrastructure**: Python environment, directory structure
3. **Essential Validation**: Markdown linting, spell checking, version sync
4. **Code Quality**: Python code quality (non-blocking warnings)

**Common Validation Commands**:
```bash
make validate                       # Quick validation (recommended)
bash scripts/tools/validation/validate-structure.sh  # Structure validation
bash scripts/tools/quality/check-python.sh          # Python quality only
bash scripts/tools/security/privilege-escalation-audit.py  # Security audit
```

**IMPORTANT**: The project references `npm run quick:validate` in documentation, but this is **legacy**. Use `make validate` or direct bash script invocation instead.

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

### ML Development Conventions (Phase 3)

**SECURITY-FIRST ML DEVELOPMENT**:

**Rule #1: NEVER Execute Malware**
```python
# ❌ FORBIDDEN: ANY form of execution
import subprocess
subprocess.run([malware_path])              # NEVER
os.system(f"chmod +x {malware_path}")      # NEVER
exec(open(malware_path).read())             # NEVER
import importlib; importlib.import_module() # NEVER with untrusted code

# ✅ CORRECT: Static analysis ONLY
with open(malware_path, 'rb') as f:
    content = f.read()  # Read bytes only
    features = extract_features(content)  # Feature extraction, no execution
```

**Rule #2: Verify Everything**
```python
# ✅ CORRECT: Hash verification pattern
def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verify file hasn't been tampered with."""
    computed_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if computed_hash.lower() != expected_hash.lower():
        logger.error(f"Hash mismatch: {file_path}")
        # Quarantine corrupted file
        quarantine_path = QUARANTINE_DIR / file_path.name
        shutil.move(file_path, quarantine_path)
        return False
    return True

# ✅ CORRECT: Always verify before processing
if not verify_file_integrity(malware_sample, metadata['sha256']):
    raise SecurityError("File integrity check failed")
```

**Rule #3: Fail-Safe File Operations**
```python
# ✅ CORRECT: Secure file permissions
import stat

# Save malware with restrictive permissions (0600)
malware_path.write_bytes(content)
malware_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # Owner read/write only

# ✅ CORRECT: Never set execute bit
# NO chmod +x, NO 0700/0755 permissions

# ✅ CORRECT: Verify permissions after save
file_perms = malware_path.stat().st_mode
if file_perms & stat.S_IXUSR:  # Check execute bit
    logger.error(f"Execute bit set on {malware_path}")
    malware_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # Fix
```

**Dataset Handling** (CRITICAL for reproducibility):
```python
# ✅ CORRECT: Use SHA256 filenames for deduplication
file_hash = hashlib.sha256(content).hexdigest()
output_path = data_dir / file_hash

# ✅ CORRECT: Reproducible train/test splits
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# ✅ CORRECT: Handle class imbalance
from sklearn.utils.class_weight import compute_class_weight
class_weights = compute_class_weight('balanced', classes=[0, 1], y=y_train)

# ❌ WRONG: Non-reproducible splits (random seed missing)
X_train, X_test = train_test_split(X, y, test_size=0.3)
```

**MalwareBazaar API Usage** (for dataset acquisition):
```python
# ✅ CORRECT: Complete secure download pattern
import pyzipper
import hashlib
import io
from pathlib import Path

def download_malware_sample(sha256_hash: str) -> Path | None:
    """Download and verify malware sample securely."""

    # Step 1: Request sample from API
    response = requests.post(
        API_URL,
        data={"query": "get_file", "sha256_hash": sha256_hash},
        timeout=60
    )

    # Step 2: Verify response is ZIP (not JSON error)
    if response.content.startswith(b'{'):
        logger.warning(f"Sample not available: {sha256_hash}")
        return None

    # Step 3: Extract from AES-encrypted ZIP
    try:
        with pyzipper.AESZipFile(io.BytesIO(response.content)) as zf:
            # MalwareBazaar standard password
            extracted_content = zf.read(zf.namelist()[0], pwd=b"infected")
    except Exception as e:
        logger.error(f"ZIP extraction failed: {e}")
        return None

    # Step 4: CRITICAL - Verify SHA256 hash
    downloaded_hash = hashlib.sha256(extracted_content).hexdigest()
    if downloaded_hash.lower() != sha256_hash.lower():
        logger.error(f"Hash mismatch: expected {sha256_hash}, got {downloaded_hash}")
        return None  # DO NOT SAVE - corrupted/tampered file

    # Step 5: Save with secure permissions (0600)
    output_path = MALWARE_DIR / sha256_hash
    output_path.write_bytes(extracted_content)
    output_path.chmod(0o600)  # Owner read/write only, NO execute

    # Step 6: Post-save verification
    if not verify_file_integrity(output_path, sha256_hash):
        output_path.unlink()  # Delete if verification fails
        return None

    # Step 7: Rate limiting (respectful API usage)
    time.sleep(REQUEST_DELAY)  # Default: 1.0 second

    logger.info(f"✅ Securely downloaded: {sha256_hash}")
    return output_path
```

**Feature Extraction** (Days 4-5 - Next Phase):

**Security Requirements**:
- **Static analysis ONLY**: Never execute samples during feature extraction
- **Read-only operations**: Features extracted from byte content only
- **Sandboxed parsing**: Use safe parsers (pefile, pyelftools) with error handling
- **Memory limits**: Process large files in chunks to prevent memory exhaustion
- **Timeout enforcement**: Kill extraction if taking >60 seconds per file

**Implementation Pattern**:
```python
# ✅ CORRECT: Safe feature extraction
import pefile
import lief
from pathlib import Path
import numpy as np

def extract_features_safe(file_path: Path) -> np.ndarray | None:
    """Extract features from malware sample WITHOUT execution."""

    try:
        # Read file as bytes (NO execution)
        content = file_path.read_bytes()

        # Size check (prevent memory exhaustion)
        if len(content) > MAX_FILE_SIZE:  # 100MB default
            logger.warning(f"File too large: {file_path}")
            return None

        features = []

        # Feature 1: File entropy (randomness indicator)
        entropy = calculate_entropy(content)
        features.append(entropy)

        # Feature 2: Byte histogram (frequency distribution)
        byte_hist = np.bincount(np.frombuffer(content, dtype=np.uint8), minlength=256)
        features.extend(byte_hist)

        # Feature 3: PE/ELF headers (SAFE parsing)
        if content.startswith(b'MZ'):  # PE file
            # Use pefile with exception handling
            pe = pefile.PE(data=content, fast_load=True)
            features.extend(extract_pe_features(pe))
        elif content.startswith(b'\x7fELF'):  # ELF file
            # Use pyelftools with safe parsing
            binary = lief.parse(raw=content)
            features.extend(extract_elf_features(binary))

        # Feature 4: String analysis (NO execution)
        strings = extract_strings_safe(content)
        features.extend(string_features(strings))

        return np.array(features, dtype=np.float32)

    except Exception as e:
        logger.error(f"Feature extraction failed for {file_path}: {e}")
        return None

# Cache features as .npz files (NumPy compressed format)
# Use file hash as cache key for deduplication
# Parallel processing: joblib.Parallel(n_jobs=-1)
```

**Feature Categories**:
- **File metadata**: Size, entropy, file type
- **PE/ELF headers**: Section count, imports, exports, entry point
- **Byte statistics**: Histogram, n-grams, compression ratio
- **String analysis**: API calls, URLs, suspicious patterns (NO execution)
- **Heuristics**: Packing detection, obfuscation indicators

**Model Training** (Days 6-14 - Next Phase):

**Security Considerations**:
- **Model poisoning prevention**: Validate training data integrity before training
- **Adversarial robustness**: Test model against evasion techniques
- **Secure model storage**: Encrypt model files at rest
- **Version control**: Track model lineage to detect tampering
- **Isolation**: Train in isolated environment (GPU passthrough to VM if needed)

**Training Pattern**:
```python
# ✅ CORRECT: Secure model training workflow
from pathlib import Path
import joblib
import json
from datetime import datetime

def train_model_secure(X_train, y_train, experiment_name: str):
    """Train ML model with security best practices."""

    # Step 1: Validate training data integrity
    assert len(X_train) == len(y_train), "Data shape mismatch"
    assert not np.any(np.isnan(X_train)), "NaN values in features"

    # Step 2: Train with class balancing
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(
        n_estimators=100,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,          # Reproducible
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Step 3: Save checkpoint securely
    checkpoint_dir = Path(f"models/checkpoints/{experiment_name}")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    model_path = checkpoint_dir / f"model_{datetime.now():%Y%m%d_%H%M%S}.pkl"
    joblib.dump(model, model_path)
    model_path.chmod(0o600)  # Owner read/write only

    # Step 4: Compute model hash (integrity verification)
    model_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()

    # Step 5: Log experiment metadata
    metadata = {
        "experiment_name": experiment_name,
        "timestamp": datetime.utcnow().isoformat(),
        "model_path": str(model_path),
        "model_hash": model_hash,
        "architecture": "RandomForest",
        "hyperparameters": model.get_params(),
        "training_samples": len(X_train),
        "class_distribution": dict(zip(*np.unique(y_train, return_counts=True)))
    }

    experiment_log = Path(f"models/experiments/{experiment_name}.json")
    experiment_log.write_text(json.dumps(metadata, indent=2))

    return model, model_hash

# Version models: model_v1.0.0.pkl (semantic versioning)
# Store metadata: architecture, hyperparams, training metrics, data hash
```

## Recent Developments

### Phase 2 Complete: Real-Time Security Dashboard (0.3.0-beta)

**Live Threat Visualization** (`app/gui/threat_visualization_widget.py`):
- **ThreatTimelineWidget**: Interactive timeline with zoom/pan, time range filtering (1h to 30d)
- **ThreatMapWidget**: Geographic visualization with auto-clustering (1° threshold)
- **SeverityHeatmapWidget**: 2D heatmap showing threat patterns across type/location/time
- Performance: FIFO eviction (max 1000 events), <100ms updates, <200MB memory
- Thread-safe design using `QTimer.singleShot()` for main thread scheduling

**Performance Metrics Dashboard** (`app/gui/performance_metrics_widget.py`):
- Real-time monitoring: CPU, memory, disk I/O, scan throughput
- Cache efficiency tracking (hit rate, cache size)
- Alert system with configurable thresholds
- Historical trends (up to 1000 data points)
- Demo: `examples/performance_metrics_demo.py`

**Customizable Widget Layout** (`app/gui/widget_layout_manager.py`):
- Drag-and-drop repositioning via QDockWidget
- Save/load custom layouts to JSON (XDG-compliant: `~/.config/xanadOS/dashboard_layouts/`)
- Multi-monitor support with floating widget geometry
- Preset layouts and toolbar controls

**Security Event Stream** (`app/gui/security_event_stream.py`):
- Live security event feed with auto-refresh
- SQLite backend with FTS5 full-text search (<200ms queries)
- Export to CSV/JSON/PDF formats
- Advanced filtering by severity, type, time range

### Phase 3 In Progress: ML-Based Threat Detection

⚠️ **CRITICAL SECURITY NOTICE** ⚠️

This phase involves **LIVE MALWARE SAMPLES**. Security is paramount:

- **NEVER execute** files from `data/malware/` or `data/benign/`
- **ALWAYS work in isolated environment** (VM, container, or air-gapped system recommended)
- **VERIFY all hashes** before and after every operation
- **NO network access** for malware samples (disable network in VM/container)
- **Immediate quarantine** if suspicious activity detected
- **Review all code** that touches malware samples for injection vulnerabilities

**Dataset Acquisition (Days 1-3 COMPLETE)**:

Location: `scripts/ml/` (acquisition scripts), `data/` (datasets), `app/ml/` (ML models)

**Acquisition Scripts** (`scripts/ml/`):
- **`download_malwarebazaar.py`**: Downloads malware samples from MalwareBazaar API
  - **Security confirmation required**: Script prompts "Continue? (yes/no)" before downloading
  - MalwareBazaar API with free access (API key: embedded in script)
  - AES-encrypted ZIP extraction using `pyzipper` (password: "infected")
  - **Triple verification**:
    1. ZIP integrity check before extraction
    2. SHA256 hash verification after extraction
    3. Hash mismatch = immediate rejection (no file saved)
  - Rate limiting: 1 req/sec (respectful API usage)
  - Resume support: Skips existing files (hash-based deduplication)
  - Metadata tracking: `data/malware/metadata.json`
  - **File permissions**: 0600 (owner read/write only)
  - **No execution bits**: Files saved without execute permissions

- **`collect_benign.py`**: Collects clean system binaries
  - Scans trusted paths: `/usr/bin`, `/usr/sbin`, `/lib`, `/usr/lib`
  - ELF format validation (magic bytes check)
  - Size filtering: 1KB - 100MB
  - SHA256 deduplication
  - Safe copying (non-destructive)

- **`organize_dataset.py`**: Splits dataset into train/val/test
  - Train: 70%, Val: 15%, Test: 15%
  - Reproducible splits (seed=42)
  - Preserves class balance
  - Generates `data/organized/metadata.json`

- **`dataset_workflow.py`**: Orchestrates complete workflow
  - `--quick`: 500 malware + 500 benign (testing)
  - `--full`: 50K malware + 50K benign (production)
  - Progress tracking with Rich library
  - Error handling and resume support

**Dataset Structure**:
```
data/
├── malware/         # Raw malware downloads (SHA256 filenames)
│   └── metadata.json
├── benign/          # System binaries (SHA256 filenames)
│   └── metadata.json
└── organized/       # Train/val/test splits
    ├── train/
    │   ├── malware/
    │   └── benign/
    ├── val/
    │   ├── malware/
    │   └── benign/
    ├── test/
    │   ├── malware/
    │   └── benign/
    └── metadata.json
```

**ML Pipeline Usage** (Days 4-7 IN PROGRESS):

**SECURITY CHECKLIST** (complete BEFORE running any ML scripts):
- [ ] **Isolated environment**: VM/container/air-gapped system active
- [ ] **Network isolation**: Disable network for malware handling (optional for downloads)
- [ ] **Backups current**: System backed up before malware download
- [ ] **Monitoring active**: File integrity monitoring enabled
- [ ] **No production data**: Keep malware samples isolated from sensitive data
- [ ] **Antivirus disabled**: (temporarily) to prevent interference with malware samples

```bash
# STEP 1: Environment verification (MANDATORY)
# Verify you're in isolated environment
hostname  # Should show VM/container name, NOT production machine
ip addr   # Verify network isolation if required

# STEP 2: Quick dataset acquisition (testing - 600 samples)
uv run python scripts/ml/dataset_workflow.py --quick
# ⚠️  Prompts for confirmation before downloading malware
# ✅  Safe for initial testing and development

# STEP 3: Full dataset (production - 100K samples)
uv run python scripts/ml/dataset_workflow.py --full
# ⚠️  WARNING: Downloads ~50K LIVE malware samples
# ⚠️  Requires ~10GB disk space
# ⚠️  Takes several hours with rate limiting

# STEP 4: Individual steps (advanced usage)
# Download malware only (with security confirmation)
uv run python scripts/ml/download_malwarebazaar.py --samples 500

# Collect benign only (safe - no malware)
uv run python scripts/ml/collect_benign.py --samples 500

# Organize existing dataset (safe - read-only on samples)
uv run python scripts/ml/organize_dataset.py --split-ratio 0.7 0.15 0.15
```

**ML Infrastructure** (`app/ml/`):
- **`ml_threat_detector.py`**: Main ML threat detection engine (in development)
- **`deep_learning.py`**: Deep learning models (PyTorch-based)
- **`models/`**: Trained model checkpoints
- **`training/`**: Training scripts and experiment tracking

**ML Dependencies** (install with `uv sync --extra malware-analysis`):
- PyTorch for deep learning
- scikit-learn for classical ML
- pandas/numpy for data processing
- LIEF/pefile/pyelftools for binary feature extraction

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

⚠️ **MALWARE HANDLING - CRITICAL SECURITY REQUIREMENTS** ⚠️

**Environment Isolation** (MANDATORY):
- **VM/Container ONLY**: Never work with malware on host system
- **Network isolation**: Disable network during malware processing
- **Snapshot before**: Take VM snapshot before downloading malware
- **Air-gapped preferred**: Physically isolated system for maximum security
- **No production data**: Keep malware completely separate from any sensitive data

**Recommended Isolation Setup**:
```bash
# Option 1: Docker container (basic isolation)
docker run -it --rm --network=none -v $(pwd)/data:/data python:3.13

# Option 2: VirtualBox VM (recommended)
# - Create Ubuntu VM with snapshots enabled
# - Disable networking in VM settings
# - Use shared folder for data transfer only

# Option 3: QEMU/KVM (advanced)
qemu-system-x86_64 -enable-kvm -m 4096 -net none ...
```

**ML-based Heuristics**:
- Behavioral analysis using scikit-learn models
- Trained on benign/malware samples (100% static analysis)
- Complements signature-based detection (ClamAV/YARA)
- Requires `[malware-analysis]` dependencies
- **NO execution**: All features extracted via static analysis only

**ML Development Workflow (Phase 3)**:

1. **Dataset Acquisition** (Days 1-3 COMPLETE):

   **Security Verification Steps**:
   ```bash
   # PRE-FLIGHT CHECKLIST
   # 1. Verify isolated environment
   hostname  # Should NOT be production system

   # 2. Check network isolation (optional for downloads)
   ping -c 1 8.8.8.8 || echo "Network isolated (good for processing)"

   # 3. Verify disk space (10GB+ for full dataset)
   df -h data/

   # 4. Backup current state (if VM)
   # Take snapshot before downloading malware

   # Quick test dataset (500 malware + 500 benign)
   uv run python scripts/ml/dataset_workflow.py --quick
   # ✅ Safe for initial testing - prompts for confirmation
   # ✅ Downloads ~100 samples (some API failures expected)
   # ✅ Completes in 5-10 minutes

   # Production dataset (50K malware + 50K benign)
   uv run python scripts/ml/dataset_workflow.py --full
   # ⚠️ WARNING: Downloads ~50K LIVE malware samples
   # ⚠️ Requires ~10GB disk space + several hours
   # ⚠️ MUST be in isolated environment
   ```

2. **Feature Extraction** (Days 4-5 IN PROGRESS):

   **Security-Focused Implementation**:
   - **Static analysis ONLY**: No code execution whatsoever
   - **Safe parsers**: pefile, pyelftools, LIEF with exception handling
   - **Timeout protection**: 60-second limit per file
   - **Memory limits**: Process files in chunks (MAX_FILE_SIZE: 100MB)
   - **Error isolation**: Failed parsing doesn't crash pipeline

   **Feature Categories**:
   - Binary analysis: PE/ELF headers, section analysis (safe parsing)
   - Static features: Entropy, byte histograms, n-grams
   - String analysis: API calls, suspicious patterns (regex-based)
   - Metadata: File size, type, structure (no execution)
   - Cache features as `.npz` files (NumPy format)
   - Parallel processing for batch operations (joblib)

3. **Model Training** (Days 6-14):

   **Security Best Practices**:
   - **Data validation**: Verify training data integrity (hashes)
   - **Random Forest baseline** (Week 1): Interpretable, robust
   - **Deep learning models** (Week 2): CNN for binary classification
   - **Model versioning**: Semantic versioning (v1.0.0, v1.1.0)
   - **Experiment tracking**: JSON logs with full reproducibility
   - **Checkpoint security**: Model files saved with 0600 permissions
   - **Adversarial testing**: Validate against evasion techniques

4. **Integration** (Week 3):

   **Production Deployment Security**:
   - Load trained models in `app/ml/ml_threat_detector.py`
   - Add to `UnifiedScannerEngine` as optional detector
   - **Model integrity check**: Verify model hash before loading
   - **Sandboxed inference**: Isolate model prediction from system
   - GUI integration for ML-based scans
   - Performance benchmarking (throughput, latency, FPR)
   - **Fail-safe design**: System works without ML if models unavailable
   - Random Forest baseline (Week 1)
   - Deep learning models (Week 2)
   - Model versioning and checkpointing
   - Experiment tracking in JSON

4. **Integration** (Week 3):
   - Load trained models in `app/ml/ml_threat_detector.py`
   - Add to `UnifiedScannerEngine` as optional detector
   - GUI integration for ML-based scans
   - Performance benchmarking

**ML File Structure** (with security annotations):
```
app/ml/
├── ml_threat_detector.py    # Main ML detection engine
├── deep_learning.py          # PyTorch models
├── models/                   # Trained model files (0600 permissions)
│   ├── checkpoints/         # Training checkpoints
│   ├── experiments/         # Experiment logs (JSON)
│   └── production/          # Production models (hash-verified)
└── training/                # Training scripts

scripts/ml/
├── download_malwarebazaar.py  # Malware acquisition (security confirmation)
├── collect_benign.py          # Benign collection (safe)
├── organize_dataset.py        # Train/val/test splitting (read-only)
└── dataset_workflow.py        # Orchestration script (prompts user)

data/  # ⚠️ CONTAINS LIVE MALWARE - HANDLE WITH EXTREME CAUTION
├── malware/                  # Raw malware (SHA256 names, 0600 perms)
│   └── metadata.json         # Sample metadata (file types, signatures)
├── benign/                   # System binaries (SHA256 names, safe)
│   └── metadata.json
└── organized/                # Split datasets (read-only after split)
    ├── train/
    │   ├── malware/          # 70% of malware samples
    │   └── benign/           # 70% of benign samples
    ├── val/
    │   ├── malware/          # 15% of malware samples
    │   └── benign/           # 15% of benign samples
    ├── test/
    │   ├── malware/          # 15% of malware samples
    │   └── benign/           # 15% of benign samples
    └── metadata.json         # Split statistics and integrity hashes
```

**Critical ML Security Rules** (ZERO TOLERANCE):

1. **NEVER Execute Malware**
   - ❌ NO `subprocess.run()`, `os.system()`, `exec()`, `eval()`
   - ❌ NO file execution: `chmod +x`, `./<file>`, `python <malware.py>`
   - ❌ NO dynamic imports: `importlib.import_module()` with untrusted code
   - ❌ NO shellcode execution: No JIT compilation of untrusted data
   - ✅ ONLY static analysis: Read bytes, parse structure, extract features

2. **ALWAYS Verify Hashes**
   - Before processing: Check SHA256 matches metadata
   - After download: Verify extraction integrity
   - Before training: Validate all training data hashes
   - After model save: Compute and store model hash
   - On model load: Verify model hasn't been tampered with

3. **Use Reproducible Splits**
   - `random_state=42` in ALL train/test splits
   - Document random seed in experiment logs
   - Stratified splits to preserve class balance
   - Save split indices for reproducibility

4. **Handle Class Imbalance**
   - Current ratio: 1:5 (malware:benign)
   - Use `class_weight='balanced'` in sklearn
   - Consider SMOTE for oversampling malware class
   - Monitor per-class metrics (precision, recall, F1)
   - Track false positives (critical for security tool)

5. **Store Metadata with Every Dataset Version**
   - Dataset size, class distribution
   - Source (MalwareBazaar, system binaries)
   - Download date, file hashes
   - Processing history, transformations
   - Schema version for backward compatibility

6. **Isolation Requirements**
   - ⚠️ VM/container MANDATORY for malware work
   - ⚠️ Network isolation during processing
   - ⚠️ No malware on production systems
   - ⚠️ Take snapshots before risky operations
   - ⚠️ Air-gapped system for maximum security

7. **File Permission Security**
   - Malware files: 0600 (owner read/write only)
   - Model files: 0600 (prevent tampering)
   - Config files: 0644 (read-only for non-owner)
   - Scripts: 0755 (executable only if needed)
   - NO execute bit on data files (EVER)

8. **Error Handling**
   - Fail-safe design: Errors don't expose malware
   - Quarantine corrupted files immediately
   - Log security events (hash mismatches, anomalies)
   - Never continue processing after integrity check failure
   - Graceful degradation if ML unavailable

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

**General Development**:
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

**ML Security (ZERO TOLERANCE)**:
❌ **Executing malware samples** → NEVER run files from `data/malware/` (criminal negligence)
❌ **Malware without hash verification** → ALWAYS verify SHA256 before AND after operations
❌ **Non-reproducible ML splits** → Always use `random_state=42` for reproducibility
❌ **Working on host system** → MUST use isolated VM/container for malware work
❌ **Network-connected malware processing** → Disable network during analysis
❌ **Execute permissions on malware** → Never `chmod +x`, always 0600 permissions
❌ **Dynamic imports of untrusted code** → No `importlib.import_module()` with malware
❌ **Skipping integrity checks** → Verify hashes even if "just testing"
❌ **Model files without hash verification** → Always verify model integrity before loading
❌ **Missing experiment metadata** → Every training run MUST log hyperparams, data hash, results
❌ **Ignoring class imbalance** → Use `class_weight='balanced'` or SMOTE
❌ **Non-atomic file operations** → Use temp file + rename pattern for safety
❌ **Hardcoded API keys in code** → Use environment variables or config files (0600)
❌ **Missing timeout on parsing** → Malicious files can cause infinite loops
❌ **Unhandled exceptions in ML pipeline** → One corrupt file shouldn't crash entire training

**Security Violations That Will Get You Fired**:
❌ Executing malware on production system
❌ Committing malware samples to git
❌ Emailing/transferring malware without encryption
❌ Disabling security features "to make it work"
❌ Bypassing hash verification "for speed"
❌ Running with elevated privileges unnecessarily

## Archive Organization (Unique to This Project)

The `archive/` directory is **central to this project's organization**:
- **NEVER commit files directly to root** - use `archive/` for deprecated/temporary work
- See `archive/ARCHIVE_INDEX.md` for structure and navigation
- Subdirectories: `deprecated/`, `legacy-versions/`, `consolidation-backup-*/`, `temp-docs/`
- This keeps the root directory clean and organized (validated by `make validate`)
- When refactoring, move old versions to `archive/` with timestamped subdirectories

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
