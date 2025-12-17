# Security Audit Preparation - xanadOS Search & Destroy

**Version**: 0.3.0-beta
**Date Prepared**: December 16, 2025
**Status**: Ready for Third-Party Audit

---

## Executive Summary

xanadOS Search & Destroy is a comprehensive Linux security scanner combining:
- **ClamAV** signature-based malware detection
- **YARA** heuristic/behavioral analysis
- **Real-time monitoring** via fanotify/inotify
- **Automated system hardening** with PolicyKit integration
- **Advanced reporting** with compliance framework support

This document outlines security architecture, threat model, implemented controls, and areas requiring external validation.

---

## 1. Application Overview

### 1.1 Core Components

| Component | Description | Security Level |
|-----------|-------------|----------------|
| **Scanner Engine** | Multi-engine malware detection | HIGH |
| **File Monitor** | Real-time file system watching | HIGH |
| **Quarantine Manager** | Isolated threat storage (0700 perms) | CRITICAL |
| **System Hardening** | Automated security configurations | CRITICAL |
| **Web API** | FastAPI REST/WebSocket interface | MEDIUM |
| **GUI** | PyQt6 desktop interface | LOW |

### 1.2 Privilege Model

**Unprivileged Operations**:
- File scanning (user-owned files)
- Report generation
- Dashboard viewing
- Configuration reading

**Privileged Operations** (require PolicyKit authentication):
- ClamAV daemon control (`systemctl restart clamav-daemon`)
- System hardening (`sysctl` modifications, firewall rules)
- Protected file scanning (`/etc`, `/var`)
- Quarantine operations (root-owned threats)

**Security Framework**: `app/core/security_integration.py`

---

## 2. Threat Model

### 2.1 Threats In Scope

1. **Command Injection** (HIGH PRIORITY)
   - User-provided file paths
   - Report generation parameters
   - Scheduler configuration

2. **Path Traversal** (HIGH PRIORITY)
   - Scan directory selection
   - Quarantine file access
   - Log file manipulation

3. **Privilege Escalation** (CRITICAL)
   - PolicyKit bypass attempts
   - Exploiting elevated operations
   - Race conditions in privilege checks

4. **Data Exposure** (MEDIUM)
   - Scan results containing sensitive paths
   - Quarantine file leakage
   - Log files with PII

5. **Denial of Service** (MEDIUM)
   - Resource exhaustion (memory, CPU)
   - Infinite scanning loops
   - Scheduler bombing (1000+ concurrent tasks)

6. **Supply Chain** (MEDIUM)
   - Malicious dependencies
   - Compromised third-party libraries
   - Update mechanism vulnerabilities

### 2.2 Threats Out of Scope

- Physical access attacks
- Social engineering
- Browser-based attacks (no web UI for end users)
- Operating system vulnerabilities
- Hardware attacks (side-channel, etc.)

---

## 3. Implemented Security Controls

### 3.1 Input Validation (`app/core/input_validation.py`)

**File Path Validation**:
```python
def validate_file_path(path: str) -> None:
    """Validates file paths against security rules."""
    # Checks:
    # - Null byte injection
    # - Path traversal (../ sequences)
    # - Forbidden paths (/proc, /sys, /dev, /boot, /etc/shadow)
    # - Symbolic link validation
    # - Maximum path length (4096 chars)
```

**Forbidden Paths**:
- `/proc/*` - Process information
- `/sys/*` - Kernel parameters
- `/dev/*` - Device files
- `/boot/*` - Boot loader
- `/etc/shadow` - Password hashes
- `/etc/sudoers` - Sudo configuration

**Size Limits**:
- `MAX_FILE_SIZE`: 100MB (prevents memory exhaustion)
- `MAX_SCAN_DEPTH`: 10 levels (prevents infinite recursion)
- `MAX_FILES_PER_SCAN`: 10,000 files (prevents DoS)

### 3.2 Privilege Escalation Protection

**PolicyKit Integration** (`config/*.policy`):
- All privileged operations require explicit PolicyKit actions
- User authentication via `pkexec` or `polkit-agent`
- Audit logging for all elevated operations

**Command Whitelist** (`app/utils/process_management.py`):
```python
ALLOWED_COMMANDS = [
    "systemctl",  # Service management
    "freshclam",  # ClamAV updates
    "sysctl",     # Kernel parameters
    "ufw",        # Firewall
]

def execute_with_privilege(command: list[str]) -> subprocess.CompletedProcess:
    """Executes command with validation."""
    if command[0] not in ALLOWED_COMMANDS:
        raise SecurityError(f"Command {command[0]} not whitelisted")
```

**No Shell Execution**:
- All commands use `subprocess` with `shell=False`
- Arguments passed as lists (prevents shell injection)
- NEVER construct commands via f-strings with user input

### 3.3 Data Protection

**Quarantine Security**:
- Directory permissions: `0700` (owner-only access)
- Files stored with `.quarantine` extension
- SHA256 hash verification on retrieval
- Encrypted metadata (optional with weasyprint)

**Log Sanitization**:
- PII redaction (email addresses, usernames)
- Path normalization (relative paths in logs)
- Sensitive data masking (passwords, tokens)

**Configuration Security**:
- Config files: `~/.config/search-and-destroy/` (0700)
- No auto-save (prevents corruption from crashes)
- Atomic writes (temp file + rename)

### 3.4 Resource Limits

**Threading**:
- Adaptive thread pool (2-8 threads based on CPU cores)
- Deadlock prevention via timeout enforcement
- Memory semaphores: `max_file_operations=50`, `max_scan_operations=20`

**Scan Cache**:
- Cache size limit: 10,000 entries
- FIFO eviction policy
- TTL: 24 hours per entry

---

## 4. Audit Scope & Objectives

### 4.1 Code Review Focus Areas

**Priority 1 (Critical)**:
1. `app/core/security_integration.py` - Privilege escalation framework
2. `app/core/input_validation.py` - Input sanitization
3. `app/utils/process_management.py` - Command execution
4. `config/*.policy` - PolicyKit configuration

**Priority 2 (High)**:
5. `app/core/unified_scanner_engine.py` - Quarantine handling
6. `app/api/web_dashboard.py` - Web API security
7. `app/monitoring/file_watcher.py` - Real-time monitoring

**Priority 3 (Medium)**:
8. `app/reporting/*` - Report generation (injection risks)
9. `app/utils/config.py` - Configuration management
10. `tests/` - Security test coverage

### 4.2 Penetration Testing Scenarios

**Scenario 1: Path Traversal Attack**
```bash
# Attempt to scan /etc/shadow via path traversal
./app.main --scan-path "/home/user/../../etc/shadow"
```
**Expected**: Blocked by `is_safe_path()` validation

**Scenario 2: Command Injection**
```bash
# Attempt injection via scheduler config
scheduler.add_schedule(name="test; rm -rf /", ...)
```
**Expected**: Blocked by parameter sanitization

**Scenario 3: Privilege Escalation**
```python
# Attempt to execute arbitrary command
execute_with_privilege(["sh", "-c", "whoami"])
```
**Expected**: Blocked by command whitelist

**Scenario 4: Resource Exhaustion**
```python
# Attempt to exhaust memory via large scan
scanner.scan_directory("/", recursive=True, max_depth=999)
```
**Expected**: Limited by `MAX_SCAN_DEPTH=10`, `MAX_FILES_PER_SCAN=10000`

**Scenario 5: Quarantine Escape**
```python
# Attempt to access quarantined file directly
shutil.copy("/quarantine/malware.quarantine", "/tmp/malware")
```
**Expected**: Blocked by 0700 permissions (owner-only)

### 4.3 Dependency Security

**Supply Chain Validation**:
- All dependencies pinned with version constraints (`pyproject.toml`)
- `safety` checks for known vulnerabilities (CI/CD)
- `bandit` static security analysis (CI/CD)

**Key Dependencies to Review**:
- `PyQt6` (GUI framework) - CVE check
- `fastapi` (Web API) - Authentication gaps
- `aiohttp` (Async HTTP) - SSRF risks
- `watchdog` (File monitoring) - Race conditions
- `yara-python` (YARA bindings) - Memory safety

---

## 5. Known Limitations

### 5.1 Acknowledged Security Gaps

**1. Web API Authentication** (Phase 3 roadmap)
- Current: No authentication on FastAPI endpoints
- Risk: Unauthorized access to scanner functions
- Mitigation: Bind to localhost only (`127.0.0.1:8000`)
- Planned: JWT authentication, API keys, rate limiting

**2. Encrypted Quarantine** (Phase 3 roadmap)
- Current: Files stored with 0700 permissions (plaintext)
- Risk: Root user can access quarantined malware
- Mitigation: Restricted permissions, separate partition
- Planned: AES-256 encryption for quarantine files

**3. Update Verification** (Phase 3 roadmap)
- Current: ClamAV updates via `freshclam` (no signature verification in code)
- Risk: Compromised update server
- Mitigation: Rely on ClamAV's built-in GPG verification
- Planned: Application-level update mechanism with GPG

**4. Audit Logging** (Partial implementation)
- Current: File-based logs (`~/.local/share/search-and-destroy/logs/`)
- Risk: Log tampering by privileged user
- Mitigation: Syslog integration available
- Planned: Immutable audit log (write-only)

### 5.2 Design Decisions (Security vs. Usability)

**Decision 1: PolicyKit vs. Sudo**
- Choice: PolicyKit (more granular control)
- Tradeoff: Complexity vs. security
- Rationale: Prevents blanket `sudo` access, per-action authentication

**Decision 2: Local-only Web API**
- Choice: Bind to 127.0.0.1 only
- Tradeoff: No remote access vs. no network exposure
- Rationale: Minimize attack surface (Phase 3: remote access with auth)

**Decision 3: Scan Cache Enabled by Default**
- Choice: Cache scan results for performance
- Tradeoff: Potential stale results vs. 70-80% performance gain
- Rationale: Cache key includes mtime (detects file changes)

---

## 6. Testing & Validation

### 6.1 Security Test Suite

**Automated Tests** (`tests/`):
- ✅ 300+ unit tests (100% pass rate)
- ✅ 23 edge case tests (`test_reporting_edge_cases.py`)
- ✅ 45+ advanced coverage tests (`test_advanced_coverage.py`)
- ✅ 15 performance regression tests (`test_performance_monitoring.py`)

**Security-Specific Tests**:
- Path traversal prevention: `tests/test_core/test_input_validation.py`
- Command injection: `tests/test_utils/test_process_management.py`
- Privilege escalation: `tests/test_core/test_security_integration.py`
- Resource limits: `tests/test_advanced_coverage.py::TestSchedulerStressTests`

### 6.2 Static Analysis

**Tools Used**:
- `bandit` - Security vulnerability scanner
- `ruff` - Python linter with security rules
- `mypy` - Type safety (prevents type confusion attacks)
- `safety` - Dependency vulnerability checker

**CI/CD Integration** (`.github/workflows/ci.yml`):
- Runs on every commit
- Blocks merge on security findings

---

## 7. Audit Deliverables

### 7.1 Expected Outputs

1. **Vulnerability Assessment Report**:
   - CVSS scores for identified vulnerabilities
   - Exploitation difficulty ratings
   - Recommended remediation timelines

2. **Penetration Testing Report**:
   - Attack scenarios tested
   - Successful exploits (if any)
   - Proof-of-concept code

3. **Code Review Summary**:
   - High-risk code patterns identified
   - Best practice violations
   - Secure coding recommendations

4. **Compliance Assessment** (optional):
   - CWE compliance (Common Weakness Enumeration)
   - OWASP Top 10 coverage
   - Security framework alignment (NIST, ISO 27001)

### 7.2 Remediation Process

**Severity Levels**:
- **Critical** (CVSS 9.0-10.0): Fix within 7 days
- **High** (CVSS 7.0-8.9): Fix within 30 days
- **Medium** (CVSS 4.0-6.9): Fix within 90 days
- **Low** (CVSS 0.1-3.9): Fix in next major release

**Remediation Workflow**:
1. Auditor submits findings
2. Development team triages and confirms
3. Security patches developed and tested
4. Regression testing (full test suite)
5. Security advisory published (if public disclosure needed)
6. Patch released with version bump

---

## 8. Contact Information

**Security Contact**:
- Email: security@xanados.dev (replace with actual)
- PGP Key: [Provide public key]
- Response SLA: 48 hours

**Responsible Disclosure Policy**:
- Report vulnerabilities privately first
- 90-day disclosure window for patch development
- Credit provided in security advisories

---

## Appendix A: Security Checklist

### Code Review Checklist

- [ ] All user inputs validated via `input_validation.py`
- [ ] No `shell=True` in subprocess calls
- [ ] Command whitelist enforced
- [ ] PolicyKit policies properly scoped
- [ ] Quarantine permissions verified (0700)
- [ ] No hardcoded credentials
- [ ] Logging sanitizes PII
- [ ] Resource limits enforced
- [ ] Error messages don't leak sensitive data
- [ ] Atomic file operations (no race conditions)

### Penetration Testing Checklist

- [ ] Path traversal attacks blocked
- [ ] Command injection attempts blocked
- [ ] Privilege escalation prevented
- [ ] Resource exhaustion mitigated
- [ ] Quarantine escape impossible
- [ ] SSRF attacks (Web API) blocked
- [ ] XSS attacks (Web UI) blocked
- [ ] CSRF protection (Web API) implemented
- [ ] Rate limiting tested
- [ ] Session management secure

### Dependency Audit Checklist

- [ ] All dependencies scanned for CVEs
- [ ] Pinned versions in `pyproject.toml`
- [ ] No deprecated packages
- [ ] License compliance verified
- [ ] Supply chain integrity (GPG/checksums)

---

**End of Security Audit Preparation Document**
