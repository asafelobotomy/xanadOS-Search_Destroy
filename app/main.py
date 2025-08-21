#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add app directory to Python path for proper imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from gui.main_window import MainWindow
from gui.setup_wizard import show_setup_wizard
from PyQt6.QtWidgets import QApplication
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
    
    # Initialize telemetry early
    from core.telemetry import initialize_telemetry, shutdown_telemetry
    from utils.config import load_config
    
    config = load_config()
    telemetry = initialize_telemetry(config)
    
    app = QApplication(sys.argv)
    app.setApplicationName("S&D - Search & Destroy")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("xanadOS")
    app.setOrganizationDomain("xanados.org")

    # Show setup wizard if needed (first time setup)
    setup_completed = show_setup_wizard()
    if not setup_completed:
        # User cancelled setup, exit gracefully
        print("Setup cancelled by user")
        sys.exit(0)

    window = MainWindow()
    
    # Set up single instance server to listen for new launch attempts
    instance_manager.setup_instance_server(window)
    
    # Clean up when application exits
    app.aboutToQuit.connect(instance_manager.cleanup)
    app.aboutToQuit.connect(shutdown_telemetry)
    
    window.show()

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
