# Security Remediation Implementation Plan
**Project**: xanadOS Search & Destroy
**Date Created**: December 17, 2025
**Target Completion**: January 7, 2026 (3 weeks)
**Status**: 📋 PLANNING

---

## Overview

This plan addresses **9 CRITICAL** and **14 HIGH** severity vulnerabilities discovered in the security audit. Implementation is divided into 3 phases over 3 weeks with specific code changes, testing requirements, and verification steps.

---

## Phase 1: CRITICAL Vulnerabilities (Week 1)

### Day 1-2: Input Validation & Code Injection Prevention

#### 1.1 Fix GitHub Actions Code Injection

**File**: `.github/workflows/train-models.yml`

**Changes Required**:
```yaml
# BEFORE (VULNERABLE):
- name: Acquire dataset
  run: |
    DATASET_SIZE="${{ github.event.inputs.dataset_size || 'quick' }}"
    uv run python scripts/ml/dataset_workflow.py --${DATASET_SIZE}

# AFTER (SECURE):
- name: Acquire dataset
  run: |
    DATASET_SIZE="${{ github.event.inputs.dataset_size }}"

    # Validate input against strict whitelist
    case "$DATASET_SIZE" in
      quick|full)
        echo "✅ Valid dataset size: $DATASET_SIZE"
        ;;
      *)
        echo "❌ ERROR: Invalid dataset size '$DATASET_SIZE'"
        echo "   Allowed values: quick, full"
        exit 1
        ;;
    esac

    # Override for scheduled runs
    if [ "${{ github.event_name }}" = "schedule" ]; then
      DATASET_SIZE="full"
    fi

    # Use explicit argument passing (not string interpolation)
    uv run python scripts/ml/dataset_workflow.py --dataset-size="$DATASET_SIZE"
```

**Testing**:
```bash
# Manual test (local)
DATASET_SIZE="quick; echo EXPLOIT" bash -c 'case "$DATASET_SIZE" in quick|full) echo OK;; *) echo BLOCKED; exit 1;; esac'
# Expected: BLOCKED
```

---

#### 1.2 Replace eval() with AST Parser

**File**: `app/core/automation/workflow_engine.py`

**Create New File**: `app/core/automation/safe_expression_evaluator.py`

```python
#!/usr/bin/env python3
"""Safe expression evaluator using AST parsing (no eval())."""

import ast
import operator
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Whitelist of safe operators
SAFE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Not: operator.not_,
    ast.In: lambda x, y: x in y,
    ast.NotIn: lambda x, y: x not in y,
}

# Whitelist of safe functions
SAFE_FUNCTIONS = {
    'len': len,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
}


class SafeExpressionEvaluator:
    """Safely evaluate expressions without eval()."""

    def __init__(self, context: dict[str, Any]):
        self.context = context

    def evaluate(self, expression: str) -> bool:
        """
        Safely evaluate a boolean expression.

        Allowed syntax:
        - context["key"]
        - context.get("key", default)
        - Comparisons: ==, !=, <, <=, >, >=, in, not in
        - Boolean ops: and, or, not
        - Literals: strings, numbers, booleans
        - Safe functions: len(), str(), int(), float(), bool()

        Examples:
        - context["status"] == "active"
        - context.get("count", 0) > 10
        - "admin" in context.get("roles", []) and context["verified"]
        """
        try:
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body)
            return bool(result)
        except Exception as e:
            logger.error(f"Expression evaluation failed: {e}")
            logger.debug(f"Expression: {expression}")
            return False

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate AST node."""

        # Literals
        if isinstance(node, ast.Constant):
            return node.value

        # Variables (only 'context' allowed)
        elif isinstance(node, ast.Name):
            if node.id == 'context':
                return self.context
            elif node.id in SAFE_FUNCTIONS:
                return SAFE_FUNCTIONS[node.id]
            else:
                raise ValueError(f"Forbidden variable: {node.id}")

        # Dictionary/list access: context["key"]
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            key = self._eval_node(node.slice)
            return value[key]

        # Attribute access: context.get
        elif isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            if node.attr == 'get' and isinstance(value, dict):
                return value.get
            else:
                raise ValueError(f"Forbidden attribute: {node.attr}")

        # Function calls (only .get() and safe functions)
        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}

            # Verify function is safe
            if func not in SAFE_FUNCTIONS.values() and func.__name__ != 'get':
                raise ValueError(f"Forbidden function: {func}")

            return func(*args, **kwargs)

        # Comparisons: ==, !=, <, >, etc.
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in SAFE_OPERATORS:
                    raise ValueError(f"Forbidden operator: {type(op)}")
                right = self._eval_node(comparator)
                if not SAFE_OPERATORS[type(op)](left, right):
                    return False
                left = right
            return True

        # Boolean operations: and, or
        elif isinstance(node, ast.BoolOp):
            if type(node.op) not in SAFE_OPERATORS:
                raise ValueError(f"Forbidden operator: {type(node.op)}")
            values = [self._eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)

        # Unary operations: not
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in SAFE_OPERATORS:
                raise ValueError(f"Forbidden operator: {type(node.op)}")
            operand = self._eval_node(node.operand)
            return SAFE_OPERATORS[type(node.op)](operand)

        # Lists
        elif isinstance(node, ast.List):
            return [self._eval_node(elem) for elem in node.elts]

        # Tuples
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem) for elem in node.elts)

        else:
            raise ValueError(f"Forbidden node type: {type(node).__name__}")


# Unit tests
if __name__ == "__main__":
    # Test safe expressions
    ctx = {"status": "active", "count": 15, "roles": ["user", "admin"], "verified": True}
    evaluator = SafeExpressionEvaluator(ctx)

    # Should work
    assert evaluator.evaluate('context["status"] == "active"') == True
    assert evaluator.evaluate('context.get("count", 0) > 10') == True
    assert evaluator.evaluate('"admin" in context["roles"]') == True
    assert evaluator.evaluate('context["verified"] and len(context["roles"]) > 1') == True

    # Should fail safely
    assert evaluator.evaluate('__import__("os").system("ls")') == False
    assert evaluator.evaluate('open("/etc/passwd").read()') == False
    assert evaluator.evaluate('eval("malicious code")') == False

    print("✅ All tests passed")
```

**Update**: `app/core/automation/workflow_engine.py`

```python
from .safe_expression_evaluator import SafeExpressionEvaluator

class WorkflowEngine:
    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """Safely evaluate condition using AST parser (no eval)."""
        evaluator = SafeExpressionEvaluator(context)
        return evaluator.evaluate(condition)
```

**Testing**:
```bash
pytest tests/security/test_safe_expression_evaluator.py -v
pytest tests/core/test_workflow_engine.py -k "test_condition" -v
```

---

### Day 3-4: Malware Handling Security

#### 1.3 Fix Hash Verification Order

**File**: `scripts/ml/download_malwarebazaar.py`

**Changes**:
```python
def download_sample(self, sha256_hash: str) -> Optional[Path]:
    """Download a single sample with secure hash verification."""

    # Check if already downloaded (early exit)
    output_path = self.output_dir / sha256_hash
    if output_path.exists():
        # Verify existing file integrity
        existing_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        if existing_hash.lower() == sha256_hash.lower():
            console.print(f"[dim]⏭️  Skip (exists): {sha256_hash[:16]}...")
            return output_path
        else:
            console.print(f"[yellow]⚠️  Existing file corrupted, re-downloading...")
            output_path.unlink()

    try:
        # Request sample download
        response = self.session.post(
            API_URL,
            data={"query": "get_file", "sha256_hash": sha256_hash},
            timeout=60,
        )

        if response.status_code != 200:
            console.print(f"[yellow]⚠️  HTTP {response.status_code}: {sha256_hash[:16]}")
            return None

        content = response.content

        # Check for JSON error response
        if content.startswith(b"{"):
            error_data = json.loads(content)
            console.print(f"[yellow]⚠️  {sha256_hash[:16]}: {error_data.get('query_status')}")
            return None

        # Extract from password-protected ZIP
        try:
            with pyzipper.AESZipFile(io.BytesIO(content)) as zf:
                names = zf.namelist()
                if not names:
                    console.print(f"[yellow]⚠️  {sha256_hash[:16]}: Empty ZIP")
                    return None

                # Extract malware content (in memory, not written yet)
                extracted_content = zf.read(names[0], pwd=b"infected")

                # CRITICAL: Verify SHA256 BEFORE writing to disk
                downloaded_hash = hashlib.sha256(extracted_content).hexdigest()

                if downloaded_hash.lower() != sha256_hash.lower():
                    console.print(f"[red]❌ HASH MISMATCH DETECTED!")
                    console.print(f"[red]   Expected: {sha256_hash}")
                    console.print(f"[red]   Got:      {downloaded_hash}")
                    console.print(f"[red]   Sample REJECTED (possible API compromise)")

                    # Log incident for security review
                    self._log_security_incident(
                        "hash_mismatch",
                        f"Expected {sha256_hash}, got {downloaded_hash}",
                        sha256_hash
                    )

                    return None  # EXIT BEFORE WRITING TO DISK

                # Hash verified, safe to write
                output_path.write_bytes(extracted_content)

                # Set secure permissions (owner read/write only, no execute)
                output_path.chmod(0o600)

                # Post-write verification (defense in depth)
                verify_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
                if verify_hash.lower() != sha256_hash.lower():
                    console.print(f"[red]❌ POST-WRITE VERIFICATION FAILED!")
                    output_path.unlink()  # Delete corrupted file immediately
                    return None

                # Update metadata
                self.metadata["samples"][sha256_hash] = {
                    "file_size": len(extracted_content),
                    "download_date": datetime.utcnow().isoformat(),
                    "sha256_verified": True,
                }
                self._save_metadata()

                console.print(f"[green]✅ Downloaded: {sha256_hash[:16]}... ({len(extracted_content):,} bytes)")
                return output_path

        except Exception as e:
            console.print(f"[red]❌ ZIP extraction failed: {sha256_hash[:16]}: {e}")
            # Clean up any partial writes
            if output_path.exists():
                output_path.unlink()
            return None

    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ Network error: {sha256_hash[:16]}: {e}")
        return None

def _log_security_incident(self, incident_type: str, details: str, sha256: str):
    """Log security incidents for review."""
    incident_log = self.output_dir.parent / "security_incidents.json"

    incidents = []
    if incident_log.exists():
        incidents = json.loads(incident_log.read_text())

    incidents.append({
        "timestamp": datetime.utcnow().isoformat(),
        "type": incident_type,
        "details": details,
        "sha256": sha256,
    })

    incident_log.write_text(json.dumps(incidents, indent=2))
    incident_log.chmod(0o600)
```

**Testing**:
```python
# tests/security/test_malware_download_security.py
def test_hash_mismatch_prevents_write(tmp_path):
    """Verify hash mismatch prevents file write."""
    downloader = MalwareBazaarDownloader(tmp_path)

    # Mock API to return wrong hash
    with patch('requests.Session.post') as mock_post:
        # Simulate hash mismatch
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = create_fake_malware_zip()  # Different hash
        mock_post.return_value = mock_response

        result = downloader.download_sample("abc123...")

        # Should return None (rejected)
        assert result is None

        # Should NOT create file on disk
        assert not (tmp_path / "abc123...").exists()

        # Should log security incident
        incident_log = tmp_path.parent / "security_incidents.json"
        assert incident_log.exists()
```

---

#### 1.4 Add Timeout Protection

**File**: `app/ml/feature_extractor.py`

**Add timeout decorator**:
```python
import signal
from contextlib import contextmanager
from functools import wraps

class FeatureExtractionTimeout(Exception):
    """Raised when feature extraction exceeds timeout."""
    pass

@contextmanager
def timeout(seconds: int):
    """
    Context manager for timeout enforcement.

    Usage:
        with timeout(60):
            # Code that must complete within 60 seconds
            result = expensive_operation()
    """
    def timeout_handler(signum, frame):
        raise FeatureExtractionTimeout(f"Operation exceeded {seconds} seconds")

    # Save old handler and set new one
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore old handler and cancel alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class FeatureExtractor:
    # Add timeout configuration
    DEFAULT_TIMEOUT = 60  # 60 seconds per file
    PE_PARSE_TIMEOUT = 30  # 30 seconds for PE parsing
    ELF_PARSE_TIMEOUT = 30  # 30 seconds for ELF parsing

    def __init__(self, max_file_size: int = 100 * 1024 * 1024, timeout: int = None):
        self.max_file_size = max_file_size
        self.timeout = timeout or self.DEFAULT_TIMEOUT

    def extract_features(self, file_path: Path) -> Optional[np.ndarray]:
        """Extract features with timeout protection."""
        try:
            # Enforce timeout for entire extraction
            with timeout(self.timeout):
                return self._extract_features_impl(file_path)

        except FeatureExtractionTimeout:
            logger.error(f"⚠️  Timeout ({self.timeout}s): {file_path.name}")
            return None

        except Exception as e:
            logger.error(f"⚠️  Feature extraction failed: {file_path.name}: {e}")
            return None

    def _extract_features_impl(self, file_path: Path) -> Optional[np.ndarray]:
        """Internal implementation (wrapped by timeout)."""
        # Read file content
        content = file_path.read_bytes()

        # Size check
        if len(content) > self.max_file_size:
            logger.warning(f"File too large: {file_path.name} ({len(content)} bytes)")
            return None

        # Initialize feature vector
        features = np.zeros(self.FEATURE_DIM, dtype=np.float32)
        idx = 0

        # 1. Entropy (fast, no timeout needed)
        features[idx] = self._calculate_entropy(content)
        idx += self.ENTROPY_DIM

        # 2. File size (fast)
        features[idx] = math.log10(len(content) + 1)
        idx += self.FILE_SIZE_DIM

        # 3. Byte histogram (fast)
        hist = self._byte_histogram(content)
        features[idx:idx + self.BYTE_HISTOGRAM_DIM] = hist
        idx += self.BYTE_HISTOGRAM_DIM

        # 4. PE header features (with timeout)
        if content.startswith(b"MZ"):
            try:
                with timeout(self.PE_PARSE_TIMEOUT):
                    pe_features = self._extract_pe_features(content)
                    features[idx:idx + self.PE_HEADER_DIM] = pe_features
            except FeatureExtractionTimeout:
                logger.warning(f"PE parsing timeout: {file_path.name}")
                # Leave PE features as zeros
        idx += self.PE_HEADER_DIM

        # 5. ELF header features (with timeout)
        if content.startswith(b"\x7fELF"):
            try:
                with timeout(self.ELF_PARSE_TIMEOUT):
                    elf_features = self._extract_elf_features(file_path)
                    features[idx:idx + self.ELF_HEADER_DIM] = elf_features
            except FeatureExtractionTimeout:
                logger.warning(f"ELF parsing timeout: {file_path.name}")
                # Leave ELF features as zeros
        idx += self.ELF_HEADER_DIM

        # ... rest of features ...

        return features

    def _extract_pe_features(self, content: bytes) -> np.ndarray:
        """Extract PE features with error handling."""
        features = np.zeros(self.PE_HEADER_DIM, dtype=np.float32)

        try:
            # Parse with pefile (fast_load=True for speed)
            pe = pefile.PE(data=content, fast_load=True)

            # Sanity checks before accessing attributes
            if not hasattr(pe, 'FILE_HEADER'):
                logger.warning("Invalid PE: missing FILE_HEADER")
                return features

            # Extract features with bounds checking
            features[0] = min(pe.FILE_HEADER.NumberOfSections, 255)
            features[1] = min(pe.FILE_HEADER.TimeDateStamp, 2**32 - 1)
            # ... more features ...

        except pefile.PEFormatError as e:
            logger.debug(f"PE format error (expected for some files): {e}")
        except Exception as e:
            logger.warning(f"Unexpected PE parsing error: {e}")

        return features
```

**Testing**:
```python
# tests/security/test_feature_extraction_timeout.py
import time

def test_timeout_enforcement(tmp_path):
    """Verify timeout kills long-running extraction."""

    # Create malicious PE that causes infinite loop
    malicious_file = tmp_path / "timeout_test.exe"
    malicious_file.write_bytes(create_timeout_exploit_pe())

    extractor = FeatureExtractor(timeout=5)  # 5-second timeout

    start = time.time()
    result = extractor.extract_features(malicious_file)
    duration = time.time() - start

    # Should timeout and return None
    assert result is None

    # Should take ~5 seconds (not forever)
    assert 4 < duration < 7  # Allow 2s margin
```

---

### Day 5-7: Quarantine & Permissions

#### 1.6 Fix Quarantine Directory Permissions

**File**: `app/core/unified_scanner_engine.py`

```python
class QuarantineManager:
    def __init__(self, quarantine_dir: str | None = None, io_manager=None):
        self.config = get_config()
        self.quarantine_dir = Path(
            quarantine_dir or self.config.get("quarantine_dir",
                                             str(Path.home() / ".local/share/search-and-destroy/quarantine"))
        )

        # Create with secure permissions (0700)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Verify permissions (defense in depth)
        current_mode = self.quarantine_dir.stat().st_mode & 0o777
        if current_mode != 0o700:
            self.logger.warning(f"Quarantine dir has insecure permissions: {oct(current_mode)}")
            self.quarantine_dir.chmod(0o700)
            self.logger.info(f"✅ Fixed quarantine permissions to 0700")

        # Verify ownership (should be current user)
        import pwd
        current_uid = os.getuid()
        dir_uid = self.quarantine_dir.stat().st_uid
        if dir_uid != current_uid:
            current_user = pwd.getpwuid(current_uid).pw_name
            dir_owner = pwd.getpwuid(dir_uid).pw_name
            self.logger.error(f"❌ SECURITY: Quarantine owned by {dir_owner}, not {current_user}!")
            raise SecurityError(f"Quarantine directory ownership mismatch")

        self.index_file = self.quarantine_dir / "quarantine_index.json"
        self.logger = logging.getLogger(__name__)
        self._quarantined_files: dict[str, QuarantinedFile] = {}
        self._load_index()
```

---

#### 1.7 Fix TOCTOU Race Condition

**File**: `app/core/unified_scanner_engine.py`

```python
import os
import stat

async def quarantine_file(self, file_path: str, threat_name: str) -> str:
    """Quarantine file with TOCTOU protection."""
    try:
        # Resolve path (fails if not exists)
        source_path = Path(file_path).resolve(strict=True)

        # Security checks (on resolved path)
        # 1. No symlinks
        if source_path.is_symlink() or Path(file_path).is_symlink():
            raise SecurityError(f"Cannot quarantine symlinks: {file_path}")

        # 2. Must be regular file
        if not source_path.is_file():
            raise SecurityError(f"Not a regular file: {file_path}")

        # 3. Check if in forbidden paths
        forbidden_paths = [
            Path("/etc"), Path("/boot"), Path("/sys"),
            Path("/proc"), Path("/dev"), Path("/root"),
        ]
        for forbidden in forbidden_paths:
            try:
                if source_path.is_relative_to(forbidden):
                    raise SecurityError(f"Cannot quarantine system files: {source_path}")
            except ValueError:
                pass

        # Open file descriptor (prevents TOCTOU)
        try:
            fd = os.open(source_path, os.O_RDONLY | os.O_NOFOLLOW)
        except OSError as e:
            raise SecurityError(f"Cannot open file: {e}")

        try:
            # Verify file descriptor points to regular file
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise SecurityError("File descriptor is not a regular file")

            # Calculate checksum from file descriptor
            hasher = hashlib.sha256()
            with os.fdopen(fd, 'rb', closefd=False) as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            checksum = hasher.hexdigest()

            # Generate quarantine ID
            quarantine_id = f"q_{int(time.time())}_{checksum[:16]}"
            quarantine_path = self.quarantine_dir / quarantine_id

            # Atomic move (prevents TOCTOU)
            try:
                # Try atomic rename (same filesystem)
                os.rename(source_path, quarantine_path)
                self.logger.info(f"✅ Quarantine (atomic rename): {file_path}")
            except OSError:
                # Cross-filesystem: secure copy + delete
                # Copy using file descriptor (not path)
                os.lseek(fd, 0, os.SEEK_SET)  # Rewind
                with open(quarantine_path, 'wb') as dest:
                    while chunk := os.read(fd, 8192):
                        dest.write(chunk)

                # Verify copy succeeded
                if quarantine_path.stat().st_size != st.st_size:
                    quarantine_path.unlink()
                    raise SecurityError("Quarantine copy size mismatch")

                # Delete original (only after successful copy)
                source_path.unlink()
                self.logger.info(f"✅ Quarantine (copy+delete): {file_path}")

        finally:
            os.close(fd)

        # Set secure permissions on quarantined file
        quarantine_path.chmod(0o600)  # Owner read/write only, NO execute

        # Create quarantine record
        quarantined_file = QuarantinedFile(
            original_path=str(source_path),
            quarantine_path=str(quarantine_path),
            threat_name=threat_name,
            timestamp=datetime.now(),
            file_size=quarantine_path.stat().st_size,
            checksum=checksum,
            quarantine_id=quarantine_id,
        )

        self._quarantined_files[quarantine_id] = quarantined_file
        self._save_index()

        self.logger.info(f"✅ Quarantine complete: {quarantine_id}")
        return quarantine_id

    except Exception as e:
        self.logger.error(f"❌ Quarantine failed: {file_path}: {e}")
        raise
```

**Testing**:
```python
# tests/security/test_quarantine_toctou.py
import os
import threading
import time

def test_symlink_attack_blocked(tmp_path):
    """Verify symlink attacks are blocked."""
    manager = QuarantineManager(str(tmp_path / "quarantine"))

    # Create malware file
    malware = tmp_path / "malware.exe"
    malware.write_bytes(b"MALWARE")

    # Create system file (forbidden)
    system_file = tmp_path / "etc" / "shadow"
    system_file.parent.mkdir()
    system_file.write_text("root:x:...")

    # Attacker replaces malware with symlink to /etc/shadow
    malware.unlink()
    malware.symlink_to(system_file)

    # Attempt quarantine (should fail)
    with pytest.raises(SecurityError, match="symlink"):
        await manager.quarantine_file(str(malware), "test")

    # Verify /etc/shadow NOT moved
    assert system_file.exists()
    assert system_file.read_text() == "root:x:..."

def test_race_condition_protection(tmp_path):
    """Verify race condition protection."""
    manager = QuarantineManager(str(tmp_path / "quarantine"))

    # Create test file
    test_file = tmp_path / "test.exe"
    original_content = b"ORIGINAL_MALWARE"
    test_file.write_bytes(original_content)

    # Attacker thread tries to swap file during quarantine
    swap_attempted = threading.Event()

    def attacker_thread():
        time.sleep(0.01)  # Wait for quarantine to start
        try:
            test_file.unlink()
            test_file.write_bytes(b"REPLACED_CONTENT")
            swap_attempted.set()
        except:
            pass

    thread = threading.Thread(target=attacker_thread)
    thread.start()

    # Quarantine file
    qid = await manager.quarantine_file(str(test_file), "test")
    thread.join()

    # Verify quarantined file has ORIGINAL content (not swapped)
    qf = manager._quarantined_files[qid]
    quarantined_content = Path(qf.quarantine_path).read_bytes()

    assert quarantined_content == original_content
    # Attacker's swap should have failed or been too late
```

---

## Phase 2: HIGH Severity (Week 2)

### Days 8-10: Security Hardening

#### 2.1 Implement Rate Limiting

**File**: `scripts/ml/download_malwarebazaar.py`

(See full implementation in audit report section 2.1)

#### 2.2 Environment Variable API Keys

**File**: `scripts/ml/download_malwarebazaar.py`

```python
import os

class MalwareBazaarDownloader:
    def __init__(self, output_dir: Path, delay: float = REQUEST_DELAY):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.session = requests.Session()

        # Get API key from environment (NEVER hardcode)
        api_key = os.environ.get("MALWAREBAZAAR_API_KEY")

        headers = {"User-Agent": "xanadOS-ML-Training/3.1.0"}
        if api_key:
            headers["Auth-Key"] = api_key
            logger.info("✅ Using authenticated API requests")
        else:
            logger.warning("⚠️  No API key set, using free tier (rate limited)")

        self.session.headers.update(headers)
```

Update `.github/workflows/train-models.yml`:
```yaml
- name: Acquire dataset
  env:
    MALWAREBAZAAR_API_KEY: ${{ secrets.MALWAREBAZAAR_API_KEY }}
  run: |
    uv run python scripts/ml/dataset_workflow.py --${DATASET_SIZE}
```

#### 2.3 Pin Vulnerable Libraries

**File**: `pyproject.toml`

```toml
[project.optional-dependencies]
malware-analysis = [
    "scikit-learn>=1.3.0,<2.0",
    "joblib>=1.3.0,<2.0",
    "pandas>=2.1.0,<3.0",
    "pefile==2023.2.7",        # Pin exact version (CVE-2022-XXXXX patched)
    "pyelftools==0.30",        # Pin exact version
    "lief==0.14.1",            # Pin exact version
    "pyzipper==0.3.6",         # Pin exact version
]
```

---

### Days 11-14: Monitoring & Validation

#### 2.4 Model Signature Verification

(See audit report section 2.4 for implementation)

#### 2.5 Enhanced CI/CD Security Scanning

(See audit report section 2.5 for implementation)

---

## Phase 3: MEDIUM Severity & Best Practices (Week 3)

### Days 15-17: Error Handling & Logging

1. Sanitize error messages (no path disclosure)
2. Add comprehensive audit logging
3. Implement structured logging

### Days 18-19: API Security

1. Add CSRF protection
2. Implement rate limiting
3. Add API key brute-force protection

### Day 20-21: Final Review & Documentation

1. Security test suite
2. Update security documentation
3. Team training session

---

## Testing Strategy

### Automated Security Tests

**Create**: `tests/security/` directory

Files:
- `test_code_injection.py`
- `test_safe_expression_evaluator.py`
- `test_malware_download_security.py`
- `test_feature_extraction_timeout.py`
- `test_quarantine_security.py`
- `test_permissions.py`

**Run Tests**:
```bash
# All security tests
pytest tests/security/ -v --cov=app --cov-report=html

# Specific vulnerability tests
pytest tests/security/test_code_injection.py -v
pytest tests/security/test_quarantine_security.py -v
```

---

## Rollout Plan

### Week 1 Checklist
- [ ] Day 1-2: Code injection fixes + AST evaluator
- [ ] Day 3-4: Hash verification + timeout protection
- [ ] Day 5-7: Quarantine TOCTOU + permissions
- [ ] **Milestone**: All CRITICAL vulnerabilities fixed
- [ ] **Gate**: Security test suite passes 100%

### Week 2 Checklist
- [ ] Day 8-10: Rate limiting + API keys + library pinning
- [ ] Day 11-14: Model verification + CI/CD scanning
- [ ] **Milestone**: All HIGH vulnerabilities fixed
- [ ] **Gate**: Penetration testing clean

### Week 3 Checklist
- [ ] Day 15-17: Error handling + logging
- [ ] Day 18-19: API security
- [ ] Day 20-21: Documentation + training
- [ ] **Milestone**: Production ready
- [ ] **Gate**: Security review approval

---

## Success Criteria

✅ **Phase 1 Complete When**:
- [ ] 0 CRITICAL vulnerabilities remaining
- [ ] All security tests passing
- [ ] Code review approved by 2 engineers

✅ **Phase 2 Complete When**:
- [ ] 0 HIGH vulnerabilities remaining
- [ ] Penetration testing clean
- [ ] CI/CD security gates passing

✅ **Phase 3 Complete When**:
- [ ] <5 MEDIUM vulnerabilities remaining
- [ ] Security documentation complete
- [ ] Team trained on secure coding

---

## Resources Required

**Engineering Time**:
- 1 Senior Engineer (security lead): 3 weeks full-time
- 1 ML Engineer (malware handling): 1 week part-time
- 1 DevOps Engineer (CI/CD): 1 week part-time

**Tools**:
- CodeQL (GitHub Advanced Security)
- Bandit (Python security linter)
- Safety (dependency checker)
- OWASP ZAP (API security testing)

**External**:
- Optional: Third-party security audit ($5K-$10K)

---

**Status**: 📋 Ready for implementation
**Next Action**: Begin Phase 1, Day 1
**Review Date**: Weekly security standup (Fridays)
