import json
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path

from core.file_scanner import FileScanner
from core.firewall_detector import get_firewall_status, toggle_firewall
from core.rkhunter_wrapper import RKHunterScanResult, RKHunterWrapper
from core.auto_updater import AutoUpdater, UpdateNotifier
from gui.rkhunter_components import RKHunterScanDialog, RKHunterScanThread
from gui.scan_thread import ScanThread
from gui.update_components import UpdateNotifier
from monitoring import MonitorConfig, MonitorState, RealTimeMonitor
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QFont,
    QIcon,
    QKeySequence,
    QMouseEvent,
    QPixmap,
    QShortcut,
    QTextOption,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
    QSpacerItem,
)
from utils.config import load_config, save_config
from utils.scan_reports import (
    ScanReportManager,
    ScanResult,
    ScanType,
    ThreatInfo,
    ThreatLevel,
)

from gui import APP_VERSION
from gui import settings_pages
from gui.theme_manager import get_theme_manager
from gui.themed_widgets import ThemedWidgetMixin


class NoWheelComboBox(QComboBox):
    """ComboBox that ignores wheel events to prevent accidental changes."""
    def wheelEvent(self, event: QWheelEvent):  # type: ignore[override]
        event.ignore()


class NoWheelSpinBox(QSpinBox):
    """SpinBox that ignores wheel events."""
    def wheelEvent(self, event: QWheelEvent):  # type: ignore[override]
        event.ignore()


class NoWheelTimeEdit(QTimeEdit):
    """TimeEdit that ignores wheel events."""
    def wheelEvent(self, event: QWheelEvent):  # type: ignore[override]
        event.ignore()


class ClickableFrame(QFrame):
    """A clickable frame widget."""

    clicked = pyqtSignal()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MainWindow(QMainWindow, ThemedWidgetMixin):
    """Primary application window with automatic theming."""

    def __init__(self):
        super().__init__()

        # Initialize optimized theming system
        # Theme manager is automatically initialized when first accessed
        
        # Set initial theme from config
        try:
            self.config = load_config()
        except Exception:
            self.config = {}
            
        theme_name = self.config.get("ui_settings", {}).get("theme", "dark")
        get_theme_manager().set_theme(theme_name)

        # 2. Core managers / engines
        self.report_manager = ScanReportManager()
        try:
            self.rkhunter = RKHunterWrapper()
        except Exception:
            self.rkhunter = None
        try:
            self.scanner = FileScanner()
        except Exception:
            self.scanner = None
        self.current_scan_thread = None

        # 3. Scan state flags (must exist before any UI logic references them)
        self._scan_running = False
        self._scan_state = "idle"
        self._scan_manually_stopped = False
        self._pending_scan_request = None
        self._stop_scan_user_wants_restart = False

        # 4. Initialize model state & UI (handles first-time UI build internally)
        self._initialize_scan_state()

        # Initialize force quit tracking
        self._force_quitting = False
        
        # Set up signal handlers for external termination
        self._setup_signal_handlers()

        # Apply text orientation setting at startup
        try:
            self.apply_text_orientation_setting()
        except Exception:
            pass  # Will use default center alignment

        # Initialize auto-update system
        try:
            self._initialize_auto_updater()
        except Exception as e:
            print(f"Warning: Could not initialize auto-updater: {e}")

        # 8. Debounced settings saver
        self._settings_save_timer = QTimer(self)
        self._settings_save_timer.setSingleShot(True)
        self._settings_save_timer.timeout.connect(self._auto_save_settings_commit)

        # 7. Post-start self checks
        QTimer.singleShot(0, self._run_startup_self_check)

    # --- RKHunter safe availability helper ---
    def _rkhunter_available(self) -> bool:
        rk = getattr(self, 'rkhunter', None)
        if not rk:
            return False
        if hasattr(rk, 'is_available'):
            try:
                return bool(rk.is_available())  # type: ignore[attr-defined]
            except Exception:
                return bool(getattr(rk, 'available', False))
        return bool(getattr(rk, 'available', False))

    def create_settings_tab(self):
        """Create the settings tab (modular layout only; legacy removed)."""
        return self._create_settings_tab_modular()

    # --- Settings Widget Factories (used by external builders) ---
    def _make_activity_retention_combo(self):
        combo = NoWheelComboBox(); combo.addItems(["10","25","50","100","200"]); combo.setCurrentText("100"); combo.currentTextChanged.connect(self.on_retention_setting_changed); return combo
    def _make_threads_spin(self):
        spin = NoWheelSpinBox(); spin.setRange(1,16); spin.setValue(4); return spin
    def _make_timeout_spin(self):
        spin = NoWheelSpinBox(); spin.setRange(30,3600); spin.setValue(300); spin.setSuffix(' seconds'); return spin
    def _make_depth_combo(self):
        combo = NoWheelComboBox()
        combo.addItem('Surface (Faster)', 1)
        combo.addItem('Normal', 2)  
        combo.addItem('Deep (Thorough)', 3)
        combo.setCurrentIndex(1)
        return combo
    def _make_file_filter_combo(self):
        combo = NoWheelComboBox()
        combo.addItem('All Files', 'all')
        combo.addItem('Executables Only', 'executables')
        combo.addItem('Documents & Media', 'documents')
        combo.addItem('System Files', 'system')
        combo.setCurrentIndex(0)  # Default to "All Files"
        return combo
    def _make_memory_limit_combo(self):
        combo = NoWheelComboBox()
        combo.addItem('Low (512MB)', 512)
        combo.addItem('Normal (1GB)', 1024)
        combo.addItem('High (2GB)', 2048)
        combo.setCurrentIndex(1)  # Default to "Normal (1GB)"
        return combo
    def _make_frequency_combo(self):
        combo = NoWheelComboBox(); combo.addItems(['Daily','Weekly','Monthly']); return combo
    def _make_time_edit(self):
        return NoWheelTimeEdit()
    def _make_scan_type_combo(self):
        combo = NoWheelComboBox(); combo.addItems(['Quick Scan','Full System Scan','Custom Directory']); return combo
    def _build_custom_dir_widget(self):
        container = QWidget(); from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton
        layout = QHBoxLayout(container); layout.setContentsMargins(0,0,0,0)
        self.settings_custom_dir_edit = QLineEdit(); self.settings_custom_dir_edit.setReadOnly(True); layout.addWidget(self.settings_custom_dir_edit)
        self.settings_custom_dir_btn = QPushButton('Browse...'); layout.addWidget(self.settings_custom_dir_btn)
        self.settings_custom_dir_widget = container

    def _format_tooltip(self, text, max_chars_per_line=50):
        """Format tooltip text with consistent width and line breaks."""
        import textwrap
        
        # Split by existing newlines and process each paragraph
        paragraphs = text.split('\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():  # Non-empty paragraph
                # Wrap long lines
                wrapped = textwrap.fill(paragraph.strip(), width=max_chars_per_line)
                formatted_paragraphs.append(wrapped)
            else:  # Empty line
                formatted_paragraphs.append("")
        
        return '\n'.join(formatted_paragraphs)

    def _initialize_scan_state(self):
        """Initialize scan state tracking variables."""
        # Enhanced scan state tracking
        self.is_quick_scan_running = False
        self._scan_state = "idle"  # idle, scanning, stopping, completing
        self._pending_scan_request = None  # Store scan parameters if user tries to start during stopping
        self._stop_scan_user_wants_restart = False  # Track if user wants to restart after stop

        # Initialize real-time monitoring
        self.real_time_monitor = None
        self.monitoring_enabled = self.config.get("security_settings", {}).get(
            "real_time_protection", False
        )
        # Firewall change tracking - to avoid reporting GUI changes as
        # "external"
        self._firewall_change_from_gui = False

        # Performance monitoring
        from core.performance_monitor import get_performance_monitor

        self.performance_monitor = get_performance_monitor()
        self.performance_monitor.add_optimization_callback(
            self.handle_performance_optimization
        )

        # Tooltip state management
        self.tooltip_detailed = False
        self.tooltip_timer = QTimer()
        self.tooltip_timer.setSingleShot(True)


        # Theme management - default to dark mode
        self.current_theme = self.config.get("ui_settings", {}).get("theme", "dark")

    def _setup_signal_handlers(self):
        """Set up signal handlers for external termination detection."""
        try:
            # Handle common termination signals
            def signal_handler(signum, frame):
                self._force_quitting = True
                # Attempt graceful shutdown
                try:
                    from PyQt6.QtWidgets import QApplication
                    QApplication.quit()
                except:
                    pass
            
            # Set up handlers for SIGINT (Ctrl+C) and SIGTERM (kill command)
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # On Unix systems, also handle SIGHUP (terminal close)
            if hasattr(signal, 'SIGHUP'):
                signal.signal(signal.SIGHUP, signal_handler)
                
        except Exception as e:
            # Signal handling might not be available on all platforms
            print(f"Warning: Could not set up signal handlers: {e}")

        # IMPORTANT: The UI is already constructed in __init__. Historically this method re-ran
        # init_ui() and other setup methods which caused duplicate widgets, signal connections,
        # excessive memory use and occasional crashes during scans when progress callbacks tried
        # to update stale/duplicate widgets. We remove those duplicate calls and add a guard so
        # future refactors don't regress.
        if getattr(self, "_ui_initialized", False):
            pass  # UI already initialized safely
        else:
            # In rare cases if _initialize_scan_state() is called prior to explicit init, allow build
            self.init_ui()
            self._ui_initialized = True

        # Initialize real-time monitoring (with error handling)
        self.init_real_time_monitoring_safe()

        # Use QTimer to update status after UI is fully initialized
        QTimer.singleShot(100, self.update_definition_status)
        QTimer.singleShot(200, self.update_protection_ui_after_init)
        # Add a safety net timer to ensure status is never left as
        # "Initializing..."
        QTimer.singleShot(1000, self.ensure_protection_status_final)

        # Load persisted activity logs after UI is created
        QTimer.singleShot(500, self.load_activity_logs)

        # Activity log saving is now handled by unified timer system for better performance
        # (Consolidated with other periodic tasks to reduce timer overhead)

        # Initialize unified timer system for performance optimization
        self.init_unified_timer_system()

        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        
        # Mark initialization as complete - scheduler can now be started safely
        self._initialization_complete = True
        print("✅ Main window initialization complete - scheduler operations now enabled")
        
        # Setup enhanced Qt effects for all buttons
        self._setup_enhanced_effects()
        
        # Add welcome message to results display
        self._show_welcome_message()
        
        # Start scheduler if scheduled scans are enabled
        QTimer.singleShot(100, self.start_scheduler_if_enabled)

    def start_scheduler_if_enabled(self):
        """Start the scheduler if scheduled scans are enabled (called after initialization)."""
        try:
            if hasattr(self, 'settings_enable_scheduled_cb') and self.settings_enable_scheduled_cb.isChecked():
                print("🔄 Starting scheduler for enabled scheduled scans...")
                if hasattr(self.scanner, 'start_scheduler'):
                    self.scanner.start_scheduler()
                    print("✅ Scheduler started successfully")
                else:
                    print("⚠️ Scanner doesn't have scheduler capability")
        except Exception as e:
            print(f"⚠️ Error starting scheduler after initialization: {e}")

    def bring_to_front(self):
        """Bring the application window to the front (called by single instance manager)."""
        try:
            # If window is hidden (minimized to tray), show it
            if not self.isVisible():
                self.show()
                print("📱 Restored window from hidden state")
            
            # If window is minimized, restore it
            if self.isMinimized():
                self.showNormal()
                print("📱 Restored window from minimized state")
            
            # Bring to front and activate
            self.raise_()
            self.activateWindow()
            
            # Show a notification if system tray is available
            if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "S&D - Search & Destroy",
                    "Application window restored - another launch attempt was detected.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
            
            print("✅ Successfully brought application to front")
                    
        except Exception as e:
            print(f"❌ Error bringing window to front: {e}")

    
    def get_status_color(self, status_type):
        """Get theme-appropriate color for status indicators."""
        if self.current_theme == "dark":
            colors = {
                "success": "#9CB898",  # Sage Green for dark theme
                "error": "#F14666",  # Deep Strawberry for dark theme
                "warning": "#EE8980",  # Coral for dark theme
            }
        else:  # light theme
            colors = {
                "success": "#75BDE0",  # Sky Blue for light theme
                "error": "#F89B9B",  # Coral Pink for light theme
                "warning": "#F8BC9B",  # Peach Orange for light theme
            }
        return colors.get(status_type, colors["error"])

    def init_unified_timer_system(self):
        """Initialize a unified timer system for better performance."""
        # Create a master timer for coordinated updates
        self.master_timer = QTimer()
        self.master_timer.timeout.connect(self.unified_timer_update)

        # Track update cycles to reduce frequency of expensive operations
        self.timer_cycle_count = 0

        # Start with a moderate interval (use 0ms for idle processing)
        self.master_timer.start(1000)  # 1 second base interval

        # Performance monitoring
        self.performance_stats = {
            "timer_calls": 0,
            "update_times": [],
            "skip_count": 0}

    def unified_timer_update(self):
        """Central timer update method for performance optimization."""
        import time

        start_time = time.time()

        try:
            self.timer_cycle_count += 1
            self.performance_stats["timer_calls"] += 1

            # Only update firewall status every 5 cycles (5 seconds)
            if self.timer_cycle_count % 5 == 0:
                self.update_firewall_status()

            # Only update monitoring stats every 10 cycles (10 seconds)
            if self.timer_cycle_count % 10 == 0:
                if hasattr(
                        self, "stats_timer") and hasattr(
                        self, "real_time_monitor"):
                    self.update_monitoring_statistics()

                # Update system tray tooltip with performance info
                self.update_system_tray_tooltip()

            # Activity logs are now saved immediately when entries are added

            # Reset counter to prevent overflow
            if self.timer_cycle_count >= 300:  # Reset every 5 minutes
                self.timer_cycle_count = 0

        except Exception as e:
            # Log error in unified timer update
            pass

        # Track performance
        execution_time = time.time() - start_time
        self.performance_stats["update_times"].append(execution_time)

        # Keep only last 100 measurements
        if len(self.performance_stats["update_times"]) > 100:
            self.performance_stats["update_times"] = self.performance_stats[
                "update_times"
            ][-100:]

    def handle_performance_optimization(self, pressure_type: str):
        """Handle performance optimization events."""
        try:
            if pressure_type == "cpu_pressure":
                # Reduce update frequency during high CPU usage
                if hasattr(self, "master_timer"):
                    self.master_timer.setInterval(2000)  # Slower updates
                # CPU optimization applied

            elif pressure_type == "memory_pressure":
                # Force garbage collection
                import gc
                gc.collect()
                # Memory optimization applied

        except Exception as e:
            # Error in performance optimization
            pass

    def get_performance_card_data(self) -> tuple:
        """Get concise performance data for system tray tooltip."""
        try:
            summary = self.performance_monitor.get_performance_summary()
            if summary.get("status") == "no_data":
                return "Initializing", "#666", ""

            score = summary.get("performance_score", 0)
            current = summary.get("current", {})

            if score >= 80:
                status = "Excellent"
                color = "#27AE60"  # Green
            elif score >= 60:
                status = "Good"
                color = "#3498DB"  # Blue
            elif score >= 40:
                status = "Fair"
                color = "#F39C12"  # Orange
            else:
                status = "Poor"
                color = "#E74C3C"  # Red

            # Create compact metrics for detailed tooltip if needed
            details = ""
            if current:
                cpu = current.get("cpu_percent", 0)
                memory = current.get("memory_mb", 0)
                details = f"CPU: {cpu:.1f}% | Memory: {memory:.0f}MB"

            return status, color, details

        except Exception as e:
            return "Error", "#E74C3C", f"Monitor error: {e}"

    def init_ui(self):
        self.setWindowTitle("S&D - Search & Destroy")
        self.setMinimumSize(1000, 750)
        self.resize(1200, 850)

        # Set window icon
        icon_path = (
            Path(__file__).parent.parent.parent
            / "packaging"
            / "icons"
            / "org.xanados.SearchAndDestroy.svg"
        )
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header section
        self.create_header_section(main_layout)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.create_dashboard_tab()  # Add dashboard as first tab
        self.create_scan_tab()
        self.create_real_time_tab()
        self.create_reports_tab()
        self.create_quarantine_tab()
        self.create_settings_tab()

        main_layout.addWidget(self.tab_widget)

        # Status bar
        self.create_status_bar()

        # Menu bar
        self.create_menu_bar()

        # System tray setup
        self.setup_system_tray()

    def create_header_section(self, layout):
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)

        # App icon and title
        title_layout = QHBoxLayout()

        # Load and display the actual S&D icon
        self.icon_label = QLabel()
        # Restored to 128x128 as requested
        self.icon_label.setFixedSize(128, 128)
        self.update_icon_for_theme()
        title_layout.addWidget(self.icon_label)

        # App title
        title_label = QLabel("S&D - Search & Destroy")
        title_label.setObjectName("appTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)

        # Quick actions
        actions_layout = QHBoxLayout()

        self.quick_scan_btn = QPushButton("Quick Scan")
        self.quick_scan_btn.setObjectName("actionButton")
        self.quick_scan_btn.setMinimumSize(
            120, 40
        )  # Increased size to prevent text cutoff
        self.quick_scan_btn.setToolTip(
            "Comprehensive Quick Scan of multiple directories\n"
            "• Downloads, Documents, Pictures, Videos, Music\n"
            "• Browser data, temporary files, application data\n"
            "• Fast scanning optimized for common threat locations"
        )
        self.quick_scan_btn.clicked.connect(self.quick_scan)

        # Update definitions button with status
        update_container = QVBoxLayout()
        update_btn = QPushButton("Update Definitions")
        update_btn.setObjectName("actionButton")
        update_btn.setMinimumSize(140, 40)  # Increased size for longer text
        update_btn.clicked.connect(self.update_definitions)

        # Last update status label
        self.last_update_label = QLabel("Checking...")
        self.last_update_label.setObjectName("lastUpdateLabel")
        self.last_update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Last checked status label
        self.last_checked_label = QLabel("Checking...")
        self.last_checked_label.setObjectName("lastCheckedLabel")
        self.last_checked_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        update_container.addWidget(update_btn)
        update_container.addWidget(self.last_update_label)
        update_container.addWidget(self.last_checked_label)
        update_container_widget = QWidget()
        update_container_widget.setObjectName("updateDefinitionsContainer")
        update_container_widget.setLayout(update_container)

        about_btn = QPushButton("About")
        about_btn.setObjectName("actionButton")
        # Increased size to prevent text cutoff
        about_btn.setMinimumSize(80, 40)
        about_btn.clicked.connect(self.show_about)

        actions_layout.addWidget(self.quick_scan_btn)
        actions_layout.addWidget(update_container_widget)
        actions_layout.addWidget(about_btn)

        header_layout.addLayout(actions_layout)
        layout.addWidget(header_frame)

    def create_dashboard_tab(self):
        """Create an overview dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Security Status Overview
        status_row = QHBoxLayout()
        status_row.setSpacing(15)

        # Protection Status Card - using strawberry palette
        self.protection_card = self.create_clickable_status_card(
            "Real-Time Protection",
            "Active" if self.monitoring_enabled else "Inactive",
            "#9CB898" if self.monitoring_enabled else "#F14666",
            (
                "Your system is being monitored"
                if self.monitoring_enabled
                else "Click to enable protection"
            ),
        )
        # Connect the click signal
        self.protection_card.clicked.connect(
            self.toggle_protection_from_dashboard)

        # Firewall Status Card - using firewall palette
        firewall_status = get_firewall_status()
        firewall_active = firewall_status.get("is_active", False)
        self.firewall_card = self.create_clickable_status_card(
            "Firewall Protection",
            "Active" if firewall_active else "Inactive",
            "#9CB898" if firewall_active else "#F14666",
            (
                "Firewall is protecting your system"
                if firewall_active
                else "Click to enable firewall"
            ),
        )
        # Connect the click signal
        self.firewall_card.clicked.connect(self.toggle_firewall_from_dashboard)

        # Last Scan Card - now clickable
        self.last_scan_card = self.create_clickable_status_card(
            "Last Scan",
            "Not scanned yet",  # Will be updated dynamically
            "#17a2b8",
            "Click to go to Scan tab",  # Updated description
        )
        # Connect the click signal
        self.last_scan_card.clicked.connect(self.open_scan_tab)

        # Threats Card - now clickable - using strawberry palette
        self.threats_card = self.create_clickable_status_card(
            "Threats Found",
            "0",  # Will be updated dynamically
            "#9CB898",
            "Click to view quarantine",  # Updated description
        )
        # Connect the click signal
        self.threats_card.clicked.connect(self.open_quarantine_tab)

        status_row.addWidget(self.protection_card)
        status_row.addWidget(self.firewall_card)
        status_row.addWidget(self.last_scan_card)
        status_row.addWidget(self.threats_card)

        layout.addLayout(
            status_row
        )  # Activity Report (expanded to fill the space)
        activity_group = QGroupBox("Activity Report")
        activity_layout = QVBoxLayout(activity_group)

        self.dashboard_activity = QListWidget()
        # Remove height restriction to allow it to expand
        self.dashboard_activity.setAlternatingRowColors(True)
        # Set custom styling for activity list
        self.setup_activity_list_styling()
        activity_layout.addWidget(self.dashboard_activity)

        # Show more link
        show_more_btn = QPushButton("View All Activity →")
        show_more_btn.setFlat(True)
        show_more_btn.clicked.connect(
            lambda: self.tab_widget.setCurrentIndex(2)
        )  # Go to protection tab
        activity_layout.addWidget(show_more_btn)

        layout.addWidget(activity_group)

        layout.addStretch()

        # Add as first tab
        self.tab_widget.addTab(dashboard_widget, "Dashboard")

    def create_status_card(self, title, value, color, description):
        """Create a modern status card widget."""
        card = QFrame()
        card.setObjectName("statusCard")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Medium)
        title_label.setFont(title_font)

        # Value (main status)
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: bold;"
        )

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDescription")
        desc_label.setWordWrap(True)
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_label.setFont(desc_font)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        layout.addStretch()

        return card

    def create_clickable_status_card(self, title, value, color, description):
        """Create a clickable modern status card widget."""
        card = ClickableFrame()
        card.setObjectName("statusCard")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Medium)
        title_label.setFont(title_font)

        # Value (main status)
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: bold;"
        )

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDescription")
        desc_label.setWordWrap(True)
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_label.setFont(desc_font)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        layout.addStretch()

        return card

    def toggle_protection_from_dashboard(self):
        """Toggle protection when the dashboard status card is clicked."""
        # If monitor wasn't initialized, try to initialize it first
        if self.real_time_monitor is None:
            success = self.init_real_time_monitoring_safe()
            if not success:
                self.add_activity_message(
                    "❌ Cannot toggle protection: Monitoring system unavailable"
                )
                return

        self.monitoring_enabled = not self.monitoring_enabled
        self.update_protection_status_card()

        # Update the protection tab if it exists
        if hasattr(self, "protection_toggle_btn"):
            if self.monitoring_enabled:
                self.start_real_time_protection()
            else:
                self.stop_real_time_protection()
        else:
            # Just update the config if the protection tab doesn't exist yet
            self.config["security_settings"] = self.config.get(
                "security_settings", {})
            self.config["security_settings"][
                "real_time_protection"
            ] = self.monitoring_enabled
            save_config(self.config)

            if self.monitoring_enabled:
                self.add_activity_message(
                    "🛡️ Real-time protection enabled from dashboard"
                )
            else:
                self.add_activity_message(
                    "Real-time protection disabled from dashboard"
                )

    def toggle_firewall_from_dashboard(self):
        """Toggle firewall when the dashboard status card is clicked."""
        
        # Get current firewall status
        try:
            current_status = get_firewall_status()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return
            
        is_currently_active = current_status.get('is_active', False)
        
        # Toggle the firewall (enable if currently disabled, disable if currently enabled)
        enable_firewall = not is_currently_active
        
        # Show confirmation dialog for critical operations
        if enable_firewall:
            action = "enable"
            message = "This will enable your firewall with basic security rules. Continue?"
        else:
            action = "disable"
            message = "This will disable your firewall, reducing system security. Continue?"
        
        reply = self.show_themed_message_box(
            "question",
            f"Confirm Firewall {action.title()}", 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Show info about authentication
        self.add_activity_message(f"🔒 Requesting admin privileges to {action} firewall...")
        
        # Set flag to indicate this change is from GUI (prevents "external" messages)
        self._firewall_change_from_gui = True
        
        # Perform the firewall toggle operation
        try:
            result = toggle_firewall(enable_firewall)
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Reset flag since operation failed
            self._firewall_change_from_gui = False
            self.add_activity_message(f"❌ Error during firewall {action}: {str(e)}")
            return
        
        if result.get('success', False):
            # Success - show message and update UI
            success_msg = str(result.get('message', f'Firewall {action}d successfully'))
            
            # Check if alternative method was used
            if 'method' in result:
                method = result['method']
                if method.startswith('iptables_direct'):
                    success_msg += "\n\n⚠️ Note: Using direct iptables (UFW unavailable due to kernel module issues)"
                elif method.startswith('systemd_'):
                    success_msg += f"\n\n⚠️ Note: Using systemd service fallback ({method.split('_')[1]})"
            
            self.add_activity_message(f"🔥 Firewall {action}d successfully from dashboard")
            self.show_themed_message_box(
                "information",
                "Firewall Control",
                success_msg
            )
            # Force immediate status update
            self.update_firewall_status()
            self.update_firewall_status_card()
        else:
            # Error - show error message and reset flag
            self._firewall_change_from_gui = False
            error_msg = str(result.get('error', 'Unknown error'))
            
            # Check if it's a permission/authentication error
            if (
                "permission denied" in error_msg.lower()
                or "authentication" in error_msg.lower()
                or "cancelled" in error_msg.lower()
            ):
                print("🔍 DEBUG: Authentication error detected")
                self.add_activity_message(
                    f"🔒 Firewall {action} cancelled - authentication required")
                self.show_themed_message_box(
                    "warning",
                    "Authentication Required",
                    f"Firewall control requires administrator privileges.\n"
                    f"Authentication was cancelled or failed.",
                )
            else:
                print("🔍 DEBUG: Other error detected")
                self.add_activity_message(f"❌ Failed to {action} firewall: {error_msg}")
                
                # Check if there's diagnostic information for kernel module issues
                diagnosis = result.get('diagnosis', '')
                if diagnosis:
                    # Kernel module issue detected - show detailed dialog
                    detailed_msg = f"Failed to {action} firewall:\n{error_msg}\n\n"
                    detailed_msg += "Diagnostic Information:\n"
                    detailed_msg += diagnosis
                    detailed_msg += "\n\nSuggestions:\n"
                    detailed_msg += "• Try 'Alternative Firewall Mode' - the app will attempt direct iptables rules\n"
                    detailed_msg += "• Update your system and reboot: sudo pacman -Syu && sudo reboot\n"
                    detailed_msg += "• Load modules manually: sudo modprobe iptable_filter iptable_nat\n"
                    detailed_msg += "• Check if iptables packages are installed"
                    
                    self.show_themed_message_box(
                        "critical",
                        "Firewall Kernel Module Error",
                        detailed_msg,
                    )
                else:
                    # Regular error message
                    self.show_themed_message_box(
                        "critical",
                        "Firewall Error",
                        f"Failed to {action} firewall:\n{error_msg}",
                    )
        print("🔍 DEBUG: toggle_firewall_from_dashboard() complete")

    def open_scan_tab(self):
        """Open the Scan tab when Last Scan card is clicked."""
        # Switch to the Scan tab (index 1)
        self.tab_widget.setCurrentIndex(1)

    def open_quarantine_tab(self):
        """Open the Quarantine tab when Threats Found card is clicked."""
        # Switch to the Quarantine tab (index 4)
        self.tab_widget.setCurrentIndex(4)
        # Refresh quarantine list to show current state
        if hasattr(self, 'refresh_quarantine'):
            self.refresh_quarantine()

    def update_protection_status_card(self):
        """Update the protection status card with current state."""
        if hasattr(self, "protection_card"):
            # Find the card's value label and update it
            for child in self.protection_card.findChildren(QLabel):
                if child.objectName() == "cardValue":
                    child.setText(
                        "Active" if self.monitoring_enabled else "Inactive")
                    child.setStyleSheet(
                        f"color: {
                            '#9CB898' if self.monitoring_enabled else '#F14666'}; font-size: 20px; font-weight: bold;")
                elif child.objectName() == "cardDescription":
                    child.setText(
                        "Your system is being monitored"
                        if self.monitoring_enabled
                        else "Click to enable protection"
                    )

    def update_firewall_status_card(self):
        """Update the firewall status card with current state."""
        if hasattr(self, "firewall_card"):
            # Get current firewall status
            firewall_status = get_firewall_status()
            is_active = firewall_status.get("is_active", False)

            # Find the card's value label and update it
            for child in self.firewall_card.findChildren(QLabel):
                if child.objectName() == "cardValue":
                    child.setText("Active" if is_active else "Inactive")
                    child.setStyleSheet(
                        f"color: {
                            '#9CB898' if is_active else '#F14666'}; font-size: 20px; font-weight: bold;")
                elif child.objectName() == "cardDescription":
                    child.setText(
                        "Firewall is protecting your system"
                        if is_active
                        else "Click to enable firewall"
                    )

    def update_protection_ui_after_init(self):
        """Update Protection tab UI after full initialization to ensure state consistency."""
        print("🔄 Updating Protection tab UI after initialization...")

        if hasattr(self, "protection_status_label") and hasattr(
            self, "protection_toggle_btn"
        ):
            if self.monitoring_enabled:
                # Check if the monitor is actually running
                if (
                    self.real_time_monitor
                    and hasattr(self.real_time_monitor, "state")
                    and self.real_time_monitor.state.name == "RUNNING"
                ):
                    self.protection_status_label.setText("🛡️ Active")
                    color = self.get_status_color("success")
                    self.protection_status_label.setStyleSheet(
                        f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                    self.protection_toggle_btn.setText("Stop")
                    print("✅ Protection tab UI updated to Active state")
                else:
                    # Monitoring was supposed to be enabled but isn't running -
                    # reset
                    print(
                        "⚠️ Monitoring was enabled but not running - resetting to inactive"
                    )
                    self.monitoring_enabled = False
                    self.protection_status_label.setText("❌ Failed to restore")
                    color = self.get_status_color("error")
                    self.protection_status_label.setStyleSheet(
                        f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                    self.protection_toggle_btn.setText("Start")

                    # Update config to reflect actual state
                    if "security_settings" not in self.config:
                        self.config["security_settings"] = {}
                    self.config["security_settings"]["real_time_protection"] = False
                    save_config(self.config)
            else:
                self.protection_status_label.setText("🔴 Inactive")
                color = self.get_status_color("error")
                self.protection_status_label.setStyleSheet(
                    f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("Start")
                print("✅ Protection tab UI updated to Inactive state")

            # Also update the dashboard card
            self.update_protection_status_card()
        else:
            print("⚠️ Protection tab UI elements not found - skipping update")

    def ensure_protection_status_final(self):
        """Final safety net to ensure protection status is never left as 'Initializing...'"""
        print("🔍 Running final protection status check...")

        if hasattr(self, "protection_status_label"):
            current_text = self.protection_status_label.text()
            if "Initializing" in current_text:
                print(
                    "⚠️ Found status still showing 'Initializing...', forcing to Inactive"
                )
                # Force status to Inactive if still showing Initializing
                self.protection_status_label.setText("🔴 Inactive")
                color = self.get_status_color("error")
                self.protection_status_label.setStyleSheet(
                    f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                if hasattr(self, "protection_toggle_btn"):
                    self.protection_toggle_btn.setText("Start")
                print("✅ Protection status forced to Inactive state")
            else:
                print(
                    f"✅ Protection status is properly set to: {current_text}")
        else:
            print("⚠️ Protection status label not found")

    def update_firewall_status(self):
        """Update the firewall status display."""
        if not hasattr(self, "firewall_status_label"):
            return

        try:
            status = get_firewall_status()

            # Check if status has changed from previous check
            current_active_state = status.get("is_active", False)
            if not hasattr(self, "_last_firewall_state"):
                self._last_firewall_state = None

            # Only log if this is the first check or if status changed
            if self._last_firewall_state != current_active_state:
                if self._last_firewall_state is not None:  # Not the first check
                    # Check if this change was made from within the GUI
                    if (
                        hasattr(self, "_firewall_change_from_gui")
                        and self._firewall_change_from_gui
                    ):
                        # Reset the flag and don't report as external change
                        self._firewall_change_from_gui = False
                    else:
                        # This is a genuine external change
                        state_msg = "enabled" if current_active_state else "disabled"
                        self.add_activity_message(
                            f"🔥 Firewall {state_msg} externally")
                self._last_firewall_state = current_active_state

            # Update firewall name
            if hasattr(self, "firewall_name_label"):
                firewall_name = status.get("firewall_name", "Unknown")
                self.firewall_name_label.setText(
                    str(firewall_name) if firewall_name else "Unknown"
                )

            # Update status based on firewall state
            is_active = status.get("is_active", False)
            error = status.get("error")

            if error:
                # Error state
                self.firewall_on_off_label.setText("ERROR")
                self.firewall_on_off_label.setStyleSheet(
                    "font-weight: bold; font-size: 16px; color: #F14666;"
                )
                self.firewall_status_circle.setStyleSheet(
                    "font-size: 20px; color: #F14666;"
                )
                if hasattr(self, "firewall_name_label"):
                    self.firewall_name_label.setText(f"Error: {error}")
            elif is_active:
                # Active state - green
                self.firewall_on_off_label.setText("ON")
                self.firewall_on_off_label.setStyleSheet(
                    "font-weight: bold; font-size: 16px; color: #9CB898;"
                )
                self.firewall_status_circle.setStyleSheet(
                    "font-size: 20px; color: #9CB898;"
                )
            else:
                # Inactive state - red
                self.firewall_on_off_label.setText("OFF")
                self.firewall_on_off_label.setStyleSheet(
                    "font-weight: bold; font-size: 16px; color: #F14666;"
                )
                self.firewall_status_circle.setStyleSheet(
                    "font-size: 20px; color: #F14666;"
                )

            # Update button text based on current status
            if hasattr(self, "firewall_toggle_btn"):
                if error:
                    self.firewall_toggle_btn.setText("Check Firewall")
                    self.firewall_toggle_btn.setEnabled(True)
                else:
                    self.firewall_toggle_btn.setText(
                        "Disable Firewall" if is_active else "Enable Firewall"
                    )
                    self.firewall_toggle_btn.setEnabled(True)

            # Also update the dashboard firewall card
            self.update_firewall_status_card()

        except Exception as e:
            print(f"⚠️ Error updating firewall status: {e}")
            # Fallback to unknown state
            self.firewall_on_off_label.setText("UNKNOWN")
            self.firewall_on_off_label.setStyleSheet(
                "font-weight: bold; font-size: 16px; color: #999;"
            )
            self.firewall_status_circle.setStyleSheet(
                "font-size: 20px; color: #999;")
            if hasattr(self, "firewall_name_label"):
                self.firewall_name_label.setText("Unable to detect")

    def toggle_firewall_status(self):
        """Toggle the firewall on/off based on current status."""
        if not hasattr(self, 'firewall_toggle_btn'):
            return
            
        # Disable button during operation
        self.firewall_toggle_btn.setEnabled(False)
        self.firewall_toggle_btn.setText("Working...")
        
        try:
            # Get current status to determine what action to take
            current_status = get_firewall_status()
            is_currently_active = current_status.get('is_active', False)
            
            # Toggle the firewall (enable if currently disabled, disable if currently enabled)
            enable_firewall = not is_currently_active
            
            # Show confirmation dialog for critical operations
            if enable_firewall:
                action = "enable"
                message = "This will enable your firewall with basic security rules. Continue?"
            else:
                action = "disable"
                message = "This will disable your firewall, reducing system security. Continue?"
            
            reply = self.show_themed_message_box(
                "question",
                f"Confirm Firewall {action.title()}", 
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                # User cancelled - restore button
                self._restore_firewall_button()
                return
            
            # Show info about authentication
            self.add_activity_message(f"🔒 Requesting admin privileges to {action} firewall...")
            
            # Update button to show authentication in progress
            self.firewall_toggle_btn.setText("Authenticating...")
            
            # Set flag to indicate this change is from GUI (prevents "external" messages)
            self._firewall_change_from_gui = True
            
            # Perform the firewall toggle operation
            print(f"🔍 DEBUG (Protection): About to call toggle_firewall({enable_firewall})")
            try:
                result = toggle_firewall(enable_firewall)
                print(f"🔍 DEBUG (Protection): toggle_firewall returned: {result}")
            except Exception as e:
                print(f"❌ DEBUG (Protection): Exception in toggle_firewall: {e}")
                import traceback
                traceback.print_exc()
                # Reset flag since operation failed
                self._firewall_change_from_gui = False
                self.add_activity_message(f"❌ Error during firewall {action}: {str(e)}")
                self._restore_firewall_button()
                return
            
            if result.get('success', False):
                # Success - show message and update UI
                success_msg = str(result.get('message', f'Firewall {action}d successfully'))
                
                # Check if alternative method was used
                if 'method' in result:
                    method = result['method']
                    if method.startswith('iptables_direct'):
                        success_msg += "\n\n⚠️ Note: Using direct iptables (UFW unavailable due to kernel module issues)"
                    elif method.startswith('systemd_'):
                        success_msg += f"\n\n⚠️ Note: Using systemd service fallback ({method.split('_')[1]})"
                
                self.add_activity_message(f"🔥 Firewall {action}d successfully")
                self.show_themed_message_box(
                    "information",
                    "Firewall Control",
                    success_msg
                )
                # Force immediate status update
                self.update_firewall_status()
            else:
                # Error - show error message and reset flag
                self._firewall_change_from_gui = False
                error_msg = str(result.get('error', 'Unknown error'))
                
                # Check if it's a permission/authentication error
                if (
                    "permission denied" in error_msg.lower()
                    or "authentication" in error_msg.lower()
                    or "cancelled" in error_msg.lower()
                ):
                    self.add_activity_message(f"🔒 Firewall {action} cancelled - authentication required")
                    self.show_themed_message_box(
                        "warning",
                        "Authentication Required",
                        f"Firewall control requires administrator privileges.\n"
                        f"Authentication was cancelled or failed."
                    )
                else:
                    self.add_activity_message(f"❌ Failed to {action} firewall: {error_msg}")
                    
                    # Check if there's diagnostic information for kernel module issues
                    diagnosis = result.get('diagnosis', '')
                    if diagnosis:
                        # Kernel module issue detected - show detailed dialog
                        detailed_msg = f"Failed to {action} firewall:\n{str(result.get('message', error_msg))}\n\n"
                        detailed_msg += "Diagnostic Information:\n"
                        detailed_msg += diagnosis
                        detailed_msg += "\n\nSuggestions:\n"
                        detailed_msg += "• Try 'Alternative Firewall Mode' - the app will attempt direct iptables rules\n"
                        detailed_msg += "• Update your system and reboot: sudo pacman -Syu && sudo reboot\n"
                        detailed_msg += "• Load modules manually: sudo modprobe iptable_filter iptable_nat\n"
                        detailed_msg += "• Check if iptables packages are installed"
                        
                        self.show_themed_message_box(
                            "critical",
                            "Firewall Kernel Module Error",
                            detailed_msg
                        )
                    else:
                        # Regular error message
                        self.show_themed_message_box(
                            "critical",
                            "Firewall Control Error",
                            f"Failed to {action} firewall:\n{str(result.get('message', error_msg))}"
                        )
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error: {str(e)}"
            self.add_activity_message(f"❌ Firewall control error: {error_msg}")
            self.show_themed_message_box(
                "critical",
                "Firewall Control Error",
                f"An unexpected error occurred:\n{error_msg}"
            )
        finally:
            # Always restore button state
            self._restore_firewall_button()

    def _restore_firewall_button(self):
        """Restore firewall button to normal state."""
        if hasattr(self, "firewall_toggle_btn"):
            self.firewall_toggle_btn.setEnabled(True)
            # Update button text based on current firewall status
            try:
                status = get_firewall_status()
                is_active = status.get("is_active", False)
                self.firewall_toggle_btn.setText(
                    "Disable Firewall" if is_active else "Enable Firewall"
                )
            except (OSError, subprocess.SubprocessError):
                self.firewall_toggle_btn.setText("Toggle Firewall")

    def toggle_alternative_firewall(self):
        """Toggle firewall using alternative methods when standard UFW fails."""
        print("🔍 DEBUG: toggle_alternative_firewall() called")
        
        # Prevent multiple simultaneous operations
        if hasattr(self, '_alt_firewall_change_from_gui') and self._alt_firewall_change_from_gui:
            print("🔍 DEBUG: Alternative firewall operation already in progress")
            return
        
        self._alt_firewall_change_from_gui = True
        self.alt_firewall_btn.setEnabled(False)
        self.alt_firewall_btn.setText("Working...")
        
        try:
            # Determine current firewall state
            current_status = get_firewall_status()
            is_active = current_status.get('is_active', False)
            
            # Toggle the opposite state
            enable_firewall = not is_active
            action = "enable" if enable_firewall else "disable"
            
            self.add_activity_message(f"🔄 Attempting alternative firewall {action}...")
            
            # Use the alternative firewall method directly
            from core.firewall_detector import FirewallDetector
            detector = FirewallDetector()
            
            try:
                result = detector._try_alternative_firewall_method(enable_firewall)
                print(f"🔍 DEBUG: Alternative firewall result: {result}")
            except Exception as e:
                print(f"❌ DEBUG: Exception in alternative firewall: {e}")
                import traceback
                traceback.print_exc()
                # Reset flag since operation failed
                self._alt_firewall_change_from_gui = False
                self.add_activity_message(f"❌ Error during alternative firewall {action}: {str(e)}")
                self._restore_alt_firewall_button()
                return
            
            if result.get('success', False):
                # Success - show message and update UI
                success_msg = str(result.get('message', f'Alternative firewall {action}d successfully'))
                method = result.get('method', 'unknown')
                
                if method.startswith('iptables_direct'):
                    success_msg += "\n\n✅ Used direct iptables rules for basic protection"
                elif method.startswith('systemd_'):
                    service_name = method.split('_')[1] if '_' in method else 'service'
                    success_msg += f"\n\n✅ Used systemd service management ({service_name})"
                
                self.add_activity_message(f"🔥 Alternative firewall {action}d successfully")
                self.show_themed_message_box(
                    "information",
                    "Alternative Firewall",
                    success_msg
                )
                
                # Force immediate status update
                self.update_firewall_status()
            else:
                # Error - show error message and reset flag
                self._alt_firewall_change_from_gui = False
                error_msg = str(result.get('message', 'Unknown error'))
                
                self.add_activity_message(f"❌ Alternative firewall {action} failed: {error_msg}")
                self.show_themed_message_box(
                    "warning",
                    "Alternative Firewall Failed",
                    f"Alternative firewall methods failed:\n{error_msg}\n\n"
                    f"This may indicate that your system needs a reboot to use newer kernel modules, "
                    f"or that firewall packages need to be reinstalled."
                )
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error: {str(e)}"
            self.add_activity_message(f"❌ Alternative firewall error: {error_msg}")
            self.show_themed_message_box(
                "critical",
                "Alternative Firewall Error",
                f"An unexpected error occurred:\n{error_msg}"
            )
        
        self._alt_firewall_change_from_gui = False
        self._restore_alt_firewall_button()

    def _restore_alt_firewall_button(self):
        """Restore the alternative firewall button to its normal state."""
        if hasattr(self, 'alt_firewall_btn'):
            self.alt_firewall_btn.setEnabled(True)
            self.alt_firewall_btn.setText("Alt Mode")

    def create_scan_tab(self):
        # DEBUG: log available rkhunter attributes related to availability/version
        try:
            import logging
            logging.getLogger(__name__).debug('create_scan_tab rkhunter attrs: %s', [m for m in dir(getattr(self,'rkhunter', object())) if 'avail' in m or 'version' in m])
        except Exception:
            pass
        scan_widget = QWidget()
        main_layout = QHBoxLayout(scan_widget)
        main_layout.setSpacing(8)  # Compact spacing between columns
        main_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins

        # ========== COLUMN 1: Scan Results ==========
        column1 = QWidget()
        column1_layout = QVBoxLayout(column1)
        column1_layout.setSpacing(8)
        column1.setMinimumWidth(300)  # Equal minimum width
        column1.setMaximumWidth(450)  # Equal maximum width

        # Results section with optimized height - now has more space
        results_group = QGroupBox("Scan Results")
        results_group.setMinimumHeight(200)  # Increased minimum since progress moved
        # No maximum height - allow full column expansion
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setObjectName("resultsText")
        self.results_text.setReadOnly(True)
        self.results_text.setAcceptRichText(True)  # Enable HTML formatting
        self.results_text.setMinimumHeight(160)  # Minimum for readability
        
        # Set default text alignment to center
        doc = self.results_text.document()
        option = doc.defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doc.setDefaultTextOption(option)
        
        # Initialize autoscroll tracking
        self._user_has_scrolled = False
        self._last_scroll_position = 0
        
        # Connect to scroll events to detect user scrolling
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_changed)
        
        # No maximum height - allow full expansion
        results_layout.addWidget(self.results_text)

        column1_layout.addWidget(results_group)
        # No stretch - let results section fill the entire column

        # ========== COLUMN 2: Progress, Scan Type & Actions ==========
        column2 = QWidget()
        column2_layout = QVBoxLayout(column2)
        column2_layout.setSpacing(8)
        column2.setMinimumWidth(300)  # Equal minimum width
        column2.setMaximumWidth(450)  # Equal maximum width

        # Progress section with compact design
        progress_group = QGroupBox("Scan Progress")
        progress_group.setMaximumHeight(90)  # Compact for column 2
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(4)

        self.status_label = QLabel("Ready to scan")
        self.status_label.setObjectName("statusLabel")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgressBar")
        self.progress_bar.setMinimumHeight(18)  # Compact height

        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        column2_layout.addWidget(progress_group)

        # === Scan Type Selection Section ===
        scan_type_group = QGroupBox("Scan Type")
        scan_type_layout = QVBoxLayout(scan_type_group)
        scan_type_layout.setSpacing(8)
        
        self.scan_type_combo = NoWheelComboBox()
        self.scan_type_combo.addItem("🚀 Quick Scan", "QUICK")
        self.scan_type_combo.addItem("🔍 Full Scan", "FULL") 
        self.scan_type_combo.addItem("⚙️ Custom Scan", "CUSTOM")
        self.scan_type_combo.setObjectName("scanTypeCombo")
        self.scan_type_combo.setToolTip(
            "Choose scan thoroughness level:\n"
            "• Quick: Scans your selected path with optimized settings\n"
            "• Full: Complete system scan of entire home directory\n"
            "• Custom: Targeted scan of your specific folder selection"
        )
        self.scan_type_combo.currentTextChanged.connect(self.on_scan_type_changed)
        # Set proper size policy and minimum size for the combo
        self.scan_type_combo.setMinimumHeight(45)  # Good height for visibility
        self.scan_type_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        scan_type_layout.addWidget(self.scan_type_combo)
        column2_layout.addWidget(scan_type_group)

        # ========== COLUMN 3: Scan Target ==========
        column3 = QWidget()
        column3_layout = QVBoxLayout(column3)
        column3_layout.setSpacing(8)
        column3.setMinimumWidth(300)  # Equal minimum width
        column3.setMaximumWidth(450)  # Equal maximum width

        # === Target Selection Section ===
        target_group = QGroupBox("Scan Target")
        target_layout = QVBoxLayout(target_group)
        target_layout.setSpacing(6)

        # Preset buttons with improved layout
        presets_container = QWidget()
        presets_grid = QGridLayout(presets_container)
        presets_grid.setSpacing(5)
        
        # Create preset buttons with proper sizing
        self.home_scan_btn = QPushButton("🏠 Home Folder")
        self.home_scan_btn.setObjectName("presetButton")
        self.home_scan_btn.setToolTip("Scan your home directory for threats")
        self.home_scan_btn.setMinimumHeight(28)  # Reduced button height
        self.home_scan_btn.clicked.connect(lambda: self.set_scan_path(str(Path.home())))

        self.downloads_scan_btn = QPushButton("📥 Downloads")
        self.downloads_scan_btn.setObjectName("presetButton")
        self.downloads_scan_btn.setToolTip("Scan Downloads folder for threats")
        self.downloads_scan_btn.setMinimumHeight(28)
        self.downloads_scan_btn.clicked.connect(
            lambda: self.set_scan_path(str(Path.home() / "Downloads"))
        )

        self.custom_scan_btn = QPushButton("📁 Choose Folder...")
        self.custom_scan_btn.setObjectName("presetButton")
        self.custom_scan_btn.setToolTip("Select a specific folder to scan")
        self.custom_scan_btn.setMinimumHeight(28)
        self.custom_scan_btn.clicked.connect(self.select_scan_path)

        # Arrange buttons in a 2x2 grid for better space usage
        presets_grid.addWidget(self.home_scan_btn, 0, 0)
        presets_grid.addWidget(self.downloads_scan_btn, 0, 1)
        presets_grid.addWidget(self.custom_scan_btn, 1, 0, 1, 2)  # Span 2 columns

        target_layout.addWidget(presets_container)

        # Selected path display with better formatting
        path_container = QWidget()
        path_layout = QVBoxLayout(path_container)
        path_layout.setSpacing(5)
        
        path_label_desc = QLabel("Selected Path:")
        path_label_desc.setObjectName("sectionLabel")
        self.path_label = QLabel("Please select a path")
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)  # Allow text wrapping for long paths

        path_layout.addWidget(path_label_desc)
        path_layout.addWidget(self.path_label)
        target_layout.addWidget(path_container)
        
        column3_layout.addWidget(target_group)
        column3_layout.addStretch()  # Fill remaining space since actions moved to column2

        # === Action Buttons Section ===
        buttons_group = QGroupBox("Actions")
        buttons_layout = QVBoxLayout(buttons_group)
        buttons_layout.setSpacing(8)  # Reduced spacing between buttons
        
        # Primary scan toggle button
        self.scan_toggle_btn = QPushButton("🚀 Start Scan")
        self.scan_toggle_btn.setObjectName("primaryButton")
        self.scan_toggle_btn.setMinimumHeight(32)
        self.scan_toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.scan_toggle_btn.clicked.connect(self.toggle_scan)
        
        # Keep track of current scan state for button toggling
        self._scan_running = False

        # RKHunter button
        self.rkhunter_scan_btn = QPushButton("🔍 RKHunter Scan")
        self.rkhunter_scan_btn.setObjectName("specialButton")
        self.rkhunter_scan_btn.setMinimumHeight(28)
        self.rkhunter_scan_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.rkhunter_scan_btn.setToolTip(
            "Run RKHunter rootkit detection scan\n(Configure scan categories in Settings → Scanning)"
        )

        # Check if RKHunter is available
        # Robust availability check (wrapper refactor safety)
        rkhunter_available = False
        if self.rkhunter is not None:
            try:
                if hasattr(self.rkhunter, 'is_available'):
                    rkhunter_available = self.rkhunter.is_available()
                else:
                    # Fallback to attribute if method missing
                    rkhunter_available = bool(getattr(self.rkhunter, 'available', False))
            except Exception:
                rkhunter_available = False
        if rkhunter_available:
            self.rkhunter_scan_btn.clicked.connect(self.start_rkhunter_scan)
        else:
            self.rkhunter_scan_btn.setText("📦 Setup RKHunter")
            self.rkhunter_scan_btn.setToolTip("RKHunter not available - click to install or configure")
            self.rkhunter_scan_btn.clicked.connect(self.install_rkhunter)

        buttons_layout.addWidget(self.scan_toggle_btn)
        buttons_layout.addWidget(self.rkhunter_scan_btn)
        
        column2_layout.addWidget(buttons_group)
        column2_layout.addStretch()  # Push everything to top

        # Add 3 columns to main layout with equal proportions
        main_layout.addWidget(column1, 1)   # 33.3% width for results
        main_layout.addWidget(column2, 1)   # 33.3% width for scan type & actions
        main_layout.addWidget(column3, 1)   # 33.3% width for target

        self.tab_widget.addTab(scan_widget, "Scan")
        
        # Initialize the scan type description
        self.on_scan_type_changed()

    def create_reports_tab(self):
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)

        # Reports controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Reports")
        refresh_btn.clicked.connect(self.refresh_reports)

        export_btn = QPushButton("Export Reports")
        export_btn.clicked.connect(self.export_reports)

        delete_all_btn = QPushButton("Delete All Reports")
        delete_all_btn.clicked.connect(self.delete_all_reports)
        color = self.get_status_color("error")
        delete_all_btn.setStyleSheet(
            f"color: {color};"
        )  # Theme-appropriate red to indicate destructive action

        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(export_btn)
        controls_layout.addWidget(delete_all_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Reports list
        self.reports_list = QListWidget()
        self.reports_list.itemClicked.connect(self.load_report)

        # Report viewer
        self.report_viewer = QTextEdit()
        self.report_viewer.setObjectName("reportViewer")
        self.report_viewer.setReadOnly(True)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.reports_list)
        splitter.addWidget(self.report_viewer)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        self.tab_widget.addTab(reports_widget, "Reports")

        # Initialize reports list
        self.refresh_reports()

    def create_quarantine_tab(self):
        quarantine_widget = QWidget()
        layout = QVBoxLayout(quarantine_widget)

        # Quarantine controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_quarantine)
        restore_btn = QPushButton("Restore Selected")
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")

        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(restore_btn)
        controls_layout.addWidget(delete_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Quarantine list
        self.quarantine_list = QListWidget()
        layout.addWidget(self.quarantine_list)

        self.tab_widget.addTab(quarantine_widget, "Quarantine")

    # --- Modular Settings Scaffold (Restored) ---
    def _create_settings_tab_modular(self):
        settings_widget = QWidget()
        settings_widget.setObjectName("settingsTabWidget")
        root_layout = QVBoxLayout(settings_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        default_btn = QPushButton("Default Settings")
        default_btn.setMinimumHeight(34)
        default_btn.clicked.connect(self.load_default_settings)
        top_bar.addWidget(default_btn)
        top_bar.addStretch()
        root_layout.addLayout(top_bar)

        split_layout = QHBoxLayout()
        split_layout.setSpacing(10)

        self.settings_category_list = QListWidget()
        self.settings_category_list.setFixedWidth(180)
        self.settings_category_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.settings_category_list.currentRowChanged.connect(self._on_settings_category_changed)
        split_layout.addWidget(self.settings_category_list)

        self.settings_pages = QStackedWidget()
        split_layout.addWidget(self.settings_pages, 1)
        root_layout.addLayout(split_layout, 1)

        self._settings_pages_builders = [
            ("General", settings_pages.build_general_page),
            ("Scanning", settings_pages.build_scanning_page),
            ("Real-Time", settings_pages.build_realtime_page),
            ("Scheduling", settings_pages.build_scheduling_page),
            ("Security", settings_pages.build_security_page),
            ("RKHunter", settings_pages.build_rkhunter_page),
            ("Interface", settings_pages.build_interface_page),
            ("Updates", settings_pages.build_updates_page),
        ]
        for label, builder in self._settings_pages_builders:
            page = builder(self)
            self.settings_pages.addWidget(page)
            self.settings_category_list.addItem(label)

        if self.settings_category_list.count():
            self.settings_category_list.setCurrentRow(0)

        self.load_current_settings()
        self.setup_auto_save_connections()
        self.tab_widget.addTab(settings_widget, "Settings")

    def _on_settings_category_changed(self, row: int):
        if 0 <= row < self.settings_pages.count():
            self.settings_pages.setCurrentIndex(row)

    # Removed inline page builder methods; now in settings_pages module.

    def _build_settings_page_security(self):
        page = QWidget(); layout = QVBoxLayout(page)
        if not hasattr(self, 'settings_auto_update_cb'):
            self.settings_auto_update_cb = QCheckBox('Auto-update Virus Definitions'); self.settings_auto_update_cb.setChecked(True)
        layout.addWidget(self.settings_auto_update_cb)
        layout.addStretch(); return page

    def create_real_time_tab(self):
        """Create the real-time protection tab with improved three-column layout."""
        real_time_widget = QWidget()

        # Main horizontal layout with proper spacing
        main_layout = QHBoxLayout(real_time_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # LEFT PANEL: Activity Report (largest panel)
        left_panel = QVBoxLayout()
        activity_group = QGroupBox("Activity Report")
        activity_layout = QVBoxLayout(activity_group)
        activity_layout.setSpacing(10)  # Add spacing between elements
        activity_layout.setContentsMargins(
            10, 10, 10, 15
        )  # Add bottom margin for button

        self.activity_list = QListWidget()
        self.activity_list.setMinimumHeight(
            350
        )  # Reduce height to make room for button
        activity_layout.addWidget(self.activity_list)

        # Add Clear Logs button with proper spacing
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_activity_logs)
        clear_logs_btn.setMinimumHeight(35)
        clear_logs_btn.setMaximumWidth(120)
        clear_logs_btn.setObjectName("dangerButton")
        clear_logs_btn.setToolTip(
            "Clear all activity logs from both Protection tab and Dashboard"
        )

        # Center the button with proper spacing
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin
        button_layout.addStretch()
        button_layout.addWidget(clear_logs_btn)
        button_layout.addStretch()
        activity_layout.addLayout(button_layout)

        left_panel.addWidget(activity_group)
        left_panel.addStretch()

        # CENTER PANEL: Protection Status and Statistics (compact but
        # well-spaced)
        center_panel = QVBoxLayout()
        center_panel.setSpacing(20)

        # Protection Status section
        status_group = QGroupBox("Protection Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(15)

        # Protection status display with better styling
        self.protection_status_label = QLabel("🔄 Initializing...")
        self.protection_status_label.setObjectName("protectionStatus")
        self.protection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.protection_status_label.setMinimumHeight(40)
        self.protection_status_label.setStyleSheet(
            "font-size: 14px; padding: 10px; font-weight: bold;"
        )
        status_layout.addWidget(self.protection_status_label)

        # Control button - centered and prominent
        self.protection_toggle_btn = QPushButton("Start")
        self.protection_toggle_btn.clicked.connect(
            self.toggle_real_time_protection)
        self.protection_toggle_btn.setMinimumHeight(40)
        self.protection_toggle_btn.setMinimumWidth(120)
        self.protection_toggle_btn.setObjectName("primaryButton")

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.protection_toggle_btn)
        button_layout.addStretch()
        status_layout.addLayout(button_layout)

        center_panel.addWidget(status_group)

        # Protection Statistics section
        stats_group = QGroupBox("Protection Statistics")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(10)

        # Create a more organized stats display
        stats_container = QVBoxLayout()

        # Events row
        events_layout = QHBoxLayout()
        events_layout.addWidget(QLabel("Events Processed:"))
        self.events_processed_label = QLabel("0")
        self.events_processed_label.setStyleSheet(
            f"font-weight: bold; color: {self.get_theme_color('accent')};"
        )
        events_layout.addStretch()
        events_layout.addWidget(self.events_processed_label)
        stats_container.addLayout(events_layout)

        # Threats row
        threats_layout = QHBoxLayout()
        threats_layout.addWidget(QLabel("Threats Detected:"))
        self.threats_detected_label = QLabel("0")
        self.threats_detected_label.setStyleSheet(
            f"font-weight: bold; color: {self.get_theme_color('error')};"
        )
        threats_layout.addStretch()
        threats_layout.addWidget(self.threats_detected_label)
        stats_container.addLayout(threats_layout)

        # Scans row
        scans_layout = QHBoxLayout()
        scans_layout.addWidget(QLabel("Scans Performed:"))
        self.scans_performed_label = QLabel("0")
        self.scans_performed_label.setStyleSheet(
            f"font-weight: bold; color: {self.get_theme_color('success')};"
        )
        scans_layout.addStretch()
        scans_layout.addWidget(self.scans_performed_label)
        stats_container.addLayout(scans_layout)

        # Uptime row
        uptime_layout = QHBoxLayout()
        uptime_layout.addWidget(QLabel("Uptime:"))
        self.uptime_label = QLabel("00:00:00")
        self.uptime_label.setStyleSheet(
            f"font-weight: bold; color: {self.get_theme_color('warning')};"
        )
        uptime_layout.addStretch()
        uptime_layout.addWidget(self.uptime_label)
        stats_container.addLayout(uptime_layout)

        stats_layout.addLayout(stats_container)
        center_panel.addWidget(stats_group)

        # Firewall Status section
        firewall_group = QGroupBox("Firewall Status")
        firewall_layout = QVBoxLayout(firewall_group)
        firewall_layout.setSpacing(10)

        # Create the firewall status display similar to your mockup
        firewall_status_container = QHBoxLayout()

        # Status text on the left
        firewall_status_left = QVBoxLayout()
        firewall_status_left.setSpacing(5)

        self.firewall_status_label = QLabel("Status:")
        self.firewall_status_label.setStyleSheet(
            "font-weight: bold; font-size: 12px;")
        firewall_status_left.addWidget(self.firewall_status_label)

        self.firewall_name_label = QLabel("Checking...")
        self.firewall_name_label.setStyleSheet(f"font-size: 11px; color: {self.get_theme_color('secondary_text')};")
        firewall_status_left.addWidget(self.firewall_name_label)

        firewall_status_container.addLayout(firewall_status_left)
        firewall_status_container.addStretch()

        # Status indicator on the right (ON/OFF with circle)
        firewall_status_right = QVBoxLayout()
        firewall_status_right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.firewall_on_off_label = QLabel("OFF")
        self.firewall_on_off_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #F14666;"
        )
        self.firewall_on_off_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        firewall_status_right.addWidget(self.firewall_on_off_label)

        # Status circle
        self.firewall_status_circle = QLabel("●")
        self.firewall_status_circle.setStyleSheet(
            "font-size: 20px; color: #F14666;")
        self.firewall_status_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        firewall_status_right.addWidget(self.firewall_status_circle)

        firewall_status_container.addLayout(firewall_status_right)
        firewall_layout.addLayout(firewall_status_container)

        # Add firewall toggle button
        firewall_button_layout = QHBoxLayout()
        firewall_button_layout.setContentsMargins(
            0, 10, 0, 0)  # Add top margin

        self.firewall_toggle_btn = QPushButton("Enable Firewall")
        self.firewall_toggle_btn.clicked.connect(self.toggle_firewall_status)
        self.firewall_toggle_btn.setMinimumHeight(35)
        self.firewall_toggle_btn.setObjectName("primaryButton")
        self.firewall_toggle_btn.setToolTip(
            "Click to enable or disable the firewall")

        # Add alternative firewall button for older kernel compatibility
        self.alt_firewall_btn = QPushButton("Alt Mode")
        self.alt_firewall_btn.clicked.connect(self.toggle_alternative_firewall)
        self.alt_firewall_btn.setMinimumHeight(35)
        self.alt_firewall_btn.setObjectName("secondaryButton")
        self.alt_firewall_btn.setToolTip(
            "Alternative firewall mode for older kernels or when UFW fails")
        self.alt_firewall_btn.setMaximumWidth(80)

        firewall_button_layout.addStretch()
        firewall_button_layout.addWidget(self.firewall_toggle_btn)
        firewall_button_layout.addSpacing(10)
        firewall_button_layout.addWidget(self.alt_firewall_btn)
        firewall_button_layout.addStretch()
        firewall_layout.addLayout(firewall_button_layout)

        center_panel.addWidget(firewall_group)
        center_panel.addStretch()

        # RIGHT PANEL: Monitored Paths
        right_panel = QVBoxLayout()
        paths_group = QGroupBox("Monitored Paths")
        paths_layout = QVBoxLayout(paths_group)

        self.paths_list = QListWidget()
        self.paths_list.setMinimumHeight(300)  # Give it good height
        paths_layout.addWidget(self.paths_list)

        # Path control buttons
        paths_controls = QHBoxLayout()
        add_path_btn = QPushButton("Add Path")
        add_path_btn.clicked.connect(self.add_watch_path)
        add_path_btn.setMinimumHeight(35)

        remove_path_btn = QPushButton("Remove Path")
        remove_path_btn.clicked.connect(self.remove_watch_path)
        remove_path_btn.setMinimumHeight(35)
        remove_path_btn.setObjectName("dangerButton")

        paths_controls.addWidget(add_path_btn)
        paths_controls.addWidget(remove_path_btn)
        paths_layout.addLayout(paths_controls)

        right_panel.addWidget(paths_group)
        right_panel.addStretch()

        # Add panels to main layout with proper proportions
        main_layout.addLayout(left_panel, 2)  # 40% - Activity Report (largest)
        # 30% - Status & Stats (compact)
        main_layout.addLayout(center_panel, 1)
        main_layout.addLayout(right_panel, 1)  # 30% - Monitored Paths

        self.tab_widget.addTab(real_time_widget, "Protection")

        # Initialize firewall status display
        QTimer.singleShot(
            1000, self.update_firewall_status
        )  # Delay initial update slightly

        # Firewall monitoring is now handled by unified timer system
        # (Reduces timer overhead by consolidating updates)

    def init_real_time_monitoring_safe(self):
        """Safely initialize the real-time monitoring system with better error handling."""
        print("🔧 Initializing real-time monitoring system...")
        try:
            # Create monitor configuration with safer defaults
            watch_paths = self.config.get(
                "watch_paths", [str(Path.home())]
            )  # Just monitor home directory initially
            excluded_paths = self.config.get(
                "excluded_paths", ["/proc", "/sys", "/dev", "/tmp"]
            )

            # Ensure paths are properly formatted and validated
            if isinstance(watch_paths, list):
                watch_paths = [
                    str(path)
                    for path in watch_paths
                    if path and os.path.exists(str(path))
                ]
            else:
                watch_paths = (
                    [str(watch_paths)]
                    if watch_paths and os.path.exists(str(watch_paths))
                    else []
                )

            # Fallback to home directory if no valid paths
            if not watch_paths:
                home_path = str(Path.home())
                if os.path.exists(home_path):
                    watch_paths = [home_path]
                else:
                    print("❌ No valid watch paths found, monitoring disabled")
                    return False

            if isinstance(excluded_paths, list):
                excluded_paths = [str(path) for path in excluded_paths]
            else:
                excluded_paths = [str(excluded_paths)]

            print(f"📁 Valid watch paths: {watch_paths}")
            print(f"🚫 Excluded paths: {excluded_paths}")

            monitor_config = MonitorConfig(
                watch_paths=watch_paths,
                excluded_paths=excluded_paths,
                scan_new_files=True,
                scan_modified_files=False,  # Start with less aggressive monitoring
                quarantine_threats=False,  # Don't auto-quarantine initially for testing
            )

            # Create real-time monitor
            self.real_time_monitor = RealTimeMonitor(monitor_config)
            print("✅ RealTimeMonitor created successfully")

            # Set up callbacks only if the methods exist
            if hasattr(self.real_time_monitor, "set_threat_detected_callback"):
                self.real_time_monitor.set_threat_detected_callback(
                    self.on_threat_detected
                )
                print("✅ Threat detection callback set")

            if hasattr(self.real_time_monitor, "set_scan_completed_callback"):
                self.real_time_monitor.set_scan_completed_callback(
                    self.on_scan_completed
                )
                print("✅ Scan completion callback set")

            if hasattr(self.real_time_monitor, "set_error_callback"):
                self.real_time_monitor.set_error_callback(
                    self.on_monitoring_error)
                print("✅ Error callback set")

            # Statistics updates now handled by unified timer system
            # (Reduces timer overhead and improves performance)
            print("✅ Statistics updates integrated with unified timer system")

            # Set initial status based on saved configuration
            if hasattr(self, "protection_status_label"):
                if self.monitoring_enabled:
                    # If protection was enabled before, restore it
                    print("🔄 Restoring real-time protection from saved state...")
                    if self.real_time_monitor and self.real_time_monitor.start():
                        self.protection_status_label.setText("🛡️ Active")
                        color = self.get_status_color("success")
                        self.protection_status_label.setStyleSheet(
                            f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                        if hasattr(self, "protection_toggle_btn"):
                            self.protection_toggle_btn.setText("Stop")
                        print("✅ Real-time protection restored successfully!")
                        self.add_activity_message(
                            "✅ Real-time protection restored from previous session"
                        )
                    else:
                        # Failed to start, reset to inactive
                        print("❌ Failed to restore real-time protection")
                        self.monitoring_enabled = False
                        self.protection_status_label.setText(
                            "❌ Failed to restore")
                        color = self.get_status_color("error")
                        self.protection_status_label.setStyleSheet(
                            f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                        if hasattr(self, "protection_toggle_btn"):
                            self.protection_toggle_btn.setText("Start")
                        self.add_activity_message(
                            "❌ Failed to restore real-time protection from previous session"
                        )
                        # Update config to reflect failure
                        if "security_settings" not in self.config:
                            self.config["security_settings"] = {}
                        self.config["security_settings"]["real_time_protection"] = False
                        save_config(self.config)
                else:
                    # Protection is disabled, set inactive status
                    self.protection_status_label.setText("🔴 Inactive")
                    color = self.get_status_color("error")
                    self.protection_status_label.setStyleSheet(
                        f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                    if hasattr(self, "protection_toggle_btn"):
                        self.protection_toggle_btn.setText("Start")

            print("✅ Real-time monitoring initialized successfully!")
            return True

        except (ImportError, AttributeError, OSError) as e:
            print(f"❌ Failed to initialize monitoring: {e}")
            # Create a dummy monitor for UI purposes
            self.real_time_monitor = None
            self.add_activity_message(
                f"⚠️ Monitoring system offline: {str(e)}")

            # Ensure status is never left as "Initializing..." - set to
            # inactive
            if hasattr(self, "protection_status_label"):
                self.protection_status_label.setText("🔴 Inactive")
                color = self.get_status_color("error")
                self.protection_status_label.setStyleSheet(
                    f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                if hasattr(self, "protection_toggle_btn"):
                    self.protection_toggle_btn.setText("Start")
                print("✅ Status reset to Inactive after initialization failure")

            return False

    def init_real_time_monitoring(self):
        """Initialize the real-time monitoring system."""
        try:
            # Create monitor configuration
            watch_paths = self.config.get(
                "watch_paths", ["/home", "/opt", "/tmp"])
            excluded_paths = self.config.get(
                "excluded_paths", ["/proc", "/sys", "/dev"]
            )

            monitor_config = MonitorConfig(
                watch_paths=watch_paths,
                excluded_paths=excluded_paths,
                scan_new_files=True,
                scan_modified_files=True,
                quarantine_threats=True,
            )

            # Create real-time monitor
            self.real_time_monitor = RealTimeMonitor(monitor_config)

            # Set up callbacks
            self.real_time_monitor.set_threat_detected_callback(
                self.on_threat_detected)
            self.real_time_monitor.set_scan_completed_callback(
                self.on_scan_completed)
            self.real_time_monitor.set_error_callback(self.on_monitoring_error)

            # Set up timer to update statistics
            self.stats_timer = QTimer()
            self.stats_timer.timeout.connect(self.update_monitoring_statistics)
            self.stats_timer.start(5000)  # Update every 5 seconds

            # Auto-start if enabled (temporarily disabled)
            # if self.monitoring_enabled:
            #     QTimer.singleShot(2000, self.start_real_time_protection)
            # else:
            # Set initial status to Inactive when monitoring is disabled by
            # default
            if hasattr(self, "protection_status_label"):
                self.protection_status_label.setText("🔴 Inactive")
                self.protection_status_label.setStyleSheet(
                    f"color: {
                        self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")

        except (ImportError, AttributeError, RuntimeError) as e:
            self.add_activity_message(
                f"❌ Failed to initialize monitoring: {e}")

    def toggle_real_time_protection(self):
        """Toggle real-time protection on/off."""
        # Check current state by looking at the button text
        if "Start" in self.protection_toggle_btn.text():
            self.start_real_time_protection()
        else:
            self.stop_real_time_protection()

    def start_real_time_protection(self):
        """Start real-time protection."""
        try:
            # If monitor wasn't initialized, try to initialize it now
            if self.real_time_monitor is None:
                print("🔄 Monitor not initialized, attempting to initialize...")
                success = self.init_real_time_monitoring_safe()
                if not success:
                    self.add_activity_message(
                        "❌ Cannot start protection: Monitoring system unavailable"
                    )
                    return

            if self.real_time_monitor and self.real_time_monitor.start():
                self.protection_status_label.setText("🛡️ Active")
                self.protection_status_label.setStyleSheet(
                    f"color: {
                        self.get_theme_color('success')}; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("Stop")
                self.add_activity_message("✅ Real-time protection started")
                self.status_bar.showMessage("Real-time protection active")

                # Save user preference
                self.monitoring_enabled = True
                if "security_settings" not in self.config:
                    self.config["security_settings"] = {}
                self.config["security_settings"]["real_time_protection"] = True
                save_config(self.config)

                # Update dashboard card to reflect the change
                self.update_protection_status_card()

                # Update paths list
                self.update_paths_list()

                # Start or restart the statistics timer
                if hasattr(self, "stats_timer"):
                    self.stats_timer.start(5000)  # Update every 5 seconds
                else:
                    self.stats_timer = QTimer()
                    self.stats_timer.timeout.connect(
                        self.update_monitoring_statistics)
                    self.stats_timer.start(5000)

                # Update statistics immediately to show current state
                self.update_monitoring_statistics()
            else:
                self.protection_status_label.setText("❌ Failed")
                self.protection_status_label.setStyleSheet(
                    f"color: {
                        self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")
                # Keep button as "Start" since protection failed to start
                self.protection_toggle_btn.setText("Start")
                self.add_activity_message(
                    "❌ Failed to start real-time protection")

                # Make sure dashboard shows failure state
                self.monitoring_enabled = False
                self.update_protection_status_card()

        except (AttributeError, RuntimeError, OSError) as e:
            self.add_activity_message(f"❌ Error starting protection: {e}")
            # Ensure button stays as "Start" if there was an error
            self.protection_toggle_btn.setText("Start")
            # Make sure dashboard shows error state
            self.monitoring_enabled = False
            self.update_protection_status_card()

    def stop_real_time_protection(self):
        """Stop real-time protection."""
        try:
            if self.real_time_monitor:
                self.real_time_monitor.stop()
                self.protection_status_label.setText("🔴 Inactive")
                self.protection_status_label.setStyleSheet(
                    f"color: {
                        self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("Start")
                self.add_activity_message("🛑 Real-time protection stopped")
                self.status_bar.showMessage("🛑 Real-time protection stopped")

                # Save user preference
                self.monitoring_enabled = False
                if "security_settings" not in self.config:
                    self.config["security_settings"] = {}
                self.config["security_settings"]["real_time_protection"] = False
                save_config(self.config)

                # Update dashboard card to reflect the change
                self.update_protection_status_card()

                # Stop the statistics timer when protection is stopped
                if hasattr(self, "stats_timer"):
                    self.stats_timer.stop()

                # Reset statistics display to show monitoring is stopped
                if hasattr(self, "events_processed_label"):
                    self.events_processed_label.setText("0")
                if hasattr(self, "threats_detected_label"):
                    self.threats_detected_label.setText("0")
                if hasattr(self, "scans_performed_label"):
                    self.scans_performed_label.setText("0")
                if hasattr(self, "uptime_label"):
                    self.uptime_label.setText("00:00:00")

        except (AttributeError, RuntimeError) as e:
            self.add_activity_message(f"❌ Error stopping protection: {e}")
            # If stopping failed, we can't be sure of the state, so show error
            # and allow retry
            self.protection_status_label.setText("❌ Error")
            self.protection_status_label.setStyleSheet(
                f"color: {
                    self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")

    def on_threat_detected(self, file_path: str, threat_name: str):
        """Handle threat detection callback."""
        message = f"🚨 THREAT DETECTED: {threat_name} in {file_path}"
        self.add_activity_message(message)

        # Show system notification
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.showMessage(
                "Threat Detected!",
                f"Found {threat_name} in {file_path}",
                QSystemTrayIcon.MessageIcon.Critical,
                5000,
            )

        # Update status bar
        self.status_bar.showMessage(f"Threat detected: {threat_name}", 10000)

    def on_scan_completed(self, file_path: str, result: str):
        """Handle scan completion callback."""
        if result != "clean":
            message = f"🔍 Scan completed: {file_path} - {result}"
            self.add_activity_message(message)

    def on_monitoring_error(self, error_message: str):
        """Handle monitoring error callback."""
        self.add_activity_message(f"⚠️ Monitoring error: {error_message}")

    def add_activity_message(self, message: str):
        """Add a message to the activity list."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"

        # Get current retention setting
        retention = self.get_activity_retention_setting()

        # Add to main activity list if it exists
        if hasattr(self, "activity_list"):
            # Add to top of list
            item = QListWidgetItem(full_message)
            self.activity_list.insertItem(0, item)

            # Keep only last N items based on retention setting
            while self.activity_list.count() > retention:
                self.activity_list.takeItem(self.activity_list.count() - 1)

        # Also add to dashboard activity list if it exists
        if hasattr(self, "dashboard_activity"):
            # Add to top of dashboard list
            item = QListWidgetItem(full_message)
            self.dashboard_activity.insertItem(0, item)

            # Keep only last 20 items on dashboard for brevity
            while self.dashboard_activity.count() > 20:
                self.dashboard_activity.takeItem(
                    self.dashboard_activity.count() - 1)

        # Save activity logs immediately when a new entry is added
        self.save_activity_logs()

    def save_activity_logs(self):
        """Save current activity logs to persistent storage immediately."""
        try:
            from utils.config import DATA_DIR

            activity_log_file = DATA_DIR / "activity_logs.json"

            # Get current retention setting
            retention = self.get_activity_retention_setting()

            # Collect activity messages from the primary activity list
            activity_messages = []

            # Primary activity list (Protection tab) has the full history
            if hasattr(
                    self,
                    "activity_list") and self.activity_list.count() > 0:
                for i in range(min(self.activity_list.count(), retention)):
                    item = self.activity_list.item(i)
                    if item:
                        activity_messages.append(item.text())

            # Only save if we have messages
            if activity_messages:
                # Save to file
                with open(activity_log_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "retention_setting": retention,
                            "messages": activity_messages,
                        },
                        f,
                        indent=2,
                    )
                print(f"Saved {len(activity_messages)} activity log entries")
            else:
                # If no messages, remove the file to start fresh
                if activity_log_file.exists():
                    activity_log_file.unlink()

        except Exception as e:
            print(f"Failed to save activity logs: {e}")

    def load_activity_logs(self):
        """Load persisted activity logs on startup."""
        try:
            from utils.config import DATA_DIR

            activity_log_file = DATA_DIR / "activity_logs.json"

            if not activity_log_file.exists():
                return

            with open(activity_log_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            messages = data.get("messages", [])
            if not messages:
                return

            # Get current retention setting from config (not UI which may not
            # be ready yet)
            retention = self.config.get("ui_settings", {}).get(
                "activity_log_retention", 100
            )

            # Limit messages to current retention setting
            messages = messages[:retention]

            # Clear existing lists first
            if hasattr(self, "activity_list"):
                self.activity_list.clear()
            if hasattr(self, "dashboard_activity"):
                self.dashboard_activity.clear()

            # Add messages in correct chronological order (newest first, as
            # they were saved)
            for message in messages:
                if hasattr(self, "activity_list"):
                    item = QListWidgetItem(message)
                    self.activity_list.addItem(item)

                # Add to dashboard activity (limited to 20 items)
                if (
                    hasattr(self, "dashboard_activity")
                    and self.dashboard_activity.count() < 20
                ):
                    item = QListWidgetItem(message)
                    self.dashboard_activity.addItem(item)

            print(f"Loaded {len(messages)} activity log entries")

        except Exception as e:
            print(f"Failed to load activity logs: {e}")

    def get_activity_retention_setting(self):
        """Get the current activity retention setting."""
        if hasattr(self, "settings_activity_retention_combo"):
            return int(self.settings_activity_retention_combo.currentText())
        return self.config.get(
            "ui_settings", {}).get(
            "activity_log_retention", 100)

    def clear_activity_logs(self):
        """Clear all activity logs from both Protection tab and Dashboard."""
        try:
            # Show confirmation dialog
            reply = self.show_themed_message_box(
                "question",
                "Clear Activity Logs",
                "Are you sure you want to clear all activity logs?\n\n"
                "This will remove all activity entries from both the Protection tab and Dashboard.\n"
                "This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Clear both activity lists
                if hasattr(self, "activity_list"):
                    self.activity_list.clear()

                if hasattr(self, "dashboard_activity"):
                    self.dashboard_activity.clear()

                # Remove the saved activity log file
                try:
                    from utils.config import DATA_DIR

                    activity_log_file = DATA_DIR / "activity_logs.json"
                    if activity_log_file.exists():
                        activity_log_file.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove activity log file: {e}")

                # Add a confirmation message to the logs
                self.add_activity_message("🗑️ Activity logs cleared by user")

                # Show success message
                self.show_themed_message_box(
                    "information",
                    "Logs Cleared",
                    "All activity logs have been cleared successfully.",
                )

        except Exception as e:
            print(f"Error clearing activity logs: {e}")
            self.show_themed_message_box(
                "warning", "Error", f"Failed to clear activity logs: {str(e)}"
            )

    def on_retention_setting_changed(self, new_value):
        """Handle changes to the activity log retention setting."""
        try:
            print(f"🔄 Activity Log Retention changed to: {new_value}")
            new_retention = int(new_value)

            # Trim current activity lists to new size
            if hasattr(self, "activity_list"):
                while self.activity_list.count() > new_retention:
                    self.activity_list.takeItem(self.activity_list.count() - 1)

            # Use unified auto-save method
            print(f"💾 Auto-saving retention setting: {new_retention}")
            self.auto_save_settings()
            print(f"✅ Retention setting saved")

        except ValueError:
            print(f"❌ Invalid retention value: {new_value}")

    def on_scheduled_scan_toggled(self, enabled):
        """Handle scheduled scan enable/disable toggle."""
        try:
            print(f"🔄 Scheduled Scans toggled to: {enabled}")
            
            # Enable/disable related controls
            self.settings_scan_frequency_combo.setEnabled(enabled)
            self.settings_scan_time_edit.setEnabled(enabled)
            self.settings_scan_type_combo.setEnabled(enabled)
            
            # Enable custom directory controls only if custom scan is selected
            if hasattr(self, 'settings_custom_dir_edit'):
                is_custom = self.settings_scan_type_combo.currentData() == "custom"
                self.settings_custom_dir_edit.setEnabled(enabled and is_custom)
                self.settings_custom_dir_btn.setEnabled(enabled and is_custom)
            
            if enabled:
                # Calculate and display next scheduled scan
                self.update_next_scheduled_scan_display()
                # Only start scheduler if initialization is complete
                if self._initialization_complete:
                    try:
                        if hasattr(self.scanner, 'start_scheduler'):
                            self.scanner.start_scheduler()
                        else:
                            print("⚠️ Scanner doesn't have scheduler capability yet - will retry when scanner is ready")
                    except Exception as e:
                        print(f"⚠️ Error starting scheduler: {e}")
                        print("⚠️ Scheduler will be started when scanner is fully initialized")
                        # Do NOT disable the checkbox here - let the setting persist
                        # The scheduler will be started later when the scanner is ready
                else:
                    print("⏳ Scheduled scans enabled but waiting for initialization to complete")
            else:
                self.settings_next_scan_label.setText("None scheduled")
                # Stop scheduler
                try:
                    if hasattr(self.scanner, 'stop_scheduler'):
                        self.scanner.stop_scheduler()
                except Exception as e:
                    print(f"Error stopping scheduler: {e}")
            
            # Auto-save the scheduled scan settings
            print(f"💾 Auto-saving scheduled scan setting: {enabled}")
            self.auto_save_settings()
            print(f"✅ Scheduled scan setting saved")
            
        except Exception as e:
            print(f"❌ Error in scheduled scan toggle: {e}")
            import traceback
            traceback.print_exc()
            # Do NOT reset the checkbox state automatically
            # Let the user know about the error but preserve their setting choice
    
    def on_scheduled_scan_type_changed(self, scan_type):
        """Handle scheduled scan type change."""
        try:
            print(f"🔄 Scheduled scan type changed to: {scan_type}")
            
            # Show/hide custom directory widget based on selection
            is_custom = scan_type == "Custom Directory"
            self.settings_custom_dir_widget.setVisible(is_custom)
            
            # Enable/disable custom directory controls
            if hasattr(self, 'settings_custom_dir_edit'):
                self.settings_custom_dir_edit.setEnabled(is_custom and self.settings_enable_scheduled_cb.isChecked())
                self.settings_custom_dir_btn.setEnabled(is_custom and self.settings_enable_scheduled_cb.isChecked())
            
            # Update next scheduled scan display to reflect new type
            self.update_next_scheduled_scan_display()
            
            # Auto-save settings
            self.auto_save_settings()
            print(f"✅ Scheduled scan type setting saved: {scan_type}")
            
        except Exception as e:
            print(f"❌ Error in scheduled scan type change: {e}")
            import traceback
            traceback.print_exc()
    
    def select_scheduled_custom_directory(self):
        """Open directory selector for scheduled custom scans."""
        try:
            current_path = self.settings_custom_dir_edit.text()
            if not current_path:
                current_path = str(Path.home())
            
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Directory for Scheduled Scans",
                current_path,
                QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )
            
            if directory:
                self.settings_custom_dir_edit.setText(directory)
                print(f"📁 Selected scheduled custom directory: {directory}")
                
                # Update next scheduled scan display
                self.update_next_scheduled_scan_display()
                
                # Auto-save settings
                self.auto_save_settings()
                print(f"✅ Custom directory setting saved: {directory}")
                
        except Exception as e:
            print(f"❌ Error selecting scheduled custom directory: {e}")
            import traceback
            traceback.print_exc()
    
    def update_next_scheduled_scan_display(self):
        """Update the display of next scheduled scan time."""
        try:
            if not self.settings_enable_scheduled_cb.isChecked():
                self.settings_next_scan_label.setText("None scheduled")
                return
                
            frequency = self.settings_scan_frequency_combo.currentData()
            scan_time = self.settings_scan_time_edit.time()
            scan_type = self.settings_scan_type_combo.currentText()
            scan_type_data = self.settings_scan_type_combo.currentData()
            
            # Validate inputs
            if not frequency or not scan_time.isValid():
                self.settings_next_scan_label.setText("Invalid configuration")
                return
            
            # For custom scans, check if directory is selected
            if scan_type_data == "custom":
                custom_dir = self.settings_custom_dir_edit.text()
                if not custom_dir:
                    self.settings_next_scan_label.setText("Select custom directory")
                    return
            
            # Calculate next scan time based on frequency
            from datetime import datetime, timedelta
            now = datetime.now()
            next_scan = None
            
            if frequency == "daily":
                next_scan = now.replace(hour=scan_time.hour(), minute=scan_time.minute(), second=0, microsecond=0)
                if next_scan <= now:
                    next_scan += timedelta(days=1)
            elif frequency == "weekly":
                # Schedule for next Sunday
                days_until_sunday = (6 - now.weekday()) % 7
                if days_until_sunday == 0:  # It's Sunday
                    next_scan = now.replace(hour=scan_time.hour(), minute=scan_time.minute(), second=0, microsecond=0)
                    if next_scan <= now:
                        days_until_sunday = 7
                    else:
                        next_scan = now + timedelta(days=days_until_sunday)
                else:
                    next_scan = now + timedelta(days=days_until_sunday)
                next_scan = next_scan.replace(hour=scan_time.hour(), minute=scan_time.minute(), second=0, microsecond=0)
            elif frequency == "monthly":
                # Schedule for first of next month
                if now.month == 12:
                    next_scan = now.replace(year=now.year + 1, month=1, day=1, hour=scan_time.hour(), minute=scan_time.minute(), second=0, microsecond=0)
                else:
                    next_scan = now.replace(month=now.month + 1, day=1, hour=scan_time.hour(), minute=scan_time.minute(), second=0, microsecond=0)
            
            if next_scan:
                display_text = f"{next_scan.strftime('%Y-%m-%d %H:%M')} ({scan_type})"
                self.settings_next_scan_label.setText(display_text)
            else:
                self.settings_next_scan_label.setText("Unable to calculate")
                
        except Exception as e:
            print(f"Error updating scheduled scan display: {e}")
            self.settings_next_scan_label.setText("Error calculating next scan")

    def update_monitoring_statistics(self):
        """Update the monitoring statistics display."""
        # Update firewall status less frequently (every 6th call = 30-60
        # seconds)
        if not hasattr(self, "_firewall_update_counter"):
            self._firewall_update_counter = 0
        self._firewall_update_counter += 1
        if self._firewall_update_counter >= 6:
            self._firewall_update_counter = 0
            self.update_firewall_status()

        if self.real_time_monitor:
            try:
                stats = self.real_time_monitor.get_statistics()
                monitor_stats = stats.get("monitor", {})

                # Update each statistic with null checking
                if hasattr(self, "events_processed_label"):
                    events = monitor_stats.get("events_processed", 0)
                    self.events_processed_label.setText(str(events))

                if hasattr(self, "threats_detected_label"):
                    threats = monitor_stats.get("threats_detected", 0)
                    self.threats_detected_label.setText(str(threats))

                if hasattr(self, "scans_performed_label"):
                    scans = monitor_stats.get("scans_performed", 0)
                    self.scans_performed_label.setText(str(scans))

                if hasattr(self, "uptime_label"):
                    uptime = monitor_stats.get("uptime_seconds", 0)
                    if uptime > 0:
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        seconds = int(uptime % 60)
                        self.uptime_label.setText(
                            f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        )
                    else:
                        self.uptime_label.setText("00:00:00")

                # Also update the dashboard cards with current statistics
                if hasattr(self, "threats_card"):
                    threats = monitor_stats.get("threats_detected", 0)
                    for child in self.threats_card.findChildren(QLabel):
                        if child.objectName() == "cardValue":
                            child.setText(str(threats))
                            break

            except (AttributeError, ValueError, KeyError) as e:
                # Log the error for debugging but don't crash the UI
                print(f"⚠️ Error updating monitoring statistics: {e}")
        else:
            # If monitor is not available, ensure all statistics show 0
            if hasattr(self, "events_processed_label"):
                self.events_processed_label.setText("0")
            if hasattr(self, "threats_detected_label"):
                self.threats_detected_label.setText("0")
            if hasattr(self, "scans_performed_label"):
                self.scans_performed_label.setText("0")
            if hasattr(self, "uptime_label"):
                self.uptime_label.setText("00:00:00")

    def update_paths_list(self):
        """Update the monitored paths list."""
        if hasattr(self, "paths_list") and self.real_time_monitor:
            self.paths_list.clear()
            config = self.real_time_monitor.config
            for path in config.watch_paths:
                self.paths_list.addItem(f"📁 {path}")

    def add_watch_path(self):
        """Add a new path to monitor."""
        path = self.show_themed_file_dialog(
            "directory", "Select Directory to Monitor")
        if path and self.real_time_monitor:
            if self.real_time_monitor.add_watch_path(path):
                self.update_paths_list()
                self.add_activity_message(f"📁 Added watch path: {path}")
            else:
                self.show_themed_message_box(
                    "warning", "Error", f"Failed to add watch path: {path}"
                )

    def remove_watch_path(self):
        """Remove a path from monitoring."""
        current_item = self.paths_list.currentItem()
        if current_item and self.real_time_monitor:
            path = current_item.text().replace("📁 ", "")
            if self.real_time_monitor.remove_watch_path(path):
                self.update_paths_list()
                self.add_activity_message(f"📁 Removed watch path: {path}")
            else:
                self.show_themed_message_box(
                    "warning", "Error", f"Failed to remove watch path: {path}"
                )

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)

    def create_menu_bar(self):
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # File menu
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        exit_action.setToolTip("Exit application (may minimize to tray if enabled)")
        file_menu.addAction(exit_action)
        
        force_exit_action = QAction("Force Exit", self)
        force_exit_action.triggered.connect(self.force_quit_application)
        force_exit_action.setShortcut("Ctrl+Shift+Q")
        force_exit_action.setToolTip("Force exit application ignoring minimize to tray setting")
        file_menu.addAction(force_exit_action)

        # View menu for theme selection
        view_menu = QMenu("View", self)
        menu_bar.addMenu(view_menu)

        # Theme submenu
        theme_menu = QMenu("Theme", self)
        view_menu.addMenu(theme_menu)

        # Theme actions
        self.dark_theme_action = QAction("Dark Mode", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(
            lambda: self.set_theme("dark"))
        theme_menu.addAction(self.dark_theme_action)

        self.light_theme_action = QAction("Light Mode", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(
            lambda: self.set_theme("light"))
        theme_menu.addAction(self.light_theme_action)

        self.system_theme_action = QAction("System Default", self)
        self.system_theme_action.setCheckable(True)
        self.system_theme_action.triggered.connect(
            lambda: self.set_theme("system"))
        theme_menu.addAction(self.system_theme_action)

        # Set initial theme state
        self.update_theme_menu()

        # Help menu
        help_menu = QMenu("Help", self)
        menu_bar.addMenu(help_menu)

        # Check for Updates menu item
        update_action = QAction("Check for Updates", self)
        update_action.triggered.connect(self.check_for_updates_manual)
        update_action.setStatusTip("Check for application updates")
        help_menu.addAction(update_action)
        
        # Separator
        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_system_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)

        # Create a system tray icon
        app_icon = QIcon()
        icon_path = (
            Path(__file__).parent.parent.parent
            / "packaging"
            / "icons"
            / "org.xanados.SearchAndDestroy.svg"
        )
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
        else:
            # Create a default icon if the SVG is not found
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.blue)
            app_icon = QIcon(pixmap)

        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("S&D - Search & Destroy")

        # Initialize performance tooltip update
        self.update_system_tray_tooltip()

        # Create system tray menu
        tray_menu = QMenu(self)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show)
        tray_menu.addAction(open_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        force_quit_action = QAction("Force Quit", self)
        force_quit_action.triggered.connect(self.force_quit_application)
        tray_menu.addAction(force_quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def update_system_tray_tooltip(self):
        """Update system tray tooltip with concise security information."""
        try:
            if not hasattr(self, "tray_icon") or not self.tray_icon:
                return

            # Get performance data for system status
            perf_status, perf_color, perf_details = self.get_performance_card_data()

            # Get app status with visual indicators and descriptive text
            firewall_icon = "○"
            protection_icon = "○"
            firewall_status = "Inactive"
            protection_status = "Disabled"

            try:
                from core.firewall_detector import get_firewall_status

                firewall_status_dict = get_firewall_status()
                firewall_active = firewall_status_dict.get("is_active", False)
                firewall_icon = "●" if firewall_active else "○"
                firewall_status = "Active" if firewall_active else "Inactive"
            except Exception as e:
                # More detailed error handling
                print(f"Error checking firewall status: {e}")
                firewall_icon = "○"
                firewall_status = "Unknown"

            try:
                protection_icon = "●" if self.monitoring_enabled else "○"
                protection_status = "Enabled" if self.monitoring_enabled else "Disabled"
            except Exception as e:
                print(f"Error checking protection status: {e}")
                protection_icon = "○"
                protection_status = "Unknown"

            # Create single, compact tooltip with minimal width
            tooltip_text = f"""S&D Security Status
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
Protection    {protection_icon} {protection_status}
Firewall      {firewall_icon} {firewall_status}
System        {perf_status}"""

            self.tray_icon.setToolTip(tooltip_text)

        except Exception as e:
            # Fallback to simple tooltip
            self.tray_icon.setToolTip("S&D - Search & Destroy")
            print(f"Error updating tray tooltip: {e}")



    def setup_accessibility(self):
        """Set up accessibility features including keyboard shortcuts and ARIA-like labels."""
        # Keyboard shortcuts
        self.quick_scan_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quick_scan_shortcut.activated.connect(self.quick_scan)

        self.update_definitions_shortcut = QShortcut(
            QKeySequence("Ctrl+U"), self)
        self.update_definitions_shortcut.activated.connect(
            self.update_definitions)

        # Tab navigation shortcuts
        self.dashboard_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        self.dashboard_shortcut.activated.connect(
            lambda: self.tab_widget.setCurrentIndex(0)
        )

        self.scan_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        self.scan_shortcut.activated.connect(
            lambda: self.tab_widget.setCurrentIndex(1))

        self.protection_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        self.protection_shortcut.activated.connect(
            lambda: self.tab_widget.setCurrentIndex(2)
        )

        # Help shortcut
        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.show_about)

        # Refresh shortcut
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self.refresh_reports)

        # Set accessible names and descriptions for better screen reader
        # support
        self.tab_widget.setAccessibleName("Main application tabs")
        self.tab_widget.setAccessibleDescription(
            "Navigate between different application functions"
        )

        # Set status bar accessibility
        if hasattr(self, "status_bar"):
            self.status_bar.setAccessibleName("Application status")

    def set_theme(self, theme):
        """Set the application theme and save to config."""
        # Update theme manager
        get_theme_manager().set_theme(theme)
        
        # Save to config
        if "ui_settings" not in self.config:
            self.config["ui_settings"] = {}
        self.config["ui_settings"]["theme"] = theme
        save_config(self.config)
        
        # Update theme menu
        self.update_theme_menu()
        
        # Update any custom components
        self.update_icon_for_theme()
        self.update_rkhunter_category_styling()
        self.update_dynamic_component_styling()

    def update_theme_menu(self):
        """Update the theme menu to reflect the current selection."""
        current_theme = get_theme_manager().get_current_theme()
        self.dark_theme_action.setChecked(current_theme == "dark")
        self.light_theme_action.setChecked(current_theme == "light")
        self.system_theme_action.setChecked(current_theme == "system")

    def update_icon_for_theme(self):
        """Update the application icon based on the current theme."""
        current_theme = get_theme_manager().get_current_theme()
        icon_path = (
            Path(__file__).parent.parent.parent
            / "packaging"
            / "icons"
            / "org.xanados.SearchAndDestroy-128.png"
        )
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))

            # Convert to black and white in dark mode
            if current_theme == "dark":
                pixmap = self.convert_to_black_and_white(pixmap)

            scaled_pixmap = pixmap.scaled(
                128,
                128,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            # Fallback to colored circle if icon not found
            fallback_color = "#404040" if current_theme == "dark" else "#2196F3"
            self.icon_label.setStyleSheet(
                f"background-color: {fallback_color}; border-radius: 64px;"
            )

    def convert_to_black_and_white(self, pixmap):
        """Convert a colored pixmap to black and white by desaturating colors."""
        # Convert pixmap to image for processing
        image = pixmap.toImage()

        # Create a simple desaturated version using a more efficient approach
        # Convert to Format_ARGB32 for easier pixel manipulation
        if image.format() != image.Format.Format_ARGB32:
            image = image.convertToFormat(image.Format.Format_ARGB32)

        width = image.width()
        height = image.height()

        # Process pixels in chunks for better performance
        for y in range(height):
            for x in range(width):
                pixel = image.pixel(x, y)

                # Extract ARGB components
                alpha = (pixel >> 24) & 0xFF
                red = (pixel >> 16) & 0xFF
                green = (pixel >> 8) & 0xFF
                blue = pixel & 0xFF

                # Calculate luminance using standard formula
                luminance = int(0.299 * red + 0.587 * green + 0.114 * blue)

                # Create grayscale pixel maintaining alpha
                gray_pixel = (
                    (alpha << 24) | (
                        luminance << 16) | (
                        luminance << 8) | luminance)
                image.setPixel(x, y, gray_pixel)

        return QPixmap.fromImage(image)

    def show_themed_file_dialog(
            self,
            dialog_type="directory",
            title="Select",
            default_path="",
            file_filter=""):
        """Show a file dialog with proper theming."""
        bg = self.get_theme_color("background")
        text = self.get_theme_color("primary_text")
        tertiary_bg = self.get_theme_color("tertiary_bg")
        border = self.get_theme_color("border")
        hover_bg = self.get_theme_color("hover_bg")
        accent = self.get_theme_color("accent")

        # Create file dialog
        if dialog_type == "directory":
            dialog = QFileDialog(self, title, default_path)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        elif dialog_type == "save":
            dialog = QFileDialog(self, title, default_path, file_filter)
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        else:  # open file
            dialog = QFileDialog(self, title, default_path, file_filter)
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        # Apply theming
        style = f"""
            QFileDialog {{
                background-color: {bg};
                color: {text};
                border: 2px solid {border};
                border-radius: 6px;
            }}
            QFileDialog QListView {{
                background-color: {tertiary_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                selection-background-color: {accent};
                selection-color: {bg};
            }}
            QFileDialog QTreeView {{
                background-color: {tertiary_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                selection-background-color: {accent};
                selection-color: {bg};
            }}
            QFileDialog QPushButton {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 5px;
                padding: 8px 16px;
                color: {text};
                font-weight: 600;
                min-width: 80px;
            }}
            QFileDialog QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
            }}
            QFileDialog QLabel {{
                color: {text};
            }}
            QFileDialog QLineEdit {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 4px;
                padding: 6px;
                color: {text};
            }}
            QFileDialog QComboBox {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 4px;
                padding: 6px;
                color: {text};
            }}
        """
        dialog.setStyleSheet(style)

        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected = dialog.selectedFiles()
            if selected:
                return selected[0]
        return ""

    def show_themed_progress_dialog(
        self, title, label_text, minimum=0, maximum=100, parent=None
    ):
        """Create a progress dialog with proper theming."""
        if parent is None:
            parent = self

        progress = QProgressDialog(
            label_text, "Cancel", minimum, maximum, parent)
        progress.setWindowTitle(title)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        # Apply theming
        bg = self.get_theme_color("background")
        text = self.get_theme_color("primary_text")
        tertiary_bg = self.get_theme_color("tertiary_bg")
        border = self.get_theme_color("border")
        hover_bg = self.get_theme_color("hover_bg")
        accent = self.get_theme_color("accent")

        style = f"""
            QProgressDialog {{
                background-color: {bg};
                color: {text};
                border: 2px solid {border};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }}
            QProgressDialog QLabel {{
                color: {text};
                font-weight: 600;
                padding: 10px;
            }}
            QProgressDialog QPushButton {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 5px;
                padding: 8px 16px;
                color: {text};
                font-weight: 600;
                min-width: 80px;
            }}
            QProgressDialog QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
            }}
            QProgressDialog QProgressBar {{
                border: 2px solid {border};
                border-radius: 5px;
                text-align: center;
                background-color: {tertiary_bg};
                color: {text};
            }}
            QProgressDialog QProgressBar::chunk {{
                background-color: {accent};
                border-radius: 3px;
            }}
        """
        progress.setStyleSheet(style)

        return progress

    def setup_activity_list_styling(self):
        """Set up proper styling for the activity list with theme-aware colors."""
        bg = self.get_theme_color("background")
        secondary_bg = self.get_theme_color("secondary_bg")
        text = self.get_theme_color("primary_text")
        accent = self.get_theme_color("accent")
        border = self.get_theme_color("border")
        hover_bg = self.get_theme_color("hover_bg")
        selection_bg = self.get_theme_color("selection_bg")

        activity_style = f"""
            QListWidget {{
                background-color: {secondary_bg};
                color: {text};
                alternate-background-color: rgba(117, 189, 224, 0.1);
                selection-background-color: {accent};
                selection-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid rgba(238, 137, 128, 0.2);
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QListWidget::item:selected {{
                background-color: {accent};
                color: {bg};
                font-weight: 600;
            }}
        """

        if hasattr(self, "dashboard_activity"):
            self.dashboard_activity.setStyleSheet(activity_style)

        # Also apply styling to other activity lists
        if hasattr(self, "activity_list"):
            self.activity_list.setStyleSheet(activity_style)

        # Apply styling to reports list
        if hasattr(self, "reports_list"):
            style = self._get_list_widget_style()
            self.reports_list.setStyleSheet(style)

        # Apply styling to quarantine list
        if hasattr(self, "quarantine_list"):
            style = self._get_list_widget_style()
            self.quarantine_list.setStyleSheet(style)

        # Apply styling to paths list
        if hasattr(self, "paths_list"):
            style = self._get_list_widget_style()
            self.paths_list.setStyleSheet(style)

    def _get_list_widget_style(self):
        """Get consistent list widget styling based on current theme."""
        if self.current_theme == "dark":
            return """
                QListWidget {
                    background-color: #2a2a2a;
                    color: #FFCDAA;
                    selection-background-color: #F14666;
                    selection-color: #ffffff;
                    border: 1px solid #EE8980;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid rgba(238, 137, 128, 0.1);
                }
                QListWidget::item:hover {
                    background-color: rgba(241, 70, 102, 0.1);
                }
                QListWidget::item:selected {
                    background-color: #F14666;
                    color: #ffffff;
                    font-weight: 600;
                }
            """
        else:  # light theme
            return """
                QListWidget {
                    background-color: #ffffff;
                    color: #2c2c2c;
                    selection-background-color: #75BDE0;
                    selection-color: #ffffff;
                    border: 1px solid #75BDE0;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid rgba(117, 189, 224, 0.1);
                }
                QListWidget::item:hover {
                    background-color: rgba(117, 189, 224, 0.15);
                    color: #1a1a1a;
                }
                QListWidget::item:selected {
                    background-color: #75BDE0;
                    color: #ffffff;
                    font-weight: 600;
                }
                QListWidget::item:selected:hover {
                    background-color: #5AADD4;
                    color: #ffffff;
                }
            """

    def apply_dark_theme(self):
        """Apply dark theme styling using Strawberry color palette for optimal readability."""
        # Based on Color Theory principles:
        # - F14666 (Deep Strawberry): Primary accent, high energy/attention
        # - EE8980 (Coral): Secondary accent, warm complement
        # - FFCDAA (Peach Cream): Main text, high contrast on dark
        # - 9CB898 (Sage Green): Success states, natural balance
        # Dark neutrals
        # (https://www.uxdesigninstitute.com/blog/what-is-a-gui/#1a1a1a,
        # #2a2a2a, #3a3a3a) for depth hierarchy

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1a1a1a;
                color: #FFCDAA;
                font-size: 12px;
                font-weight: 500;
            }

            QGroupBox {
                font-weight: 600;
                border: 2px solid #EE8980;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 0.8em;
                background-color: #2a2a2a;
                color: #FFCDAA;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 10px 0 10px;
                color: #F14666;
                font-weight: 700;
                font-size: 14px;
            }

            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 60px;
                color: #FFCDAA;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #F14666;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #2a2a2a;
                border-color: #F14666;
            }

            QPushButton#primaryButton {
                background-color: #9CB898;
                border: 2px solid #9CB898;
                color: #1a1a1a;
                font-weight: 700;
            }

            QPushButton#primaryButton:hover {
                background-color: #ACC8A8;
                border-color: #9CB898;
                color: #000000;
            }

            QPushButton#dangerButton {
                background-color: #F14666;
                border: 2px solid #F14666;
                color: #ffffff;
                font-weight: 700;
            }

            QPushButton#dangerButton:hover {
                background-color: #FF5676;
                border-color: #F14666;
                color: #ffffff;
            }

            QProgressBar {
                border: 2px solid #EE8980;
                border-radius: 4px;
                text-align: center;
                height: 20px;
                background-color: #3a3a3a;
                color: #FFCDAA;
                font-weight: 600;
            }

            QProgressBar::chunk {
                background-color: #9CB898;
                border-radius: 4px;
                margin: 2px;
            }

            QTabWidget::pane {
                border: 2px solid #EE8980;
                border-radius: 8px;
                top: -1px;
                background-color: #2a2a2a;
            }

            QTabBar::tab {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
                color: #FFCDAA;
                font-weight: 600;
            }

            QTabBar::tab:selected {
                background-color: #2a2a2a;
                border-bottom: 2px solid #2a2a2a;
                border-left: 2px solid #F14666;
                border-right: 2px solid #F14666;
                border-top: 2px solid #F14666;
                color: #F14666;
                font-weight: 700;
            }

            QTabBar::tab:hover:!selected {
                background-color: #4a4a4a;
                border-color: #F14666;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #3a3a3a;
                padding: 6px;
                border: 1px solid #EE8980;
                border-left: none;
                border-top: none;
                color: #FFCDAA;
                font-weight: 600;
            }

            QTextEdit, QListWidget {
                border: 2px solid #EE8980;
                border-radius: 6px;
                background-color: #3a3a3a;
                color: #FFCDAA;
                font-weight: 500;
                selection-background-color: #F14666;
                selection-color: #ffffff;
                padding: 5px;
            }

            QTextEdit:focus, QListWidget:focus {
                border-color: #F14666;
                background-color: #4a4a4a;
            }

            QLineEdit#themedLineEdit {
                border: 2px solid #EE8980;
                border-radius: 6px;
                background-color: #3a3a3a;
                color: #FFCDAA;
                font-weight: 500;
                padding: 5px;
            }

            QLineEdit#themedLineEdit:focus {
                border-color: #F14666;
                background-color: #4a4a4a;
            }

            QLineEdit#themedLineEdit:disabled {
                border-color: #666666;
                background-color: #2a2a2a;
                color: #999999;
            }

            QLabel {
                color: #FFCDAA;
                font-weight: 600;
            }

            QStatusBar {
                background-color: #3a3a3a;
                color: #FFCDAA;
                border-top: 2px solid #EE8980;
                font-weight: 600;
                padding: 4px;
            }

            QMenuBar {
                background-color: #3a3a3a;
                color: #FFCDAA;
                border-bottom: 2px solid #EE8980;
                font-weight: 600;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QMenuBar::item:selected {
                background-color: #4a4a4a;
                color: #ffffff;
            }

            QMenu {
                background-color: #3a3a3a;
                color: #FFCDAA;
                border: 2px solid #F14666;
                border: 2px solid #F14666;
                border-radius: 6px;
                font-weight: 600;
                padding: 4px;
            }

            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 2px;
            }

            QMenu::item:selected {
                background-color: #EE8980;
                color: #ffffff;
            }

            #headerFrame {
                background-color: #F14666;
                color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                border: 2px solid #F14666;
            }

            #appTitle {
                color: white;
                font-size: 22px;
                font-weight: 700;
            }

            #pathLabel {
                font-weight: 600;
                padding: 8px 12px;
                background-color: #4a4a4a;
                border-radius: 6px;
                color: #FFCDAA;
                border: 1px solid #EE8980;
            }

            #actionButton {
                background-color: #F14666;
                color: white;
                border: 4px solid #F14666;
                border-radius: 6px;
                font-weight: 700;
                padding: 6px 12px;
                min-width: 120px;
                min-height: 32px;
                text-align: center;
                line-height: 1.3;
                font-size: 13px;
            }

            #actionButton:hover {
                background-color: #FF5676;
                border: 4px solid #EE8980;
                color: #ffffff;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }

            #actionButton:pressed {
                background-color: #E03256;
                border: 4px solid #FFCDAA;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }

            #lastUpdateLabel {
                color: white;
                font-size: 12px;
                margin: 3px;
                font-weight: 600;
                background-color: rgba(255, 205, 170, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid rgba(255, 205, 170, 0.3);
            }

            #lastCheckedLabel {
                color: white;
                font-size: 11px;
                margin: 2px;
                font-style: italic;
                font-weight: 500;
                background-color: rgba(255, 205, 170, 0.1);
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid rgba(255, 205, 170, 0.2);
            }

            /* Scan report sections - enhanced readability */
            #resultsText {
                font-weight: 500;
                color: #FFCDAA;
                line-height: 1.4;
            }

            #reportViewer {
                font-weight: 500;
                color: #FFCDAA;
                line-height: 1.4;
            }

            /* Real-time protection status styles */
            #protectionStatus {
                font-size: 16px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
            }

            /* Dashboard Status Cards with improved visual hierarchy */
            QFrame#statusCard {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }

            QFrame#statusCard:hover {
                border-color: #F14666;
                background-color: #4a4a4a;
            }

            QLabel#cardTitle {
                color: #FFCDAA;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }

            QLabel#cardValue {
                font-size: 28px;
                font-weight: 700;
                margin: 8px 0px;
            }

            QLabel#cardDescription {
                color: #EE8980;
                font-size: 11px;
                font-weight: 500;
                line-height: 1.4;
            }

            /* Dashboard Action Buttons with solid colors */
            QPushButton#dashboardPrimaryButton {
                background-color: #9CB898;
                border: 2px solid #9CB898;
                border-radius: 8px;
                color: #1a1a1a;
                font-weight: 700;
                font-size: 14px;
                min-height: 40px;
                padding: 0px 20px;
            }

            QPushButton#dashboardPrimaryButton:hover {
                background-color: #ACC8A8;
                border-color: #ACC8A8;
            }

            QPushButton#dashboardSecondaryButton {
                background-color: #4a4a4a;
                border: 2px solid #EE8980;
                border-radius: 8px;
                color: #FFCDAA;
                font-weight: 600;
                font-size: 13px;
                min-height: 40px;
                padding: 0px 16px;
            }

            QPushButton#dashboardSecondaryButton:hover {
                background-color: #5a5a5a;
                border-color: #F14666;
                color: #ffffff;
            }

            /* Preset Scan Buttons with enhanced styling */
            QPushButton#presetButton {
                background: #4a4a4a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                min-height: 35px;
            }

            QPushButton#presetButton:hover {
                background: #5a5a5a;
                border-color: #F14666;
                color: #ffffff;
            }

            QLabel#presetLabel {
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }

            /* Scrollbar styling for consistency */
            QScrollBar:vertical {
                background-color: #3a3a3a;
                width: 12px;
                border-radius: 6px;
                border: 1px solid #EE8980;
            }

            QScrollBar::handle:vertical {
                background-color: #F14666;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #FF5676;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* Settings Tab Controls */
            QCheckBox {
                color: #FFCDAA;
                font-weight: 500;
                font-size: 12px;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #EE8980;
                border-radius: 4px;
                background-color: #3a3a3a;
            }

            QCheckBox::indicator:checked {
                background-color: #9CB898;
                border-color: #9CB898;
            }

            QCheckBox::indicator:hover {
                border-color: #F14666;
            }

            QSpinBox {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                padding: 8px 12px;
                color: #FFCDAA;
                font-weight: 500;
                font-size: 12px;
            }

            QSpinBox:focus {
                border-color: #F14666;
                background-color: #2a2a2a;
            }

            QTimeEdit, QTimeEdit#scanTimeEdit, QAbstractSpinBox {
                background-color: #3a3a3a !important;
                border: 2px solid #EE8980 !important;
                border-radius: 6px;
                padding: 8px 12px;
                color: #FFCDAA !important;
                font-weight: 500;
                font-size: 12px;
            }

            QTimeEdit:focus, QTimeEdit#scanTimeEdit:focus, QAbstractSpinBox:focus {
                border-color: #F14666 !important;
                background-color: #2a2a2a !important;
            }

            QTimeEdit:disabled, QTimeEdit#scanTimeEdit:disabled, QAbstractSpinBox:disabled {
                background-color: #2a2a2a !important;
                color: #808080 !important;
                border-color: #555555 !important;
            }

            QTimeEdit::up-button, QTimeEdit::down-button {
                background-color: #444444;
                border: 1px solid #666666;
                border-radius: 3px;
                width: 16px;
                height: 16px;
            }

            QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
                background-color: #555555;
                border-color: #F14666;
            }

            QTimeEdit::up-button:pressed, QTimeEdit::down-button:pressed {
                background-color: #333333;
            }

            QComboBox {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                padding: 10px 16px;
                color: #FFCDAA;
                font-weight: 500;
                font-size: 12px;
                min-width: 120px;
            }

            QComboBox:focus {
                border-color: #F14666;
                background-color: #2a2a2a;
            }

            QComboBox:hover {
                border-color: #F14666;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #EE8980;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #4a4a4a;
            }

            QComboBox::drop-down:hover {
                background-color: #F14666;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #FFCDAA;
                width: 0px;
                height: 0px;
            }

            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                border: 1px solid #EE8980;
                border-radius: 4px;
                color: #FFCDAA;
                selection-background-color: #F14666;
                selection-color: #ffffff;
                outline: none;
                margin: 0px;
                padding: 0px;
            }

            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 20px;
                border: none;
                margin: 0px;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #EE8980;
                color: #ffffff;
                border: none;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #F14666;
                color: #ffffff;
                border: none;
            }

            /* Fix dropdown popup frame (this causes the white borders) */
            QComboBox QListView {
                background-color: #2a2a2a;
                border: 1px solid #EE8980;
                border-radius: 4px;
                color: #FFCDAA;
                selection-background-color: #F14666;
                selection-color: #ffffff;
                outline: none;
            }

            QComboBox QFrame {
                background-color: #2a2a2a;
                border: 1px solid #EE8980;
                border-radius: 4px;
            }

            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #EE8980;
                border: none;
                border-radius: 3px;
                width: 16px;
                color: #1a1a1a;
                font-weight: 600;
            }

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #F14666;
            }

            QFormLayout QLabel {
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                padding: 5px;
            }

            QScrollArea {
                background-color: #1a1a1a;
                border: none;
            }

            /* Settings Tab Specific Widgets */
            QWidget#settingsTabWidget {
                background-color: #1a1a1a;
            }

            QScrollArea#settingsScrollArea {
                background-color: #1a1a1a;
                border: none;
            }

            QWidget#settingsScrollContent {
                background-color: #1a1a1a;
            }
        """
        )

        # Apply activity list styling after theme
        self.setup_activity_list_styling()

    def apply_light_theme(self):
        """Apply light theme styling using Sunrise color palette for optimal readability."""
        # Based on Color Theory principles:
        # - 75BDE0 (Sky Blue): Primary accent, trust and stability
        # - F8D49B (Golden Yellow): Secondary accent, warm energy
        # - F8BC9B (Peach Orange): Interactive elements, friendly warmth
        # - F89B9B (Coral Pink): Danger/attention states, warm warnings
        # Light neutrals (#fefefe, #ffffff, #f5f5f5) for clean hierarchy

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #fefefe;
                color: #2c2c2c;
                font-size: 12px;
                font-weight: 500;
            }

            QGroupBox {
                font-weight: 600;
                border: 2px solid #75BDE0;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 0.8em;
                background-color: #ffffff;
                color: #2c2c2c;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #75BDE0;
                font-weight: 700;
                font-size: 13px;
            }

            QPushButton {
                background-color: #F8D49B;
                border: 1px solid #F8BC9B;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                color: #2c2c2c;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #F8BC9B;
                border-color: #F89B9B;
                color: #1a1a1a;
            }

            QPushButton:pressed {
                background-color: #F89B9B;
                border-color: #75BDE0;
            }

            QPushButton#primaryButton {
                background-color: #75BDE0;
                border: 2px solid #75BDE0;
                color: #ffffff;
                font-weight: 700;
            }

            QPushButton#primaryButton:hover {
                background-color: #5AADD4;
                border-color: #5AADD4;
            }

            QPushButton#dangerButton {
                background-color: #F89B9B;
                border: 2px solid #F89B9B;
                color: #2c2c2c;
                font-weight: 700;
            }

            QPushButton#dangerButton:hover {
                background-color: #F67B7B;
                border-color: #F67B7B;
            }

            QProgressBar {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 600;
            }

            QProgressBar::chunk {
                background-color: #75BDE0;
                border-radius: 4px;
                margin: 2px;
            }

            QTabWidget::pane {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                top: -1px;
                background-color: #ffffff;
            }

            QTabBar::tab {
                background-color: #F8D49B;
                border: 1px solid #F8BC9B;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 3px;
                color: #2c2c2c;
                font-weight: 600;
            }

            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #ffffff;
                border-left: 2px solid #75BDE0;
                border-right: 2px solid #75BDE0;
                border-top: 2px solid #75BDE0;
                color: #75BDE0;
                font-weight: 700;
            }

            QTabBar::tab:hover:!selected {
                background-color: #F8BC9B;
                color: #1a1a1a;
            }

            QHeaderView::section {
                background-color: #F8D49B;
                padding: 6px;
                border: 1px solid #F8BC9B;
                border-left: none;
                border-top: none;
                color: #2c2c2c;
                font-weight: 600;
            }

            QTextEdit, QListWidget {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 400;
                selection-background-color: #75BDE0;
                selection-color: #ffffff;
                padding: 5px;
            }

            QTextEdit:focus, QListWidget:focus {
                border-color: #75BDE0;
            }

            QLineEdit#themedLineEdit {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 500;
                padding: 5px;
            }

            QLineEdit#themedLineEdit:focus {
                border-color: #75BDE0;
            }

            QLineEdit#themedLineEdit:disabled {
                border-color: #cccccc;
                background-color: #f5f5f5;
                color: #999999;
            }

            QLabel {
                color: #2c2c2c;
                font-weight: 600;
            }

            QStatusBar {
                background-color: #F8D49B;
                color: #2c2c2c;
                border-top: 2px solid #F8BC9B;
                font-weight: 600;
            }

            QMenuBar {
                background-color: #F8D49B;
                color: #2c2c2c;
                border-bottom: 2px solid #F8BC9B;
                font-weight: 600;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QMenuBar::item:selected {
                background-color: #F8BC9B;
                color: #1a1a1a;
            }

            QMenu {
                background-color: #ffffff;
                color: #2c2c2c;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                font-weight: 600;
            }

            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 2px;
            }

            QMenu::item:selected {
                background-color: #F8D49B;
                color: #2c2c2c;
            }

            #headerFrame {
                background-color: #75BDE0;
                color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                border: 2px solid #75BDE0;
            }

            #appTitle {
                color: white;
                font-size: 22px;
                font-weight: 700;
            }

            #pathLabel {
                font-weight: 600;
                padding: 8px;
                background-color: #F8D49B;
                border-radius: 6px;
                color: #2c2c2c;
                border: 1px solid #F8BC9B;
            }

            #actionButton {
                background-color: #75BDE0;
                color: white;
                border: 4px solid #75BDE0;
                border-radius: 6px;
                font-weight: 700;
                padding: 6px 12px;
                min-width: 120px;
                min-height: 32px;
                text-align: center;
                line-height: 1.3;
                font-size: 13px;
            }

            #actionButton:hover {
                background-color: #5AADD4;
                border: 4px solid #F8BC9B;
                color: #ffffff;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }

            #actionButton:pressed {
                background-color: #4A9DC4;
                border: 4px solid #F89B9B;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }

            #lastUpdateLabel {
                color: #2c2c2c;
                font-size: 12px;
                margin: 3px;
                font-weight: 600;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid #F8D49B;
                text-align: center;
            }

            #lastCheckedLabel {
                color: #2c2c2c;
                font-size: 11px;
                margin: 2px;
                font-style: italic;
                font-weight: 500;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid #F8BC9B;
                text-align: center;
            }

            /* Scan report sections - enhanced readability with sunrise palette */
            #resultsText {
                font-weight: 400;
                line-height: 1.5;
                color: #2c2c2c;
                background-color: #ffffff;
                border: 2px solid #F8D49B;
                border-radius: 6px;
            }

            #reportViewer {
                font-weight: 400;
                line-height: 1.5;
                color: #2c2c2c;
            }

            /* Real-time protection status styles */
            #protectionStatus {
                font-size: 16px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                background-color: #ffffff;
                border: 2px solid #F8D49B;
            }

            /* Dashboard Status Cards with solid colors */
            QFrame#statusCard {
                background-color: #ffffff;
                border: 2px solid #F8D49B;
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }

            QFrame#statusCard:hover {
                border-color: #75BDE0;
                background-color: #f8f8f8;
            }

            QLabel#cardTitle {
                color: #2c2c2c;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }

            QLabel#cardValue {
                font-size: 28px;
                font-weight: 700;
                margin: 8px 0px;
            }

            QLabel#cardDescription {
                color: #75BDE0;
                font-size: 11px;
                font-weight: 500;
                line-height: 1.4;
            }

            /* Dashboard Action Buttons with solid colors */
            QPushButton#dashboardPrimaryButton {
                background-color: #75BDE0;
                border: 2px solid #75BDE0;
                border-radius: 8px;
                color: #ffffff;
                font-weight: 700;
                font-size: 14px;
                min-height: 40px;
                padding: 0px 20px;
            }

            QPushButton#dashboardPrimaryButton:hover {
                background-color: #5AADD4;
                border-color: #5AADD4;
            }

            QPushButton#dashboardSecondaryButton {
                background-color: #F8D49B;
                border: 2px solid #F8BC9B;
                border-radius: 8px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 13px;
                min-height: 40px;
                padding: 0px 16px;
            }

            QPushButton#dashboardSecondaryButton:hover {
                background-color: #F8BC9B;
                border-color: #F89B9B;
                color: #1a1a1a;
            }

            /* Preset Scan Buttons with sunrise styling */
            QPushButton#presetButton {
                background: #F8D49B;
                border: 2px solid #F8BC9B;
                border-radius: 6px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                min-height: 35px;
            }

            QPushButton#presetButton:hover {
                background: #F8BC9B;
                border-color: #75BDE0;
                color: #1a1a1a;
            }

            QLabel#presetLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }

            /* Scrollbar styling for consistency */
            QScrollBar:vertical {
                background-color: #f8f8f8;
                width: 12px;
                border-radius: 6px;
                border: 1px solid #F8D49B;
            }

            QScrollBar::handle:vertical {
                background-color: #75BDE0;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #5AADD4;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* Settings Tab Controls */
            QCheckBox {
                color: #333333;
                font-weight: 500;
                font-size: 12px;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #75BDE0;
                border-radius: 4px;
                background-color: #ffffff;
            }

            QCheckBox::indicator:checked {
                background-color: #75BDE0;
                border-color: #75BDE0;
            }

            QCheckBox::indicator:hover {
                border-color: #F8BC9B;
            }

            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-weight: 500;
                font-size: 12px;
            }

            QSpinBox:focus {
                border-color: #F8BC9B;
                background-color: #f8f8f8;
            }

            QTimeEdit, QTimeEdit#scanTimeEdit, QAbstractSpinBox {
                background-color: #ffffff !important;
                border: 2px solid #75BDE0 !important;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333 !important;
                font-weight: 500;
                font-size: 12px;
            }

            QTimeEdit:focus, QTimeEdit#scanTimeEdit:focus, QAbstractSpinBox:focus {
                border-color: #F8BC9B !important;
                background-color: #f8f8f8 !important;
            }

            QTimeEdit:disabled, QTimeEdit#scanTimeEdit:disabled, QAbstractSpinBox:disabled {
                background-color: #f0f0f0 !important;
                color: #888888 !important;
                border-color: #cccccc !important;
            }

            QTimeEdit::up-button, QTimeEdit::down-button {
                background-color: #f8f8f8;
                border: 1px solid #cccccc;
                border-radius: 3px;
                width: 16px;
                height: 16px;
            }

            QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
                background-color: #e8e8e8;
                border-color: #F8BC9B;
            }

            QTimeEdit::up-button:pressed, QTimeEdit::down-button:pressed {
                background-color: #d8d8d8;
            }

            QComboBox {
                background-color: #ffffff;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-weight: 500;
                font-size: 12px;
                min-width: 120px;
            }

            QComboBox:focus {
                border-color: #F8BC9B;
                background-color: #f8f8f8;
            }

            QComboBox:hover {
                border-color: #F8BC9B;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #75BDE0;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #f0f0f0;
            }

            QComboBox::drop-down:hover {
                background-color: #F8BC9B;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #333333;
                width: 0px;
                height: 0px;
            }

            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #75BDE0;
                border-radius: 4px;
                color: #333333;
                selection-background-color: #F8BC9B;
                selection-color: #2c2c2c;
                outline: none;
                margin: 0px;
                padding: 0px;
            }

            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 20px;
                border: none;
                margin: 0px;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #75BDE0;
                color: #ffffff;
                border: none;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #F8BC9B;
                color: #2c2c2c;
                border: none;
            }

            /* Fix dropdown popup frame (this causes the white borders) */
            QComboBox QListView {
                background-color: #ffffff;
                border: 1px solid #75BDE0;
                border-radius: 4px;
                color: #333333;
                selection-background-color: #F8BC9B;
                selection-color: #2c2c2c;
                outline: none;
            }

            QComboBox QFrame {
                background-color: #ffffff;
                border: 1px solid #75BDE0;
                border-radius: 4px;
            }
            
            /* Scan Type Combo Specific Styling */
            QComboBox#scanTypeCombo {
                background-color: #ffffff;
                border: 2px solid #2E8B57;
                border-radius: 8px;
                padding: 12px 18px;
                font-weight: 600;
                font-size: 13px;
                min-width: 150px;
            }
            
            QComboBox#scanTypeCombo:focus {
                border-color: #32CD32;
                background-color: #f0fff0;
            }
            
            /* Next Scan Label Styling */
            QLabel#nextScanLabel {
                background-color: #f0f8ff;
                border: 1px solid #87CEEB;
                border-radius: 4px;
                padding: 6px 10px;
                color: #2E8B57;
                font-weight: 500;
                font-size: 11px;
            }

            /* Enhanced Button Styling for Better Spacing */
            QPushButton#presetButton {
                background-color: #ffffff;
                border: 2px solid #75BDE0;
                border-radius: 8px;
                padding: 8px 16px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 12px;
                min-height: 36px;
                min-width: 88px;
            }
            
            QPushButton#presetButton:hover {
                background-color: #f0f8ff;
                border-color: #32CD32;
            }
            
            QPushButton#presetButton:pressed {
                background-color: #e6f3ff;
            }

            /* Section Labels */
            QLabel#sectionLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }

            /* Path Label */
            QLabel#pathLabel {
                background-color: #f8f8f8;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px 12px;
                color: #333333;
                font-family: monospace;
                font-size: 11px;
            }

            /* Status Label */
            QLabel#statusLabel {
                color: #2c2c2c;
                font-weight: 500;
                font-size: 13px;
                padding: 4px 8px;
            }

            /* Progress Bar Enhanced */
            QProgressBar#modernProgressBar {
                background-color: #f0f0f0;
                border: 2px solid #d0d0d0;
                border-radius: 12px;
                text-align: center;
                font-weight: 600;
                font-size: 12px;
                min-height: 24px;
            }

            QProgressBar#modernProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #32CD32, stop: 1 #228B22);
                border-radius: 10px;
                margin: 2px;
            }

            /* Form Layout Improvements */
            QFormLayout QLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
                min-width: 80px;
            }

            /* Scroll Area */
            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }

            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }

            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #75BDE0;
                border: none;
                border-radius: 3px;
                width: 16px;
                color: #ffffff;
                font-weight: 600;
            }

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #F8BC9B;
            }

            QFormLayout QLabel {
                color: #333333;
                font-weight: 600;
                font-size: 12px;
                padding: 5px;
            }

            QScrollArea {
                background-color: #f8f8f8;
                border: none;
            }

            /* Settings Tab Specific Widgets */
            QWidget#settingsTabWidget {
                background-color: #f8f8f8;
            }

            QScrollArea#settingsScrollArea {
                background-color: #f8f8f8;
                border: none;
            }

            QWidget#settingsScrollContent {
                background-color: #f8f8f8;
            }
        """
        )

        # Apply activity list styling after theme
        self.setup_activity_list_styling()

    def apply_system_theme(self):
        """Apply system theme (falls back to light theme for now)."""
        # For now, system theme defaults to light theme
        # In a full implementation, you could detect system theme preference
        self.apply_light_theme()

    def apply_text_orientation_setting(self, orientation_text=None):
        """Apply text orientation setting to scan results display."""
        try:
            # Get the orientation from parameter or settings
            if orientation_text is None:
                ui_settings = self.config.get("ui_settings", {})
                orientation_text = ui_settings.get("text_orientation", "Centered")
            
            # Map text orientation to Qt alignment flags
            alignment_map = {
                "Left Aligned": Qt.AlignmentFlag.AlignLeft,
                "Centered": Qt.AlignmentFlag.AlignCenter,
                "Right Aligned": Qt.AlignmentFlag.AlignRight
            }
            
            alignment = alignment_map.get(orientation_text, Qt.AlignmentFlag.AlignCenter)
            
            # Apply the alignment to the results text widget
            if hasattr(self, 'results_text') and self.results_text:
                doc = self.results_text.document()
                option = doc.defaultTextOption()
                option.setAlignment(alignment)
                doc.setDefaultTextOption(option)
                
                # Force a repaint to apply the alignment to existing text
                self.results_text.update()
                
                print(f"✅ Applied text orientation: {orientation_text}")
            
            # Auto-save the setting if it was changed via UI
            if orientation_text and hasattr(self, 'text_orientation_combo'):
                # Only auto-save if the timer is initialized
                if hasattr(self, '_settings_save_timer'):
                    self.auto_save_settings()
                
        except Exception as e:
            print(f"❌ Error applying text orientation: {e}")

    def _initialize_auto_updater(self):
        """Initialize the auto-update system."""
        try:
            from pathlib import Path
            
            # Read current version from VERSION file
            version_file = Path(__file__).parent.parent.parent / "VERSION"
            try:
                current_version = version_file.read_text().strip()
            except (FileNotFoundError, IOError):
                current_version = "2.4.0"  # Fallback version
                
            # Repository information
            # Initialize the auto-updater with configuration
            self.auto_updater = AutoUpdater(current_version=current_version)
            
            # Initialize the update notifier  
            self.update_notifier = UpdateNotifier(self.auto_updater, self)
            
            # Check for updates in the background if auto-check is enabled
            settings = self.load_settings()
            auto_check = settings.get('auto_check_updates', True)
            check_interval = settings.get('update_check_interval', 24)  # hours
            
            if auto_check:
                # Set up periodic update checking
                self.update_check_timer = QTimer()
                self.update_check_timer.timeout.connect(self.update_notifier.check_for_updates_background)
                self.update_check_timer.start(check_interval * 60 * 60 * 1000)  # Convert hours to milliseconds
                
                # Do an initial check (delayed by 30 seconds to avoid blocking startup)
                QTimer.singleShot(30000, self.update_notifier.check_for_updates_background)
                
            print("✅ Auto-updater initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing auto-updater: {e}")

    def check_for_updates_manual(self):
        """Manually check for updates when user clicks Help menu item."""
        if hasattr(self, 'auto_updater') and self.auto_updater:
            try:
                from PyQt6.QtWidgets import QMessageBox
                
                # Check for updates directly
                update_info = self.auto_updater.check_for_updates(force_check=True)
                
                if update_info and update_info.get('available'):
                    # Show update available dialog
                    if hasattr(self, 'update_notifier') and self.update_notifier:
                        self.update_notifier.show_update_notification(update_info)
                    else:
                        # Fallback message
                        QMessageBox.information(
                            self, "Update Available",
                            f"Update available: v{update_info.get('latest_version')}\n"
                            f"Current version: v{update_info.get('current_version')}\n"
                            f"Release: {update_info.get('release_name', 'Unknown')}"
                        )
                else:
                    # No updates available
                    QMessageBox.information(
                        self, "No Updates Available",
                        f"You are running the latest version (v{self.auto_updater.current_version})."
                    )
                    
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "Update Check Failed",
                    f"Failed to check for updates:\n{str(e)}"
                )
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Update Check", 
                              "Auto-updater is not initialized. Please restart the application.")

    def get_update_settings(self):
        """Get current auto-update settings."""
        try:
            settings = self.load_settings()
            return settings.get('auto_update_settings', {
                'auto_check_updates': True,
                'auto_download_updates': False,
                'update_check_interval': 24
            })
        except Exception:
            return {
                'auto_check_updates': True,
                'auto_download_updates': False,
                'update_check_interval': 24
            }

    def load_settings(self):
        """Load and return current settings from config."""
        try:
            return self.config
        except Exception:
            # Return defaults if config is not available
            from utils.config import get_factory_defaults
            return get_factory_defaults()

    def open_update_dialog(self):
        """Open the update dialog for manual update checking."""
        try:
            if hasattr(self, 'auto_updater'):
                from gui.update_components import UpdateDialog
                # First argument must be the QWidget parent; second is current version string
                current_version = getattr(self.auto_updater, 'current_version', '0.0.0')
                dialog = UpdateDialog(self, current_version)
                dialog.exec()
            else:
                self.show_themed_message_box(
                    "warning", 
                    "Updates", 
                    "Auto-updater is not initialized. Please restart the application."
                )
        except Exception as e:
            self.show_themed_message_box(
                "warning", 
                "Error", 
                f"Could not open update dialog: {str(e)}"
            )

    def set_scan_path(self, path):
        """Set the scan path and update the UI."""
        if os.path.exists(path):
            self.scan_path = path
            
            # Auto-switch to Custom scan type when a path is selected
            for i in range(self.scan_type_combo.count()):
                if self.scan_type_combo.itemData(i) == "CUSTOM":
                    self.scan_type_combo.setCurrentIndex(i)
                    break
            
            # Update the path description with custom scan details
            self.on_scan_type_changed()
        else:
            self.show_themed_message_box(
                "warning", "Warning", f"Path does not exist: {path}"
            )

    def select_scan_path(self):
        path = self.show_themed_file_dialog(
            "directory", "Select Directory to Scan")
        if path:
            self.set_scan_path(path)  # Use set_scan_path to handle all updates
    
    def on_scan_type_changed(self):
        """Handle scan type selection changes with detailed descriptions."""
        current_type = self.scan_type_combo.currentData()
        
        if current_type == "QUICK":
            self.path_label.setText(
                "🚀 Quick Scan: Comprehensive multi-directory scanning\n"
                "• Scans user directories, browser data, temp files\n"
                "• Fast scan optimized for common threat locations"
            )
        elif current_type == "FULL":
            self.path_label.setText(
                "🔍 Full Scan: Will scan entire system\n"
                "• Complete scan of all drives and accessible files\n"
                "• Thorough protection but takes longer to complete"
            )
        elif current_type == "CUSTOM":
            if hasattr(self, 'scan_path') and self.scan_path:
                self.path_label.setText(
                    f"⚙️ Custom Scan: Selected path\n"
                    f"• {self.scan_path}\n"
                    f"• Targeted scan of your chosen location"
                )
            else:
                self.path_label.setText(
                    "⚙️ Custom Scan: Please select a custom path\n"
                    "• Choose specific folder or drive to scan\n"
                    "• Focused scanning for targeted protection"
                )
        
        # Update any relevant UI elements based on scan type

    def toggle_scan(self):
        """Toggle between starting and stopping scans based on current state."""
        print(f"\n🔄 === TOGGLE_SCAN CALLED ===")
        print(f"DEBUG: Current scan running state: {self._scan_running}")
        print(f"DEBUG: Current scan state: {self._scan_state}")
        
        if self._scan_running:
            # If scan is running, stop it
            print("🛑 Toggle: Stopping scan...")
            self.stop_scan()
        else:
            # If scan is not running, start it
            print("🚀 Toggle: Starting scan...")
            self.start_scan()

    def update_scan_button_state(self, is_running):
        """Update the scan toggle button appearance based on scan state."""
        self._scan_running = is_running
        
        if is_running:
            self.scan_toggle_btn.setText("⏹️ Stop Scan")
            self.scan_toggle_btn.setObjectName("dangerButton")
            print("🔴 Button updated to Stop Scan mode")
        else:
            self.scan_toggle_btn.setText("🚀 Start Scan")
            self.scan_toggle_btn.setObjectName("primaryButton")
            print("🟢 Button updated to Start Scan mode")
        
        # Reapply style to pick up the new object name
        self.scan_toggle_btn.style().unpolish(self.scan_toggle_btn)
        self.scan_toggle_btn.style().polish(self.scan_toggle_btn)

    def start_scan(self, quick_scan=False):
        print(f"\n🔄 === START_SCAN CALLED ===")
        print(f"DEBUG: start_scan() called with quick_scan={quick_scan}")
        print(f"DEBUG: Current scan state: {self._scan_state}")
        print(f"DEBUG: Current thread exists: {self.current_scan_thread is not None}")
        print(f"DEBUG: Thread running: {self.current_scan_thread.isRunning() if self.current_scan_thread else 'N/A'}")
        print(f"DEBUG: Manual stop flag: {self._scan_manually_stopped}")
        print(f"DEBUG: Pending request: {self._pending_scan_request}")
        print(f"DEBUG: User wants restart: {self._stop_scan_user_wants_restart}")
        
        # Check if we're in a stopping state OR if there's a completion timer running
        # This provides a broader detection window for pending requests
        if self._scan_state == "stopping" or (hasattr(self, '_stop_completion_timer') and self._stop_completion_timer.isActive()):
            # Queue the scan request to execute after current scan finishes
            print("DEBUG: ⏳ Scan is stopping OR completion timer active, queuing new scan request")
            self._pending_scan_request = {"quick_scan": quick_scan}
            self.status_bar.showMessage("⏳ New scan queued - waiting for current scan to finish...")
            print(f"DEBUG: Queued request: {self._pending_scan_request}")
            return
        
        # NEW: Check if user recently stopped a scan and wants to restart
        if self._stop_scan_user_wants_restart:
            print("DEBUG: 🔄 User previously stopped scan and wants restart - executing immediately")
            self._stop_scan_user_wants_restart = False  # Reset flag
            # Continue with normal scan start logic
        
        # Check if already scanning
        if self._scan_state == "scanning":
            print("DEBUG: ❌ Scan already in progress, ignoring request")
            self.status_bar.showMessage("⚠️ Scan already in progress")
            return
            
        # Clean up any finished threads
        if self.current_scan_thread and not self.current_scan_thread.isRunning():
            print("DEBUG: 🧹 Cleaning up finished thread reference")
            # Make sure the thread is properly cleaned up before proceeding
            try:
                self.current_scan_thread.deleteLater()
            except Exception as e:
                print(f"DEBUG: ⚠️ Error during thread cleanup: {e}")
            finally:
                self.current_scan_thread = None
        
        # Prevent starting if there's still an active thread
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            print("DEBUG: ⚠️ Thread still running, cannot start new scan")
            self.status_bar.showMessage("⚠️ Previous scan still finishing - please wait")
            return
            
        # Additional safety check: ensure we don't have lingering thread references
        if self.current_scan_thread is not None:
            print("DEBUG: ⚠️ Lingering thread reference detected, clearing it")
            self.current_scan_thread = None
            
        # Set scanning state and reset flags for new scan
        self._scan_state = "scanning"
        self._scan_manually_stopped = False
        self.is_quick_scan_running = False  # Reset quick scan flag
        self._pending_scan_request = None  # Clear any pending requests
        
        print(f"DEBUG: ✅ Starting new scan, state set to: {self._scan_state}")
        print(f"DEBUG: Reset manual stop flag to: {self._scan_manually_stopped}")
        print(f"DEBUG: Cleared pending request")
        
        # Get scan type from UI if available, otherwise use parameter
        scan_type_data = None
        if hasattr(self, 'scan_type_combo'):
            scan_type_data = self.scan_type_combo.currentData()
            
        # Determine effective scan type
        if quick_scan:
            effective_scan_type = "QUICK"
        elif scan_type_data:
            effective_scan_type = scan_type_data
        else:
            effective_scan_type = "FULL"
        
        # Handle scan path based on scan type
        if effective_scan_type == "QUICK":
            # Quick scan targets multiple common infection vectors and user directories
            import tempfile
            
            # Check if we already have comprehensive paths from quick scan button
            if hasattr(self, 'quick_scan_paths') and self.quick_scan_paths:
                # Use the comprehensive paths from the quick scan button
                valid_paths = self.quick_scan_paths
                self.scan_path = valid_paths
            else:
                # Fallback for combo box quick scan - create comprehensive path list
                quick_scan_paths = [
                    # Primary infection vectors
                    os.path.expanduser("~/Downloads"),
                    os.path.expanduser("~/Desktop"),
                    os.path.expanduser("~/Documents"),
                    os.path.expanduser("~/Pictures"),
                    os.path.expanduser("~/Videos"),
                    os.path.expanduser("~/Music"),
                    
                    # Browser directories
                    os.path.expanduser("~/.mozilla"),
                    os.path.expanduser("~/.config/google-chrome"),
                    os.path.expanduser("~/.config/chromium"),
                    
                    # System temporary
                    tempfile.gettempdir(),
                    "/tmp" if os.path.exists("/tmp") else None,
                    "/var/tmp" if os.path.exists("/var/tmp") else None,
                    
                    # User application data
                    os.path.expanduser("~/.local/share"),
                    os.path.expanduser("~/.cache"),
                ]
                
                # Filter out non-existent paths
                valid_paths = [
                    path for path in quick_scan_paths 
                    if path and os.path.exists(path) and os.path.isdir(path)
                ]
                
                if not valid_paths:
                    self.show_themed_message_box(
                        "warning", "Warning", "No valid directories found for quick scan."
                    )
                    return
                
                # For Quick Scan, always use comprehensive scan paths regardless of previous selection
                self.scan_path = valid_paths
                print(f"DEBUG: Quick scan using {len(valid_paths)} directories: {valid_paths[:3]}{'...' if len(valid_paths) > 3 else ''}")
            
        elif effective_scan_type == "FULL":
            # Full scan targets the entire home directory
            self.scan_path = os.path.expanduser("~")
            
        elif effective_scan_type == "CUSTOM":
            # Custom scan uses the user-selected path
            if not hasattr(self, "scan_path") or not self.scan_path:
                self.show_themed_message_box(
                    "warning", "Warning", "Please select a path to scan first.\n\nClick the 'Browse...' button below the scan type dropdown to choose a directory to scan."
                )
                self._scan_state = "idle"  # Reset scan state
                return
        else:
            # Default fallback
            if not hasattr(self, "scan_path") or not self.scan_path:
                self.show_themed_message_box(
                    "warning", "Warning", "Please select a path to scan first.\n\nClick the 'Browse...' button to choose a directory to scan."
                )
                self._scan_state = "idle"  # Reset scan state
                return

        # Get advanced options if available
        scan_options = {}
        if hasattr(self, 'scan_depth_combo'):
            scan_options['depth'] = self.scan_depth_combo.currentData()
        if hasattr(self, 'file_filter_combo'):
            scan_options['file_filter'] = self.file_filter_combo.currentData()
        if hasattr(self, 'memory_limit_combo'):
            scan_options['memory_limit'] = self.memory_limit_combo.currentData()
        if hasattr(self, 'exclusion_text'):
            exclusions = self.exclusion_text.toPlainText().strip()
            if exclusions:
                scan_options['exclusions'] = [pattern.strip() for pattern in exclusions.split('\n') if pattern.strip()]

        self.update_scan_button_state(True)  # Set to "Stop Scan" mode
        self.progress_bar.setValue(0)
        self._clear_results_with_header()
        
        # Reset autoscroll tracking for new scan
        self._user_has_scrolled = False
        self._last_scroll_position = 0
        
        # Initialize detailed scan tracking
        self._scan_directories_info = {}
        self._last_displayed_directory = None
        self._scanned_directories = []  # Use list to maintain order
        self._completed_directories = []  # Track truly completed directories

        # Check if this is a full system scan and RKHunter integration is enabled
        is_full_system_scan = hasattr(self, "scan_path") and (
            self.scan_path == "/" or self.scan_path == str(Path.home())
        )

        rkhunter_settings = self.config.get("rkhunter_settings", {})
        should_run_rkhunter_full = (
            is_full_system_scan
            and rkhunter_settings.get("enabled", False)
            and rkhunter_settings.get("run_with_full_scan", False)
            and self._rkhunter_available()
        )

        should_run_rkhunter_quick = (
            (quick_scan or effective_scan_type == "QUICK")  # Check both parameter and effective type
            and rkhunter_settings.get("enabled", False)
            and rkhunter_settings.get("run_with_quick_scan", False)
            and self._rkhunter_available()
        )

        should_run_rkhunter_custom = (
            effective_scan_type == "CUSTOM"
            and rkhunter_settings.get("enabled", False)
            and rkhunter_settings.get("run_with_custom_scan", False)
            and self._rkhunter_available()
        )

        should_run_rkhunter = should_run_rkhunter_full or should_run_rkhunter_quick or should_run_rkhunter_custom

        # Don't display the initial scan message yet - wait for user decision on RKHunter
        # We'll display it after the dialog choices

        if should_run_rkhunter_full and effective_scan_type == "FULL":
            # Display initial scan info before showing dialog
            self._append_with_autoscroll(f"🔍 <b>Starting {effective_scan_type.lower()} scan...</b>")
            self._append_with_autoscroll("")  # Add spacing
            self._append_with_autoscroll(f"📁 <b>Target:</b> {self.format_target_display(self.scan_path)}")
            self._append_with_autoscroll("")  # Add spacing
            if scan_options:
                friendly_options = self.format_scan_options_user_friendly(scan_options)
                self._append_with_autoscroll("⚙️ <b>Options:</b>")
                self._append_with_autoscroll(friendly_options)
            else:
                self._append_with_autoscroll("⚙️ <b>Options:</b> Default settings")
            self._append_with_autoscroll("")  # Add spacing after options
            
            # Show confirmation for combined scan
            reply = self.show_themed_message_box(
                "question",
                "Combined Security Scan",
                "This appears to be a full system scan with RKHunter integration enabled.\n\n"
                "Would you like to run both ClamAV and RKHunter scans together?\n\n"
                "• ClamAV will scan for viruses, malware, and trojans\n"
                "• RKHunter will scan for rootkits and system integrity issues\n\n"
                "This will provide the most comprehensive security analysis.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._append_with_autoscroll("🔒 <b>Enhanced Security Scan</b> - RKHunter + ClamAV")
                self._append_with_autoscroll("")  # Add spacing
                # Start combined scan with RKHunter first
                self.start_combined_security_scan(quick_scan, scan_options)
                return

        elif should_run_rkhunter_quick and (quick_scan or effective_scan_type == "QUICK"):
            # Display initial scan info before showing dialog
            self._append_with_autoscroll(f"🔍 <b>Starting {effective_scan_type.lower()} scan...</b>")
            self._append_with_autoscroll("")  # Add spacing
            self._append_with_autoscroll(f"📁 <b>Target:</b> {self.format_target_display(self.scan_path)}")
            self._append_with_autoscroll("")  # Add spacing
            if scan_options:
                friendly_options = self.format_scan_options_user_friendly(scan_options)
                self._append_with_autoscroll("⚙️ <b>Options:</b>")
                self._append_with_autoscroll(friendly_options)
            else:
                self._append_with_autoscroll("⚙️ <b>Options:</b> Default settings")
            self._append_with_autoscroll("")  # Add spacing after options
            
            # Show confirmation for combined quick scan
            reply = self.show_themed_message_box(
                "question",
                "Enhanced Quick Security Scan",
                "RKHunter integration is enabled for quick scans.\n\n"
                "Would you like to include RKHunter rootkit detection with your quick scan?\n\n"
                "• RKHunter will first check for rootkits and system issues\n"
                "• ClamAV will then perform a quick malware scan\n\n"
                "This will provide enhanced security coverage in your quick scan.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._append_with_autoscroll("🔒 <b>Enhanced Quick Security Scan</b> - RKHunter + ClamAV")
                self._append_with_autoscroll("")  # Add spacing
                # Start combined scan with RKHunter first - determine if this is truly a quick scan
                is_quick_scan = quick_scan or effective_scan_type == "QUICK"
                self.start_combined_security_scan(is_quick_scan, scan_options)
                return
            else:
                # User chose No - just run regular ClamAV scan
                self._append_with_autoscroll("🔍 <b>ClamAV Malware Scan</b>")
                self._append_with_autoscroll("")  # Add spacing

        elif should_run_rkhunter_custom and effective_scan_type == "CUSTOM":
            # Display initial scan info before showing dialog
            self._append_with_autoscroll(f"🔍 <b>Starting {effective_scan_type.lower()} scan...</b>")
            self._append_with_autoscroll("")  # Add spacing
            self._append_with_autoscroll(f"📁 <b>Target:</b> {self.format_target_display(self.scan_path)}")
            self._append_with_autoscroll("")  # Add spacing
            if scan_options:
                friendly_options = self.format_scan_options_user_friendly(scan_options)
                self._append_with_autoscroll("⚙️ <b>Options:</b>")
                self._append_with_autoscroll(friendly_options)
            else:
                self._append_with_autoscroll("⚙️ <b>Options:</b> Default settings")
            self._append_with_autoscroll("")  # Add spacing after options
            
            # Show confirmation for combined custom scan
            reply = self.show_themed_message_box(
                "question",
                "Enhanced Custom Security Scan",
                "RKHunter integration is enabled for custom scans.\n\n"
                "Would you like to include RKHunter rootkit detection with your custom scan?\n\n"
                "• RKHunter will first perform rootkit detection\n"
                "• ClamAV will then scan your selected directory for malware\n\n"
                "This will provide comprehensive security analysis for your custom scan target.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._append_with_autoscroll("🔒 <b>Enhanced Custom Security Scan</b> - RKHunter + ClamAV")
                self._append_with_autoscroll("")  # Add spacing
                # Start combined scan with RKHunter first for custom scan
                self.start_combined_security_scan(False, scan_options)  # Custom scans are not quick scans
                return
            else:
                # User chose No - just run regular ClamAV scan
                self._append_with_autoscroll("🔍 <b>ClamAV Custom Scan</b>")
                self._append_with_autoscroll("")  # Add spacing

        else:
            # No RKHunter integration - display regular scan info
            self._append_with_autoscroll(f"🔍 <b>Starting {effective_scan_type.lower()} scan...</b>")
            self._append_with_autoscroll("")  # Add spacing
            self._append_with_autoscroll(f"📁 <b>Target:</b> {self.format_target_display(self.scan_path)}")
            self._append_with_autoscroll("")  # Add spacing
            if scan_options:
                friendly_options = self.format_scan_options_user_friendly(scan_options)
                self._append_with_autoscroll("⚙️ <b>Options:</b>")
                self._append_with_autoscroll(friendly_options)
            else:
                self._append_with_autoscroll("⚙️ <b>Options:</b> Default settings")
            self._append_with_autoscroll("")  # Add spacing after options

        # Start regular scan in separate thread with enhanced options
        self.current_scan_thread = ScanThread(
            self.scanner, self.scan_path, 
            quick_scan=(effective_scan_type == "QUICK"),
            scan_options=scan_options
        )
        self.current_scan_thread.progress_updated.connect(
            self.progress_bar.setValue)
        self.current_scan_thread.status_updated.connect(
            self.status_label.setText)
        self.current_scan_thread.scan_detail_updated.connect(
            self.handle_detailed_scan_progress)
        self.current_scan_thread.scan_completed.connect(self.scan_completed)
        self.current_scan_thread.start()

    def start_combined_security_scan(self, quick_scan=False, scan_options=None):
        """Start a combined security scan with RKHunter first, then ClamAV."""
        # Check if RKHunter should still run
        if not self._rkhunter_available():
            self.results_text.append("❌ RKHunter not available, falling back to ClamAV only")
            # Fall back to regular ClamAV scan
            self.current_scan_thread = ScanThread(
                self.scanner, self.scan_path, quick_scan=quick_scan, scan_options=scan_options
            )
            self.current_scan_thread.progress_updated.connect(self.progress_bar.setValue)
            self.current_scan_thread.status_updated.connect(self.status_label.setText)
            self.current_scan_thread.scan_detail_updated.connect(
                self.handle_detailed_scan_progress)
            self.current_scan_thread.scan_completed.connect(self.scan_completed)
            self.current_scan_thread.start()
            return

        # Start RKHunter scan first
        self.status_label.setText("RKHunter scan starting...")
        
        # Add message for combined scans
        self.results_text.append("\n🔍 Starting RKHunter scan (part of combined security scan)...")
        
        # Update button state to show scan is running
        self.update_scan_button_state(True)

        # Get test categories from settings
        test_categories = self.get_selected_rkhunter_categories()

        self.current_rkhunter_thread = RKHunterScanThread(
            self.rkhunter, test_categories
        )
        self.current_rkhunter_thread.progress_updated.connect(
            self.update_rkhunter_progress
        )
        self.current_rkhunter_thread.progress_value_updated.connect(
            self.progress_bar.setValue
        )
        self.current_rkhunter_thread.output_updated.connect(
            self.update_rkhunter_output
        )
        # Store the scan parameters for the next phase
        self._pending_clamav_scan = {"quick_scan": quick_scan, "scan_options": scan_options}
        # Ensure no leftover signal connections from other scan types
        try:
            self.current_rkhunter_thread.scan_completed.disconnect()
        except:
            pass  # No connections to disconnect
        self.current_rkhunter_thread.scan_completed.connect(
            self.rkhunter_scan_completed_start_clamav
        )
        self.current_rkhunter_thread.start()

    def rkhunter_scan_completed_start_clamav(self, rkhunter_result):
        """Handle RKHunter scan completion and start ClamAV scan."""
        # Display RKHunter results first
        self.display_rkhunter_results(rkhunter_result)

        # Add separator
        self.results_text.append("\n" + "=" * 45 + "\n")

        # Retrieve the stored scan parameters
        clamav_params = getattr(self, '_pending_clamav_scan', {"quick_scan": False, "scan_options": None})
        quick_scan = clamav_params.get("quick_scan", False)
        scan_options = clamav_params.get("scan_options", None)

        # Start ClamAV scan automatically
        self.status_label.setText("ClamAV scan starting...")

        self.current_scan_thread = ScanThread(
            self.scanner, self.scan_path, quick_scan=quick_scan, scan_options=scan_options
        )
        self.current_scan_thread.progress_updated.connect(
            self.progress_bar.setValue)
        self.current_scan_thread.status_updated.connect(
            self.status_label.setText)
        self.current_scan_thread.scan_detail_updated.connect(
            self.handle_detailed_scan_progress)
        self.current_scan_thread.scan_completed.connect(
            lambda clamav_result: self.combined_scan_completed_rkhunter_first(
                rkhunter_result, clamav_result))
        self.current_scan_thread.start()

    def combined_scan_completed_rkhunter_first(
        self, rkhunter_result: RKHunterScanResult, clamav_result
    ):
        """Handle completion of combined RKHunter + ClamAV scan (RKHunter first)."""
        # Display ClamAV results
        self.display_scan_results(clamav_result)

        # Save both reports
        self.save_rkhunter_report(rkhunter_result)

        # Create combined summary
        self.results_text.append("\n" + "=" * 45)
        self.results_text.append("\n🔒 COMPREHENSIVE SECURITY SCAN SUMMARY")
        self.results_text.append("=" * 45)

        # RKHunter summary (ran first)
        self.results_text.append(f"\n🔍 RKHunter Results (Rootkit Detection):")
        self.results_text.append(
            f"   • Warnings: {rkhunter_result.warnings_found}")
        self.results_text.append(
            f"   • Infections: {rkhunter_result.infections_found}")

        # ClamAV summary (ran second)
        clamav_threats = 0
        if isinstance(clamav_result, dict):
            clamav_threats = clamav_result.get(
                "threats_found", len(clamav_result.get("threats", []))
            )
        else:
            clamav_threats = getattr(clamav_result, "threats_found", 0)

        self.results_text.append(f"\n📊 ClamAV Results (Malware Detection):")
        self.results_text.append(f"   • Threats Found: {clamav_threats}")

        # Overall assessment
        total_issues = (
            clamav_threats
            + rkhunter_result.warnings_found
            + rkhunter_result.infections_found
        )

        if total_issues == 0:
            self.results_text.append(f"\n✅ **SYSTEM CLEAN**")
            self.results_text.append(
                "   No threats or suspicious activity detected.")
        elif rkhunter_result.infections_found > 0:
            self.results_text.append(
                f"\n🚨 **CRITICAL SECURITY ISSUES DETECTED**")
            self.results_text.append(
                "   Potential rootkits found - immediate action required!"
            )
        elif clamav_threats > 0 or rkhunter_result.warnings_found > 0:
            self.results_text.append(f"\n⚠️  **SECURITY ISSUES DETECTED**")
            self.results_text.append(
                "   Review findings and take appropriate action.")

        self.results_text.append("\n" + "=" * 45)
        
        # Add reminder for future combined scans
        self.results_text.append("\n💡 Security Scan Tips:")
        self.results_text.append("   • Combined scans provide comprehensive protection")
        self.results_text.append("   • RKHunter (rootkit detection) runs first, then ClamAV (malware detection)")
        self.results_text.append("   • Regular combined scans help maintain system security")

        # Complete the scan
        self.scan_completed(clamav_result)

        # Clean up the stored parameters
        if hasattr(self, '_pending_clamav_scan'):
            delattr(self, '_pending_clamav_scan')

    def install_rkhunter(self):
        """Install or configure RKHunter."""
        self.rkhunter_scan_btn.setEnabled(False)
        self.rkhunter_scan_btn.setText("Checking...")

        # First check if RKHunter is actually installed but has permission
        # issues
        if self.rkhunter.rkhunter_path and Path(
                self.rkhunter.rkhunter_path).exists():
            # RKHunter is installed but may need configuration
            reply = self.show_themed_message_box(
                "question",
                "RKHunter Configuration",
                "RKHunter is installed but requires elevated privileges to run.\n\n"
                "This is normal for rootkit scanners as they need system-level access.\n"
                "You will be prompted for your password when running scans.\n\n"
                "Continue to enable RKHunter scanning?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Test if it works with sudo
                try:
                    result = subprocess.run(
                        ["sudo", "-v"],  # Validate sudo access
                        capture_output=True,
                        timeout=30,
                    )

                    if result.returncode == 0:
                        self.show_themed_message_box(
                            "information",
                            "RKHunter Ready",
                            "RKHunter is now configured and ready to use!\n\n"
                            "You can run rootkit scans from the scan tab.",
                        )

                        # Update button to scan mode
                        self.rkhunter_scan_btn.setText("🔍 RKHunter Scan")
                        self.rkhunter_scan_btn.setToolTip(
                            "Run RKHunter rootkit detection scan\n(Configure scan categories in Settings → Scanning)"
                        )
                        self.rkhunter_scan_btn.clicked.disconnect()
                        self.rkhunter_scan_btn.clicked.connect(
                            self.start_rkhunter_scan)
                        self.rkhunter_scan_btn.setEnabled(True)
                        return

                except subprocess.SubprocessError:
                    pass

            self.rkhunter_scan_btn.setText("📦 Install RKHunter")
            self.rkhunter_scan_btn.setEnabled(True)
            return

        # Show installation confirmation dialog
        reply = self.show_themed_message_box(
            "question",
            "Install RKHunter",
            "RKHunter will be installed to provide rootkit detection capabilities.\n\n"
            "This requires administrator privileges. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            self.rkhunter_scan_btn.setEnabled(True)
            self.rkhunter_scan_btn.setText("📦 Install RKHunter")
            return

        self.rkhunter_scan_btn.setText("Installing...")

        try:
            success, message = self.rkhunter.install_rkhunter()

            if success:
                self.show_themed_message_box(
                    "information",
                    "Success",
                    f"RKHunter installed successfully!\n{message}",
                )

                # Update button to scan mode
                self.rkhunter_scan_btn.setText("🔍 RKHunter Scan")
                self.rkhunter_scan_btn.setToolTip(
                    "Run RKHunter rootkit detection scan")
                self.rkhunter_scan_btn.clicked.disconnect()
                self.rkhunter_scan_btn.clicked.connect(
                    self.start_rkhunter_scan)
                self.rkhunter_scan_btn.setEnabled(True)

            else:
                self.show_themed_message_box(
                    "critical",
                    "Installation Failed",
                    f"Failed to install RKHunter:\n{message}",
                )
                self.rkhunter_scan_btn.setText("📦 Install RKHunter")
                self.rkhunter_scan_btn.setEnabled(True)

        except Exception as e:
            self.show_themed_message_box(
                "critical",
                "Installation Error",
                f"Error during installation:\n{str(e)}",
            )
            self.rkhunter_scan_btn.setText("📦 Install RKHunter")
            self.rkhunter_scan_btn.setEnabled(True)

    def start_rkhunter_scan(self):
        """Start an RKHunter rootkit scan."""
        # Check if already running
        if (hasattr(self, 'current_rkhunter_thread') and 
            self.current_rkhunter_thread and 
            self.current_rkhunter_thread.isRunning()):
            self.show_themed_message_box(
                "warning",
                "Scan in Progress",
                "RKHunter scan is already running.")
            return

        # Check if RKHunter is functional (this may prompt for permissions)
        if not self.rkhunter.is_functional():
            # Check authentication method available
            pkexec_available = self.rkhunter._find_executable("pkexec")

            if pkexec_available:
                auth_method_text = (
                    "RKHunter requires elevated privileges to perform rootkit scans.\n\n"
                    "This is normal security behavior for rootkit detection tools.\n"
                    "A secure GUI password dialog will appear during the scan (same as Update Definitions).\n\n"
                    "Would you like to:\n\n"
                    "• Continue and start the scan (GUI password dialog will appear)\n"
                    "• Configure RKHunter setup first")
            else:
                auth_method_text = (
                    "RKHunter requires elevated privileges to perform rootkit scans.\n\n"
                    "This is normal security behavior for rootkit detection tools.\n"
                    "You will be prompted for your administrator password in the terminal.\n\n"
                    "Would you like to:\n\n"
                    "• Continue and start the scan (terminal password prompt will appear)\n"
                    "• Configure RKHunter setup first")

            reply = self.show_themed_message_box(
                "question", "RKHunter Setup Required", auth_method_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                self.install_rkhunter()  # Show configuration dialog
                return

        # Check if regular scan is running
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            reply = self.show_themed_message_box(
                "question",
                "Scan in Progress",
                "A regular antivirus scan is currently running.\n\n"
                "Do you want to continue with RKHunter scan in parallel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Get test categories from settings
        test_categories = self.get_selected_rkhunter_categories()

        # Check if GUI authentication is available
        pkexec_available = self.rkhunter._find_executable("pkexec")

        # Build scan categories description for user
        category_names = {
            "system_commands": "System Commands",
            "rootkits": "Rootkits & Trojans",
            "network": "Network Security",
            "system_integrity": "System Integrity",
            "applications": "Applications",
        }

        selected_category_names = [
            category_names.get(cat, cat)
            for cat in test_categories
            if cat in category_names and category_names.get(cat)
        ]
        categories_text = (
            ", ".join(selected_category_names)
            if selected_category_names
            else "Default categories"
        )

        if pkexec_available:
            auth_message = (
                f"RKHunter will now scan your system for rootkits and malware.\n\n"
                f"Scan categories: {categories_text}\n\n"
                "🔐 A secure password dialog will appear to authorize the scan. "
                "This uses the same authentication method as 'Update Definitions'.\n\n"
                "The scan may take several minutes to complete."
            )
        else:
            auth_message = (
                f"RKHunter will now scan your system for rootkits and malware.\n\n"
                f"Scan categories: {categories_text}\n\n"
                "🔐 You may be prompted for your administrator password in the terminal "
                "to authorize the scan.\n\n"
                "The scan may take several minutes to complete."
            )

        # Show final confirmation with password warning
        reply = self.show_themed_message_box(
            "question",
            "Authentication Required - Ready to Start RKHunter Scan",
            auth_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Start RKHunter scan in thread
        self.rkhunter_scan_btn.setEnabled(False)
        self.rkhunter_scan_btn.setText("🔄 RKHunter scanning...")
        
        # Update button state to show scan is running
        self.update_scan_button_state(True)
        
        # Reset progress bar for RKHunter scan
        self.progress_bar.setValue(0)
        
        # Reset scan progress tracking state
        self._rkhunter_progress_stage = 0
        self._rkhunter_max_progress = 0
        self._rkhunter_scan_actually_started = False

        self.current_rkhunter_thread = RKHunterScanThread(
            self.rkhunter, test_categories
        )
        self.current_rkhunter_thread.progress_updated.connect(
            self.update_rkhunter_progress
        )
        # Don't connect directly to progress bar - use our handler instead
        self.current_rkhunter_thread.progress_value_updated.connect(
            self.handle_rkhunter_progress_value
        )
        self.current_rkhunter_thread.output_updated.connect(
            self.update_rkhunter_output
        )
        self.current_rkhunter_thread.scan_completed.connect(
            self.rkhunter_scan_completed
        )
        self.current_rkhunter_thread.start()

        # Update status - use a more appropriate initial message
        self.status_label.setText("RKHunter scan starting...")
        self.results_text.append("\n🔍 RKHunter rootkit scan starting - please authenticate when prompted...\n")

    def update_rkhunter_progress(self, message):
        """Update progress display for RKHunter scan."""
        # Only update if we don't have a more specific stage-based message
        # The dynamic progress from _update_rkhunter_progress_from_output takes priority
        current_status = self.status_label.text()
        
        # Don't override stage-specific messages with generic ones
        if not any(stage in current_status for stage in [
            "Checking system configuration", "Analyzing file properties", 
            "Scanning for rootkits", "additional rootkit checks",
            "Checking filesystem", "Scanning for malware", "Checking network",
            "Analyzing applications", "Generating system summary", "Verifying user account",
            "Checking SSH", "Scanning for hidden"
        ]):
            self.status_label.setText(f"🔍 {message}")

    def handle_rkhunter_progress_value(self, value):
        """Handle progress value updates from RKHunter thread."""
        # Only update progress bar if scan has actually started
        # This prevents progress updates during authentication phase
        if hasattr(self, '_rkhunter_scan_actually_started') and self._rkhunter_scan_actually_started:
            # Only allow progress to increase, never decrease
            if value > self.progress_bar.value():
                self.progress_bar.setValue(value)
        # If scan hasn't started yet, keep progress at 0
        elif not hasattr(self, '_rkhunter_scan_actually_started') or not self._rkhunter_scan_actually_started:
            self.progress_bar.setValue(0)

    def handle_detailed_scan_progress(self, detail_info):
        """Handle detailed scan progress updates for ClamAV scans."""
        try:
            if detail_info.get("type") == "file_scanned":
                current_dir = detail_info.get("current_directory", "")
                current_file = detail_info.get("current_file", "")
                scan_result = detail_info.get("scan_result", "clean")
                files_completed = detail_info.get("files_completed", 0)
                files_remaining = detail_info.get("files_remaining", 0)
                total_files = detail_info.get("total_files", 0)
                
                # Track actual files processed for statistics correction
                if not hasattr(self, '_scan_files_actually_processed'):
                    self._scan_files_actually_processed = 0
                self._scan_files_actually_processed = files_completed
                
                # Initialize or get existing directory information
                if not hasattr(self, '_scan_directories_info'):
                    self._scan_directories_info = {}
                    self._last_displayed_directory = None
                    self._scanned_directories = []  # Use list to maintain order
                    self._completed_directories = []  # Track truly completed directories
                
                # Track files by directory
                if current_dir not in self._scan_directories_info:
                    self._scan_directories_info[current_dir] = {
                        "clean_files": [],
                        "infected_files": [],
                        "total_files": 0
                    }
                
                # Check if file has already been displayed (to prevent duplicates)
                file_already_displayed = False
                if scan_result == "clean":
                    if current_file not in self._scan_directories_info[current_dir]["clean_files"]:
                        self._scan_directories_info[current_dir]["clean_files"].append(current_file)
                    else:
                        file_already_displayed = True
                elif scan_result == "infected":
                    if current_file not in self._scan_directories_info[current_dir]["infected_files"]:
                        self._scan_directories_info[current_dir]["infected_files"].append(current_file)
                    else:
                        file_already_displayed = True
                
                # Get the main scan directory for grouping purposes
                main_scan_dir = self._get_main_scan_directory(current_dir)
                
                # Display directory header ONLY when switching to a new MAIN directory
                last_main_dir = self._get_main_scan_directory(self._last_displayed_directory) if self._last_displayed_directory else None
                
                if last_main_dir != main_scan_dir:
                    # Mark previous main directory as completed (if there was one)
                    if last_main_dir and last_main_dir not in self._completed_directories:
                        self._completed_directories.append(last_main_dir)
                    
                    # Add current main directory to scanned list (if not already there)
                    if main_scan_dir not in self._scanned_directories:
                        self._scanned_directories.append(main_scan_dir)
                    
                    # Calculate accurate counts
                    completed_count = len(self._completed_directories)
                    remaining_estimate = self._calculate_remaining_directories(files_remaining, total_files)
                    
                    self._append_with_autoscroll("")  # Add spacing
                    short_dir = main_scan_dir.replace(str(Path.home()), "~") if str(Path.home()) in main_scan_dir else main_scan_dir
                    self._append_with_autoscroll(f"📁 <b>Scanning Directory:</b> {short_dir}")
                    
                    # Show directory progress info (always show after first directory)
                    if len(self._scanned_directories) > 1:  # Show from second directory onwards
                        self._append_with_autoscroll(f"📊 <i>Directories scanned: {completed_count} | Remaining: {remaining_estimate}</i>")
                    
                    self._last_displayed_directory = current_dir
                
                # Display file only if not already displayed (prevents duplicates)
                if not file_already_displayed:
                    if scan_result == "clean":
                        self._append_with_autoscroll(f"    ✅ {current_file}")
                    elif scan_result == "infected":
                        self.results_text.append(f"    🚨 <span style='color: #F44336;'><b>INFECTED:</b></span> {current_file}")
                
        except Exception as e:
            print(f"Error in detailed scan progress: {e}")
    
    def _calculate_remaining_directories(self, files_remaining, total_files):
        """Calculate remaining directories based on actual scanning patterns."""
        if files_remaining <= 0 or total_files <= 0:
            return 0
        
        if not hasattr(self, '_completed_directories') or not self._completed_directories:
            # For early estimation, use a conservative approach
            if files_remaining > 0 and total_files > 0:
                # Estimate based on typical directory sizes (conservative estimate)
                avg_files_per_dir = 20  # Conservative assumption
                return max(1, min(10, int(files_remaining / avg_files_per_dir)))
            return 0
        
        # Calculate based on completed directories
        completed_count = len(self._completed_directories)
        files_scanned = total_files - files_remaining
        
        if completed_count > 0 and files_scanned > 0:
            # Get average files per completed directory
            avg_files_per_dir = files_scanned / (completed_count + 1)  # +1 for current directory
            if avg_files_per_dir > 0:
                estimated = int(files_remaining / avg_files_per_dir)
                # Apply reasonable bounds
                return max(0, min(estimated, completed_count * 2))  # Cap at 2x completed directories
        
        return 0

    def _get_main_scan_directory(self, directory_path):
        """Get the main scan directory for a given path to group subdirectories."""
        if not directory_path:
            return ""
        
        # Convert to Path object for easier handling
        path = Path(directory_path)
        home_path = Path.home()
        
        # Define main directories to group by
        main_directories = [
            "Downloads", "Documents", "Pictures", "Videos", "Music", 
            "Desktop", "Public", "Templates", "tmp", "temp"
        ]
        
        # Check if this is under home directory
        if str(home_path) in str(path):
            # Get relative path from home
            try:
                rel_path = path.relative_to(home_path)
                parts = rel_path.parts
                
                # Check if first part matches main directories
                if parts and parts[0] in main_directories:
                    return str(home_path / parts[0])
                
                # Check for browser data directories
                if len(parts) >= 2:
                    if parts[0] == ".config" and any(browser in parts[1] for browser in ["google-chrome", "firefox", "chromium"]):
                        return str(home_path / parts[0] / parts[1])
                    elif parts[0] == ".mozilla" and "firefox" in str(rel_path):
                        return str(home_path / ".mozilla" / "firefox")
                    elif parts[0] == ".cache" and any(browser in parts[1] for browser in ["google-chrome", "firefox", "chromium"]):
                        return str(home_path / ".cache" / parts[1])
                
            except ValueError:
                pass
        
        # Check for system temp directories
        if "/tmp" in str(path) or "/var/tmp" in str(path):
            if "/tmp" in str(path):
                return "/tmp"
            else:
                return "/var/tmp"
        
        # Default: return the directory as-is if we can't group it
        return directory_path

    def _on_scroll_changed(self, value):
        """Track when user manually scrolls to disable auto-scrolling."""
        scrollbar = self.results_text.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # If user scrolls up from the bottom, disable auto-scroll
        if value < max_value and value != self._last_scroll_position:
            # Check if this is a user-initiated scroll (not programmatic)
            if abs(value - self._last_scroll_position) > 1:  # Threshold to ignore minor adjustments
                self._user_has_scrolled = True
        
        # If user scrolls back to bottom, re-enable auto-scroll
        if value == max_value:
            self._user_has_scrolled = False
            
        self._last_scroll_position = value

    def _append_with_autoscroll(self, text):
        """Append text to results with intelligent autoscroll behavior."""
        # Add the text
        self.results_text.append(text)
        
        # Auto-scroll to bottom unless user has manually scrolled up
        if not self._user_has_scrolled:
            scrollbar = self.results_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def update_rkhunter_output(self, output_line):
        """Update the results text with real-time RKHunter output."""
        if not output_line.strip():  # Skip empty lines
            return
            
        # Filter out common noise/warnings that don't add value
        line_lower = output_line.lower()
        
        # Skip common grep warnings and noise
        if any(skip_phrase in line_lower for skip_phrase in [
            "grep: warning: stray",
            "egrep: warning: egrep is obsolescent", 
            "invalid scriptdir configuration",
            "sudo: a terminal is required",
            "sudo: a password is required",
            "info: starting",
            "info: checking",
            "info: end of",
            "starting rkhunter update and scan sequence",
            "starting rkhunter scan...",
            "updating rkhunter database..."
        ]):
            return  # Don't display these lines
        
        # Clean and format the output line
        formatted_line = output_line.strip()
        
        # Fix missing emoji characters and clean up the text
        if "�" in formatted_line:
            # Replace missing emoji characters with appropriate ones based on content
            if "Starting RKHunter update" in formatted_line or "update.*sequence" in formatted_line.lower():
                formatted_line = formatted_line.replace("�", "🔄")
            elif "Database update completed" in formatted_line or "update completed" in formatted_line.lower():
                formatted_line = formatted_line.replace("�", "✅")
            elif "Starting RKHunter scan" in formatted_line:
                formatted_line = formatted_line.replace("�", "🔍")
            elif "Updating RKHunter database" in formatted_line:
                formatted_line = formatted_line.replace("�", "📦")
            else:
                # Generic replacement for other missing emojis
                formatted_line = formatted_line.replace("�", "ℹ️")
        
        # Enhanced formatting with better structure and visual clarity
        try:
            # Update progress based on actual scan stages
            self._update_rkhunter_progress_from_output(formatted_line)
            
            # Handle timestamped messages with special formatting
            if "[" in formatted_line and "]" in formatted_line and "2025-" in formatted_line:
                # Extract timestamp and message
                parts = formatted_line.split("]", 1)
                if len(parts) == 2:
                    timestamp = parts[0] + "]"
                    message = parts[1].strip()
                    
                    # Only show essential timestamped messages
                    if "Database update completed" in message or "completed successfully" in message:
                        self._append_with_autoscroll(f"✅ <span style='color: #4CAF50;'><b>Database updated successfully</b></span>")
                        return
                    # Skip other timestamped messages to reduce clutter
                    return
            
            # Handle section headers and major operations
            if formatted_line.startswith("Performing") or formatted_line.startswith("Starting"):
                self._append_with_autoscroll("")  # Add spacing before new sections
                self._append_with_autoscroll(f"📋 <b>{formatted_line}</b>")
                self._append_with_autoscroll("─" * 50)
                return
            
            # Handle system summary sections with better formatting
            if (formatted_line == "System checks summary" or 
                formatted_line == "=" * len(formatted_line)):  # Handle separator lines
                if formatted_line == "System checks summary":
                    self._append_with_autoscroll("")  # Add spacing
                    self._append_with_autoscroll(f"📊 <b>System Checks Summary</b>")
                    self._append_with_autoscroll("─" * 40)
                return
            
            # Handle scan statistics with proper icons and formatting
            if any(stat in formatted_line for stat in [
                "File properties checks", "Files checked:", "Suspect files:",
                "Rootkit checks", "Rootkits checked", "Possible rootkits:",
                "Applications checks", "All checks skipped",
                "The system checks took:"
            ]):
                if "File properties checks" in formatted_line:
                    self._append_with_autoscroll(f"  📂 <b>File Analysis:</b>")
                elif "Files checked:" in formatted_line:
                    count = formatted_line.split(":")[-1].strip()
                    self._append_with_autoscroll(f"    📄 Files scanned: <b>{count}</b>")
                elif "Suspect files:" in formatted_line:
                    count = formatted_line.split(":")[-1].strip()
                    color = "#F44336" if int(count) > 0 else "#4CAF50"
                    self._append_with_autoscroll(f"    🔍 Suspicious files: <span style='color: {color};'><b>{count}</b></span>")
                elif "Rootkit checks" in formatted_line:
                    self._append_with_autoscroll(f"  🛡️  <b>Rootkit Detection:</b>")
                elif "Rootkits checked" in formatted_line:
                    count = formatted_line.split(":")[-1].strip()
                    self.results_text.append(f"    📊 Rootkits checked: <b>{count}</b>")
                elif "Possible rootkits:" in formatted_line:
                    count = formatted_line.split(":")[-1].strip()
                    color = "#F44336" if int(count) > 0 else "#4CAF50"
                    self.results_text.append(f"    🚨 Possible rootkits: <span style='color: {color};'><b>{count}</b></span>")
                elif "Applications checks" in formatted_line:
                    self.results_text.append(f"  📱 <b>Application Checks:</b>")
                elif "All checks skipped" in formatted_line:
                    self.results_text.append(f"    ⏭️  <span style='color: #9E9E9E;'><i>All checks skipped</i></span>")
                elif "The system checks took:" in formatted_line:
                    duration = formatted_line.split(":")[-1].strip()
                    self.results_text.append("")  # Add spacing
                    self.results_text.append(f"  ⏱️  <b>Scan Duration:</b> {duration}")
                return
            
            # Handle log file references with better formatting
            if "written to the log file:" in formatted_line or "check the log file" in formatted_line:
                if "written to the log file:" in formatted_line:
                    self.results_text.append(f"  📝 <i>Results saved to system log</i>")
                elif "check the log file" in formatted_line:
                    self.results_text.append(f"  📋 <i>Check system log for details</i>")
                return
                
            # Handle check results with clear status indicators
            if "[ " in formatted_line and " ]" in formatted_line:
                # Extract the check description and result
                parts = formatted_line.split("[")
                if len(parts) >= 2:
                    check_desc = parts[0].strip()
                    result_part = "[" + parts[1]
                    
                    # Clean up the check description
                    if check_desc.startswith("Checking"):
                        check_desc = check_desc[8:].strip()  # Remove "Checking" prefix
                    
                    # Format based on result type
                    if "[ None found ]" in result_part or "[ OK ]" in result_part:
                        self.results_text.append(f"  ✅ {check_desc} <span style='color: #4CAF50;'><b>CLEAN</b></span>")
                    elif "[ Found ]" in result_part:
                        self.results_text.append(f"  🔍 {check_desc} <span style='color: #FF9800;'><b>FOUND</b></span>")
                    elif "[ Warning ]" in result_part or "[ WARN ]" in result_part:
                        self.results_text.append(f"  ⚠️  {check_desc} <span style='color: #FF9800;'><b>WARNING</b></span>")
                    elif "[ Not found ]" in result_part:
                        self.results_text.append(f"  ✅ {check_desc} <span style='color: #4CAF50;'><b>NOT FOUND</b></span>")
                    elif "[ Skipped ]" in result_part:
                        self.results_text.append(f"  ⏭️  {check_desc} <span style='color: #9E9E9E;'><i>SKIPPED</i></span>")
                    else:
                        # Generic result formatting
                        result_clean = result_part.replace("[", "").replace("]", "").strip()
                        self.results_text.append(f"  🔍 {check_desc} <span style='color: #2196F3;'><b>{result_clean}</b></span>")
                    return
            
            # Handle specific types of messages with enhanced formatting
            if "WARNING" in formatted_line.upper() and ":" in formatted_line:
                warning_text = formatted_line.split(":", 1)[-1].strip()
                self.results_text.append("")  # Add spacing before warnings
                self.results_text.append(f"⚠️  <span style='color: #FF9800;'><b>WARNING:</b></span> {warning_text}")
                return
            elif "ERROR" in formatted_line.upper():
                self.results_text.append(f"  ❌ <span style='color: #F44336;'><b>ERROR:</b></span> {formatted_line.replace('ERROR:', '').strip()}")
            elif ("INFECTED" in formatted_line.upper() or 
                  ("ROOTKIT" in formatted_line.upper() and 
                   not formatted_line.lower().startswith("checking") and
                   ("found" in formatted_line.lower() or "detected" in formatted_line.lower() or "positive" in formatted_line.lower()))):
                # Only show threat detected for actual detections, not status messages
                self.results_text.append(f"  🚨 <span style='color: #F44336;'><b>THREAT DETECTED:</b></span> {formatted_line}")
            elif "INFO:" in formatted_line.upper():
                info_msg = formatted_line.replace("INFO:", "").strip()
                if info_msg:  # Only show if there's actual content
                    self.results_text.append(f"  ℹ️  <span style='color: #2196F3;'>{info_msg}</span>")
            elif formatted_line.startswith("Checking"):
                # Format ongoing checks with a more subtle appearance
                check_item = formatted_line.replace("Checking", "").strip()
                self.results_text.append(f"  🔄 <i>Checking {check_item}...</i>")
            elif "scan completed" in formatted_line.lower():
                self.results_text.append("")  # Add spacing
                self.results_text.append(f"🏁 <b>{formatted_line}</b>")
                self.results_text.append("")  # Add spacing
            else:
                # Skip very generic or repetitive lines
                if formatted_line and not formatted_line.isspace():
                    # Don't show generic lines that don't add value
                    skip_lines = [
                        "please check the log file",
                        "all results have been written"
                    ]
                    if not any(skip in formatted_line.lower() for skip in skip_lines):
                        # Only show if it contains useful information
                        if len(formatted_line.strip()) > 3:  # Avoid very short meaningless lines
                            self.results_text.append(f"  ℹ️ {formatted_line}")
                    
        except Exception as e:
            # Fallback to basic formatting if parsing fails
            self.results_text.append(formatted_line)
        
        # Auto-scroll to bottom to show latest output
        scrollbar = self.results_text.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def _update_rkhunter_progress_from_output(self, formatted_line):
        """Update RKHunter scan progress based on actual scan output."""
        try:
            # Initialize progress tracking if it doesn't exist
            if not hasattr(self, '_rkhunter_progress_stage'):
                self._rkhunter_progress_stage = 0
                self._rkhunter_max_progress = 0
                self._rkhunter_scan_actually_started = False
            
            # Don't track progress until we know the scan has actually started
            # Look for indicators that the scan is really running
            if not self._rkhunter_scan_actually_started:
                # Only start tracking progress after we see clear scan start indicators
                # Use the same indicators as the thread for consistency
                scan_start_indicators = [
                    "Rootkit Hunter version",
                    "Starting to create file hashes",
                    "Please wait while the file hash values are"
                ]
                
                if any(indicator in formatted_line for indicator in scan_start_indicators):
                    self._rkhunter_scan_actually_started = True
                    self._rkhunter_max_progress = 0  # Reset to ensure clean start
                    
                    # Notify user that scan has started
                    self.results_text.append("✅ RKHunter scan started successfully\n")
                else:
                    # Scan hasn't started yet, don't update progress
                    return
            
            # Define scan stages in the EXACT order they occur based on actual scan log
            # Use more specific matching to avoid conflicts between similar stage names
            stage_map = {
                # Initial system checks (5-20%) - Use exact matches to avoid conflicts
                "Performing 'strings' command checks": (5, "🔤 Checking system commands..."),
                "Performing 'shared libraries' checks": (10, "📚 Analyzing shared libraries..."),
                "Performing file properties checks": (15, "📄 Analyzing file properties..."),
                
                # Rootkit detection (20-40%) - Use more specific terms to avoid conflicts
                "Performing check of known rootkit files and directories": (25, "🛡️ Scanning for known rootkits..."),
                "Performing additional rootkit checks": (35, "🔍 Performing additional rootkit checks..."),
                
                # Security and malware checks (40-60%)
                "Performing malware checks": (45, "🦠 Scanning for malware..."),
                "Performing Linux specific checks": (55, "🐧 Running Linux-specific checks..."),
                
                # Network and system checks (60-85%)
                "Performing checks on the network ports": (65, "🌐 Checking network ports..."),
                "Performing checks on the network interfaces": (70, "📡 Checking network interfaces..."),
                "Performing system boot checks": (75, "🚀 Checking system boot configuration..."),
                "Performing group and account checks": (80, "👥 Analyzing user accounts..."),
                "Performing system configuration file checks": (85, "⚙️ Checking system configuration..."),
                "Performing filesystem checks": (90, "💽 Checking filesystem integrity..."),
                
                # Final summary (95%)
                "System checks summary": (95, "📊 Generating scan summary..."),
            }
            
            # Sort stages by progress value to check most specific/highest progress first
            # This prevents lower progress stages from overriding higher ones
            sorted_stages = sorted(stage_map.items(), key=lambda x: x[1][0], reverse=True)
            
            # Check for major stage changes - use exact matching and check highest progress first
            for stage_text, (progress, description) in sorted_stages:
                # Use exact match or very specific substring to avoid conflicts
                stage_found = False
                
                # For exact stage names, require exact match and additional validation
                if stage_text in formatted_line:
                    # Additional validation to ensure we have the right stage
                    if stage_text == "Performing 'strings' command checks":
                        # Only match if it's specifically about strings command checks
                        if "'strings'" in formatted_line and "command" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing 'shared libraries' checks":
                        # Only match if it's specifically about shared libraries
                        if "'shared libraries'" in formatted_line or "shared libraries" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing file properties checks":
                        # Only match if it's specifically about file properties
                        if "file properties" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing check of known rootkit files and directories":
                        # Only match if it's specifically about known rootkit files
                        if "known rootkit files" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing additional rootkit checks":
                        # Only match if it's specifically about additional rootkit checks
                        if "additional rootkit" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing malware checks":
                        # Only match if it's specifically about malware
                        if "malware" in formatted_line.lower() and "additional" not in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing Linux specific checks":
                        # Only match if it's specifically about Linux checks
                        if "linux specific" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing checks on the network ports":
                        if "network ports" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing checks on the network interfaces":
                        if "network interfaces" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing system boot checks":
                        if "system boot" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing group and account checks":
                        if "group and account" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing system configuration file checks":
                        if "system configuration file" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "Performing filesystem checks":
                        if "filesystem" in formatted_line.lower():
                            stage_found = True
                    elif stage_text == "System checks summary":
                        if "system checks summary" in formatted_line.lower():
                            stage_found = True
                    else:
                        # For any other stages, exact match is sufficient
                        stage_found = True
                
                if stage_found:
                    # Only advance progress, never go backwards
                    if progress > self._rkhunter_max_progress:
                        self._rkhunter_max_progress = progress
                        self.status_label.setText(description)
                        self.progress_bar.setValue(progress)
                    return  # Exit after first match to avoid conflicts
            
            # Handle scan completion
            if "scan completed" in formatted_line.lower() or "The system checks took:" in formatted_line or "Scan Duration:" in formatted_line:
                if self._rkhunter_max_progress < 100:
                    self._rkhunter_max_progress = 100
                    self.status_label.setText("✅ Scan completed successfully!")
                    self.progress_bar.setValue(100)
                return
            
            # Handle specific detailed checks for smoother progress
            # SSH configuration checks (within system config stage)
            if "if SSH root access is allowed" in formatted_line or "if SSH protocol v1 is allowed" in formatted_line:
                if self._rkhunter_max_progress >= 85 and self._rkhunter_max_progress < 87:
                    self._rkhunter_max_progress = 87
                    self.status_label.setText("🔒 Checking SSH security settings...")
                    self.progress_bar.setValue(87)
                return
            
            # Hidden files check (within filesystem stage)
            if "for hidden files and directories" in formatted_line:
                if self._rkhunter_max_progress >= 90 and self._rkhunter_max_progress < 93:
                    self._rkhunter_max_progress = 93
                    self.status_label.setText("RKHunter scan in progress...")
                    self.progress_bar.setValue(93)
                return
            
            # Account security checks (within group/account stage)
            if any(check in formatted_line for check in [
                "for passwd file changes",
                "for group file changes",
                "for root equivalent"
            ]):
                if self._rkhunter_max_progress >= 80 and self._rkhunter_max_progress < 83:
                    self._rkhunter_max_progress = 83
                    self.status_label.setText("🔐 Verifying account security...")
                    self.progress_bar.setValue(83)
                return
                        
        except Exception as e:
            # Don't break the scan if progress update fails
            pass

    def rkhunter_scan_completed(self, result: RKHunterScanResult):
        """Handle completion of RKHunter scan."""
        self.rkhunter_scan_btn.setEnabled(True)
        self.rkhunter_scan_btn.setText("🔍 RKHunter Scan")
        
        # Reset button state if this was a standalone RKHunter scan
        # (for combined scans, button state will be managed by ClamAV completion)
        if not (self.current_scan_thread and self.current_scan_thread.isRunning()):
            self.update_scan_button_state(False)
        
        # Reset progress bar
        self.progress_bar.setValue(100 if result.success else 0)

        if not result.success:
            self.results_text.append(
                f"❌ RKHunter scan failed: {
                    result.error_message}")
            self.status_label.setText("RKHunter scan failed")
            return

        # Display results
        self.display_rkhunter_results(result)

        # Save results to report
        self.save_rkhunter_report(result)

        # Set completion status message
        if result.infections_found > 0:
            self.status_label.setText(f"✅ RKHunter scan completed - {result.infections_found} infections found")
        elif result.warnings_found > 0:
            self.status_label.setText(f"✅ RKHunter scan completed - {result.warnings_found} warnings found")
        else:
            self.status_label.setText("✅ RKHunter scan completed successfully")
        
        # Add scan completion info
        self.results_text.append("\n💡 Tip: Regular RKHunter scans help maintain system security.\n")

    def display_rkhunter_results(self, result: RKHunterScanResult):
        """Display comprehensive RKHunter scan results in the results text area."""
        # Create a separator for multiple scans
        if self.results_text.toPlainText().strip():
            self.results_text.append("\n" + "="*60 + "\n")
        
        # Header with scan completion status
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = (
            (result.end_time - result.start_time).total_seconds()
            if result.end_time
            else 0
        )
        
        # Format duration nicely
        if duration < 60:
            formatted_time = f"{duration:.1f} seconds"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            formatted_time = f"{minutes}m {seconds:.1f}s"
        
        # Determine scan status and icon
        if result.infections_found > 0:
            self.results_text.append(f"🚨 RKHUNTER SCAN COMPLETED - {result.infections_found} INFECTIONS FOUND")
            status_icon = "🚨"
        elif result.warnings_found > 0:
            self.results_text.append(f"⚠️  RKHUNTER SCAN COMPLETED - {result.warnings_found} WARNINGS FOUND")
            status_icon = "⚠️"
        else:
            self.results_text.append("✅ RKHUNTER SCAN COMPLETED - NO THREATS FOUND")
            status_icon = "✅"
        
        self.results_text.append(f"📅 Completed at: {timestamp}")
        self.results_text.append("")

        # Scan details section
        self.results_text.append("📊 SCAN DETAILS:")
        self.results_text.append(f"   🔍 Type: RKHunter Rootkit Detection")
        self.results_text.append(f"   📈 Tests run: {result.tests_run}")
        self.results_text.append(f"   ⏱️  Duration: {formatted_time}")
        self.results_text.append(f"   🔧 Scan ID: {result.scan_id}")
        self.results_text.append("")

        # Results summary section
        self.results_text.append("📋 SCAN SUMMARY:")
        self.results_text.append(f"   🚨 Infections found: {result.infections_found}")
        self.results_text.append(f"   ⚠️  Warnings found: {result.warnings_found}")
        self.results_text.append(f"   ⏭️  Tests skipped: {result.skipped_tests}")
        self.results_text.append("")

        # Overall status assessment
        if result.infections_found > 0:
            self.results_text.append("🚨 CRITICAL SECURITY ALERT:")
            self.results_text.append("   Potential rootkits or malware detected!")
            self.results_text.append("   Immediate action required to secure your system.")
            self.results_text.append("")
        elif result.warnings_found > 0:
            self.results_text.append("⚠️  ATTENTION REQUIRED:")
            self.results_text.append("   System configuration issues detected.")
            self.results_text.append("   Review warnings carefully for security implications.")
            self.results_text.append("")
        else:
            self.results_text.append("✅ SYSTEM STATUS: CLEAN")
            self.results_text.append("   No rootkits or suspicious activity detected.")
            self.results_text.append("   Your system appears secure.")
            self.results_text.append("")

        # Detailed findings section
        if result.findings:
            # Group findings by severity
            infections = [f for f in result.findings if f.result.value == "infection"]
            warnings = [f for f in result.findings if f.result.value == "warning"]
            clean = [f for f in result.findings if f.result.value == "clean"]
            
            if infections:
                self.results_text.append(f"🚨 INFECTIONS DETECTED ({len(infections)}):")
                for i, finding in enumerate(infections[:10], 1):  # Show first 10
                    self.results_text.append(f"   {i}. {finding.test_name}")
                    if hasattr(finding, 'details') and finding.details:
                        self.results_text.append(f"      ℹ️ Details: {finding.details}")
                    if hasattr(finding, 'file_path') and finding.file_path:
                        display_path = self.format_target_display(finding.file_path)
                        self.results_text.append(f"      📁 Location: {display_path}")
                if len(infections) > 10:
                    self.results_text.append(f"   ... and {len(infections)-10} more infections")
                self.results_text.append("")
            
            if warnings:
                self.results_text.append(f"⚠️  WARNINGS DETECTED ({len(warnings)}):")
                for i, finding in enumerate(warnings[:10], 1):  # Show first 10
                    self.results_text.append(f"   {i}. {finding.test_name}")
                    if hasattr(finding, 'details') and finding.details:
                        self.results_text.append(f"      📄 Details: {finding.details}")
                if len(warnings) > 10:
                    self.results_text.append(f"   ... and {len(warnings)-10} more warnings")
                self.results_text.append("")
                
                # Store findings for explanation button
                self._current_rkhunter_findings = result.findings
                
                self.results_text.append("📖 DETAILED EXPLANATIONS AVAILABLE:")
                self.results_text.append("   Use the 'Explain Warnings' button below for")
                self.results_text.append("   detailed analysis and remediation guidance.")
                self.results_text.append("")

        # Recommendations section
        recommendations = self.rkhunter.get_scan_recommendations(result)
        if recommendations:
            self.results_text.append("🔧 RECOMMENDED ACTIONS:")
            for i, rec in enumerate(recommendations, 1):
                self.results_text.append(f"   {i}. {rec}")
            self.results_text.append("")
        elif result.infections_found == 0 and result.warnings_found == 0:
            self.results_text.append("💡 MAINTENANCE RECOMMENDATIONS:")
            self.results_text.append("   • Run regular rootkit scans weekly")
            self.results_text.append("   • Keep system packages updated")
            self.results_text.append("   • Monitor system logs for unusual activity")
            self.results_text.append("   • Enable file integrity monitoring")
            self.results_text.append("")

        # Performance and scan statistics
        if hasattr(result, 'scan_stats') or duration > 0:
            self.results_text.append("📈 SCAN STATISTICS:")
            if duration > 0:
                tests_per_second = result.tests_run / duration if duration > 0 else 0
                self.results_text.append(f"   ⚡ Performance: {tests_per_second:.1f} tests/second")
            if hasattr(result, 'memory_usage'):
                self.results_text.append(f"   💾 Memory usage: {result.memory_usage}")
            self.results_text.append("")

        # Add helpful tip
        self.results_text.append("💡 TIP:")
        self.results_text.append("   Regular RKHunter scans help detect rootkits and system integrity issues.")
        self.results_text.append("   Consider scheduling automated scans for ongoing protection.")
        
        # Add explanation buttons for warnings if any exist
        self._add_warning_explanation_buttons(result)
        
        # Scroll to bottom to show latest results
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)

    def save_rkhunter_report(self, result: RKHunterScanResult):
        """Save RKHunter scan results to a report file."""
        print(f"\n📄 === SAVE RKHUNTER REPORT ===")
        print(f"DEBUG: save_rkhunter_report() called")
        print(f"DEBUG: RKHunter result scan_id: {result.scan_id}")
        print(f"DEBUG: RKHunter result has end_time: {result.end_time is not None}")
        
        try:
            reports_dir = (
                Path.home() /
                ".local/share/search-and-destroy/rkhunter_reports")
            print(f"DEBUG: 📁 RKHunter reports directory: {reports_dir}")
            
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"DEBUG: ✅ RKHunter reports directory created/verified")

            report_file = reports_dir / f"rkhunter_scan_{result.scan_id}.json"
            print(f"DEBUG: 📝 Will save RKHunter report to: {report_file}")

            # Convert result to dictionary for JSON serialization
            print("DEBUG: 🔄 Converting RKHunter result to dictionary")
            report_data = {
                "scan_id": result.scan_id,
                "scan_type": "rkhunter_rootkit_scan",
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration": (
                    (result.end_time - result.start_time).total_seconds()
                    if result.end_time
                    else 0
                ),
                "success": result.success,
                "summary": result.scan_summary,
                "statistics": {
                    "total_tests": result.total_tests,
                    "tests_run": result.tests_run,
                    "warnings_found": result.warnings_found,
                    "infections_found": result.infections_found,
                    "skipped_tests": result.skipped_tests,
                },
                "findings": [
                    {
                        "test_name": finding.test_name,
                        "result": finding.result.value,
                        "severity": finding.severity.value,
                        "description": finding.description,
                        "details": finding.details,
                        "file_path": finding.file_path,
                        "recommendation": finding.recommendation,
                        "timestamp": (
                            finding.timestamp.isoformat() if finding.timestamp else None
                        ),
                    }
                    for finding in (result.findings or [])
                ],
                "recommendations": self.rkhunter.get_scan_recommendations(result),
                "error_message": result.error_message,
            }

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            print(f"RKHunter report saved to {report_file}")

        except Exception as e:
            print(f"Error saving RKHunter report: {e}")

    def _add_warning_explanation_buttons(self, result: RKHunterScanResult):
        """Add a single button to view all warning explanations."""
        # Clear any existing warning buttons
        if hasattr(self, '_warning_buttons_layout'):
            # Remove existing buttons
            while self._warning_buttons_layout.count():
                child = self._warning_buttons_layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
            
        # Only add button if there are warnings
        warnings = [f for f in (result.findings or []) if f.result.value == "warning"]
        if not warnings:
            return
            
        # Find the results text widget's parent layout
        results_text_parent = self.results_text.parent()
        if not hasattr(results_text_parent, 'layout') or not results_text_parent.layout():
            return
            
        results_layout = results_text_parent.layout()
        
        # Create buttons layout if it doesn't exist
        if not hasattr(self, '_warning_buttons_layout'):
            from PyQt6.QtWidgets import QHBoxLayout, QPushButton
            
            self._warning_buttons_layout = QHBoxLayout()
            self._warning_buttons_layout.setObjectName("warningButtonsLayout")
            
            # Single button for all warnings
            warnings_count = len(warnings)
            btn = QPushButton(f"View All Warnings ({warnings_count})")
            btn.setObjectName("viewAllWarnings")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFA500;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background-color: #FF8C00;
                }
                QPushButton:pressed {
                    background-color: #FF7F00;
                }
            """)
            btn.clicked.connect(lambda: self._show_all_warnings_dialog())
            self._warning_buttons_layout.addWidget(btn)
            
            # Add stretch to left-align button
            self._warning_buttons_layout.addStretch()
            
            # Add the button layout to the results layout
            results_layout.addLayout(self._warning_buttons_layout)
        
        # Store current warnings for dialog access
        self._current_warnings = warnings

    def _show_all_warnings_dialog(self):
        """Show a comprehensive dialog with all warning explanations."""
        if not hasattr(self, '_current_warnings') or not self._current_warnings:
            return
            
        # Always use the simpler, more reliable approach for now
        # TODO: Fix complex dialog import/compatibility issues
        self._show_simple_warnings_dialog()
    
    def _show_simple_warnings_dialog(self):
        """Fallback simple warnings dialog using basic Qt widgets."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout
        
        class SimpleWarningsDialog(QDialog):
            def __init__(self, warnings, parent=None):
                super().__init__(parent)
                self.setWindowTitle(f"⚠️ Scan Warnings ({len(warnings)} found)")
                self.setModal(True)
                self.resize(800, 600)
                
                # Apply dialog theme styling
                if parent and hasattr(parent, 'get_theme_color'):
                    bg_color = parent.get_theme_color('background')
                    text_color = parent.get_theme_color('primary_text')
                    self.setStyleSheet(f"""
                        QDialog {{
                            background-color: {bg_color};
                            color: {text_color};
                        }}
                    """)
                
                layout = QVBoxLayout(self)
                
                # Header
                header = QLabel(f"Found {len(warnings)} security warnings that require attention:")
                error_color = parent.get_theme_color('error') if parent and hasattr(parent, 'get_theme_color') else '#F14666'
                header.setStyleSheet(f"font-weight: bold; color: {error_color}; margin-bottom: 10px;")
                layout.addWidget(header)
                
                # Text area with all warnings
                text_area = QTextEdit()
                text_area.setReadOnly(True)
                
                # Apply themed styling
                bg_color = parent.get_theme_color('background') if parent and hasattr(parent, 'get_theme_color') else '#1E1E1E'
                tertiary_bg = parent.get_theme_color('tertiary_bg') if parent and hasattr(parent, 'get_theme_color') else '#3a3a3a'
                text_color = parent.get_theme_color('primary_text') if parent and hasattr(parent, 'get_theme_color') else '#FFFFFF'
                border_color = parent.get_theme_color('border') if parent and hasattr(parent, 'get_theme_color') else '#444444'
                accent_color = parent.get_theme_color('accent') if parent and hasattr(parent, 'get_theme_color') else '#F14666'
                
                text_area.setStyleSheet(f"""
                    QTextEdit {{
                        background-color: {tertiary_bg};
                        color: {text_color};
                        border: 2px solid {border_color};
                        border-radius: 6px;
                        padding: 10px;
                        font-family: 'Courier New', monospace;
                        font-size: 11px;
                        selection-background-color: {accent_color};
                        selection-color: {bg_color};
                    }}
                """)
                
                # Build content
                content = []
                for i, warning in enumerate(warnings):
                    content.append(f"{'='*60}")
                    content.append(f"WARNING #{i+1}")
                    content.append(f"{'='*60}")
                    
                    if hasattr(warning, 'description'):
                        content.append(f"Description: {warning.description}")
                    if hasattr(warning, 'check_name'):
                        content.append(f"Check: {warning.check_name}")
                    if hasattr(warning, 'file_path'):
                        content.append(f"File/Path: {warning.file_path}")
                    
                    content.append("")
                    content.append("RECOMMENDATIONS:")
                    content.append("• Review the warning details carefully")
                    content.append("• Check recent system changes and installations") 
                    content.append("• Verify the legitimacy of any flagged files or processes")
                    content.append("• Consider running additional security scans")
                    content.append("• Consult system logs for related events")
                    content.append("")
                
                text_area.setPlainText("\n".join(content))
                layout.addWidget(text_area)
                
                # Buttons
                button_layout = QHBoxLayout()
                
                close_btn = QPushButton("Close")
                close_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6C757D;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #545B62; }
                """)
                close_btn.clicked.connect(self.accept)
                
                button_layout.addStretch()
                button_layout.addWidget(close_btn)
                layout.addLayout(button_layout)
        
        # Create and show the simple dialog
        dialog = SimpleWarningsDialog(self._current_warnings, parent=self)
        dialog.show()  # Use show() instead of exec() for non-blocking

    def _show_warning_explanation(self, warning_index: int):
        """Show explanation dialog for a specific warning."""
        if not hasattr(self, '_current_warnings') or warning_index >= len(self._current_warnings):
            return
            
        warning = self._current_warnings[warning_index]
        if not warning.explanation:
            # Create a simple message for warnings without detailed explanation
            self.show_themed_message_box(
                "information",
                "Warning Information", 
                f"Warning: {warning.description}\n\n"
                f"This warning indicates a potential security concern that should be investigated. "
                f"Consider checking recent system changes and consulting security documentation."
            )
            return
            
        # Import and show the explanation dialog
        try:
            import sys
            from pathlib import Path
            
            # Add project root to path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from app.gui.warning_explanation_dialog import WarningExplanationDialog
            
            dialog = WarningExplanationDialog(
                warning.description, 
                warning.explanation, 
                parent=self
            )
            
            # Connect signals
            dialog.mark_as_safe.connect(self._mark_warning_as_safe)
            dialog.investigate_requested.connect(self._investigate_warning)
            
            dialog.exec()
            
        except ImportError as e:
            # Fallback to simple message box
            self.show_themed_message_box(
                "information",
                "Warning Explanation",
                f"Warning: {warning.description}\n\n"
                f"Category: {warning.explanation.category.value.replace('_', ' ').title()}\n"
                f"Severity: {warning.explanation.severity.value.upper()}\n\n"
                f"Description: {warning.explanation.description}\n\n"
                f"Likely Cause: {warning.explanation.likely_cause}\n\n"
                f"Recommended Action: {warning.explanation.recommended_action}"
            )
    
    def _mark_warning_as_safe(self, warning_text: str):
        """Mark a warning as safe (placeholder for future implementation)."""
        self.show_themed_message_box(
            "information",
            "Warning Marked as Safe",
            f"Warning marked as safe:\n{warning_text[:100]}...\n\n"
            f"This warning will be hidden in future scans.\n"
            f"(Feature implementation pending)"
        )
    
    def _investigate_warning(self, warning_text: str):
        """Handle investigation request (placeholder for future implementation)."""
        self.show_themed_message_box(
            "information",
            "Investigation Resources",
            f"To investigate this warning:\n\n"
            f"1. Search online for the warning text\n"
            f"2. Check RKHunter documentation\n"
            f"3. Review recent system changes\n"
            f"4. Consult security forums if concerned\n\n"
            f"Warning: {warning_text[:100]}..."
        )

    def get_selected_rkhunter_categories(self):
        """Get list of selected RKHunter test categories from settings."""
        if not hasattr(self, "settings_rkhunter_category_checkboxes"):
            # Return default categories if settings aren't loaded yet
            return [
                "system_commands",
                "rootkits",
                "network",
                "system_integrity"]

        selected = []
        for category_id, checkbox in self.settings_rkhunter_category_checkboxes.items():
            if checkbox.isChecked():
                selected.append(category_id)

        # Return default categories if nothing selected
        return (
            selected
            if selected
            else ["system_commands", "rootkits", "network", "system_integrity"]
        )

    def select_all_rkhunter_categories(self):
        """Select all RKHunter test categories."""
        if hasattr(self, "settings_rkhunter_category_checkboxes"):
            for checkbox in self.settings_rkhunter_category_checkboxes.values():
                checkbox.setChecked(True)

    def select_recommended_rkhunter_categories(self):
        """Select recommended RKHunter test categories."""
        if hasattr(self, "settings_rkhunter_category_checkboxes"):
            recommended = {
                "system_commands",
                "rootkits",
                "network",
                "system_integrity"}
            for (
                category_id,
                checkbox,
            ) in self.settings_rkhunter_category_checkboxes.items():
                checkbox.setChecked(category_id in recommended)

    def select_no_rkhunter_categories(self):
        """Deselect all RKHunter test categories."""
        if hasattr(self, "settings_rkhunter_category_checkboxes"):
            for checkbox in self.settings_rkhunter_category_checkboxes.values():
                checkbox.setChecked(False)

    def apply_rkhunter_category_styling(self, widget):
        """Apply theme-appropriate styling to an RKHunter category widget."""
        bg_color = self.get_theme_color("secondary_bg")
        hover_color = self.get_theme_color("hover_bg")
        border_color = self.get_theme_color("border")
        text_color = self.get_theme_color("text")
        secondary_text_color = self.get_theme_color("secondary_text")
        accent_color = self.get_theme_color("accent")
        
        widget.setStyleSheet(
            f"""
            QWidget {{
                border: 1px solid {border_color};
                border-radius: 8px;
                background-color: {bg_color};
                color: {text_color};
                margin: 2px;
            }}
            QWidget:hover {{
                background-color: {hover_color};
                border-color: {accent_color};
            }}
            QCheckBox {{
                color: {text_color};
                font-weight: bold;
                font-size: 12px;
            }}
            QLabel {{
                color: {secondary_text_color};
            }}
        """
        )

    def update_rkhunter_category_styling(self):
        """Update styling for all RKHunter category widgets when theme changes."""
        if hasattr(self, "settings_rkhunter_category_widgets"):
            for widget in self.settings_rkhunter_category_widgets.values():
                self.apply_rkhunter_category_styling(widget)
    
    def update_dynamic_component_styling(self):
        """Update styling for components that use dynamic colors based on theme."""
        # Update firewall name label if it exists
        if hasattr(self, "firewall_name_label"):
            self.firewall_name_label.setStyleSheet(
                f"font-size: 11px; color: {self.get_theme_color('secondary_text')};"
            )
        
        # Update any other components that need theme refresh
        # Note: Most components are handled by the main setStyleSheet() calls
        # in apply_dark_theme() and apply_light_theme()
    
    def _configure_platform_dropdown_behavior(self):
        """Configure application to prevent popup window issues on Wayland"""
        try:
            # Get Qt application instance
            app = QApplication.instance()
            if app:
                # Set attribute to prevent popup windows for combo boxes
                app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
                
        except Exception as e:
            print(f"Warning: Could not configure platform dropdown behavior: {e}")

    def stop_scan(self):
        print(f"\n🛑 === STOP_SCAN CALLED ===")
        print(f"DEBUG: stop_scan() called")
        print(f"DEBUG: Current scan state: {self._scan_state}")
        print(f"DEBUG: Current scan thread exists: {self.current_scan_thread is not None}")
        print(f"DEBUG: Scan thread running: {self.current_scan_thread.isRunning() if self.current_scan_thread else 'N/A'}")
        print(f"DEBUG: Current RKHunter thread exists: {hasattr(self, 'current_rkhunter_thread') and self.current_rkhunter_thread is not None}")
        print(f"DEBUG: RKHunter thread running: {self.current_rkhunter_thread.isRunning() if hasattr(self, 'current_rkhunter_thread') and self.current_rkhunter_thread else 'N/A'}")
        print(f"DEBUG: Manual stop flag: {self._scan_manually_stopped}")
        
        # Check if any scan threads are running (with safe error handling)
        clamav_running = False
        rkhunter_running = False
        
        try:
            clamav_running = self.current_scan_thread and self.current_scan_thread.isRunning()
        except Exception as e:
            print(f"DEBUG: ⚠️ Error checking ClamAV thread state: {e}")
            # If we can't check state, assume it might be running
            clamav_running = self.current_scan_thread is not None
        
        try:
            rkhunter_running = (hasattr(self, 'current_rkhunter_thread') and 
                              self.current_rkhunter_thread and 
                              self.current_rkhunter_thread.isRunning())
        except Exception as e:
            print(f"DEBUG: ⚠️ Error checking RKHunter thread state: {e}")
            # If we can't check state, assume it might be running
            rkhunter_running = (hasattr(self, 'current_rkhunter_thread') and 
                              self.current_rkhunter_thread is not None)
        
        if clamav_running or rkhunter_running:
            print("DEBUG: 🔍 At least one thread is running, showing confirmation dialog")
            
            # Determine what type of scan is running
            if clamav_running and rkhunter_running:
                scan_type = "combined scan (RKHunter + ClamAV)"
            elif rkhunter_running:
                scan_type = "RKHunter scan"
            else:
                scan_type = "ClamAV scan"
            
            # Show confirmation dialog first
            reply = QMessageBox.question(
                self, "Confirm Stop Scan",
                f"Are you sure you want to stop the current {scan_type}?\n\nNote: The scan may take a few moments to finish safely.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                print("DEBUG: ✅ User confirmed stop")
                # Set stopping state immediately
                self._scan_state = "stopping"
                self._scan_manually_stopped = True
                self.is_quick_scan_running = False
                
                print(f"DEBUG: 🔄 Scan stop requested, state set to: {self._scan_state}")
                print(f"DEBUG: Manual stop flag set to: {self._scan_manually_stopped}")
                
                # Update UI to show stopping state
                self.scan_toggle_btn.setEnabled(False)  # Disable during stopping process
                self.progress_bar.setValue(100)  # Start progress bar at 100% for stop countdown
                self.status_label.setText("🛑 Stopping scan - please wait...")
                self.status_bar.showMessage("🛑 Stopping scan safely - please wait...")
                
                # Add appropriate message based on what's running
                if rkhunter_running:
                    self.results_text.append("\n🛑 Scan stop requested - stopping RKHunter scan safely...")
                else:
                    self.results_text.append("\n🛑 Scan stop requested - finishing current files...")
                
                print("DEBUG: 📱 UI updated to stopping state")
                
                # Stop threads in the right order - stop RKHunter first if running
                if rkhunter_running:
                    print("DEBUG: 🛑 Stopping RKHunter thread first")
                    if (hasattr(self, 'current_rkhunter_thread') and 
                        self.current_rkhunter_thread and 
                        hasattr(self.current_rkhunter_thread, 'stop_scan')):
                        self.current_rkhunter_thread.stop_scan()
                    if (hasattr(self, 'current_rkhunter_thread') and 
                        self.current_rkhunter_thread):
                        self.current_rkhunter_thread.requestInterruption()
                
                # Then stop ClamAV scan if running
                if clamav_running:
                    print("DEBUG: 🛑 Stopping ClamAV thread")
                    if hasattr(self.current_scan_thread, 'stop_scan'):
                        self.current_scan_thread.stop_scan()
                    self.current_scan_thread.requestInterruption()
                
                # Disconnect signals to prevent completion events during stop
                self._disconnect_scan_signals()
                
                # Start stop completion monitoring with shorter timeout
                print("DEBUG: ⏲️ Starting completion timer")
                self._start_stop_completion_timer()
            else:
                print("DEBUG: ❌ User cancelled stop request")
        else:
            print("DEBUG: ❌ No running scan to stop")

    def _disconnect_scan_signals(self):
        """Disconnect scan thread signals to prevent events during stop"""
        try:
            # Disconnect ClamAV scan signals
            if self.current_scan_thread:
                if hasattr(self.current_scan_thread, 'scan_completed'):
                    try:
                        self.current_scan_thread.scan_completed.disconnect(self.scan_completed)
                    except (TypeError, RuntimeError):
                        # Already disconnected or not connected to this slot
                        pass
                if hasattr(self.current_scan_thread, 'progress_updated'):
                    try:
                        self.current_scan_thread.progress_updated.disconnect(self.progress_bar.setValue)
                    except (TypeError, RuntimeError):
                        # Already disconnected or not connected to this slot
                        pass
                if hasattr(self.current_scan_thread, 'status_updated'):
                    try:
                        self.current_scan_thread.status_updated.disconnect(self.status_label.setText)
                    except (TypeError, RuntimeError):
                        # Already disconnected or not connected to this slot
                        pass
                if hasattr(self.current_scan_thread, 'scan_detail_updated'):
                    try:
                        self.current_scan_thread.scan_detail_updated.disconnect(self.handle_detailed_scan_progress)
                    except (TypeError, RuntimeError):
                        # Already disconnected or not connected to this slot
                        pass
            
            # Disconnect RKHunter scan signals
            if hasattr(self, 'current_rkhunter_thread') and self.current_rkhunter_thread:
                if hasattr(self.current_rkhunter_thread, 'scan_completed'):
                    try:
                        self.current_rkhunter_thread.scan_completed.disconnect()
                    except (TypeError, RuntimeError):
                        # Already disconnected
                        pass
                if hasattr(self.current_rkhunter_thread, 'progress_updated'):
                    try:
                        self.current_rkhunter_thread.progress_updated.disconnect()
                    except (TypeError, RuntimeError):
                        # Already disconnected
                        pass
                if hasattr(self.current_rkhunter_thread, 'progress_value_updated'):
                    try:
                        self.current_rkhunter_thread.progress_value_updated.disconnect()
                    except (TypeError, RuntimeError):
                        # Already disconnected
                        pass
            
            print("DEBUG: ✅ Signals disconnected successfully")
        except Exception as e:
            print(f"DEBUG: ❌ Error disconnecting signals: {e}")
            
    def _start_stop_completion_timer(self):
        """Start a timer to monitor scan completion after stop request with faster checking"""
        print(f"\n⏲️ === STARTING COMPLETION TIMER ===")
        print(f"DEBUG: _start_stop_completion_timer() called")
        
        # Initialize or reset the stop attempt counter
        self._stop_completion_attempts = 0
        self._stop_max_attempts = 5  # Reduced to 5 seconds for better user experience
        
        if not hasattr(self, '_stop_completion_timer'):
            from PyQt6.QtCore import QTimer
            self._stop_completion_timer = QTimer()
            self._stop_completion_timer.timeout.connect(self._check_stop_completion)
            print("DEBUG: 🆕 Created new QTimer instance")
        else:
            print("DEBUG: ♻️ Reusing existing QTimer instance")
        
        # Check every 1 second for thread completion
        self._stop_completion_timer.start(1000)
        print("DEBUG: ⏰ Started stop completion monitoring timer (1000ms interval)")
            
    
    def _check_stop_completion(self):
        """Check if the stopped scan has completed and handle cleanup"""
        print(f"\n🔍 === CHECKING STOP COMPLETION ===")
        print(f"DEBUG: _check_stop_completion() called")
        print(f"DEBUG: Current scan thread exists: {self.current_scan_thread is not None}")
        print(f"DEBUG: Scan thread running: {self.current_scan_thread.isRunning() if self.current_scan_thread else 'N/A'}")
        print(f"DEBUG: Current RKHunter thread exists: {hasattr(self, 'current_rkhunter_thread') and self.current_rkhunter_thread is not None}")
        print(f"DEBUG: RKHunter thread running: {self.current_rkhunter_thread.isRunning() if hasattr(self, 'current_rkhunter_thread') and self.current_rkhunter_thread else 'N/A'}")
        print(f"DEBUG: Current state: {self._scan_state}")
        
        # Increment attempt counter
        if not hasattr(self, '_stop_completion_attempts'):
            self._stop_completion_attempts = 0
        self._stop_completion_attempts += 1
        
        # Use shorter timeout for better responsiveness - 5 seconds instead of 10-30
        max_attempts = 5
        if not hasattr(self, '_stop_max_attempts'):
            self._stop_max_attempts = max_attempts
        
        # Update progress bar to show stop progress (reverse progress from 100% to 0%)
        stop_progress = max(0, 100 - int((self._stop_completion_attempts / max_attempts) * 100))
        self.progress_bar.setValue(stop_progress)
        
        # Update status label and status bar to show stop progress
        remaining_time = max_attempts - self._stop_completion_attempts
        self.status_label.setText(f"🛑 Stopping scan... ({remaining_time}s remaining)")
        self.status_bar.showMessage(f"🛑 Stopping scan... ({remaining_time}s remaining)")
        print(f"DEBUG: 📊 Stop progress: {stop_progress}% (attempt {self._stop_completion_attempts}/{max_attempts})")
        
        # Check current thread states with safe error handling
        clamav_running = False
        rkhunter_running = False
        
        try:
            clamav_running = self.current_scan_thread and self.current_scan_thread.isRunning()
        except Exception as e:
            print(f"DEBUG: ⚠️ Error checking ClamAV thread state: {e}")
            # If we can't check, assume it's not running
            clamav_running = False
            
        try:
            rkhunter_running = (hasattr(self, 'current_rkhunter_thread') and 
                               self.current_rkhunter_thread and 
                               self.current_rkhunter_thread.isRunning())
        except Exception as e:
            print(f"DEBUG: ⚠️ Error checking RKHunter thread state: {e}")
            # If we can't check, assume it's not running
            rkhunter_running = False
        
        # Check for timeout - force completion after reduced timeout
        if self._stop_completion_attempts >= max_attempts:
            print(f"DEBUG: ⏰ Stop timeout reached ({self._stop_completion_attempts} attempts)")
            print("DEBUG: 🚨 Forcing scan stop completion due to timeout")
            
            # Force cleanup regardless of thread state
            if hasattr(self, '_stop_completion_timer'):
                self._stop_completion_timer.stop()
                print("DEBUG: ⏰ Stopped completion timer (timeout)")
            
            # Force cleanup both thread types
            self._force_cleanup_threads()
            
            # Reset states
            self._scan_state = "idle"
            self._scan_manually_stopped = False
            self._stop_scan_user_wants_restart = True
            
            # Reset UI
            self.update_scan_button_state(False)  # Reset to "Start Scan" mode
            self.scan_toggle_btn.setEnabled(True)  # Re-enable the button
            self.progress_bar.setValue(0)
            
            # Show appropriate completion message
            if rkhunter_running or clamav_running:
                self.results_text.append("🛑 Scan stop completed (forced after 5 seconds)\n\n"
                                        "⚠️ Note: Some background processes may continue briefly "
                                        "but will not affect the application.")
            else:
                self.results_text.append("🛑 Scan stop completed successfully")
            
            self.status_label.setText("Ready to scan")
            self.status_bar.showMessage("🔴 Ready to scan")
            print("DEBUG: ✅ Forced stop completed due to timeout")
            return
        
        # Check if all threads have actually stopped
        if not clamav_running and not rkhunter_running:
            # All threads have finished - complete the stop process
            print("DEBUG: ✅ All threads have finished - starting cleanup process")
            
            # Stop the timer
            if hasattr(self, '_stop_completion_timer'):
                self._stop_completion_timer.stop()
                print("DEBUG: ⏰ Stopped completion timer")
            
            # Clean up thread references properly
            self._cleanup_finished_threads()
            
            # Set state back to idle
            self._scan_state = "idle"
            self._scan_manually_stopped = False
            self._stop_scan_user_wants_restart = True
            
            print(f"DEBUG: 🔄 State set back to: {self._scan_state}")
            print(f"DEBUG: 🔄 Reset _scan_manually_stopped flag to: {self._scan_manually_stopped}")
            
            # Reset UI to ready state
            self.update_scan_button_state(False)  # Reset to "Start Scan" mode
            self.scan_toggle_btn.setEnabled(True)  # Re-enable the button
            self.progress_bar.setValue(0)
            self.status_label.setText("Ready to scan")
            self.status_bar.showMessage("🔴 Ready to scan")
            
            # Show success message
            self.results_text.append("🛑 Scan stopped successfully")
            
            print("DEBUG: ✅ Clean stop completed successfully")
        else:
            # Still waiting for threads to finish
            threads_still_running = []
            if clamav_running:
                threads_still_running.append("ClamAV")
            if rkhunter_running:
                threads_still_running.append("RKHunter")
            
            print(f"DEBUG: ⏳ Still waiting for {', '.join(threads_still_running)} to finish... (attempt {self._stop_completion_attempts}/{max_attempts})")

    def _force_cleanup_threads(self):
        """Force cleanup of all scan threads"""
        print("DEBUG: 🧹 Starting forced thread cleanup")
        
        # Force cleanup scan thread
        if self.current_scan_thread:
            try:
                if self.current_scan_thread.isRunning():
                    print("DEBUG: 🔧 Force terminating stuck ClamAV thread")
                    self.current_scan_thread.requestInterruption()
                    # Give it 1 more second
                    if not self.current_scan_thread.wait(1000):
                        print("DEBUG: ⚠️ ClamAV thread did not stop gracefully, forcing cleanup")
            except Exception as e:
                print(f"DEBUG: ⚠️ Error during force ClamAV thread cleanup: {e}")
            finally:
                self.current_scan_thread = None
                print("DEBUG: 🧹 Forced ClamAV thread cleanup completed")
        
        # Force cleanup RKHunter thread
        if hasattr(self, 'current_rkhunter_thread') and self.current_rkhunter_thread:
            try:
                if self.current_rkhunter_thread.isRunning():
                    print("DEBUG: 🔧 Force terminating stuck RKHunter thread")
                    if hasattr(self.current_rkhunter_thread, 'stop_scan'):
                        self.current_rkhunter_thread.stop_scan()
                    # Give it 1 more second
                    if not self.current_rkhunter_thread.wait(1000):
                        print("DEBUG: ⚠️ RKHunter thread did not stop gracefully, forcing cleanup")
            except Exception as e:
                print(f"DEBUG: ⚠️ Error during force RKHunter thread cleanup: {e}")
            finally:
                self.current_rkhunter_thread = None
                print("DEBUG: 🧹 Forced RKHunter thread cleanup completed")

    def _cleanup_finished_threads(self):
        """Clean up finished thread references properly"""
        print("DEBUG: 🧹 Cleaning up finished thread references")
        
        if self.current_scan_thread:
            try:
                # Ensure the thread is properly cleaned up
                if not self.current_scan_thread.isRunning():
                    self.current_scan_thread.deleteLater()
                    print("DEBUG: 🧹 ClamAV thread marked for deletion")
            except Exception as e:
                print(f"DEBUG: ⚠️ Error during ClamAV thread cleanup: {e}")
            finally:
                self.current_scan_thread = None
        
        if self.current_rkhunter_thread:
            try:
                # Ensure the RKHunter thread is properly cleaned up
                if not self.current_rkhunter_thread.isRunning():
                    self.current_rkhunter_thread.deleteLater()
                    print("DEBUG: 🧹 RKHunter thread marked for deletion")
            except Exception as e:
                print(f"DEBUG: ⚠️ Error during RKHunter thread cleanup: {e}")
            finally:
                self.current_rkhunter_thread = None
            self._stop_scan_user_wants_restart = True
            print(f"DEBUG: 🔄 Set user wants restart flag to: {self._stop_scan_user_wants_restart}")
            
            # Reset UI to ready state with visual confirmation
            self.update_scan_button_state(False)  # Reset to "Start Scan" mode
            self.scan_toggle_btn.setEnabled(True)  # Re-enable the button
            
            # Brief visual confirmation that stop completed (flash to 0% then reset)
            self.progress_bar.setValue(0)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(200, lambda: self.progress_bar.setValue(0))  # Keep at 0%
            print("DEBUG: 📱 UI reset to ready state")
            
            # Show completion message
            self.results_text.append("✅ Scan stopped successfully")
            self.status_label.setText("Ready to scan")  # Reset status label
            self.status_bar.showMessage("🔴 Ready to scan")
            print("DEBUG: 💬 Completion messages displayed")
            
            print(f"DEBUG: ✅ Stop completed, final state: {self._scan_state}")
            
            # Check if there's a pending scan request
            if self._pending_scan_request:
                print(f"DEBUG: 🚀 Found pending scan request: {self._pending_scan_request}")
                print("DEBUG: Executing queued scan request")
                pending = self._pending_scan_request
                self._pending_scan_request = None
                print(f"DEBUG: Cleared pending request, will execute: {pending}")
                # Execute the queued scan
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(500, lambda: self.start_scan(pending.get("quick_scan", False)))
                print("DEBUG: 📅 Queued scan execution scheduled (500ms delay)")
            else:
                print("DEBUG: ❌ No pending scan request found")
        else:
            print(f"DEBUG: ⏳ Scan still running, continuing to monitor... (attempt {self._stop_completion_attempts}/{getattr(self, '_stop_max_attempts', 30)})")

    def update_dashboard_cards(self):
        """Update all dashboard status cards with current information."""
        print(f"\n📊 === UPDATE DASHBOARD CARDS ===")
        print("DEBUG: update_dashboard_cards() called")
        
        # Update Last Scan card
        if hasattr(self, "last_scan_card"):
            try:
                print("DEBUG: 🔍 Updating Last Scan card")
                # Get the most recent scan report from the reports directory
                reports_dir = (
                    Path.home() /
                    ".local/share/search-and-destroy/scan_reports/daily")
                print(f"DEBUG: Looking for reports in: {reports_dir}")
                print(f"DEBUG: Reports directory exists: {reports_dir.exists()}")
                
                if reports_dir.exists():
                    report_files = list(reports_dir.glob("scan_*.json"))
                    print(f"DEBUG: Found {len(report_files)} report files")
                    print(f"DEBUG: Found {len(report_files)} report files")
                    if report_files:
                        # Get the most recent file
                        latest_file = max(
                            report_files, key=lambda p: p.stat().st_mtime)
                        print(f"DEBUG: Latest report file: {latest_file}")
                        try:
                            with open(latest_file, "r", encoding="utf-8") as f:
                                report_data = json.load(f)

                            # Get data from the correct structure
                            scan_time = report_data.get("start_time", "")
                            scan_type = report_data.get("scan_type", "unknown")
                            scan_success = report_data.get("success", True)

                            # Clean up scan type (remove ScanType. prefix if
                            # present)
                            if scan_type.startswith("ScanType."):
                                scan_type = scan_type.replace(
                                    "ScanType.", "").lower()

                            # Format the scan type for display
                            scan_type_display = {
                                "quick": "Quick",
                                "full": "Full",
                                "custom": "Custom",
                                "scheduled": "Scheduled",
                            }.get(scan_type.lower(), "Unknown")

                            if scan_time:
                                try:
                                    scan_date = datetime.fromisoformat(
                                        scan_time.replace("Z", "+00:00")
                                    )
                                    # Format time (12-hour) above date (full
                                    # format with year)
                                    formatted_time = scan_date.strftime(
                                        "%I:%M %p"
                                    )  # 12:17 PM
                                    formatted_date = scan_date.strftime(
                                        "%A %b %d, %Y"
                                    )  # Wednesday Aug 07, 2025
                                    formatted_display = (
                                        f"{formatted_time}\n{formatted_date}"
                                    )
                                except (ValueError, AttributeError):
                                    formatted_display = "Recently"
                            else:
                                formatted_display = "Recently"

                            threats_count = report_data.get("threats_found", 0)

                            # Determine status text
                            if not scan_success:
                                status_text = "Failed"
                            elif threats_count > 0:
                                status_text = f"{threats_count} threats found"
                            else:
                                status_text = "No threats found"

                            # Update the card
                            for child in self.last_scan_card.findChildren(
                                    QLabel):
                                if child.objectName() == "cardValue":
                                    child.setText(formatted_display)
                                    child.setStyleSheet(
                                        "color: #17a2b8; font-size: 16px; font-weight: bold;"
                                    )
                                elif child.objectName() == "cardDescription":
                                    child.setText(
                                        f"{scan_type_display} scan - {status_text}")

                            # Update Threats Found card
                            if hasattr(self, "threats_card"):
                                for child in self.threats_card.findChildren(
                                        QLabel):
                                    if child.objectName() == "cardValue":
                                        child.setText(str(threats_count))
                                        color = (
                                            "#dc3545"
                                            if threats_count > 0
                                            else "#28a745"
                                        )
                                        child.setStyleSheet(
                                            f"color: {color}; font-size: 20px; font-weight: bold;")
                                    elif child.objectName() == "cardDescription":
                                        child.setText(
                                            "Click to view quarantine"
                                            if threats_count > 0
                                            else "Click to view quarantine"
                                        )
                        except (OSError, ValueError, KeyError) as file_error:
                            print(f"Error reading report file: {file_error}")

            except (OSError, ImportError) as e:
                print(f"Error updating dashboard cards: {e}")

    def scan_completed(self, result):
        print(f"\n🏁 === SCAN_COMPLETED CALLED ===")
        print(f"DEBUG: scan_completed() called")
        print(f"DEBUG: Current scan state: {self._scan_state}")
        print(f"DEBUG: Manual stop flag: {self._scan_manually_stopped}")
        print(f"DEBUG: Current thread exists: {self.current_scan_thread is not None}")
        print(f"DEBUG: Result type: {type(result)}")
        print(f"DEBUG: Result preview: {str(result)[:200]}...")
        
        # If scan was manually stopped, ignore this signal to prevent crashes
        if self._scan_manually_stopped:
            print("DEBUG: ❌ Ignoring scan_completed signal - scan was manually stopped")
            return
            
        # Also ignore if the scan was cancelled
        if isinstance(result, dict) and result.get("status") == "cancelled":
            print("DEBUG: ❌ Ignoring scan_completed signal - scan was cancelled")
            self.results_text.append("🛑 Scan was cancelled")
            self.status_bar.showMessage("🛑 Scan cancelled")
            return
            
        # Ignore if no thread reference (shouldn't happen)
        if not self.current_scan_thread:
            print("DEBUG: ❌ Ignoring scan_completed signal - no active thread")
            return
            
        print("DEBUG: ✅ Processing scan completion (natural completion)")
        
        self.update_scan_button_state(False)  # Reset to "Start Scan" mode
        self.scan_toggle_btn.setEnabled(True)  # Re-enable the button
        self.progress_bar.setValue(100)

        # Reset scan state to idle
        self._scan_state = "idle"
        print(f"DEBUG: 🔄 Scan completed naturally, state reset to: {self._scan_state}")

        # Clean up thread reference properly
        if self.current_scan_thread:
            print("DEBUG: 🧹 Cleaning up thread reference")
            try:
                # Ensure the thread is properly cleaned up
                self.current_scan_thread.deleteLater()
            except Exception as e:
                print(f"DEBUG: ⚠️ Error during thread cleanup: {e}")
            finally:
                self.current_scan_thread = None

        # Reset quick scan button if it was a quick scan
        if hasattr(
                self,
                "is_quick_scan_running") and self.is_quick_scan_running:
            self.reset_quick_scan_button()

        if "error" in result:
            error_msg = result["error"]
            self.results_text.setText(f"Scan error: {error_msg}")
            self.status_bar.showMessage(f"Scan failed: {error_msg}")
            # Reset button state on error
            self.update_scan_button_state(False)
            self.scan_toggle_btn.setEnabled(True)
            return

        # Handle cancelled scans
        if result.get("status") == "cancelled":
            cancel_msg = result.get("message", "Scan was cancelled")
            self.results_text.setText(cancel_msg)
            self.status_bar.showMessage(cancel_msg)
            # Reset button state on cancellation
            self.update_scan_button_state(False)
            self.scan_toggle_btn.setEnabled(True)
            return

        # Save the scan result to a report file
        try:
            print(f"\n📊 === SCAN RESULT PROCESSING ===")
            print(f"DEBUG: Processing scan result for reporting")
            print(f"DEBUG: Result type: {type(result)}")
            
            # Note: Report saving is now handled by the FileScanner itself to prevent duplicates
            # The scanner automatically saves reports with proper scan type detection
            #
            # Create a proper ScanResult object from the dictionary for display
            # purposes only
            scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"DEBUG: Generated scan ID: {scan_id}")

            # Handle both dictionary and dataclass result formats
            if isinstance(result, dict):
                print("DEBUG: Result is dictionary format")
                total_files = result.get("total_files", 0)
                scanned_files = result.get(
                    "scanned_files", result.get("files_scanned", 0)
                )
                threats_found = result.get(
                    "threats_found", len(result.get("threats", []))
                )
                duration = result.get("duration", result.get("scan_time", 0))
                threats_data = result.get("threats", [])
                print(f"DEBUG: Extracted from dict - total_files: {total_files}, scanned: {scanned_files}, threats: {threats_found}, duration: {duration}")
            else:
                print("DEBUG: Result is object format")
                # Assume it's already a proper result object
                total_files = getattr(result, "total_files", 0)
                scanned_files = getattr(result, "scanned_files", 0)
                threats_found = getattr(result, "threats_found", 0)
                duration = getattr(result, "duration", 0)
                threats_data = getattr(result, "threats", [])
                print(f"DEBUG: Extracted from object - total_files: {total_files}, scanned: {scanned_files}, threats: {threats_found}, duration: {duration}")

            print(f"DEBUG: Processing {len(threats_data)} threat entries")
            # Convert threat dictionaries to ThreatInfo objects if any
            threats = []
            for i, threat_data in enumerate(threats_data):
                print(f"DEBUG: Processing threat {i+1}/{len(threats_data)}: {type(threat_data)}")
                if isinstance(threat_data, dict):
                    print(f"DEBUG: Threat dict keys: {list(threat_data.keys())}")
                    # Create ThreatInfo object from the dictionary
                    threat = ThreatInfo(
                        file_path=threat_data.get(
                            "file_path", threat_data.get("file", "")
                        ),
                        threat_name=threat_data.get(
                            "threat_name", threat_data.get("threat", "")
                        ),
                        threat_type=threat_data.get(
                            "threat_type", threat_data.get("type", "virus")
                        ),
                        threat_level=ThreatLevel.INFECTED,
                        action_taken=threat_data.get(
                            "action_taken", threat_data.get("action", "none")
                        ),
                        timestamp=datetime.now().isoformat(),
                        file_size=threat_data.get(
                            "file_size", threat_data.get("size", 0)
                        ),
                        file_hash=threat_data.get(
                            "file_hash", threat_data.get("hash", "")
                        ),
                    )
                else:
                    # Already a ThreatInfo object
                    threat = threat_data
                    print(f"DEBUG: Using existing ThreatInfo object")
                threats.append(threat)
                print(f"DEBUG: Added threat: {threat.threat_name if hasattr(threat, 'threat_name') else 'unknown'}")

            print(f"DEBUG: Converted {len(threats)} threats to ThreatInfo objects")
            
            # Create the ScanResult object with correct scan type
            # Determine scan type based on context
            if hasattr(
                    self,
                    "is_quick_scan_running") and self.is_quick_scan_running:
                scan_type = ScanType.QUICK
                print("DEBUG: Determined scan type: QUICK (from is_quick_scan_running)")
            elif (isinstance(self.scan_path, str) and 
                  self.scan_path == os.path.expanduser("~")):
                scan_type = ScanType.FULL
                print("DEBUG: Determined scan type: FULL (from scan_path)")
            else:
                scan_type = ScanType.CUSTOM
                print(f"DEBUG: Determined scan type: CUSTOM (scan_path: {self.scan_path})")

            print(f"DEBUG: Creating ScanResult object with scan_type: {scan_type}")
            scan_result = ScanResult(
                scan_id=scan_id,
                scan_type=scan_type,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration=duration,
                scanned_paths=[self.scan_path],
                total_files=total_files,
                scanned_files=scanned_files,
                threats_found=threats_found,
                threats=threats,
                errors=[],
                scan_settings={},
                engine_version="1.0",
                signature_version="1.0",
                success=True,
            )
            print(f"DEBUG: ScanResult created successfully: ID={scan_id}, type={scan_type}, files={scanned_files}/{total_files}, threats={threats_found}")

            # Save the scan result
            # Note: Commented out to prevent duplicate reports - FileScanner handles this
            # self.report_manager.save_scan_result(scan_result)
            print("DEBUG: Report saving skipped (handled by FileScanner to prevent duplicates)")

            # Always refresh the reports list after a scan completes
            # This ensures reports show up regardless of which tab is currently active
            # Use a more reliable approach than QTimer
            print("DEBUG: Preparing to refresh reports after completion")
            def delayed_refresh():
                try:
                    print("DEBUG: About to call update_dashboard_cards() after scan completion")
                    self.update_dashboard_cards()
                    print("DEBUG: About to refresh reports")
                    self.refresh_reports()
                    print("DEBUG: Reports refreshed after scan completion")
                except Exception as e:
                    print(f"DEBUG: Error refreshing reports: {e}")

            from PyQt6.QtCore import QTimer

            QTimer.singleShot(500, delayed_refresh)  # Increased delay to 500ms

        except (OSError, IOError, json.JSONDecodeError) as e:
            print(f"Error saving scan report: {e}")

        # Display the results in the UI
        self.display_scan_results(result)
        
        # Set completion status message
        if isinstance(result, dict):
            threats_found = result.get("threats_found", len(result.get("threats", [])))
        else:
            threats_found = getattr(result, "threats_found", 0)
        
        if threats_found > 0:
            self.status_bar.showMessage(f"✅ Scan completed - {threats_found} threats found")
        else:
            self.status_bar.showMessage("✅ Scan completed successfully - No threats found")

        # Update dashboard cards with new scan information
        print("DEBUG: About to call update_dashboard_cards() after scan completion")
        try:
            if not self._scan_manually_stopped:
                self.update_dashboard_cards()
            else:
                print("DEBUG: Skipping dashboard update - scan was manually stopped")
        except Exception as e:
            print(f"DEBUG: Error updating dashboard cards: {e}")
            import traceback
            traceback.print_exc()

    def _setup_enhanced_effects(self):
        """Setup enhanced Qt effects for all interactive widgets."""
        try:
            from .theme_manager import setup_widget_effects, apply_button_effects
            
            # Apply effects to all buttons in the main window
            buttons = self.findChildren(QPushButton)
            print(f"🎨 Setting up enhanced effects for {len(buttons)} buttons...")
            
            for button in buttons:
                apply_button_effects(button)
            
            # Apply general effects to the main window
            setup_widget_effects(self)
            
            print("✅ Enhanced Qt effects setup complete")
            
        except Exception as e:
            print(f"⚠️ Failed to setup enhanced effects: {e}")

    def _show_welcome_message(self):
        """Display a welcome message with app information and instructions."""
        
        self.results_text.append("🛡️  XANADOS SEARCH & DESTROY")
        self.results_text.append("=" * 45)
        self.results_text.append("Advanced Anti-Malware & Rootkit Detection System")
        self.results_text.append("")
        
        self.results_text.append(" SCAN TYPES:")
        self.results_text.append("   • Quick: Common threat locations")
        self.results_text.append("   • Full: Comprehensive system scan")
        self.results_text.append("   • Custom: Specific files/directories")
        self.results_text.append("   • RKHunter: Rootkit detection")
        self.results_text.append("")
        
        self.results_text.append("💡 QUICK START:")
        self.results_text.append("   1. Choose scan type above")
        self.results_text.append("   2. Click 'Start Scan'")
        self.results_text.append("   3. Results appear here")
        self.results_text.append("")
        
        self.results_text.append("Ready to scan! 🚀")
        self.results_text.append("=" * 40)

    def _clear_results_with_header(self):
        """Clear results and show a scan preparation header."""
        self.results_text.clear()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.results_text.append("🔄 PREPARING NEW SCAN")
        self.results_text.append("=" * 45)
        self.results_text.append(f"📅 Scan initiated: {timestamp}")
        self.results_text.append("")
        self.results_text.append("⏳ Initializing scan engine...")
        self.results_text.append("")
        
        # Record scan start time for accurate duration calculation
        self._scan_start_time = datetime.now()
        
        # Reset file tracking for accurate statistics
        if hasattr(self, '_scan_files_actually_processed'):
            delattr(self, '_scan_files_actually_processed')

    def format_target_display(self, scan_path):
        """Format the scan target for user-friendly display."""
        if isinstance(scan_path, list):
            # For Quick Scan with multiple directories
            if len(scan_path) <= 3:
                # Show individual paths for small lists
                formatted_paths = []
                for path in scan_path:
                    display_path = path.replace(str(Path.home()), "~") if str(Path.home()) in str(path) else str(path)
                    formatted_paths.append(display_path)
                return ", ".join(formatted_paths)
            else:
                # Show count for large lists
                home_dirs = sum(1 for path in scan_path if str(Path.home()) in str(path))
                system_dirs = len(scan_path) - home_dirs
                
                parts = []
                if home_dirs > 0:
                    parts.append(f"{home_dirs} user directories")
                if system_dirs > 0:
                    parts.append(f"{system_dirs} system directories")
                
                return f"Multiple directories ({', '.join(parts)})"
        else:
            # Single directory/file path
            if str(Path.home()) in str(scan_path):
                return str(scan_path).replace(str(Path.home()), "~")
            return str(scan_path)

    def format_scan_options_user_friendly(self, scan_options):
        """Convert technical scan options into user-friendly descriptions."""
        if not scan_options:
            return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Default settings</b>"
        
        friendly_options = []
        
        # Format scan depth
        if 'depth' in scan_options:
            depth = scan_options['depth']
            try:
                depth_int = int(depth)
            except (TypeError, ValueError):
                depth_int = None
            if depth == 1:
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📏 <b>Depth:</b> Shallow (top-level files only)")
            elif depth == 2:
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📏 <b>Depth:</b> Medium (2 folder levels)")
            elif depth == 3:
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📏 <b>Depth:</b> Deep (3 folder levels)")
            elif isinstance(depth_int, int) and depth_int >= 4:
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📏 <b>Depth:</b> Very Deep (all subfolders)")
            else:
                friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📏 <b>Depth:</b> {depth} levels")
        
        # Format file filter
        if 'file_filter' in scan_options:
            file_filter = scan_options['file_filter']
            if file_filter == 'all':
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 <b>Files:</b> All file types")
            elif file_filter == 'executables':
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 <b>Files:</b> Executable files only")
            elif file_filter == 'documents':
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 <b>Files:</b> Document files only")
            elif file_filter == 'archives':
                friendly_options.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 <b>Files:</b> Archive files only")
            else:
                friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 <b>Files:</b> {file_filter}")
        
        # Format memory limit
        if 'memory_limit' in scan_options:
            memory_mb = scan_options['memory_limit']
            try:
                mem_int = int(memory_mb)
            except (TypeError, ValueError):
                mem_int = None
            if mem_int is not None:
                if mem_int < 512:
                    friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;💾 <b>Memory:</b> Low usage ({mem_int}MB)")
                elif mem_int < 1024:
                    friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;💾 <b>Memory:</b> Medium usage ({mem_int}MB)")
                elif mem_int < 2048:
                    friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;💾 <b>Memory:</b> High usage ({mem_int}MB)")
                else:
                    friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;💾 <b>Memory:</b> Very high usage ({mem_int}MB)")
        
        # Format exclusions
        if 'exclusions' in scan_options:
            exclusions = scan_options['exclusions']
            if exclusions:
                count = len(exclusions)
                friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🚫 <b>Exclusions:</b> {count} pattern{'s' if count != 1 else ''}")
        
        # Handle any other custom options
        for key, value in scan_options.items():
            if key not in ['depth', 'file_filter', 'memory_limit', 'exclusions']:
                friendly_options.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⚙️ <b>{key.replace('_', ' ').title()}:</b> {value}")
        
        return "<br>".join(friendly_options) if friendly_options else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Default settings</b>"

    def display_scan_results(self, result):
        """Display comprehensive scan results with detailed information."""
        # Create a separator for multiple scans
        if self.results_text.toPlainText().strip():
            self.results_text.append("\n" + "="*60 + "\n")
        
        # Header with scan completion status
        if isinstance(result, dict) and result.get("status") == "error":
            self.results_text.append("❌ Scan Failed!")
            self.results_text.append(f"Error: {result.get('error', 'Unknown error')}")
            return
        elif isinstance(result, dict) and result.get("status") == "cancelled":
            self.results_text.append("🛑 Scan Cancelled")
            self.results_text.append(f"Reason: {result.get('message', 'User cancelled')}")
            return
        
        # Handle both dictionary and dataclass result formats
        if isinstance(result, dict):
            files_scanned = result.get("scanned_files", result.get("files_scanned", 0))
            total_files = result.get("total_files", files_scanned)
            threats_found = result.get("threats_found", len(result.get("threats", [])))
            scan_time = result.get("duration", result.get("scan_time", 0))
            threats = result.get("threats", [])
            scan_type = result.get("scan_type", "Unknown")
            scan_path = result.get("scan_path", result.get("scanned_paths", "Unknown"))
            errors = result.get("errors", [])
            
            # Debug the scan statistics to identify issues
            print(f"DEBUG: Scan result dictionary analysis:")
            print(f"  - scanned_files: {result.get('scanned_files', 'NOT_FOUND')}")
            print(f"  - files_scanned: {result.get('files_scanned', 'NOT_FOUND')}")
            print(f"  - total_files: {result.get('total_files', 'NOT_FOUND')}")
            print(f"  - duration: {result.get('duration', 'NOT_FOUND')}")
            print(f"  - scan_time: {result.get('scan_time', 'NOT_FOUND')}")
            print(f"  - Final values: files_scanned={files_scanned}, total_files={total_files}, scan_time={scan_time}")
        else:
            # Assume it's a dataclass-like object
            files_scanned = getattr(result, "scanned_files", 0)
            total_files = getattr(result, "total_files", files_scanned)
            threats_found = getattr(result, "threats_found", 0)
            scan_time = getattr(result, "duration", 0)
            threats = getattr(result, "threats", [])
            scan_type = getattr(result, "scan_type", "Unknown")
            scan_path = getattr(result, "scanned_paths", ["Unknown"])
            errors = getattr(result, "errors", [])
            
            # Debug the scan statistics for object format
            print(f"DEBUG: Scan result object analysis:")
            print(f"  - scanned_files attr: {getattr(result, 'scanned_files', 'NOT_FOUND')}")
            print(f"  - total_files attr: {getattr(result, 'total_files', 'NOT_FOUND')}")
            print(f"  - duration attr: {getattr(result, 'duration', 'NOT_FOUND')}")
            print(f"  - Final values: files_scanned={files_scanned}, total_files={total_files}, scan_time={scan_time}")
            
        # Handle scan statistics inconsistencies and edge cases
        if files_scanned == 0 and hasattr(self, '_scan_files_actually_processed'):
            # Use the count from our progress tracking if FileScanner result is incorrect
            files_scanned = getattr(self, '_scan_files_actually_processed', 0)
            print(f"DEBUG: Using progress tracking count: {files_scanned} files")
            
        # Ensure total_files is at least as large as files_scanned
        if total_files < files_scanned:
            total_files = files_scanned
            print(f"DEBUG: Corrected total_files to match scanned_files: {total_files}")
            
        # Handle scan_time default to avoid "Unknown" in final display
        if scan_time == "Unknown" or scan_time == 0:
            # Calculate actual duration from our tracked start time
            if hasattr(self, '_scan_start_time'):
                actual_duration = (datetime.now() - self._scan_start_time).total_seconds()
                scan_time = actual_duration
                self._last_scan_duration = actual_duration
                print(f"DEBUG: Calculated actual scan duration: {scan_time:.1f} seconds")
            else:
                scan_time = getattr(self, '_last_scan_duration', 0)
                print(f"DEBUG: Using fallback scan duration: {scan_time}")
        
        # Also fix the path consistency issue for better display
        if isinstance(scan_path, str) and scan_path == "Unknown":
            # Fallback to the actual scan path that was used
            scan_path = getattr(self, 'scan_path', 'Unknown')
            print(f"DEBUG: Using fallback scan path: {scan_path}")

        # Format scan time nicely
        if isinstance(scan_time, (int, float)) and scan_time != "Unknown":
            if scan_time < 60:
                formatted_time = f"{scan_time:.1f} seconds"
            else:
                minutes = int(scan_time // 60)
                seconds = scan_time % 60
                formatted_time = f"{minutes}m {seconds:.1f}s"
        else:
            formatted_time = str(scan_time)

        # Main result header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if threats_found > 0:
            self.results_text.append(f"⚠️  SCAN COMPLETED - {threats_found} THREATS FOUND")
        else:
            self.results_text.append("✅ SCAN COMPLETED - NO THREATS FOUND")
        
        self.results_text.append(f"📅 Completed at: {timestamp}")
        self.results_text.append("")

        # Scan details section
        self.results_text.append("📊 SCAN DETAILS:")
        
        # Format scan type
        if scan_type != "Unknown":
            if hasattr(scan_type, 'value'):  # Handle enum
                type_display = scan_type.value.title()
            else:
                type_display = str(scan_type).replace("_", " ").title()
            self.results_text.append(f"   📋 Type: {type_display}")
        
        # Format scan path
        if scan_path != "Unknown":
            if isinstance(scan_path, list):
                if len(scan_path) == 1:
                    path_display = self.format_target_display(scan_path[0])
                    self.results_text.append(f"   📁 Target: {path_display}")
                else:
                    self.results_text.append(f"   📁 Targets: {len(scan_path)} directories")
                    for i, path in enumerate(scan_path[:5]):  # Show first 5
                        path_display = self.format_target_display(path)
                        self.results_text.append(f"      {i+1}. {path_display}")
                    if len(scan_path) > 5:
                        self.results_text.append(f"      ... and {len(scan_path)-5} more")
            else:
                path_display = self.format_target_display(scan_path)
                self.results_text.append(f"   📁 Target: {path_display}")
        
        self.results_text.append(f"   📈 Files scanned: {files_scanned:,}")
        if total_files != files_scanned:
            self.results_text.append(f"   📊 Total files found: {total_files:,}")
        self.results_text.append(f"   ⏱️  Duration: {formatted_time}")
        self.results_text.append("")

        # Threats section
        if threats_found > 0:
            self.results_text.append(f"🚨 THREATS DETECTED ({threats_found}):")
            for i, threat in enumerate(threats, 1):
                if isinstance(threat, dict):
                    file_path = threat.get("file_path", threat.get("file", "Unknown"))
                    threat_name = threat.get("threat_name", threat.get("threat", "Unknown"))
                    threat_type = threat.get("threat_type", threat.get("type", "Unknown"))
                    action_taken = threat.get("action_taken", threat.get("action", "detected"))
                else:
                    file_path = getattr(threat, "file_path", "Unknown")
                    threat_name = getattr(threat, "threat_name", "Unknown")
                    threat_type = getattr(threat, "threat_type", "Unknown")
                    action_taken = getattr(threat, "action_taken", "detected")
                
                # Format file path for display
                display_path = self.format_target_display(file_path)
                
                self.results_text.append(f"   {i}. {threat_name}")
                self.results_text.append(f"      📄 File: {display_path}")
                if threat_type != "Unknown":
                    self.results_text.append(f"      🏷️  Type: {threat_type}")
                if action_taken != "detected":
                    self.results_text.append(f"      ⚡ Action: {action_taken}")
                self.results_text.append("")
        else:
            self.results_text.append("✅ NO THREATS DETECTED")
            self.results_text.append("   Your system appears clean!")
            self.results_text.append("")

        # Errors section
        if errors:
            self.results_text.append(f"⚠️  SCAN WARNINGS ({len(errors)}):")
            for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
                self.results_text.append(f"   {i}. {error}")
            if len(errors) > 10:
                self.results_text.append(f"   ... and {len(errors)-10} more warnings")
            self.results_text.append("")

        # Summary and recommendations
        if threats_found > 0:
            self.results_text.append("🔧 RECOMMENDED ACTIONS:")
            self.results_text.append("   • Review detected threats carefully")
            self.results_text.append("   • Consider quarantining or removing infected files")
            self.results_text.append("   • Run additional scans to ensure complete cleanup")
            self.results_text.append("   • Update your antivirus definitions regularly")
        else:
            self.results_text.append("💡 RECOMMENDATIONS:")
            self.results_text.append("   • Schedule regular scans for ongoing protection")
            self.results_text.append("   • Keep your antivirus definitions up to date")
            self.results_text.append("   • Enable real-time protection if available")
        
        # Scroll to bottom to show latest results
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)

    def quick_scan(self):
        # Toggle quick scan based on current state
        if self.is_quick_scan_running:
            # Stop the quick scan
            self.stop_quick_scan()
        else:
            # Start a quick scan
            self.start_quick_scan()

    def start_quick_scan(self):
        """Start a comprehensive quick scan of multiple high-risk directories."""
        # Quick scan targets multiple common infection vectors and user directories
        # This provides comprehensive coverage while still being faster than full system scan
        import tempfile

        # Comprehensive quick scan paths - ordered by infection risk priority
        quick_scan_paths = [
            # Primary infection vectors (highest priority)
            os.path.expanduser("~/Downloads"),     # Downloads - most common infection vector
            os.path.expanduser("~/Desktop"),       # Desktop - user accessible files
            
            # User content directories (medium-high priority)  
            os.path.expanduser("~/Documents"),     # Documents - user documents and files
            os.path.expanduser("~/Pictures"),      # Pictures - image files, potential threats
            os.path.expanduser("~/Videos"),        # Videos - media files
            os.path.expanduser("~/Music"),         # Music - audio files
            
            # Web browser directories (medium priority)
            os.path.expanduser("~/.mozilla"),      # Firefox profile
            os.path.expanduser("~/.config/google-chrome"),  # Chrome config
            os.path.expanduser("~/.config/chromium"),       # Chromium config
            
            # System and temporary directories (medium priority)
            tempfile.gettempdir(),                 # System temporary files
            "/tmp" if os.path.exists("/tmp") else None,  # Linux temp
            "/var/tmp" if os.path.exists("/var/tmp") else None,  # Linux var temp
            
            # User application directories (lower priority but still important)
            os.path.expanduser("~/.local/share"),  # User application data
            os.path.expanduser("~/.cache"),        # User cache files
        ]

        # Filter out non-existent paths and None values
        valid_paths = [
            path for path in quick_scan_paths 
            if path and os.path.exists(path) and os.path.isdir(path)
        ]

        if not valid_paths:
            self.show_themed_message_box(
                "warning", "Warning", "No valid directories found for quick scan.")
            self.reset_quick_scan_button()
            return

        # Store all valid paths for comprehensive scanning
        self.quick_scan_paths = valid_paths
        self.scan_path = valid_paths  # Pass all paths to the scanner
        
        # Update UI to show comprehensive scan
        self.path_label.setText(
            f"Comprehensive Quick Scan\n"
            f"Scanning {len(valid_paths)} directories:\n" +
            "\n".join([f"• {os.path.basename(path)}" for path in valid_paths[:5]]) +
            (f"\n• ...and {len(valid_paths) - 5} more" if len(valid_paths) > 5 else "")
        )

        # Update button state
        self.is_quick_scan_running = True
        self.quick_scan_btn.setText("Stop Quick Scan")

        # Start the comprehensive scan
        self.start_scan(quick_scan=True)

    def stop_quick_scan(self):
        """Stop the quick scan and reset button state."""
        try:
            if (
                hasattr(self, "current_scan_thread")
                and self.current_scan_thread
                and self.current_scan_thread.isRunning()
            ):
                # Cooperative cancellation path
                if hasattr(self.current_scan_thread, "stop_scan"):
                    self.current_scan_thread.stop_scan()
                else:
                    # Fallback: set interruption request
                    try:
                        self.current_scan_thread.requestInterruption()
                    except Exception:
                        pass
                # Wait up to 3 seconds for graceful exit
                self.current_scan_thread.wait(3000)
                if self.current_scan_thread.isRunning():
                    print("Warning: scan thread still running after cooperative cancellation window")

                self.scan_completed(
                    {"status": "cancelled", "message": "Quick scan cancelled by user"}
                )
        except (RuntimeError, AttributeError) as e:
            print(f"Error stopping quick scan: {e}")
        finally:
            # Always reset button state
            self.reset_quick_scan_button()

    def reset_quick_scan_button(self):
        """Reset the quick scan button to its initial state."""
        self.is_quick_scan_running = False
        self.quick_scan_btn.setText("Quick Scan")

    def update_definitions(self):
        """Update virus definitions with progress dialog and user feedback."""
        try:
            # First check if definitions need updating
            freshness = self.scanner.clamav_wrapper.check_definition_freshness()

            # Create and show progress dialog
            progress_dialog = self.show_themed_progress_dialog(
                "Updating Virus Definitions", "Checking virus definitions...", 0, 100)
            progress_dialog.setValue(0)
            progress_dialog.show()

            # Start update in background thread with progress callbacks
            import time
            from threading import Thread

            self.update_result = None
            self.update_progress = 0
            self.update_status = "Initializing..."

            def run_update():
                try:
                    # Update progress
                    self.update_status = "Checking current definitions..."
                    self.update_progress = 10

                    # Check if update is needed
                    if not freshness.get("needs_update", True):
                        self.update_status = "Definitions are already up to date"
                        self.update_progress = 100
                        self.update_result = True
                        return

                    self.update_status = "Starting virus definition update..."
                    self.update_progress = 20
                    time.sleep(0.5)

                    # Check if we need sudo by testing write permissions first
                    clamav_db_dir = "/var/lib/clamav"
                    needs_sudo = (
                        not os.access(clamav_db_dir, os.W_OK)
                        if os.path.exists(clamav_db_dir)
                        else True
                    )

                    if needs_sudo:
                        self.update_status = "Administrator permissions required - please check your terminal"
                        self.update_progress = 30
                        # Give user time to see the message
                        time.sleep(2)
                    else:
                        self.update_status = "Attempting direct update..."
                        self.update_progress = 30

                    # Call the actual update method
                    success = self.scanner.update_virus_definitions()

                    if success:
                        self.update_status = "Virus definitions updated successfully!"
                        self.update_progress = 100
                        self.update_result = True
                    else:
                        self.update_status = "Failed to update virus definitions"
                        self.update_progress = 100
                        self.update_result = False

                except (
                    subprocess.CalledProcessError,
                    OSError,
                    FileNotFoundError,
                    subprocess.TimeoutExpired,
                ) as e:
                    self.update_status = f"Error updating definitions: {e}"
                    self.update_progress = 100
                    self.update_result = False

            # Start update thread
            update_thread = Thread(target=run_update)
            update_thread.daemon = True
            update_thread.start()

            # Create timer to update progress dialog
            timer = QTimer()
            dialog_closed = False

            def update_progress():
                nonlocal dialog_closed

                if dialog_closed:
                    return

                # Handle cancel button first (before processing updates)
                if progress_dialog.wasCanceled():
                    timer.stop()
                    dialog_closed = True
                    progress_dialog.close()
                    self.status_bar.showMessage(
                        "Virus definition update cancelled", 3000
                    )
                    return

                if hasattr(self, "update_progress"):
                    progress_dialog.setValue(self.update_progress)
                    progress_dialog.setLabelText(self.update_status)

                    # Check if completed
                    if self.update_progress >= 100:
                        timer.stop()
                        dialog_closed = True
                        progress_dialog.close()

                        # Show result message
                        if hasattr(self, "update_result"):
                            if self.update_result:
                                self.show_themed_message_box(
                                    "information",
                                    "Update Complete",
                                    "Virus definitions updated successfully!",
                                )
                                self.status_bar.showMessage(
                                    "Virus definitions updated successfully", 5000)
                                # Refresh the definition status display with a
                                # small delay
                                QTimer.singleShot(
                                    500, self.update_definition_status)
                            else:
                                self.show_themed_message_box(
                                    "warning",
                                    "Update Failed",
                                    f"Failed to update virus definitions.\n\n"
                                    f"Status: {self.update_status}\n\n"
                                    f"You may need to:\n"
                                    f"• Run the application as administrator\n"
                                    f"• Check your internet connection\n"
                                    f"• Verify ClamAV is properly installed",
                                )
                                self.status_bar.showMessage(
                                    "Failed to update virus definitions", 5000
                                )
                        return

            timer.timeout.connect(update_progress)
            timer.start(250)  # Update every 250ms

        except (OSError, IOError, RuntimeError) as e:
            self.show_themed_message_box(
                "critical", "Update Error", f"Could not start update: {e}"
            )

    def refresh_quarantine(self):
        """Load and display quarantined files."""
        try:
            # Clear the current list
            self.quarantine_list.clear()

            # Get quarantine directory from config
            from utils.config import QUARANTINE_DIR

            # Verify the directory exists
            if not QUARANTINE_DIR.exists():
                return

            # Find all quarantined files
            quarantine_files = list(QUARANTINE_DIR.glob("*.quarantine"))

            if not quarantine_files:
                return

            # Add to list widget
            for qfile in quarantine_files:
                # Extract original filename from quarantine file
                original_name = qfile.stem
                item = QListWidgetItem(original_name)
                item.setData(Qt.ItemDataRole.UserRole, str(qfile))
                self.quarantine_list.addItem(item)

        except (OSError, IOError, PermissionError) as e:
            self.status_bar.showMessage(f"Error loading quarantine: {e}", 5000)

    def show_about(self):
        self.show_themed_message_box(
            "information",
            "About S&D",
            f"""<h1>S&D - Search & Destroy</h1>
                         <p>A modern GUI for ClamAV virus scanning.</p>
                         <p>Version {APP_VERSION}</p>
                         <p>© 2025 xanadOS</p>""",
        )

    def update_definition_status(self):
        """Update the last virus definition update time display."""
        # Set the "Last Checked" timestamp to now
        current_time = datetime.now()
        formatted_checked = current_time.strftime("%Y-%m-%d %H:%M")
        self.last_checked_label.setText(f"Last checked: {formatted_checked}")

        try:
            freshness = self.scanner.clamav_wrapper.check_definition_freshness()

            # Handle error cases gracefully
            if freshness.get("error"):
                print(
                    f"Warning: Error checking definitions: {
                        freshness['error']}")
                self.last_update_label.setText("Status: Check failed")
                return

            if freshness.get("last_update"):
                # Handle different types of last_update values
                last_update_value = freshness["last_update"]

                if last_update_value == "No definitions found":
                    self.last_update_label.setText("Status: No definitions")
                elif last_update_value.startswith("Error:"):
                    self.last_update_label.setText("Status: Check failed")
                else:
                    # Parse the date string and format it nicely
                    try:
                        last_update = datetime.fromisoformat(
                            last_update_value.replace("Z", "+00:00")
                        )
                        # Format as readable date
                        formatted_date = last_update.strftime("%Y-%m-%d %H:%M")
                        label_text = f"Last updated: {formatted_date}"
                        self.last_update_label.setText(label_text)
                    except (ValueError, AttributeError):
                        # If parsing fails, show the raw date
                        label_text = f"Last updated: {last_update_value}"
                        self.last_update_label.setText(label_text)
            else:
                # Check if definitions exist at all
                if freshness.get("definitions_exist", False):
                    self.last_update_label.setText("Last updated: Unknown")
                else:
                    self.last_update_label.setText("Status: No definitions")

        except Exception as e:
            print(f"Error checking definition status: {e}")
            self.last_update_label.setText("Status: Error checking")
            self.last_checked_label.setText(
                f"Last checked: {formatted_checked} (error)"
            )

            # Try a fallback method using clamscan --version (doesn't require
            # sudo)
            try:
                result = subprocess.run(
                    ["clamscan", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if result.returncode == 0:
                    # If clamscan works, definitions are probably there, just
                    # couldn't access them
                    self.last_update_label.setText("Status: Permissions issue")
                else:
                    self.last_update_label.setText("Status: ClamAV not found")
            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                self.last_update_label.setText("Status: ClamAV not available")

    def tray_icon_activated(self, reason):
        # ActivationReason.Trigger is a single click, DoubleClick is double
        # click
        if (
            reason == QSystemTrayIcon.ActivationReason.Trigger
            or reason == QSystemTrayIcon.ActivationReason.DoubleClick
        ):
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    def quit_application(self):
        # Check if minimize to tray is enabled in settings
        ui_settings = self.config.get("ui_settings", {})
        minimize_to_tray = ui_settings.get("minimize_to_tray", True)
        
        # If minimize to tray is enabled and system tray is available, minimize instead of quitting
        if (
            minimize_to_tray
            and hasattr(self, "tray_icon")
            and self.tray_icon
            and self.tray_icon.isVisible()
        ):
            self.hide()
            self.tray_icon.showMessage(
                "S&D - Search & Destroy",
                "Application minimized to system tray. Click the tray icon to restore.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            return

        # If minimize to tray is disabled, proceed with normal quit behavior
        # Check if real-time protection is active
        if (
            self.monitoring_enabled
            and self.real_time_monitor
            and hasattr(self.real_time_monitor, "state")
            and self.real_time_monitor.state.name == "RUNNING"
        ):
            reply = self.show_themed_message_box(
                "question",
                "Exit Application",
                "Real-time protection is currently active and will be stopped if you exit the application.\n\n"
                "Are you sure you want to exit and stop real-time protection?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return  # User chose not to exit

            # User confirmed exit - stop real-time protection
            try:
                print("🛑 Stopping real-time protection due to application exit...")
                self.stop_real_time_protection()
                print("✅ Real-time protection stopped successfully")
            except Exception as e:
                print(f"⚠️ Error stopping real-time protection: {e}")

        # Check for running scans
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            reply = self.show_themed_message_box(
                "question",
                "Quit",
                "A scan is in progress. Do you want to quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
            # Cooperative cancellation instead of terminate()
            if hasattr(self.current_scan_thread, "stop_scan"):
                self.current_scan_thread.stop_scan()
            else:
                try:
                    self.current_scan_thread.requestInterruption()
                except Exception:
                    pass
            self.current_scan_thread.wait(3000)

        # Force application to quit instead of just closing the window
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    def force_quit_application(self):
        """Force quit the application regardless of minimize to tray setting."""
        # Set flag to indicate we're force quitting (prevents minimize notification)
        self._force_quitting = True
        
        # Check if real-time protection is active
        if (
            self.monitoring_enabled
            and self.real_time_monitor
            and hasattr(self.real_time_monitor, "state")
            and self.real_time_monitor.state.name == "RUNNING"
        ):
            reply = self.show_themed_message_box(
                "question",
                "Force Exit Application",
                "Real-time protection is currently active and will be stopped if you exit the application.\n\n"
                "Are you sure you want to force exit and stop real-time protection?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return  # User chose not to exit

            # User confirmed exit - stop real-time protection
            try:
                print("🛑 Stopping real-time protection due to force application exit...")
                self.stop_real_time_protection()
                print("✅ Real-time protection stopped successfully")
            except Exception as e:
                print(f"⚠️ Error stopping real-time protection: {e}")

        # Check for running scans
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            reply = self.show_themed_message_box(
                "question",
                "Force Quit",
                "A scan is in progress. Do you want to force quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
            if hasattr(self.current_scan_thread, "stop_scan"):
                self.current_scan_thread.stop_scan()
            else:
                try:
                    self.current_scan_thread.requestInterruption()
                except Exception:
                    pass
            self.current_scan_thread.wait(1500)

        # Force application to quit
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    def closeEvent(self, event):
        # Check if minimize to tray is enabled in settings
        ui_settings = self.config.get("ui_settings", {})
        minimize_to_tray = ui_settings.get("minimize_to_tray", True)
        
        # If we're force quitting, don't minimize to tray or show notification
        if hasattr(self, '_force_quitting') and self._force_quitting:
            # Skip minimize to tray behavior during force quit
            self._cleanup_before_exit(event)
            return
        
        # If minimize to tray is enabled and system tray is available, minimize instead of closing
        if (
            minimize_to_tray
            and hasattr(self, "tray_icon")
            and self.tray_icon
            and self.tray_icon.isVisible()
        ):
            self.hide()
            self.tray_icon.showMessage(
                "S&D - Search & Destroy",
                "Application minimized to system tray. Click the tray icon to restore.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            event.ignore()
            return

        # If minimize to tray is disabled, proceed with normal close behavior
        self._cleanup_before_exit(event)

    def _cleanup_before_exit(self, event):
        """Common cleanup logic for application exit."""
        # Check if real-time protection is active before closing
        if (
            self.monitoring_enabled
            and self.real_time_monitor
            and hasattr(self.real_time_monitor, "state")
            and self.real_time_monitor.state.name == "RUNNING"
        ):
            reply = self.show_themed_message_box(
                "question",
                "Close Application",
                "Real-time protection is currently active and will be stopped if you close the application.\n\n"
                "Are you sure you want to close and stop real-time protection?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            # User chose to close - stop real-time protection
            try:
                print("🛑 Stopping real-time protection due to application close...")
                self.stop_real_time_protection()
                print("✅ Real-time protection stopped successfully")
            except Exception as e:
                print(f"⚠️ Error stopping real-time protection: {e}")

        # Stop real-time monitoring before closing
        if hasattr(self, "real_time_monitor") and self.real_time_monitor:
            try:
                self.real_time_monitor.stop()
            except Exception:
                pass  # Ignore errors during shutdown

        # Save activity logs before closing
        try:
            self.save_activity_logs()
        except Exception as e:
            print(f"Warning: Failed to save activity logs on close: {e}")

        # Accept the close event (actually close the application)
        event.accept()

        # Force application to quit
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    def refresh_reports(self):
        """Load and display scan reports in the reports list."""
        print(f"\n📋 === REFRESH REPORTS ===")
        print("DEBUG: refresh_reports() called")
        
        try:
            # Clear the current list
            print("DEBUG: 🧹 Clearing current reports list")
            self.reports_list.clear()

            # Get ClamAV reports directory from the report manager
            clamav_reports_dir = self.report_manager.daily_reports
            print(f"DEBUG: 📁 ClamAV reports directory: {clamav_reports_dir}")

            # Get RKHunter reports directory
            rkhunter_reports_dir = (
                Path.home() /
                ".local/share/search-and-destroy/rkhunter_reports"
            )
            print(f"DEBUG: 📁 RKHunter reports directory: {rkhunter_reports_dir}")

            all_reports = []

            # Load ClamAV reports
            if clamav_reports_dir.exists():
                clamav_files = list(clamav_reports_dir.glob("scan_*.json"))
                print(f"DEBUG: 🔍 Found {len(clamav_files)} ClamAV report files")
                
                for report_file in clamav_files:
                    try:
                        with open(report_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        # Extract scan ID from filename
                        scan_id = report_file.stem.replace("scan_", "")
                        
                        all_reports.append({
                            'type': 'clamav',
                            'file_path': report_file,
                            'scan_id': scan_id,
                            'data': data,
                            'start_time': data.get('start_time', 'Unknown'),
                            'scan_type': data.get('scan_type', 'Unknown'),
                            'threats': data.get('threats_found', 0)
                        })
                    except (OSError, IOError, PermissionError, json.JSONDecodeError) as e:
                        print(f"Error loading ClamAV report {report_file}: {e}")

            # Load RKHunter reports
            if rkhunter_reports_dir.exists():
                rkhunter_files = list(rkhunter_reports_dir.glob("rkhunter_scan_*.json"))
                print(f"DEBUG: 🔍 Found {len(rkhunter_files)} RKHunter report files")
                
                for report_file in rkhunter_files:
                    try:
                        with open(report_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        # Extract scan ID from filename
                        scan_id = report_file.stem
                        
                        all_reports.append({
                            'type': 'rkhunter',
                            'file_path': report_file,
                            'scan_id': scan_id,
                            'data': data,
                            'start_time': data.get('start_time', 'Unknown'),
                            'scan_type': data.get('scan_type', 'Unknown'),
                            'warnings': data.get('statistics', {}).get('warnings_found', 0),
                            'infections': data.get('statistics', {}).get('infections_found', 0)
                        })
                    except (OSError, IOError, PermissionError, json.JSONDecodeError) as e:
                        print(f"Error loading RKHunter report {report_file}: {e}")

            # Check if no reports found
            if not all_reports:
                print("DEBUG: ❌ No report files found")
                if self.current_theme == "dark":
                    no_reports_html = """
                    <style>
                        body {
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: #FFCDAA;
                            background-color: #2b2b2b;
                            margin: 20px;
                            text-align: center;
                            line-height: 1.6;
                        }
                        h3 {
                            color: #EE8980;
                            font-weight: 600;
                            margin-bottom: 10px;
                        }
                        p {
                            color: #FFCDAA;
                            font-weight: 500;
                        }
                    </style>
                    <h3>No Scan Reports Found</h3>
                    <p>Run a ClamAV or RKHunter scan to generate your first report.</p>
                    """
                else:
                    no_reports_html = """
                    <style>
                        body {
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: #2c2c2c;
                            background-color: #fefefe;
                            margin: 20px;
                            text-align: center;
                            line-height: 1.5;
                        }
                        h3 {
                            color: #75BDE0;
                            font-weight: 600;
                            margin-bottom: 10px;
                        }
                        p {
                            color: #2c2c2c;
                            font-weight: 500;
                        }
                    </style>
                    <h3>No Scan Reports Found</h3>
                    <p>Run a ClamAV or RKHunter scan to generate your first report.</p>
                    """
                self.report_viewer.setHtml(no_reports_html)
                return

            # Sort reports by start time (newest first)
            all_reports.sort(key=lambda x: x['start_time'], reverse=True)

            # Add to list widget
            for report in all_reports:
                try:
                    data = report['data']
                    
                    # Create item text with type indicator
                    if report['type'] == 'clamav':
                        type_icon = "🦠"  # Virus icon for ClamAV
                        scan_type = data.get('scan_type', 'Unknown')
                        threats = report['threats']
                        status = f" - {threats} threats found" if threats else " - Clean"
                    else:  # rkhunter
                        type_icon = "🔍"  # Magnifying glass for RKHunter
                        scan_type = "RKHunter Rootkit Scan"
                        warnings = report['warnings']
                        infections = report['infections']
                        if infections > 0:
                            status = f" - {infections} infections, {warnings} warnings"
                        elif warnings > 0:
                            status = f" - {warnings} warnings"
                        else:
                            status = " - Clean"

                    # Format timestamp
                    start_time = report['start_time']
                    if start_time != 'Unknown':
                        try:
                            # Parse ISO format and format for display
                            from datetime import datetime
                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            formatted_time = start_time
                    else:
                        formatted_time = start_time

                    item_text = f"{type_icon} {formatted_time} - {scan_type}{status}"

                    # Create and add the item
                    item = QListWidgetItem(item_text)
                    # Store report info for loading
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'type': report['type'],
                        'scan_id': report['scan_id'],
                        'file_path': str(report['file_path'])
                    })
                    self.reports_list.addItem(item)

                except Exception as e:
                    print(f"Error processing report {report.get('file_path', 'unknown')}: {e}")

            if self.current_theme == "dark":
                select_report_html = """
                <style>
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #FFCDAA;
                        background-color: #2b2b2b;
                        margin: 20px;
                        text-align: center;
                        line-height: 1.6;
                    }
                    h3 {
                        color: #EE8980;
                        font-weight: 600;
                        margin-bottom: 10px;
                    }
                    p {
                        color: #FFCDAA;
                        font-weight: 500;
                    }
                </style>
                <h3>Select a Report</h3>
                <p>Choose a scan report from the list to view detailed results.</p>
                """
            else:
                select_report_html = """
                <style>
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #2c2c2c;
                        background-color: #fefefe;
                        margin: 20px;
                        text-align: center;
                        line-height: 1.5;
                    }
                    h3 {
                        color: #75BDE0;
                        font-weight: 600;
                        margin-bottom: 10px;
                    }
                    p {
                        color: #2c2c2c;
                        font-weight: 500;
                    }
                </style>
                <h3>Select a Report</h3>
                <p>Choose a scan report from the list to view detailed results.</p>
                """
            self.report_viewer.setHtml(select_report_html)

        except Exception as e:
            if self.current_theme == "dark":
                error_html = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #FFCDAA;
                        background-color: #2b2b2b;
                        margin: 20px;
                        line-height: 1.6;
                    }}
                    h3 {{
                        color: #F14666;
                        font-weight: 600;
                        margin-bottom: 10px;
                    }}
                    p {{
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                </style>
                <h3>Error Loading Reports</h3>
                <p>{e}</p>
                """
            else:
                error_html = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #2c2c2c;
                        background-color: #fefefe;
                        margin: 20px;
                        line-height: 1.5;
                    }}
                    h3 {{
                        color: #F89B9B;
                        font-weight: 600;
                        margin-bottom: 10px;
                    }}
                    p {{
                        color: #2c2c2c;
                        font-weight: 500;
                    }}
                </style>
                <h3>Error Loading Reports</h3>
                <p>{e}</p>
                """
            self.report_viewer.setHtml(error_html)

    def load_report(self, item):
        """Load and display the selected scan report."""
        try:
            # Get report info from item data
            report_info = item.data(Qt.ItemDataRole.UserRole)
            if not report_info:
                self._show_report_error("No report data available for this item.")
                return

            # Handle new format with report type and file path
            if isinstance(report_info, dict):
                report_type = report_info.get('type')
                file_path_str = report_info.get('file_path')
                if not file_path_str:
                    self._show_report_error("No file path available for this report.")
                    return
                file_path = Path(file_path_str)
                
                if report_type == 'clamav':
                    self._load_clamav_report(file_path, report_info.get('scan_id'))
                elif report_type == 'rkhunter':
                    self._load_rkhunter_report(file_path, report_info.get('scan_id'))
                else:
                    self._show_report_error(f"Unknown report type: {report_type}")
                return

            # Legacy format handling for old ClamAV reports
            scan_id = report_info
            if not scan_id:
                if self.current_theme == "dark":
                    no_id_html = """
                    <style>
                        body {
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: #FFCDAA;
                            background-color: #2b2b2b;
                            margin: 20px;
                            text-align: center;
                            line-height: 1.6;
                        }
                        h3 {
                            color: #F14666;
                            font-weight: 600;
                            margin-bottom: 10px;
                        }
                        p {
                            color: #FFCDAA;
                            font-weight: 500;
                        }
                    </style>
                    <h3>Report Error</h3>
                    <p>No scan ID available for this report.</p>
                    """
                else:
                    no_id_html = """
                    <style>
                        body {
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: #2c2c2c;
                            background-color: #fefefe;
                            margin: 20px;
                            text-align: center;
                            line-height: 1.5;
                        }
                        h3 {
                            color: #F89B9B;
                            font-weight: 600;
                            margin-bottom: 10px;
                        }
                        p {
                            color: #2c2c2c;
                            font-weight: 500;
                        }
                    </style>
                    <h3>Report Error</h3>
                    <p>No scan ID available for this report.</p>
                    """
                self.report_viewer.setHtml(no_id_html)
                return

            # Load the report using the report manager
            scan_result = self.report_manager.load_scan_result(scan_id)

            if not scan_result:
                if self.current_theme == "dark":
                    load_error_html = f"""
                    <style>
                        body {{
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: #FFCDAA;
                            background-color: #2b2b2b;
                            margin: 20px;
                            text-align: center;
                            line-height: 1.6;
                        }}
                        h3 {{
                            color: #F14666;
                            font-weight: 600;
                            margin-bottom: 10px;
                        }}
                        p {{
                            color: #FFCDAA;
                            font-weight: 500;
                        }}
                    </style>
                    <h3>Report Load Error</h3>
                    <p>Could not load report with ID: {scan_id}</p>
                    """
                else:
                    load_error_html = f"""
                    <style>
                        body {{
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: #2c2c2c;
                            background-color: #fefefe;
                            margin: 20px;
                            text-align: center;
                            line-height: 1.5;
                        }}
                        h3 {{
                            color: #F89B9B;
                            font-weight: 600;
                            margin-bottom: 10px;
                        }}
                        p {{
                            color: #2c2c2c;
                            font-weight: 500;
                        }}
                    </style>
                    <h3>Report Load Error</h3>
                    <p>Could not load report with ID: {scan_id}</p>
                    """
                self.report_viewer.setHtml(load_error_html)
                return

            # Format the report for display
            # Create a formatted text output
            output = f"<h2>Scan Report: {scan_id}</h2>"
            output += f"<p><b>Date:</b> {scan_result.start_time}</p>"
            output += f"<p><b>Scan Type:</b> {scan_result.scan_type.value}</p>"
            output += f"<p><b>Duration:</b> {
                scan_result.duration:.2f} seconds</p>"
            output += f"<p><b>Files Scanned:</b> {
                scan_result.scanned_files}/{
                scan_result.total_files}</p>"
            output += f"<p><b>Threats Found:</b> {
                scan_result.threats_found}</p>"

            # Add paths that were scanned
            output += "<h3>Scanned Paths:</h3><ul>"
            for path in scan_result.scanned_paths:
                output += f"<li>{path}</li>"
            output += "</ul>"

            # Add threats if any were found
            if scan_result.threats_found > 0:
                output += "<h3>Detected Threats:</h3><table border='1' cellpadding='3'>"
                output += (
                    "<tr><th>File</th><th>Threat</th><th>Level</th><th>Action</th></tr>"
                )

                for threat in scan_result.threats:
                    threat_level_class = (
                        "error"
                        if threat.threat_level.value == "error"
                        else (
                            "infected"
                            if threat.threat_level.value == "infected"
                            else (
                                "suspicious"
                                if threat.threat_level.value == "suspicious"
                                else "clean"
                            )
                        )
                    )

                    output += f"<tr class='{threat_level_class}'>"
                    output += f"<td>{threat.file_path}</td>"
                    output += f"<td>{threat.threat_name}</td>"
                    output += f"<td>{threat.threat_level.value}</td>"
                    output += f"<td>{threat.action_taken}</td>"
                    output += "</tr>"

                output += "</table>"
            else:
                output += "<h3>No threats detected!</h3>"

            # Add any errors
            if scan_result.errors:
                output += "<h3>Errors:</h3><ul>"
                for error in scan_result.errors:
                    output += f"<li>{error}</li>"
                output += "</ul>"

            # Add CSS styling based on current theme
            if self.current_theme == "dark":
                # Dark mode styling with Strawberry color palette
                output = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #FFCDAA;
                        background-color: #2b2b2b;
                        margin: 8px;
                        line-height: 1.6;
                    }}
                    h2 {{
                        color: #F14666;
                        font-weight: 700;
                        margin-top: 16px;
                        margin-bottom: 12px;
                        border-bottom: 2px solid #EE8980;
                        padding-bottom: 8px;
                        font-size: 20px;
                    }}
                    h3 {{
                        color: #F14666;
                        font-weight: 600;
                        margin-top: 16px;
                        margin-bottom: 10px;
                        font-size: 16px;
                    }}
                    p {{
                        margin: 8px 0;
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 10px 0;
                        border: 2px solid #EE8980;
                        border-radius: 6px;
                        overflow: hidden;
                        background-color: #353535;
                    }}
                    th {{
                        background-color: #EE8980;
                        color: #ffffff;
                        font-weight: 700;
                        padding: 10px;
                        text-align: left;
                        font-size: 13px;
                    }}
                    td {{
                        padding: 8px 10px;
                        border-bottom: 1px solid #404040;
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                    tr:nth-child(even) {{
                        background-color: #404040;
                    }}
                    tr:nth-child(odd) {{
                        background-color: #353535;
                    }}
                    tr.infected {{
                        background-color: #4A2B2B;
                        border-left: 4px solid #F14666;
                        color: #ffffff;
                    }}
                    tr.suspicious {{
                        background-color: #4A3B2B;
                        border-left: 4px solid #EE8980;
                        color: #ffffff;
                    }}
                    tr.error {{
                        background-color: #4A2B2B;
                        border-left: 4px solid #F14666;
                        color: #ffffff;
                    }}
                    tr.clean {{
                        background-color: #2B4A3B;
                        border-left: 4px solid #9CB898;
                        color: #ffffff;
                    }}
                    ul {{
                        margin: 10px 0;
                        padding-left: 22px;
                    }}
                    li {{
                        margin: 6px 0;
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                    b {{
                        color: #EE8980;
                        font-weight: 700;
                    }}
                </style>
                {output}
                """
            else:
                # Light mode styling with Sunrise color palette
                output = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #2c2c2c;
                        background-color: #fefefe;
                        margin: 8px;
                        line-height: 1.5;
                    }}
                    h2 {{
                        color: #75BDE0;
                        font-weight: 700;
                        margin-top: 16px;
                        margin-bottom: 12px;
                        border-bottom: 2px solid #F8D49B;
                        padding-bottom: 6px;
                    }}
                    h3 {{
                        color: #75BDE0;
                        font-weight: 600;
                        margin-top: 16px;
                        margin-bottom: 8px;
                    }}
                    p {{
                        margin: 6px 0;
                        color: #2c2c2c;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 8px 0;
                        border: 2px solid #F8D49B;
                        border-radius: 6px;
                        overflow: hidden;
                    }}
                    th {{
                        background-color: #F8D49B;
                        color: #2c2c2c;
                        font-weight: 600;
                        padding: 8px;
                        text-align: left;
                    }}
                    td {{
                        padding: 6px 8px;
                        border-bottom: 1px solid #F8F8F8;
                    }}
                    tr:nth-child(even) {{
                        background-color: #FAFAFA;
                    }}
                    tr.infected {{
                        background-color: #FEF5F5;
                        border-left: 4px solid #F89B9B;
                    }}
                    tr.suspicious {{
                        background-color: #FEF9F5;
                        border-left: 4px solid #F8BC9B;
                    }}
                    tr.error {{
                        background-color: #FEF5F5;
                        border-left: 4px solid #F89B9B;
                    }}
                    tr.clean {{
                        background-color: #F5FAFF;
                        border-left: 4px solid #75BDE0;
                    }}
                    ul {{
                        margin: 8px 0;
                        padding-left: 20px;
                    }}
                    li {{
                        margin: 4px 0;
                        color: #2c2c2c;
                    }}
                    b {{
                        color: #75BDE0;
                        font-weight: 600;
                    }}
                </style>
                {output}
                """

            self.report_viewer.setHtml(output)

        except Exception as e:
            if self.current_theme == "dark":
                final_error_html = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #FFCDAA;
                        background-color: #2b2b2b;
                        margin: 20px;
                        text-align: center;
                        line-height: 1.6;
                    }}
                    h3 {{
                        color: #F14666;
                        font-weight: 600;
                        margin-bottom: 10px;
                    }}
                    p {{
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                </style>
                <h3>Report Display Error</h3>
                <p>Error loading report: {e}</p>
                """
            else:
                final_error_html = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        color: #2c2c2c;
                        background-color: #fefefe;
                        margin: 20px;
                        text-align: center;
                        line-height: 1.5;
                    }}
                    h3 {{
                        color: #F89B9B;
                        font-weight: 600;
                        margin-bottom: 10px;
                    }}
                    p {{
                        color: #2c2c2c;
                        font-weight: 500;
                    }}
                </style>
                <h3>Report Display Error</h3>
                <p>Error loading report: {e}</p>
                """
            self.report_viewer.setHtml(final_error_html)

    def export_reports(self):
        """Export scan reports to file."""
        try:
            from PyQt6.QtCore import QDate
            from PyQt6.QtWidgets import (
                QComboBox,
                QDateEdit,
                QDialog,
                QFileDialog,
                QHBoxLayout,
                QLabel,
                QMessageBox,
                QPushButton,
                QVBoxLayout,
            )

            # Create a dialog for export options
            dialog = QDialog(self)
            dialog.setWindowTitle("Export Reports")
            dialog.setMinimumWidth(400)

            # Apply theming
            bg = self.get_theme_color("background")
            text = self.get_theme_color("primary_text")
            tertiary_bg = self.get_theme_color("tertiary_bg")
            border = self.get_theme_color("border")
            hover_bg = self.get_theme_color("hover_bg")
            accent = self.get_theme_color("accent")

            dialog_style = f"""
                QDialog {{
                    background-color: {bg};
                    color: {text};
                    border: 2px solid {border};
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {text};
                    font-weight: 600;
                }}
                QComboBox {{
                    background-color: {tertiary_bg};
                    border: 2px solid {border};
                    border-radius: 4px;
                    padding: 6px;
                    color: {text};
                }}
                QComboBox:hover {{
                    border-color: {accent};
                }}
                QDateEdit {{
                    background-color: {tertiary_bg};
                    border: 2px solid {border};
                    border-radius: 4px;
                    padding: 6px;
                    color: {text};
                }}
                QDateEdit:hover {{
                    border-color: {accent};
                }}
                QPushButton {{
                    background-color: {tertiary_bg};
                    border: 2px solid {border};
                    border-radius: 5px;
                    padding: 8px 16px;
                    color: {text};
                    font-weight: 600;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                    border-color: {accent};
                }}
                QPushButton:default {{
                    background-color: {accent};
                    color: {bg};
                }}
            """
            dialog.setStyleSheet(dialog_style)

            layout = QVBoxLayout(dialog)

            # Format selection
            format_layout = QHBoxLayout()
            format_label = QLabel("Export Format:")
            format_combo = QComboBox()
            format_combo.addItems(["JSON", "CSV", "HTML"])
            format_layout.addWidget(format_label)
            format_layout.addWidget(format_combo)
            layout.addLayout(format_layout)

            # Date range
            date_layout = QVBoxLayout()
            date_label = QLabel("Date Range (Optional):")
            date_layout.addWidget(date_label)

            start_date_layout = QHBoxLayout()
            start_date_label = QLabel("Start Date:")
            start_date = QDateEdit()
            start_date.setCalendarPopup(True)
            start_date.setDate(
                QDate.currentDate().addDays(-30))  # Last 30 days
            start_date_layout.addWidget(start_date_label)
            start_date_layout.addWidget(start_date)
            date_layout.addLayout(start_date_layout)

            end_date_layout = QHBoxLayout()
            end_date_label = QLabel("End Date:")
            end_date = QDateEdit()
            end_date.setCalendarPopup(True)
            end_date.setDate(QDate.currentDate())
            end_date_layout.addWidget(end_date_label)
            end_date_layout.addWidget(end_date)
            date_layout.addLayout(end_date_layout)

            layout.addLayout(date_layout)

            # Buttons
            button_layout = QHBoxLayout()
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(dialog.reject)
            export_button = QPushButton("Export")
            export_button.clicked.connect(dialog.accept)
            export_button.setDefault(True)
            button_layout.addWidget(cancel_button)
            button_layout.addWidget(export_button)
            layout.addLayout(button_layout)

            # Show dialog
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Get export format
            format_type = format_combo.currentText().lower()

            # Get date range
            start_date_str = start_date.date().toString("yyyy-MM-dd")
            end_date_str = end_date.date().toString("yyyy-MM-dd")

            # Get output file path
            file_extensions = {
                "json": "JSON Files (*.json)",
                "csv": "CSV Files (*.csv)",
                "html": "HTML Files (*.html)",
            }

            file_path = self.show_themed_file_dialog(
                "save",
                "Save Export File",
                "",
                file_extensions.get(format_type, "All Files (*)"),
            )

            if not file_path:
                return

            # Add extension if missing
            if not file_path.lower().endswith(f".{format_type}"):
                file_path += f".{format_type}"

            # Export the reports
            success = self.report_manager.export_reports(
                file_path,
                format_type=format_type,
                start_date=f"{start_date_str}T00:00:00",
                end_date=f"{end_date_str}T23:59:59",
            )

            if success:
                self.show_themed_message_box(
                    "information",
                    "Export Complete",
                    f"Reports successfully exported to:\n{file_path}",
                )
            else:
                self.show_themed_message_box(
                    "warning",
                    "Export Failed",
                    "Failed to export reports. See log for details.",
                )

        except Exception as e:
            self.show_themed_message_box(
                "warning", "Export Error", f"Error exporting reports: {e}"
            )

    def delete_all_reports(self):
        """Delete all scan reports after confirmation."""
        try:
            from pathlib import Path

            from PyQt6.QtWidgets import QMessageBox

            # Show confirmation dialog
            reply = self.show_themed_message_box(
                "question",
                "Delete All Reports",
                "Are you sure you want to delete ALL scan reports?\n\nThis includes both ClamAV and RKHunter reports.\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Delete all reports by cleaning up both directories
                try:
                    deleted_count = 0
                    
                    # Delete ClamAV reports from the report manager's reports directory
                    clamav_reports_dir = self.report_manager.reports_dir
                    if clamav_reports_dir.exists():
                        # Delete all .json report files
                        for report_file in clamav_reports_dir.glob("*.json"):
                            report_file.unlink()
                            deleted_count += 1

                        # Also clean up any subdirectories like daily
                        # summaries, threats, etc.
                        for subdir in clamav_reports_dir.iterdir():
                            if subdir.is_dir():
                                for file in subdir.rglob("*"):
                                    if file.is_file():
                                        file.unlink()
                                        deleted_count += 1
                                # Remove empty directories
                                try:
                                    if not any(subdir.iterdir()):
                                        subdir.rmdir()
                                except OSError:
                                    pass  # Directory not empty or other issue

                    # Delete RKHunter reports from their separate directory
                    rkhunter_reports_dir = (
                        Path.home() /
                        ".local/share/search-and-destroy/rkhunter_reports"
                    )
                    if rkhunter_reports_dir.exists():
                        # Delete all RKHunter report files
                        for report_file in rkhunter_reports_dir.glob("rkhunter_scan_*.json"):
                            report_file.unlink()
                            deleted_count += 1
                        
                        # Also delete any other files in the RKHunter reports directory
                        for report_file in rkhunter_reports_dir.glob("*.json"):
                            report_file.unlink()
                            deleted_count += 1

                    self.show_themed_message_box(
                        "information",
                        "Reports Deleted",
                        f"Successfully deleted {deleted_count} report files (ClamAV and RKHunter).",
                    )
                    # Refresh the reports list to show it's empty
                    self.refresh_reports()

                except Exception as delete_error:
                    self.show_themed_message_box(
                        "warning",
                        "Delete Failed",
                        f"Failed to delete reports: {delete_error}",
                    )

        except Exception as e:
            self.show_themed_message_box(
                "warning", "Delete Error", f"Error deleting reports: {e}"
            )

    def load_current_settings(self):
        """Load current settings from config into the settings UI controls."""
        try:
            # Block signals during loading to prevent auto-save triggers
            self.block_settings_signals(True)
            
            # Scan settings
            scan_settings = self.config.get("scan_settings", {})
            max_threads = scan_settings.get("max_threads", 4)
            timeout_seconds = scan_settings.get("timeout_seconds", 300)
            self.settings_max_threads_spin.setValue(max_threads)
            self.settings_timeout_spin.setValue(timeout_seconds)

            # UI settings
            ui_settings = self.config.get("ui_settings", {})
            minimize_to_tray = ui_settings.get("minimize_to_tray", True)
            show_notifications = ui_settings.get("show_notifications", True)
            text_orientation = ui_settings.get("text_orientation", "Centered")
            
            self.settings_minimize_to_tray_cb.setChecked(minimize_to_tray)
            self.settings_show_notifications_cb.setChecked(show_notifications)
            
            # Set text orientation if combo exists
            if hasattr(self, 'text_orientation_combo'):
                self.text_orientation_combo.setCurrentText(text_orientation)
                # Apply the loaded text orientation setting
                self.apply_text_orientation_setting(text_orientation)

            # Activity log retention setting
            retention = str(ui_settings.get("activity_log_retention", 100))
            self.settings_activity_retention_combo.setCurrentText(retention)

            # Security settings
            security_settings = self.config.get("security_settings", {})
            auto_update_defs = security_settings.get("auto_update_definitions", True)
            self.settings_auto_update_cb.setChecked(auto_update_defs)

            # Advanced settings
            advanced_settings = self.config.get("advanced_settings", {})
            scan_archives = advanced_settings.get("scan_archives", True)
            follow_symlinks = advanced_settings.get("follow_symlinks", False)
            self.settings_scan_archives_cb.setChecked(scan_archives)
            self.settings_follow_symlinks_cb.setChecked(follow_symlinks)

            # Advanced scan settings (moved from Scan tab)
            scan_depth = advanced_settings.get("scan_depth", 2)
            for i in range(self.scan_depth_combo.count()):
                if self.scan_depth_combo.itemData(i) == scan_depth:
                    self.scan_depth_combo.setCurrentIndex(i)
                    break
            
            file_filter = advanced_settings.get("file_filter", "all")
            for i in range(self.file_filter_combo.count()):
                if self.file_filter_combo.itemData(i) == file_filter:
                    self.file_filter_combo.setCurrentIndex(i)
                    break
            
            memory_limit = advanced_settings.get("memory_limit", 1024)
            for i in range(self.memory_limit_combo.count()):
                if self.memory_limit_combo.itemData(i) == memory_limit:
                    self.memory_limit_combo.setCurrentIndex(i)
                    break
            
            exclusion_patterns = advanced_settings.get("exclusion_patterns", "")
            self.exclusion_text.setPlainText(exclusion_patterns)

            # Real-time protection settings
            protection_settings = self.config.get("realtime_protection", {})
            monitor_mods = protection_settings.get("monitor_modifications", True)
            monitor_new = protection_settings.get("monitor_new_files", True)
            scan_modified = protection_settings.get("scan_modified_files", False)
            self.settings_monitor_modifications_cb.setChecked(monitor_mods)
            self.settings_monitor_new_files_cb.setChecked(monitor_new)
            self.settings_scan_modified_cb.setChecked(scan_modified)

            # RKHunter settings
            rkhunter_settings = self.config.get("rkhunter_settings", {})
            
            enabled = rkhunter_settings.get("enabled", False)
            run_with_full = rkhunter_settings.get("run_with_full_scan", False)
            run_with_quick = rkhunter_settings.get("run_with_quick_scan", False)
            run_with_custom = rkhunter_settings.get("run_with_custom_scan", False)
            auto_update = rkhunter_settings.get("auto_update", True)
            
            self.settings_enable_rkhunter_cb.setChecked(enabled)
            self.settings_run_rkhunter_with_full_scan_cb.setChecked(run_with_full)
            self.settings_run_rkhunter_with_quick_scan_cb.setChecked(run_with_quick)
            self.settings_run_rkhunter_with_custom_scan_cb.setChecked(run_with_custom)
            self.settings_rkhunter_auto_update_cb.setChecked(auto_update)

            # Load RKHunter category selections
            if hasattr(self, "settings_rkhunter_category_checkboxes"):
                saved_categories = rkhunter_settings.get("categories", {})
                for (
                    category_id,
                    checkbox,
                ) in self.settings_rkhunter_category_checkboxes.items():
                    # Use saved value if available, otherwise use the default
                    # from settings creation
                    if category_id in saved_categories:
                        checkbox.setChecked(saved_categories[category_id])
                    # Note: If not in saved_categories, keep the default set
                    # during checkbox creation

            # Scheduled scan settings
            scheduled_settings = self.config.get("scheduled_settings", {})
            enabled = scheduled_settings.get("enabled", False)
            frequency = scheduled_settings.get("frequency", "daily")
            time_str = scheduled_settings.get("time", "02:00")
            scan_type = scheduled_settings.get("scan_type", "quick")
            custom_directory = scheduled_settings.get("custom_directory", "")
            
            self.settings_enable_scheduled_cb.setChecked(enabled)
            
            # Load scan frequency
            for i in range(self.settings_scan_frequency_combo.count()):
                if self.settings_scan_frequency_combo.itemData(i) == frequency:
                    self.settings_scan_frequency_combo.setCurrentIndex(i)
                    break
            
            # Load scan type
            for i in range(self.settings_scan_type_combo.count()):
                if self.settings_scan_type_combo.itemData(i) == scan_type:
                    self.settings_scan_type_combo.setCurrentIndex(i)
                    break
            
            # Load custom directory
            if custom_directory:
                self.settings_custom_dir_edit.setText(custom_directory)
            
            # Show/hide custom directory widget based on scan type
            self.settings_custom_dir_widget.setVisible(scan_type == "custom")
            
            # Load scan time
            from PyQt6.QtCore import QTime
            time_obj = QTime.fromString(time_str, "HH:mm")
            if time_obj.isValid():
                self.settings_scan_time_edit.setTime(time_obj)
                
            # Auto-update settings
            auto_update_settings = self.config.get("auto_update_settings", {})
            if hasattr(self, 'settings_auto_check_updates_cb'):
                auto_check = auto_update_settings.get("auto_check_updates", True)
                self.settings_auto_check_updates_cb.setChecked(auto_check)
            
            if hasattr(self, 'settings_auto_download_updates_cb'):
                auto_download = auto_update_settings.get("auto_download_updates", False)
                self.settings_auto_download_updates_cb.setChecked(auto_download)
                
            if hasattr(self, 'settings_update_check_interval_spin'):
                check_interval = auto_update_settings.get("update_check_interval", 24)
                self.settings_update_check_interval_spin.setValue(check_interval)
                
            # Re-enable signals after loading is complete
            self.block_settings_signals(False)
            
            # Update UI state for dependent controls after loading
            # This ensures controls are properly enabled/disabled based on loaded settings
            self.update_ui_state_after_loading()

        except (OSError, IOError, PermissionError) as e:
            print(f"❌ Error loading settings: {e}")
            # Make sure to re-enable signals even if there's an error
            self.block_settings_signals(False)

    def load_default_settings(self):
        """Reset all settings to their default values."""
        try:
            # Import the default config
            from utils.config import get_factory_defaults
            
            # Get default configuration
            default_config = get_factory_defaults()
            
            # Update our local config with defaults
            self.config = default_config
            
            # Load the default settings into the UI
            self.load_current_settings()
            
            # Auto-save the default settings
            self.auto_save_settings()

            self.show_themed_message_box(
                "information",
                "Settings",
                "Settings have been reset to defaults and saved.")

        except Exception as e:
            print(f"❌ Error loading default settings: {e}")
            import traceback
            traceback.print_exc()
            self.show_themed_message_box(
                "warning", "Error", f"Could not reset settings: {str(e)}"
            )

    def auto_save_settings(self):
        """Schedule a debounced settings save to reduce disk writes."""
        # 300ms debounce window groups rapid UI changes
        self._settings_save_timer.start(300)
    
    def _auto_save_settings_commit(self):
        """Commit the pending settings to disk (invoked after debounce)."""
        try:
            from utils.config import update_multiple_settings
            
            # Collect all settings in one batch for efficient saving
            settings_updates = {
                "scan_settings": {
                    "max_threads": self.settings_max_threads_spin.value(),
                    "timeout_seconds": self.settings_timeout_spin.value(),
                },
                "ui_settings": {
                    "minimize_to_tray": self.settings_minimize_to_tray_cb.isChecked(),
                    "show_notifications": self.settings_show_notifications_cb.isChecked(),
                    "activity_log_retention": int(
                        self.settings_activity_retention_combo.currentText()
                    ),
                    "theme": self.current_theme,
                    "text_orientation": self.text_orientation_combo.currentText() if hasattr(self, 'text_orientation_combo') else "Centered",
                },
                "security_settings": {
                    "auto_update_definitions": self.settings_auto_update_cb.isChecked(),
                },
                "advanced_settings": {
                    "scan_archives": self.settings_scan_archives_cb.isChecked(),
                    "follow_symlinks": self.settings_follow_symlinks_cb.isChecked(),
                    "scan_depth": self.scan_depth_combo.currentData(),
                    "file_filter": self.file_filter_combo.currentData(),
                    "memory_limit": self.memory_limit_combo.currentData(),
                    "exclusion_patterns": self.exclusion_text.toPlainText().strip(),
                },
                "realtime_protection": {
                    "monitor_modifications": self.settings_monitor_modifications_cb.isChecked(),
                    "monitor_new_files": self.settings_monitor_new_files_cb.isChecked(),
                    "scan_modified_files": self.settings_scan_modified_cb.isChecked(),
                },
                "rkhunter_settings": {
                    "enabled": self.settings_enable_rkhunter_cb.isChecked(),
                    "run_with_full_scan": self.settings_run_rkhunter_with_full_scan_cb.isChecked(),
                    "run_with_quick_scan": self.settings_run_rkhunter_with_quick_scan_cb.isChecked(),
                    "run_with_custom_scan": self.settings_run_rkhunter_with_custom_scan_cb.isChecked(),
                    "auto_update": self.settings_rkhunter_auto_update_cb.isChecked(),
                },
                "scheduled_settings": {
                    "enabled": self.settings_enable_scheduled_cb.isChecked(),
                    "frequency": self.settings_scan_frequency_combo.currentData(),
                    "time": self.settings_scan_time_edit.time().toString("HH:mm"),
                    "scan_type": self.settings_scan_type_combo.currentData(),
                    "custom_directory": self.settings_custom_dir_edit.text(),
                },
                "auto_update_settings": {
                    "auto_check_updates": getattr(self, 'settings_auto_check_updates_cb', None) and self.settings_auto_check_updates_cb.isChecked() if hasattr(self, 'settings_auto_check_updates_cb') else True,
                    "auto_download_updates": getattr(self, 'settings_auto_download_updates_cb', None) and self.settings_auto_download_updates_cb.isChecked() if hasattr(self, 'settings_auto_download_updates_cb') else False,
                    "update_check_interval": getattr(self, 'settings_update_check_interval_spin', None) and self.settings_update_check_interval_spin.value() if hasattr(self, 'settings_update_check_interval_spin') else 24,
                },
            }
            
            # Add RKHunter categories if available
            if hasattr(self, "settings_rkhunter_category_checkboxes"):
                rkhunter_categories = {}
                for category_id, checkbox in self.settings_rkhunter_category_checkboxes.items():
                    rkhunter_categories[category_id] = checkbox.isChecked()
                settings_updates["rkhunter_settings"]["categories"] = rkhunter_categories
            
            # Save all settings in one operation for efficiency
            success = update_multiple_settings(self.config, settings_updates)
            
            if success:
                # Settings auto-saved successfully
                # Update real-time monitor settings if needed
                if hasattr(self, "real_time_monitor") and self.real_time_monitor:
                    try:
                        # Update real-time monitor settings if it's running
                        pass  # Could add real-time settings update here if needed
                    except Exception as monitor_error:
                        print(f"⚠️ Could not update real-time monitor settings: {monitor_error}")
            else:
                print(f"❌ Failed to auto-save settings")

        except Exception as e:
            print(f"❌ Error auto-saving settings: {e}")
            import traceback
            traceback.print_exc()

    def _run_startup_self_check(self):
        """Perform basic integrity & permission checks; log warnings only."""
        try:
            from utils.config import CONFIG_DIR, DATA_DIR, QUARANTINE_DIR, LOG_DIR
            dirs = {
                "config": CONFIG_DIR,
                "data": DATA_DIR,
                "quarantine": QUARANTINE_DIR,
                "logs": LOG_DIR,
            }
            issues = []
            for name, d in dirs.items():
                if not d.exists():
                    issues.append(f"Missing {name} dir: {d}")
                    continue
                if os.name == "posix":
                    mode = d.stat().st_mode & 0o777
                    if name in ("config", "quarantine") and mode not in (0o700, 0o750):
                        # Try to fix quarantine permissions automatically
                        if name == "quarantine":
                            try:
                                d.chmod(0o700)
                                print(f"✅ Fixed quarantine directory permissions: {oct(mode)} → 0o700")
                                continue  # Skip adding to issues since we fixed it
                            except (OSError, PermissionError) as e:
                                issues.append(f"Weak permissions on {name} ({oct(mode)}); expected 0o700 - Failed to fix: {e}")
                                continue
                        issues.append(f"Weak permissions on {name} ({oct(mode)}); expected 0o700")
            # Config sanity keys
            expected_sections = ["scan_settings", "advanced_settings", "security_settings"]
            for sec in expected_sections:
                if sec not in self.config:
                    issues.append(f"Config missing section: {sec}")
            if issues:
                msg = "Startup self-check warnings:\n" + "\n".join(issues)
                print(msg)
        except Exception as e:
            print(f"Self-check error: {e}")

    def block_settings_signals(self, block):
        """Block or unblock signals from settings controls to prevent auto-save during loading."""
        try:
            # Block signals from controls that have early connections or need to be blocked during loading
            controls_to_block = [
                'settings_activity_retention_combo',
                'settings_enable_scheduled_cb', 
                'settings_scan_frequency_combo',
                'settings_scan_time_edit',
                'settings_scan_type_combo',
                'settings_custom_dir_edit',
                'scan_depth_combo',
                'file_filter_combo', 
                'memory_limit_combo',
                'exclusion_text',
                'settings_max_threads_spin',
                'settings_timeout_spin',
                'settings_minimize_to_tray_cb',
                'settings_show_notifications_cb',
                'settings_auto_update_cb',
                'settings_scan_archives_cb',
                'settings_follow_symlinks_cb',
                'settings_monitor_modifications_cb',
                'settings_monitor_new_files_cb',
                'settings_scan_modified_cb',
                'settings_enable_rkhunter_cb',
                'settings_run_rkhunter_with_full_scan_cb',
                'settings_rkhunter_auto_update_cb'
            ]
            
            for control_name in controls_to_block:
                if hasattr(self, control_name):
                    control = getattr(self, control_name)
                    control.blockSignals(block)
                    
            # Also block RKHunter category checkboxes
            if hasattr(self, 'settings_rkhunter_category_checkboxes'):
                for checkbox in self.settings_rkhunter_category_checkboxes.values():
                    checkbox.blockSignals(block)
                    
            action = "Blocked" if block else "Unblocked"
            print(f"🔧 {action} signals for {len(controls_to_block)} controls during settings loading")
                    
        except Exception as e:
            print(f"❌ Error blocking/unblocking signals: {e}")

    def update_ui_state_after_loading(self):
        """Update UI state for dependent controls after loading settings."""
        try:
            # Update scheduled scan controls based on enable checkbox state
            scheduled_enabled = self.settings_enable_scheduled_cb.isChecked()
            self.settings_scan_frequency_combo.setEnabled(scheduled_enabled)
            self.settings_scan_time_edit.setEnabled(scheduled_enabled)
            self.settings_scan_type_combo.setEnabled(scheduled_enabled)
            
            # Update custom directory controls based on scan type and enabled state
            if hasattr(self, 'settings_scan_type_combo'):
                is_custom = self.settings_scan_type_combo.currentData() == "custom"
                self.settings_custom_dir_edit.setEnabled(scheduled_enabled and is_custom)
                self.settings_custom_dir_btn.setEnabled(scheduled_enabled and is_custom)
                self.settings_custom_dir_widget.setVisible(is_custom)
            
            # Update next scheduled scan display if enabled
            if scheduled_enabled:
                self.update_next_scheduled_scan_display()
            else:
                if hasattr(self, 'settings_next_scan_label'):
                    self.settings_next_scan_label.setText("None scheduled")
            
            # Add other dependent UI state updates here as needed
            # For example, if RKHunter enable state affects other controls, etc.
            
        except Exception as e:
            print(f"❌ Error updating UI state after loading: {e}")

    def update_single_setting(self, section, key, value):
        """Update a single setting and save immediately.
        
        Args:
            section: Configuration section (e.g., 'ui_settings')
            key: Setting key within the section
            value: New value for the setting
        """
        try:
            from utils.config import update_config_setting
            success = update_config_setting(self.config, section, key, value)
            
            if not success:
                print(f"⚠️ Failed to save setting {section}.{key}")
                
        except Exception as e:
            print(f"❌ Error updating setting {section}.{key}: {e}")

    def get_setting(self, section, key, default=None):
        """Get a setting value with optional default.
        
        Args:
            section: Configuration section
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default
        """
        try:
            from utils.config import get_config_setting
            return get_config_setting(self.config, section, key, default)
        except Exception as e:
            print(f"❌ Error getting setting {section}.{key}: {e}")
            return default

    # Example usage methods for specific setting updates
    def on_theme_changed(self, new_theme):
        """Called when theme is changed in UI."""
        self.update_single_setting('ui_settings', 'theme', new_theme)
    
    def on_max_threads_changed(self, value):
        """Called when max threads setting is changed."""
        self.update_single_setting('scan_settings', 'max_threads', value)
    
    def on_real_time_protection_toggled(self, enabled):
        """Called when real-time protection is toggled."""
        updates = {
            'realtime_protection': {
                'monitor_modifications': enabled,
                'monitor_new_files': enabled,
            }
        }
        try:
            from utils.config import update_multiple_settings
            update_multiple_settings(self.config, updates)
        except Exception as e:
            print(f"❌ Error updating real-time protection: {e}")

    def setup_auto_save_connections(self):
        """Set up auto-save connections for all settings controls."""
        try:
            # Spin box controls
            self.settings_max_threads_spin.valueChanged.connect(self.auto_save_settings)
            self.settings_timeout_spin.valueChanged.connect(self.auto_save_settings)
            
            # Checkbox controls - UI Settings
            self.settings_minimize_to_tray_cb.toggled.connect(self.auto_save_settings)
            self.settings_show_notifications_cb.toggled.connect(self.auto_save_settings)
            
            # Combo box controls - UI Settings
            if hasattr(self, 'text_orientation_combo'):
                # Note: We don't connect to auto_save_settings here because the combo already 
                # calls apply_text_orientation_setting which calls auto_save_settings
                pass
            
            # Checkbox controls - Security Settings
            self.settings_auto_update_cb.toggled.connect(self.auto_save_settings)
            
            # Checkbox controls - Advanced Settings  
            self.settings_scan_archives_cb.toggled.connect(self.auto_save_settings)
            self.settings_follow_symlinks_cb.toggled.connect(self.auto_save_settings)
            
            # Checkbox controls - Real-time Protection
            self.settings_monitor_modifications_cb.toggled.connect(self.auto_save_settings)
            self.settings_monitor_new_files_cb.toggled.connect(self.auto_save_settings)
            self.settings_scan_modified_cb.toggled.connect(self.auto_save_settings)
            
            # Checkbox controls - RKHunter Settings
            self.settings_enable_rkhunter_cb.toggled.connect(self.auto_save_settings)
            self.settings_run_rkhunter_with_full_scan_cb.toggled.connect(self.auto_save_settings)
            self.settings_run_rkhunter_with_quick_scan_cb.toggled.connect(self.auto_save_settings)
            self.settings_run_rkhunter_with_custom_scan_cb.toggled.connect(self.auto_save_settings)
            
            # RKHunter auto-update checkbox - ensure it's always connected
            try:
                self.settings_rkhunter_auto_update_cb.toggled.connect(self.auto_save_settings)
                print("✅ RKHunter auto-update checkbox connected to auto-save")
            except AttributeError:
                print("⚠️ RKHunter auto-update checkbox not found during connection setup")
            
            # NOTE: Scheduled Scans checkbox connected to on_scheduled_scan_toggled() which calls auto_save_settings()
            self.settings_enable_scheduled_cb.toggled.connect(self.on_scheduled_scan_toggled)
            
            # Combo box controls - Advanced Settings
            self.scan_depth_combo.currentTextChanged.connect(self.auto_save_settings)
            self.file_filter_combo.currentTextChanged.connect(self.auto_save_settings)
            self.memory_limit_combo.currentTextChanged.connect(self.auto_save_settings)
            
            # NOTE: Activity Log Retention combo already has auto-save via on_retention_setting_changed()
            # Do NOT add duplicate connection to avoid double auto-save calls
            
            # Combo box controls - Scheduled Settings
            self.settings_scan_frequency_combo.currentTextChanged.connect(self.auto_save_settings)
            self.settings_scan_type_combo.currentTextChanged.connect(self.auto_save_settings)
            
            # Time edit control
            self.settings_scan_time_edit.timeChanged.connect(self.auto_save_settings)
            
            # Text edit control
            self.exclusion_text.textChanged.connect(self.auto_save_settings)
            
            # RKHunter category checkboxes - connect them to auto-save
            if hasattr(self, 'settings_rkhunter_category_checkboxes'):
                for category_id, checkbox in self.settings_rkhunter_category_checkboxes.items():
                    checkbox.toggled.connect(self.auto_save_settings)
                print(f"✅ Connected {len(self.settings_rkhunter_category_checkboxes)} RKHunter category checkboxes to auto-save")
            else:
                print("⚠️ RKHunter category checkboxes not found during connection setup")
                    
            print("✅ Auto-save connections set up successfully")
            print("📌 Enhanced RKHunter settings auto-save connections")
            
        except Exception as e:
            print(f"⚠️ Error setting up auto-save connections: {e}")

    def _load_clamav_report(self, file_path, scan_id):
        """Load and display a ClamAV report."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert to scan result format for display
            class MockScanResult:
                def __init__(self, data):
                    self.start_time = data.get('start_time', 'Unknown')
                    self.scan_type = type('obj', (object,), {'value': data.get('scan_type', 'Unknown')})
                    self.duration = data.get('duration', 0)
                    self.scanned_files = data.get('scanned_files', 0)
                    self.total_files = data.get('total_files', 0)
                    self.threats_found = data.get('threats_found', 0)
                    self.scanned_paths = data.get('scanned_paths', [])
                    self.threats = []
                    self.errors = data.get('errors', [])
                    
                    # Convert threats to objects if present
                    for threat_data in data.get('threats', []):
                        threat = type('obj', (object,), {
                            'file_path': threat_data.get('file_path', ''),
                            'threat_name': threat_data.get('threat_name', ''),
                            'threat_level': type('obj', (object,), {'value': threat_data.get('threat_level', 'unknown')}),
                            'action_taken': threat_data.get('action_taken', '')
                        })
                        self.threats.append(threat)

            scan_result = MockScanResult(data)
            self._display_clamav_report(scan_result, scan_id)
            
        except Exception as e:
            self._show_report_error(f"Error loading ClamAV report: {e}")

    def _load_rkhunter_report(self, file_path, scan_id):
        """Load and display an RKHunter report."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._display_rkhunter_report(data, scan_id)
            
        except Exception as e:
            self._show_report_error(f"Error loading RKHunter report: {e}")

    def _display_clamav_report(self, scan_result, scan_id):
        """Display a ClamAV scan report."""
        output = f"<h2>🦠 ClamAV Scan Report: {scan_id}</h2>"
        output += f"<p><b>Date:</b> {scan_result.start_time}</p>"
        output += f"<p><b>Scan Type:</b> {scan_result.scan_type.value}</p>"
        output += f"<p><b>Duration:</b> {scan_result.duration:.2f} seconds</p>"
        output += f"<p><b>Files Scanned:</b> {scan_result.scanned_files}/{scan_result.total_files}</p>"
        output += f"<p><b>Threats Found:</b> {scan_result.threats_found}</p>"

        # Add paths that were scanned
        if scan_result.scanned_paths:
            output += "<h3>Scanned Paths:</h3><ul>"
            for path in scan_result.scanned_paths:
                output += f"<li>{path}</li>"
            output += "</ul>"

        # Add threats if any were found
        if scan_result.threats_found > 0:
            output += "<h3>Detected Threats:</h3><table border='1' cellpadding='3'>"
            output += "<tr><th>File</th><th>Threat</th><th>Level</th><th>Action</th></tr>"

            for threat in scan_result.threats:
                threat_level_class = (
                    "error" if threat.threat_level.value == "error"
                    else ("infected" if threat.threat_level.value == "infected"
                          else ("suspicious" if threat.threat_level.value == "suspicious"
                                else "clean")))

                output += f"<tr class='{threat_level_class}'>"
                output += f"<td>{threat.file_path}</td>"
                output += f"<td>{threat.threat_name}</td>"
                output += f"<td>{threat.threat_level.value}</td>"
                output += f"<td>{threat.action_taken}</td>"
                output += "</tr>"

            output += "</table>"
        else:
            output += "<h3>✅ No threats detected!</h3>"

        # Add any errors
        if scan_result.errors:
            output += "<h3>Errors:</h3><ul>"
            for error in scan_result.errors:
                output += f"<li>{error}</li>"
            output += "</ul>"

        self._apply_report_styling(output)

    def _display_rkhunter_report(self, data, scan_id):
        """Display an RKHunter scan report."""
        output = f"<h2>🔍 RKHunter Rootkit Scan Report: {scan_id}</h2>"
        
        # Basic info
        output += f"<p><b>Date:</b> {data.get('start_time', 'Unknown')}</p>"
        output += f"<p><b>Scan Type:</b> {data.get('scan_type', 'Unknown')}</p>"
        output += f"<p><b>Duration:</b> {data.get('duration', 0):.2f} seconds</p>"
        output += f"<p><b>Success:</b> {'Yes' if data.get('success', False) else 'No'}</p>"

        # Statistics
        stats = data.get('statistics', {})
        output += "<h3>Scan Statistics:</h3>"
        output += f"<p><b>Total Tests:</b> {stats.get('total_tests', 0)}</p>"
        output += f"<p><b>Tests Run:</b> {stats.get('tests_run', 0)}</p>"
        output += f"<p><b>Warnings Found:</b> {stats.get('warnings_found', 0)}</p>"
        output += f"<p><b>Infections Found:</b> {stats.get('infections_found', 0)}</p>"
        output += f"<p><b>Skipped Tests:</b> {stats.get('skipped_tests', 0)}</p>"

        # Overall status
        infections = stats.get('infections_found', 0)
        warnings = stats.get('warnings_found', 0)
        
        if infections > 0:
            output += "<h3 style='color: #F14666;'>🚨 CRITICAL: Potential rootkits detected!</h3>"
        elif warnings > 0:
            output += "<h3 style='color: #FFA500;'>⚠️ Warnings found - review carefully</h3>"
        else:
            output += "<h3 style='color: #4CAF50;'>✅ No rootkits detected</h3>"

        # Detailed findings
        findings = data.get('findings', [])
        if findings:
            output += "<h3>Detailed Findings:</h3>"
            output += "<table border='1' cellpadding='3'>"
            output += "<tr><th>Test</th><th>Result</th><th>Severity</th><th>Description</th></tr>"
            
            for finding in findings:
                result_value = finding.get('result', 'unknown')
                status_icon = "🚨" if result_value == "infected" else "⚠️"
                
                output += f"<tr>"
                output += f"<td>{status_icon} {finding.get('test_name', 'Unknown')}</td>"
                output += f"<td>{result_value.upper()}</td>"
                output += f"<td>{finding.get('severity', 'unknown').upper()}</td>"
                output += f"<td>{finding.get('description', 'No description')}</td>"
                output += "</tr>"
            
            output += "</table>"

        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            output += "<h3>Recommendations:</h3><ul>"
            for rec in recommendations:
                output += f"<li>{rec}</li>"
            output += "</ul>"

        # Summary
        summary = data.get('summary', '')
        if summary:
            output += f"<h3>Summary:</h3><p>{summary}</p>"

        # Error message if any
        error_message = data.get('error_message')
        if error_message:
            output += f"<h3>Error:</h3><p style='color: #F14666;'>{error_message}</p>"

        self._apply_report_styling(output)

    def _show_report_error(self, message):
        """Show an error message in the report viewer."""
        if self.current_theme == "dark":
            error_html = f"""
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #FFCDAA;
                    background-color: #2b2b2b;
                    margin: 20px;
                    text-align: center;
                    line-height: 1.6;
                }}
                h3 {{
                    color: #F14666;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #FFCDAA;
                    font-weight: 500;
                }}
            </style>
            <h3>Report Error</h3>
            <p>{message}</p>
            """
        else:
            error_html = f"""
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #2c2c2c;
                    background-color: #fefefe;
                    margin: 20px;
                    text-align: center;
                    line-height: 1.5;
                }}
                h3 {{
                    color: #F89B9B;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #2c2c2c;
                    font-weight: 500;
                }}
            </style>
            <h3>Report Error</h3>
            <p>{message}</p>
            """
        self.report_viewer.setHtml(error_html)

    def _apply_report_styling(self, output):
        """Apply theme-appropriate styling to report output."""
        if self.current_theme == "dark":
            # Dark mode styling with Strawberry color palette
            styled_output = f"""
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #FFCDAA;
                    background-color: #2b2b2b;
                    margin: 8px;
                    line-height: 1.6;
                }}
                h2 {{
                    color: #F14666;
                    font-weight: 700;
                    margin-top: 16px;
                    margin-bottom: 12px;
                    border-bottom: 2px solid #EE8980;
                    padding-bottom: 8px;
                }}
                h3 {{
                    color: #EE8980;
                    font-weight: 600;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 12px 0;
                    background-color: #3a3a3a;
                    border: 1px solid #EE8980;
                }}
                th {{
                    background-color: #F14666;
                    color: #FFFFFF;
                    font-weight: 600;
                    padding: 10px;
                    text-align: left;
                    border: 1px solid #EE8980;
                }}
                td {{
                    padding: 8px 10px;
                    border: 1px solid #EE8980;
                    color: #FFCDAA;
                }}
                tr.error td {{
                    background-color: #5D1A20;
                    color: #F14666;
                    font-weight: 600;
                }}
                tr.infected td {{
                    background-color: #5D1A20;
                    color: #F14666;
                    font-weight: 600;
                }}
                tr.suspicious td {{
                    background-color: #4A3419;
                    color: #F0A500;
                }}
                ul {{
                    margin: 12px 0;
                    padding-left: 25px;
                }}
                li {{
                    margin: 4px 0;
                    color: #FFCDAA;
                }}
                b {{
                    color: #EE8980;
                    font-weight: 600;
                }}
                p {{
                    margin: 8px 0;
                    color: #FFCDAA;
                }}
            </style>
            {output}
            """
        else:
            # Light mode styling with balanced contrast
            styled_output = f"""
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #2c2c2c;
                    background-color: #fefefe;
                    margin: 8px;
                    line-height: 1.5;
                }}
                h2 {{
                    color: #75BDE0;
                    font-weight: 700;
                    margin-top: 16px;
                    margin-bottom: 12px;
                    border-bottom: 2px solid #F89B9B;
                    padding-bottom: 8px;
                }}
                h3 {{
                    color: #F89B9B;
                    font-weight: 600;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 12px 0;
                    background-color: #f9f9f9;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #75BDE0;
                    color: #FFFFFF;
                    font-weight: 600;
                    padding: 10px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                td {{
                    padding: 8px 10px;
                    border: 1px solid #ddd;
                    color: #2c2c2c;
                }}
                tr.error td {{
                    background-color: #ffe6e6;
                    color: #d32f2f;
                    font-weight: 600;
                }}
                tr.infected td {{
                    background-color: #ffe6e6;
                    color: #d32f2f;
                    font-weight: 600;
                }}
                tr.suspicious td {{
                    background-color: #fff3cd;
                    color: #856404;
                }}
                ul {{
                    margin: 12px 0;
                    padding-left: 25px;
                }}
                li {{
                    margin: 4px 0;
                    color: #2c2c2c;
                }}
                b {{
                    color: #75BDE0;
                    font-weight: 600;
                }}
                p {{
                    margin: 8px 0;
                    color: #2c2c2c;
                }}
            </style>
            {output}
            """

        self.report_viewer.setHtml(styled_output)
