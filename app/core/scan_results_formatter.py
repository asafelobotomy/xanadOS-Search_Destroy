#!/usr/bin/env python3
"""
Enhanced Scan Results Formatter for xanadOS Search & Destroy
Provides improved readability and organization for scan output.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScanResultType(Enum):
    """Types of scan results for formatting."""

    CLEAN = "clean"
    WARNING = "warning"
    INFECTION = "infection"
    INFO = "info"
    SKIP = "skip"


@dataclass
class FormattedScanSection:
    """A formatted section of scan results."""

    title: str
    content: List[str]
    section_type: str
    priority: int = 0


class ModernScanResultsFormatter:
    """
    Modern, user-friendly formatter for scan results.
    Focuses on readability, organization, and visual hierarchy.
    """

    def __init__(self):
        self.sections = []
        self.current_section = None

        # Formatting constants
        self.HEADER_LINE = "═" * 60
        self.SECTION_LINE = "─" * 50
        self.SUBSECTION_LINE = "┄" * 40

        # Color-coded status indicators
        self.STATUS_ICONS = {
            ScanResultType.CLEAN: "✅",
            ScanResultType.WARNING: "⚠️",
            ScanResultType.INFECTION: "🚨",
            ScanResultType.INFO: "ℹ️",
            ScanResultType.SKIP: "⏭️",
        }

        # Priority levels for section ordering
        self.SECTION_PRIORITIES = {
            "header": 1,
            "summary": 2,
            "infections": 3,
            "warnings": 4,
            "details": 5,
            "recommendations": 6,
            "footer": 7,
        }

    def format_scan_header(
        self, scan_type: str, timestamp: Optional[str] = None
    ) -> List[str]:
        """Create a clean, professional scan header."""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = [
            "",
            self.HEADER_LINE,
            f"🔍 {scan_type.upper()} SECURITY SCAN",
            self.HEADER_LINE,
            f"📅 Started: {timestamp}",
            "",
        ]
        return header

    def format_scan_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Format scan configuration in a clean, organized way."""
        if not config:
            return []

        lines = [
            "⚙️  SCAN CONFIGURATION",
            self.SECTION_LINE,
        ]

        # Group related settings
        if "targets" in config:
            lines.append("📁 Scan Targets:")
            targets = config["targets"]
            if isinstance(targets, list):
                for i, target in enumerate(targets[:5], 1):
                    display_path = self._format_path(target)
                    lines.append(f"   {i}. {display_path}")
                if len(targets) > 5:
                    lines.append(f"   ... and {len(targets) - 5} more directories")
            else:
                lines.append(f"   • {self._format_path(targets)}")
            lines.append("")

        if "options" in config:
            lines.append("🔧 Scan Options:")
            options = config["options"]
            for key, value in options.items():
                formatted_key = key.replace("_", " ").title()
                lines.append(f"   • {formatted_key}: {value}")
            lines.append("")

        return lines

    def format_rkhunter_output(self, raw_output: str) -> List[str]:
        """Format RKHunter output with improved organization and readability."""
        lines = raw_output.split("\n")
        formatted_lines = []
        current_section = None
        section_items = []

        # Track statistics
        stats = {
            "clean_count": 0,
            "warning_count": 0,
            "infection_count": 0,
            "skip_count": 0,
            "total_checks": 0,
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip noise and warnings that clutter output
            if any(
                skip_phrase in line.lower()
                for skip_phrase in [
                    "grep: warning:",
                    "egrep: warning:",
                    "unknown option",
                ]
            ):
                continue

            # Detect section headers
            if line.startswith("Checking ") or "Performing" in line:
                # Save previous section
                if current_section and section_items:
                    formatted_lines.extend(
                        self._format_check_section(
                            current_section, section_items, stats
                        )
                    )
                    section_items = []

                # Start new section
                current_section = self._clean_section_name(line)
                continue

            # Process check results
            if any(
                marker in line
                for marker in [
                    "[ OK ]",
                    "[ Not found ]",
                    "[ Warning ]",
                    "[ Infected ]",
                    "[ Skipped ]",
                ]
            ):
                item_type, item_text = self._parse_check_result(line)
                section_items.append((item_type, item_text))
                stats["total_checks"] += 1

                if item_type == ScanResultType.CLEAN:
                    stats["clean_count"] += 1
                elif item_type == ScanResultType.WARNING:
                    stats["warning_count"] += 1
                elif item_type == ScanResultType.INFECTION:
                    stats["infection_count"] += 1
                elif item_type == ScanResultType.SKIP:
                    stats["skip_count"] += 1

        # Save final section
        if current_section and section_items:
            formatted_lines.extend(
                self._format_check_section(current_section, section_items, stats)
            )

        # Add summary at the end
        formatted_lines.extend(self._format_rkhunter_summary(stats))

        return formatted_lines

    def _format_check_section(
        self, section_name: str, items: List[tuple], stats: Dict
    ) -> List[str]:
        """Format a section of RKHunter checks with grouped results."""
        if not items:
            return []

        # Group items by result type
        grouped = {
            ScanResultType.CLEAN: [],
            ScanResultType.WARNING: [],
            ScanResultType.INFECTION: [],
            ScanResultType.SKIP: [],
        }

        for item_type, item_text in items:
            grouped[item_type].append(item_text)

        # Format section header
        section_lines = [
            "",
            f"📋 {section_name}",
            self.SECTION_LINE,
        ]

        # Show infections first (highest priority)
        if grouped[ScanResultType.INFECTION]:
            section_lines.append("🚨 INFECTIONS DETECTED:")
            for item in grouped[ScanResultType.INFECTION]:
                section_lines.append(f"   • {item}")
            section_lines.append("")

        # Show warnings next
        if grouped[ScanResultType.WARNING]:
            section_lines.append("⚠️  WARNINGS FOUND:")
            for item in grouped[ScanResultType.WARNING][
                :5
            ]:  # Limit to 5 for readability
                section_lines.append(f"   • {item}")
            if len(grouped[ScanResultType.WARNING]) > 5:
                section_lines.append(
                    f"   ... and {len(grouped[ScanResultType.WARNING]) - 5} more warnings"
                )
            section_lines.append("")

        # Summarize clean results (don't list all)
        if grouped[ScanResultType.CLEAN]:
            clean_count = len(grouped[ScanResultType.CLEAN])
            section_lines.append(f"✅ {clean_count} checks passed successfully")
            section_lines.append("")

        # Show skipped if any
        if grouped[ScanResultType.SKIP]:
            skip_count = len(grouped[ScanResultType.SKIP])
            section_lines.append(f"⏭️  {skip_count} checks skipped")
            section_lines.append("")

        return section_lines

    def _format_rkhunter_summary(self, stats: Dict) -> List[str]:
        """Create a comprehensive but concise summary."""
        summary_lines = [
            "",
            "📊 SCAN SUMMARY",
            self.SECTION_LINE,
        ]

        # Overall status
        if stats["infection_count"] > 0:
            summary_lines.extend(
                [
                    "🚨 CRITICAL: Potential rootkits or malware detected!",
                    "   Immediate security action required.",
                    "",
                ]
            )
        elif stats["warning_count"] > 0:
            summary_lines.extend(
                [
                    "⚠️  ATTENTION: System configuration warnings found.",
                    "   Review and address security recommendations.",
                    "",
                ]
            )
        else:
            summary_lines.extend(
                [
                    "✅ CLEAN: No rootkits or suspicious activity detected.",
                    "   System appears secure.",
                    "",
                ]
            )

        # Statistics breakdown
        summary_lines.extend(
            [
                "📈 Detailed Results:",
                f"   • Total Checks: {stats['total_checks']}",
                f"   • Passed: {stats['clean_count']}",
                f"   • Warnings: {stats['warning_count']}",
                f"   • Infections: {stats['infection_count']}",
                f"   • Skipped: {stats['skip_count']}",
                "",
            ]
        )

        return summary_lines

    def format_scan_completion(
        self,
        scan_type: str,
        duration: float,
        files_scanned: int = 0,
        threats_found: int = 0,
    ) -> List[str]:
        """Create a clean scan completion summary."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format duration
        if duration < 60:
            duration_str = f"{duration:.1f} seconds"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            duration_str = f"{minutes}m {seconds:.1f}s"

        # Choose status icon and message
        if threats_found > 0:
            status_icon = "🚨"
            status_msg = f"{threats_found} THREATS FOUND"
        else:
            status_icon = "✅"
            status_msg = "NO THREATS FOUND"

        completion_lines = [
            "",
            self.HEADER_LINE,
            f"{status_icon} SCAN COMPLETED - {status_msg}",
            self.HEADER_LINE,
            f"📅 Completed: {timestamp}",
            f"⏱️  Duration: {duration_str}",
        ]

        if files_scanned > 0:
            completion_lines.append(f"📁 Files Scanned: {files_scanned:,}")

        completion_lines.extend(
            [
                "",
                "💡 RECOMMENDATIONS:",
                "   • Schedule regular scans for ongoing protection",
                "   • Keep security definitions up to date",
                "   • Monitor system for unusual activity",
                "",
            ]
        )

        return completion_lines

    def _clean_section_name(self, raw_name: str) -> str:
        """Clean up section names for better readability."""
        # Remove common prefixes and clean up
        cleaned = raw_name.replace("Checking ", "").replace("Performing ", "")
        cleaned = cleaned.replace("check of ", "").replace("checks", "")
        cleaned = cleaned.replace("...", "").strip()

        # Capitalize properly
        return cleaned.title()

    def _parse_check_result(self, line: str) -> tuple:
        """Parse a check result line and return type and cleaned text."""
        line = line.strip()

        # Determine result type
        if "[ OK ]" in line or "[ Not found ]" in line or "[ None found ]" in line:
            result_type = ScanResultType.CLEAN
        elif "[ Warning ]" in line:
            result_type = ScanResultType.WARNING
        elif "[ Infected ]" in line:
            result_type = ScanResultType.INFECTION
        elif "[ Skipped ]" in line:
            result_type = ScanResultType.SKIP
        else:
            result_type = ScanResultType.INFO

        # Clean up the text
        cleaned_text = line
        for marker in [
            "[ OK ]",
            "[ Not found ]",
            "[ None found ]",
            "[ Warning ]",
            "[ Infected ]",
            "[ Skipped ]",
        ]:
            cleaned_text = cleaned_text.replace(marker, "").strip()

        # Remove excessive paths for readability
        if "/usr/bin/" in cleaned_text:
            cleaned_text = cleaned_text.replace("/usr/bin/", "")

        return result_type, cleaned_text

    def _format_path(self, path: str) -> str:
        """Format file paths for better readability."""
        import os

        path_str = str(path)

        # Replace home directory with ~
        home = os.path.expanduser("~")
        if path_str.startswith(home):
            return path_str.replace(home, "~")

        return path_str

    def format_combined_scan_summary(
        self, rkhunter_results: Dict, clamav_results: Dict
    ) -> List[str]:
        """Create a unified summary for combined scans."""
        summary_lines = [
            "",
            self.HEADER_LINE,
            "🔒 COMPREHENSIVE SECURITY SCAN SUMMARY",
            self.HEADER_LINE,
            "",
        ]

        # RKHunter results
        rk_warnings = rkhunter_results.get("warnings", 0)
        rk_infections = rkhunter_results.get("infections", 0)
        rk_tests_run = rkhunter_results.get("tests_run", 0)
        rk_total_tests = rkhunter_results.get("total_tests", 0)
        rk_skipped = rkhunter_results.get("skipped_tests", 0)

        summary_lines.extend(
            [
                "🛡️  RKHunter Results (Rootkit Detection):",
                f"   • Warnings: {rk_warnings}",
                f"   • Infections: {rk_infections}",
            ]
        )

        # Add test statistics if available
        if rk_tests_run > 0 or rk_total_tests > 0:
            summary_lines.append(f"   • Tests Run: {rk_tests_run}")
            if rk_total_tests > 0:
                summary_lines.append(f"   • Total Tests: {rk_total_tests}")
            if rk_skipped > 0:
                summary_lines.append(f"   • Skipped Tests: {rk_skipped}")

        summary_lines.append("")

        # ClamAV results
        cv_threats = clamav_results.get("threats", 0)
        cv_files = clamav_results.get("files_scanned", 0)
        cv_total = clamav_results.get("total_files", 0)
        cv_duration = clamav_results.get("scan_duration", 0)

        summary_lines.extend(
            [
                "🦠 ClamAV Results (Malware Detection):",
                f"   • Threats Found: {cv_threats}",
                f"   • Files Scanned: {cv_files:,}",
            ]
        )

        # Add additional stats if available and meaningful
        if cv_total > 0 and cv_total != cv_files:
            summary_lines.append(f"   • Total Files: {cv_total:,}")

        if cv_duration > 0:
            if cv_duration < 60:
                duration_str = f"{cv_duration:.1f}s"
            else:
                minutes = int(cv_duration // 60)
                seconds = cv_duration % 60
                duration_str = f"{minutes}m {seconds:.1f}s"
            summary_lines.append(f"   • Scan Duration: {duration_str}")

        summary_lines.append("")

        # Overall assessment
        total_threats = rk_infections + cv_threats
        total_issues = rk_warnings + rk_infections + cv_threats

        if total_threats > 0:
            summary_lines.extend(
                [
                    "🚨 **SECURITY ALERT**",
                    f"   {total_threats} active threats detected!",
                    "   Immediate action required.",
                ]
            )
        elif total_issues > 0:
            summary_lines.extend(
                [
                    "⚠️  **ATTENTION REQUIRED**",
                    f"   {total_issues} security warnings found.",
                    "   Review recommendations carefully.",
                ]
            )
        else:
            summary_lines.extend(
                [
                    "✅ **SYSTEM CLEAN**",
                    "   No threats or suspicious activity detected.",
                    "   Your system appears secure.",
                ]
            )

        summary_lines.extend(["", self.HEADER_LINE, ""])

        return summary_lines


# Global formatter instance
_formatter = ModernScanResultsFormatter()


def format_scan_results(scan_type: str, raw_output: str, **kwargs) -> str:
    """Main entry point for formatting scan results."""
    if scan_type.lower() == "rkhunter":
        lines = _formatter.format_rkhunter_output(raw_output)
    else:
        # Fallback to basic formatting
        lines = raw_output.split("\n")

    return "\n".join(lines)
