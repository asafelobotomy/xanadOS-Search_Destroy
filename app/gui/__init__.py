#!/usr/bin/env python3
"""xanadOS Search & Destroy - Main Application Package
A modern GUI for ClamAV antivirus scanning with real-time monitoring.
"""


def get_version():
    """Delegate to root app.get_version() for a single source of truth."""
    try:
        from app import get_version as _root_get_version  # local import to avoid cycles

        return _root_get_version()
    except Exception:
        return "dev"


__version__ = get_version()
__author__ = "xanadOS Team"
__license__ = "GPL-3.0"

# Application metadata
APP_NAME = "S&D - Search & Destroy"
APP_DESCRIPTION = "Modern GUI for ClamAV antivirus scanning"
APP_VERSION = __version__
