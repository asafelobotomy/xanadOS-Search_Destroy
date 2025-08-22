#!/usr/bin/env python3
"""
xanadOS Search & Destroy - Main Application Package
A modern GUI for ClamAV antivirus scanning with real-time monitoring.
"""

import os
from pathlib import Path


def get_version():
    """Read version from VERSION file in the project root."""
    try:
        # Get the project root directory (2 levels up from this file)
        project_root = Path(__file__).parent.parent
        version_file = project_root / "VERSION"
        
        if version_file.exists():
            return version_file.read_text().strip()
        else:
            # Fallback version if VERSION file doesn't exist
            return "2.9.0"
    except (OSError, IOError, FileNotFoundError):
        # Fallback version in case of any file reading errors
        return "2.9.0"

__version__ = get_version()
__author__ = "xanadOS Team"
__license__ = "GPL-3.0"

# Application metadata
APP_NAME = "S&D - Search & Destroy"
APP_DESCRIPTION = "Modern GUI for ClamAV antivirus scanning"
APP_VERSION = __version__
