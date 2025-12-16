"""Live Threat Visualization Dashboard Demo.

Demonstrates the real-time threat visualization dashboard with sample data.
Run this to see the dashboard in action with simulated threat events.

Phase 2, Task 2.1.1: Live Threat Visualization

Usage:
    python examples/dashboard_demo.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from random import randint, choice, uniform

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import QTimer

# Dashboard imports
from app.gui.dashboard import ThreatVisualizationWidget


class DashboardDemo(QMainWindow):
    """Demo window showing threat visualization dashboard."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛡️ xanadOS Threat Visualization Dashboard - Demo")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create dashboard widget
        self.dashboard = ThreatVisualizationWidget(
            max_events=1000, refresh_interval_ms=1000
        )
        layout.addWidget(self.dashboard)

        # Control buttons
        button_layout = QHBoxLayout()

        add_threat_btn = QPushButton("➕ Add Random Threat")
        add_threat_btn.clicked.connect(self.add_random_threat)
        button_layout.addWidget(add_threat_btn)

        add_10_btn = QPushButton("➕➕ Add 10 Threats")
        add_10_btn.clicked.connect(
            lambda: [self.add_random_threat() for _ in range(10)]
        )
        button_layout.addWidget(add_10_btn)

        add_100_btn = QPushButton("➕💯 Add 100 Threats")
        add_100_btn.clicked.connect(
            lambda: [self.add_random_threat() for _ in range(100)]
        )
        button_layout.addWidget(add_100_btn)

        start_simulation_btn = QPushButton("▶️ Start Simulation")
        start_simulation_btn.clicked.connect(self.start_simulation)
        button_layout.addWidget(start_simulation_btn)

        stop_simulation_btn = QPushButton("⏹️ Stop Simulation")
        stop_simulation_btn.clicked.connect(self.stop_simulation)
        button_layout.addWidget(stop_simulation_btn)

        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.dashboard.clear_all)
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)

        # Connect signals
        self.dashboard.threat_added.connect(self.on_threat_added)
        self.dashboard.view_changed.connect(self.on_view_changed)

        # Simulation timer
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.add_random_threat)
        self.simulation_timer.setInterval(500)  # Add threat every 500ms

        # Sample data for demo
        self.threat_types = [
            "Ransomware",
            "Trojan",
            "Worm",
            "Spyware",
            "Adware",
            "Rootkit",
            "Backdoor",
            "Keylogger",
            "Botnet",
            "Exploit",
        ]

        self.severities = ["low", "medium", "high", "critical"]

        self.locations = [
            ("New York, USA", 40.7128, -74.0060),
            ("London, UK", 51.5074, -0.1278),
            ("Tokyo, Japan", 35.6762, 139.6503),
            ("Berlin, Germany", 52.5200, 13.4050),
            ("Moscow, Russia", 55.7558, 37.6173),
            ("Beijing, China", 39.9042, 116.4074),
            ("Sydney, Australia", -33.8688, 151.2093),
            ("São Paulo, Brazil", -23.5505, -46.6333),
            ("Mumbai, India", 19.0760, 72.8777),
            ("Dubai, UAE", 25.2048, 55.2708),
        ]

        # Add initial sample data
        self.add_sample_data()

    def add_sample_data(self):
        """Add initial sample threats to demonstrate dashboard."""
        print("Adding sample data...")

        # Add historical threats (past 24 hours)
        now = datetime.now()
        for i in range(50):
            # Random time in past 24 hours
            hours_ago = randint(1, 24)
            threat_time = now - timedelta(hours=hours_ago)

            city, lat, lon = choice(self.locations)

            self.dashboard.add_threat(
                threat_type=choice(self.threat_types),
                severity=choice(self.severities),
                file_path=f"/tmp/sample_{i}.exe",
                description=f"Sample threat detected {hours_ago}h ago",
                latitude=lat,
                longitude=lon,
                metadata={
                    "scanner": choice(["clamav", "yara", "ml_detector"]),
                    "confidence": round(uniform(0.7, 1.0), 2),
                    "location": city,
                    "timestamp": threat_time.isoformat(),
                },
            )

        print(f"Added 50 sample threats spanning past 24 hours")

    def add_random_threat(self):
        """Add a random threat to the dashboard."""
        city, lat, lon = choice(self.locations)
        threat_type = choice(self.threat_types)
        severity = choice(self.severities)

        # Add some randomness to coordinates (within ±2 degrees)
        lat += uniform(-2, 2)
        lon += uniform(-2, 2)

        self.dashboard.add_threat(
            threat_type=threat_type,
            severity=severity,
            file_path=f"/tmp/threat_{randint(1000, 9999)}.bin",
            description=f"{threat_type} detected near {city}",
            latitude=lat,
            longitude=lon,
            metadata={
                "scanner": choice(["clamav", "yara", "ml_detector"]),
                "confidence": round(uniform(0.6, 1.0), 2),
                "location": city,
                "source_ip": f"{randint(1, 255)}.{randint(1, 255)}.{randint(1, 255)}.{randint(1, 255)}",
            },
        )

    def start_simulation(self):
        """Start automatic threat simulation."""
        print("Starting threat simulation (1 threat every 500ms)...")
        self.simulation_timer.start()

    def stop_simulation(self):
        """Stop automatic threat simulation."""
        print("Stopping threat simulation")
        self.simulation_timer.stop()

    def on_threat_added(self, threat):
        """Handle threat_added signal."""
        print(f"Threat added: {threat}")

    def on_view_changed(self, view_name):
        """Handle view_changed signal."""
        print(f"View changed to: {view_name}")


def main():
    """Run the dashboard demo."""
    app = QApplication(sys.argv)

    # Create and show demo window
    demo = DashboardDemo()
    demo.show()

    print("=" * 80)
    print("🛡️  xanadOS Threat Visualization Dashboard Demo")
    print("=" * 80)
    print()
    print("Controls:")
    print("  ➕ Add Random Threat    - Add a single random threat")
    print("  ➕➕ Add 10 Threats      - Add 10 random threats")
    print("  ➕💯 Add 100 Threats     - Add 100 random threats")
    print("  ▶️  Start Simulation    - Auto-add threats every 500ms")
    print("  ⏹️  Stop Simulation     - Stop automatic simulation")
    print("  🗑️  Clear All          - Remove all threats")
    print()
    print("Features:")
    print(
        "  📊 Timeline Tab        - Interactive threat timeline with time range filtering"
    )
    print("  🗺️  Map Tab            - Geographic visualization with location clustering")
    print("  🔥 Heatmap Tab        - 2D severity heatmap (type vs location)")
    print()
    print("Demonstrated Capabilities:")
    print("  ✓ Real-time threat visualization")
    print("  ✓ Max 1000 events with FIFO eviction")
    print("  ✓ Severity-based color coding")
    print("  ✓ Thread-safe event addition")
    print("  ✓ Auto-refresh (1s timeline, 5s heatmap)")
    print("  ✓ Statistics tracking (total, active, critical)")
    print()
    print("=" * 80)

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
