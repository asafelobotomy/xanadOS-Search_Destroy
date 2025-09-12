#!/usr/bin/env python3
"""
Modern Test Suite Runner
========================
Comprehensive test runner that orchestrates all test suites with detailed
reporting, performance metrics, and future-proofing validation.
Author: GitHub Copilot
Date: 22 August 2025
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add app directory to path
repo_root = Path(__file__).parent.parent
app_dir = repo_root / "app"
sys.path.insert(0, str(app_dir))


class TestSuiteRunner:
    """Modern test suite runner with comprehensive reporting"""

    def __init__(self):
        self.start_time = None
        self.results = {}
        self.system_info = self._get_system_info()
        self.report_file = (
            repo_root
            / "test_results"
            / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Ensure report directory exists
        self.report_file.parent.mkdir(exist_ok=True)

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information for the test report"""
        try:
            return {
                "platform": sys.platform,
                "python_version": sys.version,
                "cpu_count": os.cpu_count(),
                "memory_gb": psutil.virtual_memory().total / 1024**3,
                "disk_free_gb": psutil.disk_usage("/").free / 1024**3,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Could not gather system info: {e}")
            return {"error": str(e)}

    def run_comprehensive_tests(self) -> dict[str, Any]:
        """Run the complete test suite with all categories"""

        print("🚀 Starting Comprehensive Modern Test Suite")
        print("=" * 80)
        print(f"Platform: {self.system_info.get('platform', 'unknown')}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"CPUs: {self.system_info.get('cpu_count', 'unknown')}")
        print(f"Memory: {self.system_info.get('memory_gb', 0):.1f}GB")
        print("=" * 80)

        # Determine Python executable from virtual environment
        repo_root = Path(__file__).parent.parent
        venv_python = repo_root / ".venv" / "bin" / "python"

        if venv_python.exists():
            python_exec = str(venv_python)
        else:
            python_exec = sys.executable or "python"

        # Test suites to run
        test_suites = [
            {
                "name": "Unit Tests",
                "description": "Basic functionality and unit tests",
                "command": [
                    python_exec,
                    "-m",
                    "pytest",
                    "tests/test_gui.py",
                    "tests/test_monitoring.py",
                    "-v",
                    "--tb=short",
                ],
                "critical": True,
                "timeout": 120,
            },
            {
                "name": "Comprehensive Suite",
                "description": "Core functionality, integration, and future-proofing",
                "command": [
                    python_exec,
                    "-m",
                    "pytest",
                    "tests/test_comprehensive_suite.py",
                    "-v",
                ],
                "critical": True,
                "timeout": 180,
            },
            {
                "name": "Security Validation",
                "description": "Security testing and vulnerability checks",
                "command": [
                    python_exec,
                    "-m",
                    "pytest",
                    "tests/test_security_validation.py",
                    "-v",
                ],
                "critical": True,
                "timeout": 120,
            },
            {
                "name": "Performance Benchmarks",
                "description": "Performance testing and benchmarks",
                "command": [
                    python_exec,
                    "-m",
                    "pytest",
                    "tests/test_performance_benchmarks.py",
                    "-v",
                ],
                "critical": False,
                "timeout": 300,
            },
            {
                "name": "Hardening Tests",
                "description": "System hardening functionality",
                "command": [
                    python_exec,
                    "-m",
                    "pytest",
                    "tests/hardening/",
                    "-v",
                    "--tb=short",
                ],
                "critical": False,
                "timeout": 180,
            },
        ]

        # Run each test suite
        for suite in test_suites:
            result = self._run_test_suite(suite)
            self.results[suite["name"]] = result

            # Stop on critical failures
            if suite["critical"] and not result["success"]:
                print(f"\n❌ Critical test suite '{suite['name']}' failed!")
                print("Stopping execution due to critical failure.")
                break

        # Generate comprehensive report
        total_duration = time.time() - self.start_time
        final_report = self._generate_final_report(total_duration)

        # Save detailed report
        self._save_detailed_report(final_report)

        # Print summary
        self._print_summary(final_report)

        return final_report

    def _run_test_suite(self, suite: dict[str, Any]) -> dict[str, Any]:
        """Run a single test suite"""

        print(f"\n🧪 Running: {suite['name']}")
        print(f"📋 {suite['description']}")
        print("-" * 60)

        start_time = time.time()

        try:
            # Change to repo root for consistent paths
            os.chdir(repo_root)

            # Set up environment
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{app_dir}:{env.get('PYTHONPATH', '')}"

            # Run the test suite
            result = subprocess.run(
                suite["command"],
                capture_output=True,
                text=True,
                timeout=suite.get("timeout", 300),
                env=env,
            )

            duration = time.time() - start_time

            # Parse results
            success = result.returncode == 0

            test_result = {
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(suite["command"]),
                "timeout": suite.get("timeout", 300),
                "critical": suite.get("critical", False),
            }

            # Extract test statistics from pytest output
            stats = self._parse_pytest_output(result.stdout)
            test_result.update(stats)

            # Print result
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} in {duration:.1f}s")

            if stats.get("tests_run", 0) > 0:
                print(
                    f"Tests: {stats['tests_run']} run, {stats.get('tests_passed', 0)} passed, {
                        stats.get('tests_failed', 0)
                    } failed"
                )

            if not success and result.stderr:
                print(f"Error output:\n{result.stderr[:500]}...")

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"❌ TIMEOUT after {duration:.1f}s")

            return {
                "success": False,
                "duration": duration,
                "return_code": -1,
                "error": "Test suite timed out",
                "timeout": suite.get("timeout", 300),
                "critical": suite.get("critical", False),
            }

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ ERROR: {e}")

            return {
                "success": False,
                "duration": duration,
                "return_code": -1,
                "error": str(e),
                "critical": suite.get("critical", False),
            }

    def _parse_pytest_output(self, output: str) -> dict[str, int]:
        """Parse pytest output to extract test statistics"""
        stats = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "tests_errors": 0,
        }

        try:
            # Look for pytest summary line
            lines = output.split("\n")
            for line in lines:
                if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                    # Parse line like: "5 passed, 2 failed, 1 skipped in 10.23s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            stats["tests_passed"] = int(parts[i - 1])
                            stats["tests_run"] += stats["tests_passed"]
                        elif part == "failed" and i > 0:
                            stats["tests_failed"] = int(parts[i - 1])
                            stats["tests_run"] += stats["tests_failed"]
                        elif part == "skipped" and i > 0:
                            stats["tests_skipped"] = int(parts[i - 1])
                        elif part == "error" and i > 0:
                            stats["tests_errors"] = int(parts[i - 1])
                            stats["tests_run"] += stats["tests_errors"]
                    break
                elif "passed" in line and "in" in line:
                    # Simple case: "5 passed in 2.34s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            stats["tests_passed"] = int(parts[i - 1])
                            stats["tests_run"] = stats["tests_passed"]
                            break
                    break
        except Exception as e:
            logger.warning(f"Could not parse pytest output: {e}")

        return stats

    def _generate_final_report(self, total_duration: float) -> dict[str, Any]:
        """Generate comprehensive final report"""

        # Calculate overall statistics
        total_suites = len(self.results)
        successful_suites = sum(1 for r in self.results.values() if r["success"])
        critical_failures = sum(
            1 for r in self.results.values() if not r["success"] and r.get("critical", False)
        )

        total_tests = sum(r.get("tests_run", 0) for r in self.results.values())
        total_passed = sum(r.get("tests_passed", 0) for r in self.results.values())
        total_failed = sum(r.get("tests_failed", 0) for r in self.results.values())
        total_skipped = sum(r.get("tests_skipped", 0) for r in self.results.values())

        # Determine overall success
        overall_success = critical_failures == 0 and successful_suites > 0

        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_duration": total_duration,
                "system_info": self.system_info,
                "test_runner_version": "2.0.0",
            },
            "summary": {
                "overall_success": overall_success,
                "total_suites": total_suites,
                "successful_suites": successful_suites,
                "failed_suites": total_suites - successful_suites,
                "critical_failures": critical_failures,
                "total_tests": total_tests,
                "tests_passed": total_passed,
                "tests_failed": total_failed,
                "tests_skipped": total_skipped,
                "success_rate": ((total_passed / total_tests * 100) if total_tests > 0 else 0),
            },
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Check for critical failures
        critical_failures = [
            name
            for name, result in self.results.items()
            if not result["success"] and result.get("critical", False)
        ]

        if critical_failures:
            recommendations.append(f"❌ Critical test failures in: {', '.join(critical_failures)}")
            recommendations.append("🔧 Fix critical issues before deploying to production")

        # Check for performance issues
        slow_suites = [
            name for name, result in self.results.items() if result.get("duration", 0) > 120
        ]

        if slow_suites:
            recommendations.append(f"⚠️ Slow test suites detected: {', '.join(slow_suites)}")
            recommendations.append("🚀 Consider optimizing test performance")

        # Check for skipped tests
        total_skipped = sum(r.get("tests_skipped", 0) for r in self.results.values())
        if total_skipped > 0:
            recommendations.append(f"📝 {total_skipped} tests were skipped")
            recommendations.append(
                "🔍 Review skipped tests for missing dependencies or requirements"
            )

        # Success case
        if not critical_failures:
            recommendations.append("✅ All critical tests passed!")
            recommendations.append("🚀 Application is ready for deployment")
            recommendations.append("📊 Consider running performance tests regularly")
            recommendations.append("🔒 Security validation completed successfully")

        return recommendations

    def _save_detailed_report(self, report: dict[str, Any]) -> None:
        """Save detailed report to file"""
        try:
            with open(self.report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📊 Detailed report saved to: {self.report_file}")
        except Exception as e:
            logger.error(f"Could not save report: {e}")

    def _print_summary(self, report: dict[str, Any]) -> None:
        """Print test summary"""

        print("\n" + "=" * 80)
        print("🎯 TEST SUITE SUMMARY")
        print("=" * 80)

        summary = report["summary"]

        # Overall result
        if summary["overall_success"]:
            print("🎉 OVERALL RESULT: SUCCESS")
        else:
            print("❌ OVERALL RESULT: FAILURE")

        print(f"⏱️ Total Duration: {report['metadata']['total_duration']:.1f} seconds")
        print()

        # Suite breakdown
        print("📋 Test Suite Results:")
        for name, result in self.results.items():
            status = "✅" if result["success"] else "❌"
            duration = result.get("duration", 0)
            tests_info = ""

            if result.get("tests_run", 0) > 0:
                tests_info = f" ({result['tests_run']} tests)"

            critical_indicator = " [CRITICAL]" if result.get("critical", False) else ""

            print(f"  {status} {name}: {duration:.1f}s{tests_info}{critical_indicator}")

        print()

        # Test statistics
        if summary["total_tests"] > 0:
            print("📊 Test Statistics:")
            print(f"  Total Tests: {summary['total_tests']}")
            print(f"  Passed: {summary['tests_passed']} ({summary['success_rate']:.1f}%)")
            print(f"  Failed: {summary['tests_failed']}")
            print(f"  Skipped: {summary['tests_skipped']}")
            print()

        # Recommendations
        print("💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  {rec}")

        print("=" * 80)

    def run_quick_validation(self) -> bool:
        """Run quick validation tests only"""
        print("⚡ Running Quick Validation Tests")
        print("=" * 60)

        quick_tests = [
            {
                "name": "Syntax Check",
                "description": "Python syntax validation",
                "command": [
                    "python",
                    "-m",
                    "pytest",
                    "tests/test_gui.py::TestCodeQuality::test_no_syntax_errors",
                    "-v",
                ],
                "critical": True,
                "timeout": 30,
            },
            {
                "name": "Import Check",
                "description": "Module import validation",
                "command": [
                    "python",
                    "-m",
                    "pytest",
                    "tests/test_comprehensive_suite.py::TestCoreFunctionality::test_application_startup",
                    "-v",
                ],
                "critical": True,
                "timeout": 30,
            },
        ]

        all_passed = True
        for test in quick_tests:
            result = self._run_test_suite(test)
            if not result["success"]:
                all_passed = False
                if test["critical"]:
                    break

        status = "✅ PASSED" if all_passed else "❌ FAILED"
        print(f"\n{status} Quick validation completed")

        return all_passed


def main():
    """Main test runner entry point"""

    runner = TestSuiteRunner()

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            success = runner.run_quick_validation()
            return 0 if success else 1
        elif sys.argv[1] == "--help":
            print("Modern Test Suite Runner")
            print("Usage:")
            print("  python run_tests.py           # Run full test suite")
            print("  python run_tests.py --quick   # Run quick validation only")
            print("  python run_tests.py --help    # Show this help")
            return 0

    # Run comprehensive tests
    report = runner.run_comprehensive_tests()

    # Return appropriate exit code
    return 0 if report["summary"]["overall_success"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
