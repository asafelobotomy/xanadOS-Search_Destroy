#!/usr/bin/env python3
"""
RKHunter False Positive Analyzer and Optimizer

This tool analyzes RKHunter scan results and provides optimization recommendations
to reduce false positives while maintaining security coverage.
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class FalsePositivePattern:
    """Represents a common false positive pattern in RKHunter."""

    name: str
    description: str
    warning_pattern: str
    recommended_config: str
    severity: str = "medium"
    common_files: list[str] = None

    def __post_init__(self):
        if self.common_files is None:
            self.common_files = []


class RKHunterOptimizer:
    """Main class for analyzing and optimizing RKHunter configuration."""

    def __init__(self, config_path: str = "/etc/rkhunter.conf"):
        self.config_path = Path(config_path)
        self.log_path = Path("/var/log/rkhunter.log")
        self.false_positive_patterns = self._load_false_positive_patterns()
        self.analysis_results = {}

    def _load_false_positive_patterns(self) -> list[FalsePositivePattern]:
        """Load known false positive patterns."""
        return [
            FalsePositivePattern(
                name="shared_memory_segments",
                description="Processes with large shared memory allocations",
                warning_pattern=r"Process.*shared memory segments",
                recommended_config='ALLOWHIDDENPROC="/usr/bin/process_name"',
                severity="low",
            ),
            FalsePositivePattern(
                name="application_versions",
                description="Application version mismatches",
                warning_pattern=r"Version.*differs.*expected",
                recommended_config='DISABLE_TESTS="apps"',
                severity="medium",
            ),
            FalsePositivePattern(
                name="system_startup_files",
                description="Legitimate system startup files",
                warning_pattern=r"Startup.*hidden.*file",
                recommended_config='ALLOWHIDDENFILE="/path/to/file"',
                severity="low",
            ),
            FalsePositivePattern(
                name="dev_directories",
                description="Dynamic device directories",
                warning_pattern=r"Hidden directory.*\/dev\/",
                recommended_config='ALLOWHIDDENDIR="/dev/.udev"',
                severity="low",
            ),
            FalsePositivePattern(
                name="network_interfaces",
                description="Network interface monitoring issues",
                warning_pattern=r"Network.*interface.*warning",
                recommended_config='ALLOWPROCS="/usr/sbin/NetworkManager"',
                severity="medium",
            ),
            FalsePositivePattern(
                name="deleted_files",
                description="Processes using deleted shared libraries",
                warning_pattern=r"deleted.*shared library",
                recommended_config='DISABLE_TESTS="deleted_files"',
                severity="high",
            ),
        ]

    def analyze_log_file(self, log_file: Path | None = None) -> dict:
        """Analyze RKHunter log file for false positive patterns."""
        if log_file is None:
            log_file = self.log_path

        if not log_file.exists():
            logger.error(f"Log file not found: {log_file}")
            return {}

        analysis = {
            "total_warnings": 0,
            "pattern_matches": defaultdict(list),
            "unmatched_warnings": [],
            "recommendations": [],
        }

        try:
            with open(log_file) as f:
                log_content = f.read()

            # Extract warnings
            warning_lines = []
            for line in log_content.split("\n"):
                if "Warning:" in line or "FAIL:" in line or "INFECTED:" in line:
                    warning_lines.append(line.strip())
                    analysis["total_warnings"] += 1

            # Match patterns
            for warning in warning_lines:
                matched = False
                for pattern in self.false_positive_patterns:
                    if re.search(pattern.warning_pattern, warning, re.IGNORECASE):
                        analysis["pattern_matches"][pattern.name].append(
                            {
                                "warning": warning,
                                "pattern": pattern,
                                "timestamp": self._extract_timestamp(warning),
                            }
                        )
                        matched = True
                        break

                if not matched:
                    analysis["unmatched_warnings"].append(warning)

            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)

        except Exception as e:
            logger.error(f"Error analyzing log file: {e}")

        return analysis

    def _extract_timestamp(self, log_line: str) -> str | None:
        """Extract timestamp from log line."""
        timestamp_pattern = r"\[(\d{2}:\d{2}:\d{2})\]"
        match = re.search(timestamp_pattern, log_line)
        return match.group(1) if match else None

    def _generate_recommendations(self, analysis: dict) -> list[dict]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        for pattern_name, matches in analysis["pattern_matches"].items():
            if len(matches) > 0:
                pattern = next(p for p in self.false_positive_patterns if p.name == pattern_name)

                rec = {
                    "pattern": pattern_name,
                    "description": pattern.description,
                    "severity": pattern.severity,
                    "frequency": len(matches),
                    "config_recommendation": pattern.recommended_config,
                    "sample_warnings": [m["warning"] for m in matches[:3]],  # First 3 examples
                }

                # Specific recommendations based on pattern
                if pattern_name == "application_versions" and len(matches) > 5:
                    rec["priority"] = "high"
                    rec["note"] = "High frequency suggests disabling app version checks"
                elif pattern_name == "deleted_files":
                    rec["priority"] = "critical"
                    rec["note"] = "Consider system reboot to clear deleted file references"
                else:
                    rec["priority"] = "medium"

                recommendations.append(rec)

        # Sort by priority and frequency
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "medium"), 2),
                -x["frequency"],
            )
        )

        return recommendations

    def generate_optimized_config(self, analysis: dict, output_path: Path | None = None) -> str:
        """Generate optimized RKHunter configuration based on analysis."""
        config_lines = [
            "# RKHunter Optimized Configuration",
            "# Generated by RKHunter False Positive Optimizer",
            f"# Generated on: {datetime.now().isoformat()}",
            "",
            "# Basic optimization settings",
            "UPDATE_MIRRORS=1",
            "MIRRORS_MODE=0",
            'WEB_CMD="/usr/bin/curl"',
            "",
            "# Performance optimizations",
            'HASH_FUNC="SHA256"',
            "SCAN_MODE_DEV=THOROUGH",
            "",
        ]

        # Add recommendations based on analysis
        for rec in analysis.get("recommendations", []):
            config_line = rec["config_recommendation"]

            config_lines.extend(
                [
                    f"# Fix for {rec['description']} (frequency: {rec['frequency']})",
                    config_line,
                    "",
                ]
            )

        # Common optimizations
        config_lines.extend(
            [
                "# Common false positive reductions",
                'ALLOWHIDDENDIR="/dev/.udev"',
                'ALLOWHIDDENDIR="/dev/.static"',
                'ALLOWHIDDENDIR="/dev/.initramfs"',
                'ALLOWHIDDENDIR="/sys/kernel/security"',
                'ALLOWHIDDENDIR="/sys/kernel/debug"',
                "",
                "# Disable problematic tests (customize based on environment)",
                '# DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps"',
                '# DISABLE_TESTS="apps"  # Uncomment to disable application version checking',
                "",
                "# Mail configuration",
                'MAIL-ON-WARNING="root@localhost"',
                '# MAIL-ON-WARNING=""  # Uncomment to disable email alerts',
                "",
                "# Logging",
                "VERBOSE=0",
                "APPEND_LOG=1",
            ]
        )

        config_content = "\n".join(config_lines)

        if output_path:
            try:
                with open(output_path, "w") as f:
                    f.write(config_content)
                logger.info(f"Optimized configuration written to: {output_path}")
            except Exception as e:
                logger.error(f"Error writing config file: {e}")

        return config_content

    def run_test_scan(self, config_file: Path | None = None) -> tuple[bool, str]:
        """Run a test RKHunter scan with optional custom config."""
        cmd = ["rkhunter", "--check", "--skip-keypress", "--report-warnings-only"]

        if config_file and config_file.exists():
            cmd.extend(["--configfile", str(config_file)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,  # 5 minute timeout
            )

            return result.returncode == 0, result.stdout + result.stderr

        except subprocess.TimeoutExpired:
            return False, "Scan timed out after 5 minutes"
        except Exception as e:
            return False, f"Error running scan: {e}"

    def generate_report(self, analysis: dict, output_format: str = "text") -> str:
        """Generate a human-readable report of the analysis."""
        if output_format == "json":
            return json.dumps(analysis, indent=2, default=str)

        report_lines = [
            "RKHunter False Positive Analysis Report",
            "=" * 50,
            f"Generated: {datetime.now().isoformat()}",
            f"Total warnings analyzed: {analysis.get('total_warnings', 0)}",
            "",
        ]

        # Pattern matches summary
        if analysis.get("pattern_matches"):
            report_lines.extend(["False Positive Pattern Matches:", "-" * 30])

            for pattern_name, matches in analysis["pattern_matches"].items():
                if matches:
                    pattern = next(
                        p for p in self.false_positive_patterns if p.name == pattern_name
                    )
                    report_lines.extend(
                        [
                            f"• {pattern.description}: {len(matches)} occurrences",
                            f"  Severity: {pattern.severity}",
                            f"  Sample: {matches[0]['warning'][:100]}...",
                            "",
                        ]
                    )

        # Recommendations
        if analysis.get("recommendations"):
            report_lines.extend(["Optimization Recommendations:", "-" * 30])

            for i, rec in enumerate(analysis["recommendations"], 1):
                report_lines.extend(
                    [
                        f"{i}. {rec['description']}",
                        f"   Priority: {rec.get('priority', 'medium')}",
                        f"   Frequency: {rec['frequency']} occurrences",
                        f"   Config: {rec['config_recommendation']}",
                        "",
                    ]
                )

        # Unmatched warnings
        if analysis.get("unmatched_warnings"):
            report_lines.extend(["Unmatched Warnings (require manual review):", "-" * 45])

            for warning in analysis["unmatched_warnings"][:10]:  # Show first 10
                report_lines.append(f"• {warning}")

            if len(analysis["unmatched_warnings"]) > 10:
                report_lines.append(f"... and {len(analysis['unmatched_warnings']) - 10} more")

        return "\n".join(report_lines)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="RKHunter False Positive Analyzer and Optimizer")
    parser.add_argument("--log-file", type=Path, help="Path to RKHunter log file")
    parser.add_argument("--config-file", type=Path, help="Path to RKHunter config file")
    parser.add_argument("--output-config", type=Path, help="Output path for optimized config")
    parser.add_argument(
        "--report-format",
        choices=["text", "json"],
        default="text",
        help="Report output format",
    )
    parser.add_argument("--test-scan", action="store_true", help="Run test scan after optimization")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize optimizer
    config_path = args.config_file or "/etc/rkhunter.conf"
    optimizer = RKHunterOptimizer(str(config_path))

    # Analyze log file
    logger.info("Analyzing RKHunter log file...")
    analysis = optimizer.analyze_log_file(args.log_file)

    if not analysis:
        logger.error("No analysis results generated")
        sys.exit(1)

    # Generate report
    report = optimizer.generate_report(analysis, args.report_format)
    print(report)

    # Generate optimized configuration
    if args.output_config:
        logger.info("Generating optimized configuration...")
        optimizer.generate_optimized_config(analysis, args.output_config)

        if args.test_scan:
            logger.info("Running test scan with optimized configuration...")
            success, output = optimizer.run_test_scan(args.output_config)

            if success:
                logger.info("Test scan completed successfully")
            else:
                logger.warning("Test scan completed with warnings")

            print("\nTest Scan Output:")
            print("-" * 20)
            print(output)


if __name__ == "__main__":
    main()
