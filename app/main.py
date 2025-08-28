#!/usr/bin/env python3
"""Application entry point for xanadOS Search & Destroy (PyQt6 GUI)."""

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication  # pylint: disable=no-name-in-module

# Ensure package imports resolve whether run via `python -m app.main` or script
app_dir = Path(__file__).parent
project_root = app_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.single_instance import SingleInstanceManager

# Import version info

# Suppress Wayland popup warnings if on Wayland
if os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ.setdefault("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")


def main():
    """Launch the application with single-instance guard and splash workflow."""
    # Check for existing instance before creating QApplication
    instance_manager = SingleInstanceManager()

    if instance_manager.is_already_running():
        print("Application is already running. Bringing existing instance to front...")
        instance_manager.notify_existing_instance()
        sys.exit(0)  # Exit silently, existing instance will be shown

    # Create QApplication first
    app = QApplication(sys.argv)
    app.setApplicationName("S&D - Search & Destroy")
    # Prefer VERSION file from project root to avoid fragile app.__init__ coupling
    try:
        with open(project_root / "VERSION", "r", encoding="utf-8") as vf:
            version = vf.read().strip()
    except Exception:
        version = "dev"
    app.setApplicationVersion(version)
    app.setOrganizationName("xanadOS")
    app.setOrganizationDomain("xanados.org")

    # Import GUI modules only AFTER QApplication is constructed
    from app.core.telemetry import (  # pylint: disable=import-outside-toplevel
        initialize_telemetry,
        record_error,
        shutdown_telemetry,
    )
    from app.gui.main_window import MainWindow
    from app.gui.setup_wizard import show_setup_wizard
    from app.gui.splash_screen import ModernSplashScreen, StartupProgressTracker
    from app.utils.config import load_config  # pylint: disable=import-outside-toplevel

    # Create and show splash screen immediately
    splash = ModernSplashScreen()
    progress_tracker = StartupProgressTracker(splash)
    splash.show()
    progress_tracker.start_tracking()

    # Process events to show splash screen
    app.processEvents()

    # Phase 1: UI Initialization
    progress_tracker.complete_phase("ui_init")
    app.processEvents()

    # Initialize telemetry early

    config = load_config()
    initialize_telemetry(config)

    # Phase 2: Cache Initialization
    progress_tracker.complete_phase("cache_init")
    app.processEvents()

    # Show setup wizard if needed (first time setup)
    setup_completed = show_setup_wizard()
    if not setup_completed:
        # User cancelled setup, exit gracefully
        print("Setup cancelled by user")
        splash.close()
        sys.exit(0)

    # Phase 3: System Check (will be optimized with caching)
    progress_tracker.complete_phase("system_check")
    app.processEvents()

    # Create main window with progressive loading
    window = MainWindow(splash_screen=splash, progress_tracker=progress_tracker)

    # Set up single instance server to listen for new launch attempts
    instance_manager.setup_instance_server(window)

    # Clean up when application exits
    app.aboutToQuit.connect(instance_manager.cleanup)
    app.aboutToQuit.connect(shutdown_telemetry)

    # Phase 4: Dashboard Loading (handled by MainWindow)
    # Phase 5: Finalization (handled by MainWindow)

    try:
        exit_code = app.exec()
    except Exception as e:
        record_error("app_crash", "main", str(e))
        raise
    finally:
        shutdown_telemetry()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
