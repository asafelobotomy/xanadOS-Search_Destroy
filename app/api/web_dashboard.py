#!/usr/bin/env python3
"""Web-based Security Dashboard for xanadOS Search & Destroy.

This module provides a modern web-based dashboard using FastAPI and WebSockets
for real-time security monitoring. It complements the Qt-based dashboard with
web accessibility and responsive design.

Features:
- Real-time WebSocket updates for live data
- RESTful API for dashboard data
- Interactive charts using Plotly
- Responsive web interface
- Mobile-friendly design
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.gui.security_dashboard import (
    RealTimeDataCollector,
    ThreatEvent,
    SystemMetrics,
    DashboardConfig,
)
from app.core.ml_threat_detector import MLThreatDetector
from app.core.edr_engine import EDREngine
from app.core.unified_memory_management import get_memory_manager


class WebDashboardManager:
    """Manager for web-based security dashboard."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(
            title="xanadOS Security Dashboard API",
            description="Real-time security monitoring and threat intelligence",
            version="2.0.0",
        )

        # Initialize components
        self.data_collector = None
        self.active_connections: list[WebSocket] = []
        self.recent_threats: list[ThreatEvent] = []
        self.recent_metrics: list[SystemMetrics] = []
        self.max_history = 1000

        # Setup FastAPI app
        self.setup_app()

    def setup_app(self):
        """Setup FastAPI application with routes and middleware."""

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self.setup_routes()

        # Setup static files (for dashboard assets)
        dashboard_static = Path(__file__).parent / "dashboard_static"
        if dashboard_static.exists():
            self.app.mount(
                "/static", StaticFiles(directory=str(dashboard_static)), name="static"
            )

    def setup_routes(self):
        """Setup API routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve the main dashboard page."""
            return self.get_dashboard_html()

        @self.app.get("/api/health")
        async def health_check():
            """API health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {
                    "data_collector": self.data_collector is not None,
                    "active_connections": len(self.active_connections),
                },
            }

        @self.app.get("/api/dashboard/overview")
        async def dashboard_overview():
            """Get dashboard overview data."""
            try:
                if not self.data_collector:
                    raise HTTPException(
                        status_code=503, detail="Data collector not initialized"
                    )

                # Get recent threats summary
                recent_threats = [
                    t for t in self.recent_threats if time.time() - t.timestamp < 3600
                ]  # Last hour

                threat_summary = {
                    "total": len(recent_threats),
                    "critical": len(
                        [t for t in recent_threats if t.severity == "CRITICAL"]
                    ),
                    "high": len([t for t in recent_threats if t.severity == "HIGH"]),
                    "medium": len(
                        [t for t in recent_threats if t.severity == "MEDIUM"]
                    ),
                    "low": len([t for t in recent_threats if t.severity == "LOW"]),
                }

                # Get latest metrics
                latest_metrics = (
                    self.recent_metrics[-1] if self.recent_metrics else None
                )

                return {
                    "timestamp": time.time(),
                    "threats": threat_summary,
                    "system_metrics": {
                        "cpu_usage": latest_metrics.cpu_usage if latest_metrics else 0,
                        "memory_usage": (
                            latest_metrics.memory_usage if latest_metrics else 0
                        ),
                        "scan_rate": latest_metrics.scan_rate if latest_metrics else 0,
                        "active_processes": (
                            latest_metrics.active_processes if latest_metrics else 0
                        ),
                    },
                    "status": "operational",
                }

            except Exception as e:
                self.logger.error(f"Error getting dashboard overview: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/threats")
        async def get_threats(
            limit: int = 100,
            severity: str | None = None,
            event_type: str | None = None,
            hours: int = 24,
        ):
            """Get recent threats with filtering."""
            try:
                # Filter by time
                cutoff_time = time.time() - (hours * 3600)
                filtered_threats = [
                    t for t in self.recent_threats if t.timestamp >= cutoff_time
                ]

                # Apply filters
                if severity:
                    filtered_threats = [
                        t for t in filtered_threats if t.severity == severity.upper()
                    ]

                if event_type:
                    filtered_threats = [
                        t
                        for t in filtered_threats
                        if t.event_type == event_type.upper()
                    ]

                # Sort by timestamp (most recent first)
                filtered_threats.sort(key=lambda x: x.timestamp, reverse=True)

                # Limit results
                filtered_threats = filtered_threats[:limit]

                # Convert to dict format
                threats_data = []
                for threat in filtered_threats:
                    threats_data.append(
                        {
                            "event_id": threat.event_id,
                            "timestamp": threat.timestamp,
                            "datetime": datetime.fromtimestamp(
                                threat.timestamp
                            ).isoformat(),
                            "event_type": threat.event_type,
                            "severity": threat.severity,
                            "source": threat.source,
                            "target": threat.target,
                            "description": threat.description,
                            "confidence": threat.confidence,
                            "status": threat.status,
                            "geolocation": threat.geolocation,
                        }
                    )

                return {
                    "threats": threats_data,
                    "total_count": len(threats_data),
                    "query_time": time.time(),
                }

            except Exception as e:
                self.logger.error(f"Error getting threats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/metrics")
        async def get_metrics(limit: int = 100, hours: int = 1):
            """Get recent system metrics."""
            try:
                # Filter by time
                cutoff_time = time.time() - (hours * 3600)
                filtered_metrics = [
                    m for m in self.recent_metrics if m.timestamp >= cutoff_time
                ]

                # Sort by timestamp
                filtered_metrics.sort(key=lambda x: x.timestamp)

                # Limit results
                filtered_metrics = filtered_metrics[-limit:]

                # Convert to dict format
                metrics_data = []
                for metric in filtered_metrics:
                    metrics_data.append(
                        {
                            "timestamp": metric.timestamp,
                            "datetime": datetime.fromtimestamp(
                                metric.timestamp
                            ).isoformat(),
                            "cpu_usage": metric.cpu_usage,
                            "memory_usage": metric.memory_usage,
                            "disk_usage": metric.disk_usage,
                            "scan_rate": metric.scan_rate,
                            "threat_detection_rate": metric.threat_detection_rate,
                            "active_connections": metric.active_connections,
                            "active_processes": metric.active_processes,
                        }
                    )

                return {
                    "metrics": metrics_data,
                    "total_count": len(metrics_data),
                    "query_time": time.time(),
                }

            except Exception as e:
                self.logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/charts/threat-timeline")
        async def threat_timeline_chart(hours: int = 24):
            """Generate threat timeline chart data."""
            try:
                # Get threats from the specified time period
                cutoff_time = time.time() - (hours * 3600)
                threats = [t for t in self.recent_threats if t.timestamp >= cutoff_time]

                # Group threats by hour
                hourly_counts = {}
                for threat in threats:
                    hour = datetime.fromtimestamp(threat.timestamp).replace(
                        minute=0, second=0, microsecond=0
                    )
                    hour_key = hour.isoformat()

                    if hour_key not in hourly_counts:
                        hourly_counts[hour_key] = {
                            "total": 0,
                            "critical": 0,
                            "high": 0,
                            "medium": 0,
                            "low": 0,
                        }

                    hourly_counts[hour_key]["total"] += 1
                    hourly_counts[hour_key][threat.severity.lower()] += 1

                # Convert to chart format
                chart_data = {
                    "labels": list(hourly_counts.keys()),
                    "datasets": [
                        {
                            "label": "Critical",
                            "data": [
                                hourly_counts[h]["critical"] for h in hourly_counts
                            ],
                            "backgroundColor": "#e74c3c",
                        },
                        {
                            "label": "High",
                            "data": [hourly_counts[h]["high"] for h in hourly_counts],
                            "backgroundColor": "#f39c12",
                        },
                        {
                            "label": "Medium",
                            "data": [hourly_counts[h]["medium"] for h in hourly_counts],
                            "backgroundColor": "#f1c40f",
                        },
                        {
                            "label": "Low",
                            "data": [hourly_counts[h]["low"] for h in hourly_counts],
                            "backgroundColor": "#95a5a6",
                        },
                    ],
                }

                return chart_data

            except Exception as e:
                self.logger.error(f"Error generating threat timeline chart: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time dashboard updates."""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                self.logger.info(
                    f"New WebSocket connection established. Total: {len(self.active_connections)}"
                )

                # Send initial data
                await self.send_initial_data(websocket)

                # Keep connection alive
                while True:
                    try:
                        # Wait for ping or client messages
                        await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send_text(
                            json.dumps({"type": "ping", "timestamp": time.time()})
                        )
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")

            finally:
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
                self.logger.info(
                    f"WebSocket connection closed. Remaining: {len(self.active_connections)}"
                )

    async def send_initial_data(self, websocket: WebSocket):
        """Send initial dashboard data to new WebSocket connection."""
        try:
            # Send recent threats
            recent_threats = self.recent_threats[-50:]  # Last 50 threats
            for threat in recent_threats:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "threat_event",
                            "data": {
                                "event_id": threat.event_id,
                                "timestamp": threat.timestamp,
                                "event_type": threat.event_type,
                                "severity": threat.severity,
                                "source": threat.source,
                                "target": threat.target,
                                "description": threat.description,
                                "confidence": threat.confidence,
                            },
                        }
                    )
                )

            # Send recent metrics
            recent_metrics = self.recent_metrics[-10:]  # Last 10 metrics
            for metric in recent_metrics:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "metrics_update",
                            "data": {
                                "timestamp": metric.timestamp,
                                "cpu_usage": metric.cpu_usage,
                                "memory_usage": metric.memory_usage,
                                "scan_rate": metric.scan_rate,
                                "threat_detection_rate": metric.threat_detection_rate,
                            },
                        }
                    )
                )

        except Exception as e:
            self.logger.error(f"Error sending initial data: {e}")

    async def broadcast_threat_event(self, threat: ThreatEvent):
        """Broadcast new threat event to all connected WebSocket clients."""
        if not self.active_connections:
            return

        message = json.dumps(
            {
                "type": "threat_event",
                "data": {
                    "event_id": threat.event_id,
                    "timestamp": threat.timestamp,
                    "datetime": datetime.fromtimestamp(threat.timestamp).isoformat(),
                    "event_type": threat.event_type,
                    "severity": threat.severity,
                    "source": threat.source,
                    "target": threat.target,
                    "description": threat.description,
                    "confidence": threat.confidence,
                    "status": threat.status,
                },
            }
        )

        # Send to all connected clients
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.warning(
                    f"Failed to send threat event to WebSocket client: {e}"
                )
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.active_connections.remove(ws)

    async def broadcast_metrics_update(self, metrics: SystemMetrics):
        """Broadcast metrics update to all connected WebSocket clients."""
        if not self.active_connections:
            return

        message = json.dumps(
            {
                "type": "metrics_update",
                "data": {
                    "timestamp": metrics.timestamp,
                    "datetime": datetime.fromtimestamp(metrics.timestamp).isoformat(),
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "disk_usage": metrics.disk_usage,
                    "scan_rate": metrics.scan_rate,
                    "threat_detection_rate": metrics.threat_detection_rate,
                    "active_connections": metrics.active_connections,
                    "active_processes": metrics.active_processes,
                },
            }
        )

        # Send to all connected clients
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.warning(f"Failed to send metrics to WebSocket client: {e}")
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.active_connections.remove(ws)

    def get_dashboard_html(self) -> str:
        """Generate the main dashboard HTML page."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xanadOS Security Operations Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1a1a1a;
            color: #ecf0f1;
            line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, #2c3e50, #34495e);
            padding: 1rem 2rem;
            border-bottom: 3px solid #4ecdc4;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .header h1 {
            color: #4ecdc4;
            font-size: 2rem;
            font-weight: 700;
        }

        .header .status {
            color: #2ecc71;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .widget {
            background-color: #2c3e50;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border: 1px solid #34495e;
        }

        .widget-header {
            color: #4ecdc4;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            border-bottom: 2px solid #4ecdc4;
            padding-bottom: 0.5rem;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            margin: 1rem 0;
        }

        .metric-cpu { color: #3498db; }
        .metric-memory { color: #e74c3c; }
        .metric-scan { color: #2ecc71; }

        .threat-item {
            background-color: #34495e;
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid;
        }

        .threat-critical { border-left-color: #e74c3c; }
        .threat-high { border-left-color: #f39c12; }
        .threat-medium { border-left-color: #f1c40f; }
        .threat-low { border-left-color: #95a5a6; }

        .threat-time {
            font-size: 0.8rem;
            color: #bdc3c7;
        }

        .chart-container {
            height: 300px;
            margin-top: 1rem;
        }

        .connection-status {
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .connected {
            background-color: #2ecc71;
            color: white;
        }

        .disconnected {
            background-color: #e74c3c;
            color: white;
        }

        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
                padding: 1rem;
            }

            .header {
                padding: 1rem;
            }

            .header h1 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>xanadOS Security Operations Center</h1>
        <div class="status">Real-time Security Monitoring & Threat Intelligence</div>
    </div>

    <div class="connection-status disconnected" id="connectionStatus">
        Connecting...
    </div>

    <div class="dashboard-grid">
        <!-- CPU Usage Widget -->
        <div class="widget">
            <div class="widget-header">CPU Usage</div>
            <div class="metric-value metric-cpu" id="cpuUsage">--</div>
            <div class="chart-container">
                <canvas id="cpuChart"></canvas>
            </div>
        </div>

        <!-- Memory Usage Widget -->
        <div class="widget">
            <div class="widget-header">Memory Usage</div>
            <div class="metric-value metric-memory" id="memoryUsage">--</div>
            <div class="chart-container">
                <canvas id="memoryChart"></canvas>
            </div>
        </div>

        <!-- Scan Rate Widget -->
        <div class="widget">
            <div class="widget-header">Scan Rate</div>
            <div class="metric-value metric-scan" id="scanRate">--</div>
            <div class="chart-container">
                <canvas id="scanChart"></canvas>
            </div>
        </div>

        <!-- Threat Timeline Widget -->
        <div class="widget" style="grid-column: span 2;">
            <div class="widget-header">Threat Timeline</div>
            <div class="chart-container" style="height: 400px;">
                <div id="threatTimeline"></div>
            </div>
        </div>

        <!-- Recent Threats Widget -->
        <div class="widget">
            <div class="widget-header">Recent Threats</div>
            <div id="recentThreats" style="max-height: 400px; overflow-y: auto;">
                <!-- Threats will be populated dynamically -->
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection
        let ws;
        let cpuChart, memoryChart, scanChart;
        let cpuData = [], memoryData = [], scanData = [];
        let timeLabels = [];
        const maxDataPoints = 30;

        // Initialize charts
        function initCharts() {
            const chartOptions = {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#444' },
                        ticks: { color: '#ecf0f1' }
                    },
                    x: {
                        grid: { color: '#444' },
                        ticks: { color: '#ecf0f1' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            };

            // CPU Chart
            cpuChart = new Chart(document.getElementById('cpuChart'), {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        data: cpuData,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    }]
                },
                options: chartOptions
            });

            // Memory Chart
            memoryChart = new Chart(document.getElementById('memoryChart'), {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        data: memoryData,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4
                    }]
                },
                options: chartOptions
            });

            // Scan Rate Chart (different scale)
            const scanOptions = { ...chartOptions };
            scanOptions.scales.y.max = null;

            scanChart = new Chart(document.getElementById('scanChart'), {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        data: scanData,
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        tension: 0.4
                    }]
                },
                options: scanOptions
            });

            // Initialize threat timeline
            initThreatTimeline();
        }

        function initThreatTimeline() {
            const layout = {
                paper_bgcolor: '#2c3e50',
                plot_bgcolor: '#34495e',
                font: { color: '#ecf0f1' },
                xaxis: { gridcolor: '#444' },
                yaxis: { gridcolor: '#444' },
                margin: { t: 20, b: 40, l: 40, r: 20 }
            };

            Plotly.newPlot('threatTimeline', [], layout);
        }

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'connection-status connected';
            };

            ws.onclose = function() {
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').className = 'connection-status disconnected';

                // Attempt to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);

                if (message.type === 'metrics_update') {
                    updateMetrics(message.data);
                } else if (message.type === 'threat_event') {
                    addThreatEvent(message.data);
                }
            };
        }

        function updateMetrics(data) {
            // Update metric values
            document.getElementById('cpuUsage').textContent = `${data.cpu_usage.toFixed(1)}%`;
            document.getElementById('memoryUsage').textContent = `${data.memory_usage.toFixed(1)}%`;
            document.getElementById('scanRate').textContent = `${data.scan_rate.toFixed(1)} f/s`;

            // Update charts
            const timeLabel = new Date(data.timestamp * 1000).toLocaleTimeString();

            if (timeLabels.length >= maxDataPoints) {
                timeLabels.shift();
                cpuData.shift();
                memoryData.shift();
                scanData.shift();
            }

            timeLabels.push(timeLabel);
            cpuData.push(data.cpu_usage);
            memoryData.push(data.memory_usage);
            scanData.push(data.scan_rate);

            cpuChart.update('none');
            memoryChart.update('none');
            scanChart.update('none');
        }

        function addThreatEvent(threat) {
            const threatsContainer = document.getElementById('recentThreats');

            const threatDiv = document.createElement('div');
            threatDiv.className = `threat-item threat-${threat.severity.toLowerCase()}`;

            const timeStr = new Date(threat.timestamp * 1000).toLocaleTimeString();

            threatDiv.innerHTML = `
                <div style="font-weight: bold;">${threat.event_type}</div>
                <div>${threat.description}</div>
                <div class="threat-time">${timeStr} - Confidence: ${(threat.confidence * 100).toFixed(0)}%</div>
            `;

            threatsContainer.insertBefore(threatDiv, threatsContainer.firstChild);

            // Keep only recent threats (max 20)
            while (threatsContainer.children.length > 20) {
                threatsContainer.removeChild(threatsContainer.lastChild);
            }
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            connectWebSocket();

            // Load initial data
            fetch('/api/dashboard/overview')
                .then(response => response.json())
                .then(data => {
                    if (data.system_metrics) {
                        document.getElementById('cpuUsage').textContent = `${data.system_metrics.cpu_usage.toFixed(1)}%`;
                        document.getElementById('memoryUsage').textContent = `${data.system_metrics.memory_usage.toFixed(1)}%`;
                        document.getElementById('scanRate').textContent = `${data.system_metrics.scan_rate.toFixed(1)} f/s`;
                    }
                })
                .catch(err => console.error('Error loading initial data:', err));
        });
    </script>
</body>
</html>
        """

    async def start_data_collection(self):
        """Start the data collection for web dashboard."""
        if self.data_collector:
            return

        # Create custom data collector for web dashboard
        self.data_collector = RealTimeDataCollector()

        # Connect signals to broadcast methods
        self.data_collector.threat_detected.connect(self.on_threat_detected)
        self.data_collector.metrics_updated.connect(self.on_metrics_updated)

        # Start data collector
        self.data_collector.start()

        self.logger.info("Web dashboard data collection started")

    def on_threat_detected(self, threat: ThreatEvent):
        """Handle threat detection for web broadcasting."""
        # Store threat
        self.recent_threats.append(threat)
        if len(self.recent_threats) > self.max_history:
            self.recent_threats.pop(0)

        # Broadcast to WebSocket clients
        asyncio.create_task(self.broadcast_threat_event(threat))

    def on_metrics_updated(self, metrics: SystemMetrics):
        """Handle metrics update for web broadcasting."""
        # Store metrics
        self.recent_metrics.append(metrics)
        if len(self.recent_metrics) > self.max_history:
            self.recent_metrics.pop(0)

        # Broadcast to WebSocket clients
        asyncio.create_task(self.broadcast_metrics_update(metrics))

    async def stop_data_collection(self):
        """Stop the data collection."""
        if self.data_collector:
            self.data_collector.stop()
            self.data_collector = None

        self.logger.info("Web dashboard data collection stopped")

    def run(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """Run the web dashboard server."""
        self.logger.info(f"Starting web dashboard server on {host}:{port}")

        # Start data collection
        asyncio.create_task(self.start_data_collection())

        # Run the server
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info" if debug else "warning",
            access_log=debug,
        )


# Global web dashboard instance
_web_dashboard = None


def get_web_dashboard() -> WebDashboardManager:
    """Get the global web dashboard instance."""
    global _web_dashboard
    if _web_dashboard is None:
        _web_dashboard = WebDashboardManager()
    return _web_dashboard


async def start_web_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Start the web dashboard server."""
    dashboard = get_web_dashboard()
    await dashboard.start_data_collection()

    # Configure uvicorn server
    config = uvicorn.Config(dashboard.app, host=host, port=port, log_level="info")

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    dashboard = WebDashboardManager()
    dashboard.run(debug=True)
