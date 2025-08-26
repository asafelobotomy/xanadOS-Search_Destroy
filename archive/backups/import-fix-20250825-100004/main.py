#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add app directory to Python path for proper imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from gui.main_window import MainWindow
from gui.setup_wizard import show_setup_wizard
from gui.splash_screen import ModernSplashScreen, StartupProgressTracker
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from core.single_instance import SingleInstanceManager
from gui import APP_VERSION

# Import version info

# Suppress Wayland popup warnings if on Wayland
if os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ.setdefault("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")


def main():
    # Check for existing instance before creating QApplication
    instance_manager = SingleInstanceManager()
    
    if instance_manager.is_already_running():
        print("Application is already running. Bringing existing instance to front...")
        instance_manager.notify_existing_instance()
        sys.exit(0)  # Exit silently, existing instance will be shown
    
    # Create QApplication first
    app = QApplication(sys.argv)
    app.setApplicationName("S&D - Search & Destroy")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("xanadOS")
    app.setOrganizationDomain("xanados.org")

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
    from core.telemetry import initialize_telemetry, shutdown_telemetry
    from utils.config import load_config
    
    config = load_config()
    telemetry = initialize_telemetry(config)
    
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
        from core.telemetry import record_error
        record_error("app_crash", "main", str(e))
        raise
    finally:
        shutdown_telemetry()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
