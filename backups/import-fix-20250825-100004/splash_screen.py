#!/usr/bin/env python3
"""
Modern Splash Screen for xanadOS Search & Destroy
Progressive loading with real-time progress tracking (2025)

Features:
- Official xanadOS Search & Destroy logo display
- Progressive loading phases with visual feedback
- Modern dark theme with coral accent colors
- Smooth animations and professional appearance
- Fallback handling for missing logo files
"""

import os
import sys
from typing import Optional, Callable
from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen, QBrush
from pathlib import Path

class ModernSplashScreen(QSplashScreen):
    """
    Modern splash screen with progress tracking and phase-based loading.
    Following 2025 best practices for user experience.
    """

    progress_updated = pyqtSignal(int, str)  # progress, message
    phase_completed = pyqtSignal(str)  # phase_name

    def __init__(self, width=600, height=400):
        # Create a modern splash pixmap
        pixmap = self.create_modern_pixmap(width, height)
        super().__init__(pixmap)

        # Set splash screen flags for modern behavior
        self.setWindowFlags(
            Qt.WindowType.SplashScreen |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Initialize progress tracking
        self.current_progress = 0
        self.current_message = "Initializing xanadOS Search & Destroy..."
        self.phases = {
            "ui_init": {"progress": 20, "message": "Loading user interface..."},
            "cache_init": {"progress": 40, "message": "Initializing cache system..."},
            "system_check": {"progress": 60, "message": "Checking system status..."},
            "dashboard_load": {"progress": 80, "message": "Loading dashboard..."},
            "finalization": {"progress": 100, "message": "Finalizing startup..."}
        }

        # Connect signals
        self.progress_updated.connect(self.update_display)

        # Auto-update timer for smooth progress
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.repaint)
        self.update_timer.start(16)  # 60 FPS for smooth updates

    def create_modern_pixmap(self, width: int, height: int) -> QPixmap:
        """Create a modern, professional splash screen pixmap with logo."""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(43, 43, 43))  # Dark professional background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Load and draw the logo
        try:
            # Get the project root directory
            current_dir = Path(__file__).parent.parent.parent
            logo_path = current_dir / "packaging" / "icons" / "io.github.asafelobotomy.SearchAndDestroy.png"

            if logo_path.exists():
                logo_pixmap = QPixmap(str(logo_path))
                if not logo_pixmap.isNull():
                    # Scale logo to appropriate size (64x64 for splash screen)
                    logo_size = 64
                    scaled_logo = logo_pixmap.scaled(
                        logo_size, logo_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                    # Center the logo horizontally, place it at the top
                    logo_x = (width - logo_size) // 2
                    logo_y = 20
                    painter.drawPixmap(logo_x, logo_y, scaled_logo)

                    # Adjust text positions to accommodate logo
                    title_y_offset = logo_y + logo_size + 20
                else:
                    # Fallback if logo can't be loaded
                    title_y_offset = 50
            else:
                # Fallback if logo file doesn't exist
                title_y_offset = 50

        except Exception as e:
            # Fallback if there's any error loading the logo
            title_y_offset = 50

        # Main title (adjusted position)
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 255, 255))  # White text
        painter.drawText(0, title_y_offset, width, 50, Qt.AlignmentFlag.AlignCenter,
                        "xanadOS Search & Destroy")

        # Subtitle (adjusted position)
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(224, 224, 224))  # Light gray
        painter.drawText(0, title_y_offset + 50, width, 30, Qt.AlignmentFlag.AlignCenter,
                        "Advanced Malware Detection & System Protection")

        # Version info (adjusted position)
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(229, 115, 115))  # Coral accent
        painter.drawText(0, title_y_offset + 80, width, 20, Qt.AlignmentFlag.AlignCenter,
                        "Version 2.9.0 - Professional Edition")

        # Draw accent line (adjusted position)
        accent_line_y = title_y_offset + 110
        painter.setPen(QPen(QColor(229, 115, 115), 2))
        painter.drawLine(100, accent_line_y, width - 100, accent_line_y)

        painter.end()
        return pixmap

    def update_progress(self, phase: str):
        """Update progress for a specific phase."""
        if phase in self.phases:
            phase_data = self.phases[phase]
            self.current_progress = phase_data["progress"]
            self.current_message = phase_data["message"]
            self.progress_updated.emit(self.current_progress, self.current_message)
            self.phase_completed.emit(phase)

    def update_display(self, progress: int, message: str):
        """Update the display with new progress and message."""
        self.current_progress = progress
        self.current_message = message
        self.showMessage(
            f"{message} ({progress}%)",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor(255, 255, 255)
        )

    def drawContents(self, painter: QPainter):
        """Custom drawing for modern progress display."""
        super().drawContents(painter)

        # Draw progress bar at bottom
        progress_rect_y = self.height() - 60
        progress_rect = painter.fontMetrics().boundingRect(
            20, progress_rect_y, self.width() - 40, 20,
            Qt.AlignmentFlag.AlignLeft, "Progress"
        )

        # Background progress bar
        painter.fillRect(20, progress_rect_y, self.width() - 40, 8,
                        QColor(64, 64, 64))

        # Progress fill
        progress_width = int((self.width() - 40) * (self.current_progress / 100))
        painter.fillRect(20, progress_rect_y, progress_width, 8,
                        QColor(229, 115, 115))  # Coral progress

        # Status message
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(20, progress_rect_y + 25, self.current_message)

    def finish_splash(self, main_window):
        """Smoothly finish the splash screen and show main window."""
        self.update_timer.stop()
        self.update_progress("finalization")

        # Smooth transition with timer
        QTimer.singleShot(500, lambda: self.finish(main_window))


class StartupProgressTracker:
    """
    Tracks startup progress across different components.
    Implements modern progress tracking patterns.
    """

    def __init__(self, splash_screen: ModernSplashScreen):
        self.splash = splash_screen
        self.start_time = None
        self.phase_times = {}

    def start_tracking(self):
        """Start tracking startup time."""
        import time
        self.start_time = time.time()

    def complete_phase(self, phase: str):
        """Mark a phase as complete and update splash."""
        import time
        if self.start_time:
            self.phase_times[phase] = time.time() - self.start_time

        self.splash.update_progress(phase)
        print(f"✅ Phase '{phase}' completed in {self.phase_times.get(phase, 0):.2f}s")

    def get_total_time(self) -> float:
        """Get total startup time."""
        import time
        if self.start_time:
            return time.time() - self.start_time
        return 0.0

    def print_summary(self):
        """Print startup performance summary."""
        total_time = self.get_total_time()
        print(f"\n🚀 Startup Performance Summary:")
        print(f"Total startup time: {total_time:.2f}s")
        for phase, time_taken in self.phase_times.items():
            print(f"  {phase}: {time_taken:.2f}s")
