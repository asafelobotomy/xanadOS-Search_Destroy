"""
GUI module for xanadOS Search & Destroy application.
Contains all graphical user interface components.
"""

try:
    from .main_window import MainWindow
    from .scan_dialog import ScanDialog  
    from .settings_dialog import SettingsDialog
except ImportError as e:
    print(f"Warning: Could not import GUI components: {e}")
    MainWindow = None
    ScanDialog = None
    SettingsDialog = None

__all__ = [
    'MainWindow',
    'ScanDialog',
    'SettingsDialog'
]
