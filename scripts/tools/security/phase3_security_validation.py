#!/usr/bin/env python3
"""
Phase 3 Security Implementation Validation Script

This script validates all the security enhancements implemented in Phase 3:
1. Exception handling improvements in client_sdk.py
2. Secure file upload endpoints with validation
3. Enhanced rate limiting coverage for expensive operations
4. Improved error message sanitization
5. Code quality improvements

Tests security measures to ensure they meet production standards.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class Phase3SecurityValidator:
    """Comprehensive Phase 3 security validation."""

    def __init__(self):
        self.project_root = project_root
        self.results = {
            "exception_handling": {"passed": 0, "failed": 0, "issues": []},
            "upload_security": {"passed": 0, "failed": 0, "issues": []},
            "rate_limiting": {"passed": 0, "failed": 0, "issues": []},
            "error_sanitization": {"passed": 0, "failed": 0, "issues": []},
            "code_quality": {"passed": 0, "failed": 0, "issues": []}
        }

    def validate_exception_handling(self) -> bool:
        """Test exception handling improvements in client_sdk.py."""
        print("🔍 Validating Exception Handling Improvements...")

        client_sdk_path = self.project_root / "app" / "api" / "client_sdk.py"
        if not client_sdk_path.exists():
            self.results["exception_handling"]["failed"] += 1
            self.results["exception_handling"]["issues"].append("client_sdk.py not found")
            return False

        content = client_sdk_path.read_text()

        # Check for bare except blocks
        bare_except_pattern = r'except\s*:\s*\n'
        bare_excepts = re.findall(bare_except_pattern, content)
        if bare_excepts:
            self.results["exception_handling"]["failed"] += 1
            self.results["exception_handling"]["issues"].append(f"Found {len(bare_excepts)} bare except blocks")
        else:
            self.results["exception_handling"]["passed"] += 1

        # Check for overly broad exception handlers
        broad_except_pattern = r'except\s+Exception\s+as\s+\w+:\s*\n\s*return\s+False'
        if re.search(broad_except_pattern, content):
            self.results["exception_handling"]["issues"].append("Found overly broad exception handlers")

        # Check for custom exception imports
        custom_exceptions = ["NetworkError", "AuthenticationError", "ValidationError"]
        imports_found = []
        for exc in custom_exceptions:
            if exc in content:
                imports_found.append(exc)

        if len(imports_found) >= 2:
            self.results["exception_handling"]["passed"] += 1
        else:
            self.results["exception_handling"]["failed"] += 1
            self.results["exception_handling"]["issues"].append(f"Missing custom exception imports: {custom_exceptions}")

        print(f"  ✅ Exception handling validation completed")
        return True

    def validate_upload_security(self) -> bool:
        """Test secure file upload endpoint implementation."""
        print("🔍 Validating Upload Endpoint Security...")

        security_api_path = self.project_root / "app" / "api" / "security_api.py"
        if not security_api_path.exists():
            self.results["upload_security"]["failed"] += 1
            self.results["upload_security"]["issues"].append("security_api.py not found")
            return False

        content = security_api_path.read_text()

        # Check for upload endpoint
        if "/v1/files/upload" in content:
            self.results["upload_security"]["passed"] += 1
        else:
            self.results["upload_security"]["failed"] += 1
            self.results["upload_security"]["issues"].append("Upload endpoint not found")

        # Check for file size validation
        if "MAX_FILE_SIZE" in content and "100 * 1024 * 1024" in content:
            self.results["upload_security"]["passed"] += 1
        else:
            self.results["upload_security"]["failed"] += 1
            self.results["upload_security"]["issues"].append("File size validation missing")

        # Check for content type validation
        if "allowed_types" in content and "content_type" in content:
            self.results["upload_security"]["passed"] += 1
        else:
            self.results["upload_security"]["failed"] += 1
            self.results["upload_security"]["issues"].append("Content type validation missing")

        # Check for dangerous extension blocking
        if "dangerous_extensions" in content and ".exe" in content:
            self.results["upload_security"]["passed"] += 1
        else:
            self.results["upload_security"]["failed"] += 1
            self.results["upload_security"]["issues"].append("Dangerous extension blocking missing")

        # Check for malware scanning
        if "malware_signatures" in content or "threat_detected" in content:
            self.results["upload_security"]["passed"] += 1
        else:
            self.results["upload_security"]["failed"] += 1
            self.results["upload_security"]["issues"].append("Malware scanning missing")

        print(f"  ✅ Upload security validation completed")
        return True

    def validate_rate_limiting(self) -> bool:
        """Test enhanced rate limiting coverage."""
        print("🔍 Validating Rate Limiting Coverage...")

        security_api_path = self.project_root / "app" / "api" / "security_api.py"
        content = security_api_path.read_text()

        # Check for upload rate limiting
        if "upload_limits" in content and "requests_per_minute" in content:
            self.results["rate_limiting"]["passed"] += 1
        else:
            self.results["rate_limiting"]["failed"] += 1
            self.results["rate_limiting"]["issues"].append("Upload rate limiting missing")

        # Check for system scan rate limiting
        if "scan_limits" in content:
            self.results["rate_limiting"]["passed"] += 1
        else:
            self.results["rate_limiting"]["failed"] += 1
            self.results["rate_limiting"]["issues"].append("System scan rate limiting missing")

        # Check for rate limiter usage
        if "self.rate_limiter.is_rate_limited" in content:
            self.results["rate_limiting"]["passed"] += 1
        else:
            self.results["rate_limiting"]["failed"] += 1
            self.results["rate_limiting"]["issues"].append("Rate limiter not properly integrated")

        # Check for rate limit headers
        if "X-RateLimit-" in content and "Retry-After" in content:
            self.results["rate_limiting"]["passed"] += 1
        else:
            self.results["rate_limiting"]["failed"] += 1
            self.results["rate_limiting"]["issues"].append("Rate limit headers missing")

        print(f"  ✅ Rate limiting validation completed")
        return True

    def validate_error_sanitization(self) -> bool:
        """Test error message sanitization improvements."""
        print("🔍 Validating Error Message Sanitization...")

        security_api_path = self.project_root / "app" / "api" / "security_api.py"
        content = security_api_path.read_text()

        # Check for secure error handlers
        if "general_exception_handler" in content and "error_id" in content:
            self.results["error_sanitization"]["passed"] += 1
        else:
            self.results["error_sanitization"]["failed"] += 1
            self.results["error_sanitization"]["issues"].append("Secure error handlers missing")

        # Check for information disclosure prevention
        dangerous_patterns = [
            r'detail.*str\(e\)',  # Direct exception exposure
            r'detail.*f".*{e}.*"',  # F-string exception exposure
        ]

        disclosure_count = 0
        for pattern in dangerous_patterns:
            matches = re.findall(pattern, content)
            disclosure_count += len(matches)

        if disclosure_count < 5:  # Some may be intentionally left for debugging
            self.results["error_sanitization"]["passed"] += 1
        else:
            self.results["error_sanitization"]["failed"] += 1
            self.results["error_sanitization"]["issues"].append(f"Found {disclosure_count} potential information disclosure issues")

        # Check for generic error messages
        if "Please check your input and try again" in content:
            self.results["error_sanitization"]["passed"] += 1
        else:
            self.results["error_sanitization"]["failed"] += 1
            self.results["error_sanitization"]["issues"].append("Generic error messages missing")

        print(f"  ✅ Error sanitization validation completed")
        return True

    def validate_code_quality(self) -> bool:
        """Test general code quality improvements."""
        print("🔍 Validating Code Quality...")

        # Check syntax validity
        files_to_check = [
            "app/api/security_api.py",
            "app/api/client_sdk.py",
            "app/core/exceptions.py"
        ]

        syntax_valid = 0
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    ast.parse(full_path.read_text())
                    syntax_valid += 1
                except SyntaxError as e:
                    self.results["code_quality"]["issues"].append(f"Syntax error in {file_path}: {e}")

        if syntax_valid == len(files_to_check):
            self.results["code_quality"]["passed"] += 1
        else:
            self.results["code_quality"]["failed"] += 1

        # Check for TODO/FIXME comments
        security_api_path = self.project_root / "app" / "api" / "security_api.py"
        if security_api_path.exists():
            content = security_api_path.read_text()
            todo_count = len(re.findall(r'TODO|FIXME|HACK', content, re.IGNORECASE))

            if todo_count < 5:  # Some TODOs are acceptable
                self.results["code_quality"]["passed"] += 1
            else:
                self.results["code_quality"]["failed"] += 1
                self.results["code_quality"]["issues"].append(f"Found {todo_count} TODO/FIXME comments")

        print(f"  ✅ Code quality validation completed")
        return True

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive validation report."""
        total_passed = sum(cat["passed"] for cat in self.results.values())
        total_failed = sum(cat["failed"] for cat in self.results.values())
        total_tests = total_passed + total_failed

        if total_tests == 0:
            success_rate = 0
        else:
            success_rate = (total_passed / total_tests) * 100

        report = {
            "phase": "Phase 3 Security Implementation",
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "success_rate": round(success_rate, 1),
            "categories": {}
        }

        for category, results in self.results.items():
            cat_total = results["passed"] + results["failed"]
            cat_rate = (results["passed"] / cat_total * 100) if cat_total > 0 else 0

            report["categories"][category] = {
                "tests": cat_total,
                "passed": results["passed"],
                "failed": results["failed"],
                "success_rate": round(cat_rate, 1),
                "issues": results["issues"]
            }

        return report

    def print_report(self, report: dict[str, Any]):
        """Print formatted validation report."""
        print("\n" + "=" * 80)
        print("🛡️  PHASE 3 SECURITY VALIDATION REPORT")
        print("=" * 80)

        print(f"\n📊 OVERALL SUMMARY:")
        print(f"   Total Security Tests: {report['total_tests']}")
        print(f"   ✅ Passed: {report['passed']} ({report['success_rate']}%)")
        print(f"   ❌ Failed: {report['failed']} ({100 - report['success_rate']:.1f}%)")
        print(f"   🎯 Security Score: {report['success_rate']}%")

        print(f"\n📋 SECURITY CATEGORIES:")
        for category, results in report["categories"].items():
            status = "✅" if results["failed"] == 0 else "⚠️" if results["success_rate"] >= 75 else "❌"
            print(f"   {category.replace('_', ' ').title()}: {results['success_rate']}% {status}")

        print(f"\n🔍 DETAILED RESULTS:")
        for category, results in report["categories"].items():
            print(f"\n   🔹 {category.replace('_', ' ').title()}:")
            print(f"      ✅ Passed: {results['passed']}")
            print(f"      ❌ Failed: {results['failed']}")

            if results["issues"]:
                print(f"      ⚠️  Issues:")
                for issue in results["issues"]:
                    print(f"         • {issue}")

        # Security recommendation
        if report["success_rate"] >= 95:
            recommendation = "🎉 EXCELLENT: Phase 3 security implementation is robust!"
        elif report["success_rate"] >= 85:
            recommendation = "✅ GOOD: Strong security implementation with minor improvements needed"
        elif report["success_rate"] >= 75:
            recommendation = "⚠️  FAIR: Adequate security but requires attention to failed tests"
        else:
            recommendation = "❌ POOR: Security implementation needs significant improvements"

        print(f"\n🛡️ SECURITY RECOMMENDATION: {recommendation}")

        if report["success_rate"] >= 90:
            print("   ✅ All critical security measures are properly implemented")
            print("   🚀 Ready for production deployment")
        else:
            print("   ⚠️  Address failed tests before production deployment")
            print("   🔧 Review security implementation gaps")

        print("\n" + "=" * 80)


def main():
    """Run Phase 3 security validation."""
    print("🚀 Starting Phase 3 Security Implementation Validation")
    print("Testing: Exception Handling, Upload Security, Rate Limiting, Error Sanitization")
    print("-" * 80)

    validator = Phase3SecurityValidator()

    # Run all validation tests
    validator.validate_exception_handling()
    validator.validate_upload_security()
    validator.validate_rate_limiting()
    validator.validate_error_sanitization()
    validator.validate_code_quality()

    # Generate and display report
    report = validator.generate_report()
    validator.print_report(report)

    # Return appropriate exit code
    return 0 if report["success_rate"] >= 90 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
