"""Pytest configuration & shared fixtures/mocks."""
import sys
import os
import types
import pytest
from unittest.mock import Mock

# Ensure app on path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_dir = os.path.join(repo_root, 'app')
for p in (repo_root, app_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

@pytest.fixture(autouse=True)
def mock_pyqt(monkeypatch):
    """Auto-mock PyQt6 for headless test runs."""
    for mod in ["PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui"]:
        if mod not in sys.modules:
            sys.modules[mod] = Mock()
    yield

@pytest.fixture
def fake_elevated_run_success(monkeypatch):
    from types import SimpleNamespace
    def _factory(stdout="", returncode=0):
        def _impl(argv, **kwargs):
            return SimpleNamespace(args=argv, stdout=stdout, stderr="", returncode=returncode)
        return _impl
    monkeypatch.setattr("app.core.rkhunter_wrapper.elevated_run", _factory("System checks summary", 1))
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
