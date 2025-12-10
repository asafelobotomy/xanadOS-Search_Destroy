#!/usr/bin/env python3
"""
Scan report management for S&D - Search & Destroy
"""

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .config import DATA_DIR, setup_logging


class ThreatLevel(Enum):
    """Threat severity levels."""

    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    INFECTED = "infected"
    ERROR = "error"


class ScanType(Enum):
    """Types of scans."""

    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    SCHEDULED = "scheduled"


@dataclass
class ThreatInfo:
    """Information about a detected threat."""

    file_path: str
    threat_name: str
    threat_type: str
    threat_level: ThreatLevel
    action_taken: str
    timestamp: str
    file_size: int
    file_hash: str


@dataclass
class ScanResult:
    """Complete scan result information."""

    scan_id: str
    scan_type: ScanType
    start_time: str
    end_time: str
    duration: float
    scanned_paths: list[str]
    total_files: int
    scanned_files: int
    threats_found: int
    threats: list[ThreatInfo]
    errors: list[str]
    scan_settings: dict[str, Any]
    engine_version: str
    signature_version: str
    success: bool


class ScanReportManager:
    """Manages scan reports and logging."""

    def __init__(self):
        self.logger = setup_logging()
        self.reports_dir = DATA_DIR / "scan_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for organization
        self.daily_reports = self.reports_dir / "daily"
        self.threat_logs = self.reports_dir / "threats"
        self.summary_reports = self.reports_dir / "summaries"

        for directory in [self.daily_reports, self.threat_logs, self.summary_reports]:
            directory.mkdir(parents=True, exist_ok=True)

    def generate_scan_id(self) -> str:
        """Generate unique scan ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    def _serialize_for_json(self, obj):
        """Custom serializer for JSON that handles enums properly."""
        if isinstance(obj, ScanType):
            return obj.value
        return str(obj)

    def save_scan_result(self, result: ScanResult) -> str:
        """Save scan result to file and return report path."""
        try:
            # Ensure the directory exists before saving
            self.daily_reports.mkdir(parents=True, exist_ok=True)

            # Save detailed report
            report_file = self.daily_reports / f"scan_{result.scan_id}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(asdict(result), f, indent=2, default=self._serialize_for_json)

            # Save threat summary if threats found
            if result.threats_found > 0:
                self._save_threat_summary(result)

            # Update daily summary
            self._update_daily_summary(result)

            self.logger.info(
                "Scan report saved: %s - %d threats found in %d files",
                result.scan_id,
                result.threats_found,
                result.scanned_files,
            )

            return str(report_file)

        except OSError as e:
            self.logger.error("Failed to save scan result: %s", e)
            return ""

    def _save_threat_summary(self, result: ScanResult) -> None:
        """Save threat-specific information."""
        # Ensure the directory exists before saving
        self.threat_logs.mkdir(parents=True, exist_ok=True)

        threat_file = self.threat_logs / f"threats_{result.scan_id}.json"
        threat_data = {
            "scan_id": result.scan_id,
            "timestamp": result.start_time,
            "scan_type": result.scan_type.value,
            "threats": [asdict(threat) for threat in result.threats],
        }

        with open(threat_file, "w", encoding="utf-8") as f:
            json.dump(threat_data, f, indent=2, default=str)

    def _update_daily_summary(self, result: ScanResult) -> None:
        """Update daily summary statistics."""
        # Ensure the directory exists before saving
        self.summary_reports.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        summary_file = self.summary_reports / f"daily_{today}.json"

        # Load existing summary or create new
        summary = {}
        if summary_file.exists():
            try:
                with open(summary_file, encoding="utf-8") as f:
                    summary = json.load(f)
            except (OSError, json.JSONDecodeError):
                summary = {}

        # Initialize if empty
        if not summary:
            summary = {
                "date": today,
                "total_scans": 0,
                "total_files_scanned": 0,
                "total_threats_found": 0,
                "scan_types": {},
                "threat_types": {},
                "scans": [],
            }

        # Update statistics
        summary["total_scans"] += 1
        summary["total_files_scanned"] += result.scanned_files
        summary["total_threats_found"] += result.threats_found

        # Track scan types
        scan_type = result.scan_type.value
        summary["scan_types"][scan_type] = summary["scan_types"].get(scan_type, 0) + 1

        # Track threat types
        for threat in result.threats:
            threat_type = threat.threat_type
            summary["threat_types"][threat_type] = (
                summary["threat_types"].get(threat_type, 0) + 1
            )

        # Add scan summary
        summary["scans"].append(
            {
                "scan_id": result.scan_id,
                "time": result.start_time,
                "type": scan_type,
                "files": result.scanned_files,
                "threats": result.threats_found,
                "duration": result.duration,
            }
        )

        # Save updated summary
        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, default=str)
        except OSError as e:
            self.logger.error("Failed to update daily summary: %s", e)

    def load_scan_result(self, scan_id: str) -> ScanResult | None:
        """Load scan result by ID."""
        report_file = self.daily_reports / f"scan_{scan_id}.json"

        if not report_file.exists():
            return None

        try:
            with open(report_file, encoding="utf-8") as f:
                data = json.load(f)

            # Convert back to ScanResult object
            threats = []
            for threat_data in data.get("threats", []):
                # Handle ThreatLevel conversion
                if isinstance(threat_data.get("threat_level"), str):
                    try:
                        threat_data["threat_level"] = ThreatLevel(
                            threat_data["threat_level"]
                        )
                    except ValueError:
                        threat_data["threat_level"] = ThreatLevel.ERROR

                threats.append(ThreatInfo(**threat_data))

            data["threats"] = threats

            # Handle ScanType conversion
            if isinstance(data.get("scan_type"), str):
                scan_type_str = data["scan_type"]
                try:
                    data["scan_type"] = ScanType(scan_type_str)
                except ValueError:
                    self.logger.warning(
                        "Unknown scan type: %s, defaulting to CUSTOM",
                        scan_type_str,
                    )
                    data["scan_type"] = ScanType.CUSTOM

            return ScanResult(**data)

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
            self.logger.error(f"Failed to load scan result {scan_id}: {e}")
            return None

    def get_recent_scans(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get list of recent scan summaries."""
        scan_files = sorted(
            self.daily_reports.glob("scan_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        recent_scans = []
        for scan_file in scan_files[:limit]:
            try:
                with open(scan_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Extract summary information
                summary = {
                    "scan_id": data["scan_id"],
                    "scan_type": data["scan_type"],
                    "start_time": data["start_time"],
                    "duration": data["duration"],
                    "scanned_files": data["scanned_files"],
                    "threats_found": data["threats_found"],
                    "success": data["success"],
                }
                recent_scans.append(summary)

            except (OSError, json.JSONDecodeError, KeyError):
                self.logwarning(
                    "Failed to read scan summary from %s: %s".replace(
                        "%s", "{scan_file, e}"
                    ).replace("%d", "{scan_file, e}")
                )
                continue

        return recent_scans

    def get_threat_statistics(self, days: int = 30) -> dict[str, Any]:
        """Get threat statistics for the last N days."""

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        stats = {
            "period_days": days,
            "total_threats": 0,
            "threat_types": {},
            "threat_levels": {},
            "daily_counts": {},
            "most_infected_paths": {},
        }

        # Scan through threat logs
        for threat_file in self.threat_logs.glob("threats_*.json"):
            try:
                with open(threat_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Check if within date range
                scan_date = datetime.fromisoformat(
                    data["timestamp"].replace("Z", "+00:00")
                )
                if start_date <= scan_date <= end_date:
                    for threat in data["threats"]:
                        stats["total_threats"] += 1

                        # Count by type
                        threat_type = threat["threat_type"]
                        stats["threat_types"][threat_type] = (
                            stats["threat_types"].get(threat_type, 0) + 1
                        )

                        # Count by level
                        threat_level = threat["threat_level"]
                        stats["threat_levels"][threat_level] = (
                            stats["threat_levels"].get(threat_level, 0) + 1
                        )

                        # Count by day
                        day_key = scan_date.strftime("%Y-%m-%d")
                        stats["daily_counts"][day_key] = (
                            stats["daily_counts"].get(day_key, 0) + 1
                        )

                        # Track infected paths
                        path_parent = str(Path(threat["file_path"]).parent)
                        stats["most_infected_paths"][path_parent] = (
                            stats["most_infected_paths"].get(path_parent, 0) + 1
                        )

            except (OSError, json.JSONDecodeError, KeyError, ValueError):
                self.logwarning(
                    "Failed to process threat file %s: %s".replace(
                        "%s", "{threat_file, e}"
                    ).replace("%d", "{threat_file, e}")
                )
                continue

        return stats

    def cleanup_old_reports(self, days_to_keep: int = 90) -> None:
        """Clean up old report files."""

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        for report_dir in [self.daily_reports, self.threat_logs, self.summary_reports]:
            for report_file in report_dir.glob("*.json"):
                try:
                    if (
                        datetime.fromtimestamp(report_file.stat().st_mtime)
                        < cutoff_date
                    ):
                        report_file.unlink()
                        deleted_count += 1
                except OSError as e:
                    self.logwarning(f"Failed to delete old report {report_file}: {e}")

        if deleted_count > 0:
            self.loginfo(f"Cleaned up {deleted_count} old report files")

    def export_reports(
        self,
        output_path: str,
        format_type: str = "json",
        start_date: str = None,
        end_date: str = None,
    ) -> bool:
        """Export reports to the specified format.

        Args:
            output_path: Path to save the export file
            format_type: Export format ('json', 'csv', or 'html')
            start_date: Start date for filtering (ISO format)
            end_date: End date for filtering (ISO format)

        Returns:
            bool: True if export was successful
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "start_date": start_date,
                "end_date": end_date,
                "scans": [],
                "threats": [],
                "statistics": self.get_threat_statistics(),
            }

            # Collect all scans in date range
            for scan_file in self.daily_reports.glob("scan_*.json"):
                try:
                    with open(scan_file, encoding="utf-8") as f:
                        scan_data = json.load(f)

                    # Date filtering if specified
                    if start_date or end_date:
                        scan_date = datetime.fromisoformat(scan_data["start_time"])
                        if start_date and scan_date < datetime.fromisoformat(
                            start_date
                        ):
                            continue
                        if end_date and scan_date > datetime.fromisoformat(end_date):
                            continue

                    export_data["scans"].append(scan_data)

                    # Collect all threats for easier reporting
                    if scan_data.get("threats"):
                        for threat in scan_data["threats"]:
                            threat["scan_id"] = scan_data["scan_id"]
                            threat["scan_date"] = scan_data["start_time"]
                            export_data["threats"].append(threat)

                except (OSError, json.JSONDecodeError, ValueError):
                    continue

            # Generate appropriate format
            if format_type.lower() == "json":
                self._export_json(export_data, output_path)
            elif format_type.lower() == "csv":
                self._export_csv(export_data, output_path)
            elif format_type.lower() == "html":
                self._export_html(export_data, output_path)
            else:
                self.logger.error("Unsupported export format: %s", format_type)
                return False

            self.loginfo(
                "Reports exported to %s".replace("%s", "{output_path}").replace(
                    "%d", "{output_path}"
                )
            )
            return True

        except OSError as e:
            self.logger.error("Failed to export reports: %s", e)
            return False

    def _export_json(self, export_data: dict, output_path: str) -> None:
        """Export data to JSON format."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

    def _export_csv(self, export_data: dict, output_path: str) -> None:
        """Export data to CSV format."""

        # Create threats CSV
        threats_csv_path = output_path.replace(".csv", "_threats.csv")
        with open(threats_csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "scan_id",
                "scan_date",
                "file_path",
                "threat_name",
                "threat_type",
                "threat_level",
                "action_taken",
                "file_size",
                "file_hash",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for threat in export_data["threats"]:
                writer.writerow({k: threat.get(k, "") for k in fieldnames})

        # Create scans CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "scan_id",
                "scan_type",
                "start_time",
                "end_time",
                "duration",
                "scanned_files",
                "total_files",
                "threats_found",
                "success",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for scan in export_data["scans"]:
                writer.writerow({k: scan.get(k, "") for k in fieldnames})

    def _export_html(self, export_data: dict, output_path: str) -> None:
        """Export data to HTML format."""
        total_scans = len(export_data["scans"])
        total_threats = len(export_data["threats"])
        files_scanned = sum(
            scan.get("scanned_files", 0) for scan in export_data["scans"]
        )

        # Build CSS in small chunks to keep source lines short for pylint C0301
        style_lines = [
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1, h2 { color: #2196F3; }",
            "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            "tr:nth-child(even) { background-color: #f9f9f9; }",
            ".threat-infected { background-color: #ffebee; }",
            ".threat-suspicious { background-color: #fff8e1; }",
            ".stats { display: flex; justify-content: space-around; }",
            (
                ".stat-box { border: 1px solid #ddd; padding: 15px; "
                "border-radius: 5px; text-align: center; }"
            ),
            ".stat-value { font-size: 24px; font-weight: bold; color: #2196F3; }",
        ]
        style_block = "\n".join(style_lines)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>S&D Scan Reports</title>
            <style>
                {style_block}
            </style>
        </head>
        <body>
            <h1>S&D Scan Reports</h1>
            <p>Export generated on {export_data["export_timestamp"]}</p>

            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{total_scans}</div>
                    <div>Total Scans</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{total_threats}</div>
                    <div>Threats Found</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{files_scanned}</div>
                    <div>Files Scanned</div>
                </div>
            </div>

            <h2>Threat Summary</h2>
            <table>
                <tr>
                    <th>Date</th>
                    <th>File Path</th>
                    <th>Threat Name</th>
                    <th>Threat Type</th>
                    <th>Action Taken</th>
                </tr>
        """

        # Add threat rows
        for threat in export_data["threats"]:
            threat_class = (
                "threat-infected"
                if threat.get("threat_level") == "infected"
                else "threat-suspicious"
            )
            html_content += f"""
                <tr class="{threat_class}">
                    <td>{threat.get("scan_date", "")}</td>
                    <td>{threat.get("file_path", "")}</td>
                    <td>{threat.get("threat_name", "")}</td>
                    <td>{threat.get("threat_type", "")}</td>
                    <td>{threat.get("action_taken", "")}</td>
                </tr>
            """

        html_content += """
            </table>

            <h2>Scan History</h2>
            <table>
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Duration</th>
                    <th>Files Scanned</th>
                    <th>Threats</th>
                    <th>Status</th>
                </tr>
        """

        # Add scan rows
        for scan in sorted(
            export_data["scans"], key=lambda x: x.get("start_time", ""), reverse=True
        ):
            status = "Success" if scan.get("success") else "Failed"
            html_content += f"""
                <tr>
                    <td>{scan.get("start_time", "")}</td>
                    <td>{scan.get("scan_type", "")}</td>
                    <td>{scan.get("duration", 0):.2f}s</td>
                    <td>{scan.get("scanned_files", 0)}/{scan.get("total_files", 0)}</td>
                    <td>{scan.get("threats_found", 0)}</td>
                    <td>{status}</td>
                </tr>
            """

        html_content += """
            </table>
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
