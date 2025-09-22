#!/usr/bin/env python3
"""
Comprehensive Security Validation for Phase 2 Implementation
Tests all security fixes: JWT hardening, input validation, database security, and rate limiting.
"""

import asyncio
import json
import logging
import os
import sys
import time
import hashlib
import tempfile
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.utils.config import get_api_security_config, get_secure_database_url


class ComprehensiveSecurityValidator:
    """Comprehensive security validation for Phase 2 implementations."""

    def __init__(self):
        self.results = []
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for validation."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def validate_jwt_security(self):
        """Validate JWT security hardening."""
        self.logger.info("🔐 Validating JWT Security Hardening...")

        try:
            config = get_api_security_config()
            jwt_config = config.get("jwt", {})

            # Check required JWT configuration
            required_fields = ["secret_key", "algorithm", "access_token_expire_minutes",
                             "refresh_token_expire_days", "issuer", "audience"]

            missing_fields = [field for field in required_fields if field not in jwt_config]

            # Validate secret key strength
            secret_key = jwt_config.get("secret_key", "")
            secret_strength = len(secret_key) >= 32 and any(c.isdigit() for c in secret_key) and any(c.isalpha() for c in secret_key)

            # Check algorithm security
            secure_algorithm = jwt_config.get("algorithm", "") in ["HS256", "RS256", "ES256"]

            # Check token expiration settings
            access_expire = jwt_config.get("access_token_expire_minutes", 0)
            refresh_expire = jwt_config.get("refresh_token_expire_days", 0)
            secure_expiration = 1 <= access_expire <= 60 and 1 <= refresh_expire <= 30

            # Auto key rotation
            key_rotation = jwt_config.get("auto_rotate_keys", False)

            if not missing_fields and secret_strength and secure_algorithm and secure_expiration:
                self.results.append({
                    "category": "JWT Security",
                    "test": "JWT Configuration Hardening",
                    "status": "PASS",
                    "details": f"All JWT security measures properly configured. Key rotation: {key_rotation}"
                })
            else:
                issues = []
                if missing_fields:
                    issues.append(f"Missing fields: {missing_fields}")
                if not secret_strength:
                    issues.append("Weak secret key")
                if not secure_algorithm:
                    issues.append("Insecure algorithm")
                if not secure_expiration:
                    issues.append("Insecure token expiration")

                self.results.append({
                    "category": "JWT Security",
                    "test": "JWT Configuration Hardening",
                    "status": "FAIL",
                    "details": f"JWT security issues: {'; '.join(issues)}"
                })

            self.logger.info("✅ JWT security validation completed")

        except Exception as e:
            self.results.append({
                "category": "JWT Security",
                "test": "JWT Configuration Hardening",
                "status": "ERROR",
                "details": f"Error validating JWT security: {e}"
            })
            self.logger.error(f"❌ JWT security validation failed: {e}")

    def validate_input_validation(self):
        """Validate input validation implementation."""
        self.logger.info("🛡️ Validating Input Validation Implementation...")

        try:
            # Check if security_api.py contains input validation middleware
            api_file = Path("/home/solon/Documents/xanadOS-Search_Destroy/app/api/security_api.py")

            if not api_file.exists():
                self.results.append({
                    "category": "Input Validation",
                    "test": "API File Presence",
                    "status": "FAIL",
                    "details": "security_api.py file not found"
                })
                return

            content = api_file.read_text()

            # Check for key input validation components
            validation_components = {
                "InputValidationMiddleware": "class InputValidationMiddleware",
                "SQL Injection Protection": "prevent_sql_injection",
                "XSS Protection": "prevent_xss",
                "Path Traversal Protection": "path_traversal",
                "Request Size Limits": "max_request_size",
                "Header Validation": "max_headers",
                "Content Type Validation": "application/json"
            }

            passed_components = []
            failed_components = []

            for component, search_term in validation_components.items():
                if search_term in content:
                    passed_components.append(component)
                else:
                    failed_components.append(component)

            # Check for Pydantic validators
            pydantic_validators = [
                "validate_file_path", "validate_file_content", "validate_scan_type",
                "validate_paths", "validate_exclude_patterns", "validate_event_type",
                "validate_source", "validate_description", "validate_url"
            ]

            validator_count = sum(1 for validator in pydantic_validators if validator in content)

            if len(failed_components) == 0 and validator_count >= len(pydantic_validators) * 0.8:
                self.results.append({
                    "category": "Input Validation",
                    "test": "Input Validation Implementation",
                    "status": "PASS",
                    "details": f"All validation components present. Validators: {validator_count}/{len(pydantic_validators)}"
                })
            else:
                self.results.append({
                    "category": "Input Validation",
                    "test": "Input Validation Implementation",
                    "status": "PARTIAL",
                    "details": f"Missing: {failed_components}. Validators: {validator_count}/{len(pydantic_validators)}"
                })

            self.logger.info("✅ Input validation check completed")

        except Exception as e:
            self.results.append({
                "category": "Input Validation",
                "test": "Input Validation Implementation",
                "status": "ERROR",
                "details": f"Error validating input validation: {e}"
            })
            self.logger.error(f"❌ Input validation check failed: {e}")

    def validate_database_security(self):
        """Validate database security configuration."""
        self.logger.info("🗄️ Validating Database Security Configuration...")

        try:
            config = get_api_security_config()
            db_config = config.get("database", {})

            # Check database security configuration
            security_checks = {
                "Non-hardcoded path": bool(db_config.get("path") and not db_config["path"].startswith("/tmp")),
                "Connection pooling": bool(db_config.get("pool_size", 0) > 0),
                "Pool limits": bool(db_config.get("max_overflow", 0) > 0),
                "Backup enabled": bool(db_config.get("backup_enabled", False)),
                "Retention policy": bool(db_config.get("backup_retention_days", 0) > 0)
            }

            # Test secure database URL generation
            try:
                db_url = get_secure_database_url()
                url_secure = "sqlite://" in db_url and "search-and-destroy" in db_url
                security_checks["Secure URL generation"] = url_secure
            except Exception as e:
                security_checks["Secure URL generation"] = False
                self.logger.warning(f"Database URL generation failed: {e}")

            passed_checks = sum(1 for check in security_checks.values() if check)
            total_checks = len(security_checks)

            if passed_checks == total_checks:
                self.results.append({
                    "category": "Database Security",
                    "test": "Database Security Configuration",
                    "status": "PASS",
                    "details": f"All {total_checks} database security checks passed"
                })
            elif passed_checks >= total_checks * 0.8:
                failed_checks = [name for name, passed in security_checks.items() if not passed]
                self.results.append({
                    "category": "Database Security",
                    "test": "Database Security Configuration",
                    "status": "PARTIAL",
                    "details": f"{passed_checks}/{total_checks} passed. Failed: {failed_checks}"
                })
            else:
                failed_checks = [name for name, passed in security_checks.items() if not passed]
                self.results.append({
                    "category": "Database Security",
                    "test": "Database Security Configuration",
                    "status": "FAIL",
                    "details": f"Only {passed_checks}/{total_checks} passed. Failed: {failed_checks}"
                })

            self.logger.info("✅ Database security validation completed")

        except Exception as e:
            self.results.append({
                "category": "Database Security",
                "test": "Database Security Configuration",
                "status": "ERROR",
                "details": f"Error validating database security: {e}"
            })
            self.logger.error(f"❌ Database security validation failed: {e}")

    def validate_rate_limiting(self):
        """Validate rate limiting implementation."""
        self.logger.info("⚡ Validating Rate Limiting Implementation...")

        try:
            config = get_api_security_config()
            rate_config = config.get("rate_limiting", {})

            # Check rate limiting configuration
            required_fields = ["enabled", "requests_per_minute", "requests_per_hour",
                             "requests_per_day", "burst_limit", "whitelist_ips", "blacklist_ips"]

            missing_fields = [field for field in required_fields if field not in rate_config]

            # Validate configuration values
            config_valid = (
                isinstance(rate_config.get("enabled"), bool) and
                isinstance(rate_config.get("requests_per_minute"), int) and
                isinstance(rate_config.get("requests_per_hour"), int) and
                isinstance(rate_config.get("requests_per_day"), int) and
                isinstance(rate_config.get("burst_limit"), int) and
                isinstance(rate_config.get("whitelist_ips"), list) and
                isinstance(rate_config.get("blacklist_ips"), list)
            )

            # Check API implementation
            api_file = Path("/home/solon/Documents/xanadOS-Search_Destroy/app/api/security_api.py")
            content = api_file.read_text() if api_file.exists() else ""

            implementation_components = {
                "RateLimiter class": "class RateLimiter:",
                "Rate limiting middleware": "rate_limit_middleware",
                "Redis backend": "redis_available",
                "Memory fallback": "memory_cache",
                "Burst protection": "burst_limit",
                "IP whitelisting": "whitelist_ips",
                "IP blacklisting": "blacklist_ips",
                "Management endpoints": "/v1/rate-limit/"
            }

            implemented_components = [name for name, search in implementation_components.items()
                                    if search in content]

            if (not missing_fields and config_valid and
                len(implemented_components) == len(implementation_components)):
                self.results.append({
                    "category": "Rate Limiting",
                    "test": "Rate Limiting Implementation",
                    "status": "PASS",
                    "details": f"Complete rate limiting implementation with all {len(implemented_components)} components"
                })
            else:
                issues = []
                if missing_fields:
                    issues.append(f"Missing config: {missing_fields}")
                if not config_valid:
                    issues.append("Invalid configuration values")
                missing_impl = len(implementation_components) - len(implemented_components)
                if missing_impl > 0:
                    issues.append(f"Missing {missing_impl} implementation components")

                self.results.append({
                    "category": "Rate Limiting",
                    "test": "Rate Limiting Implementation",
                    "status": "PARTIAL",
                    "details": f"Rate limiting issues: {'; '.join(issues)}"
                })

            self.logger.info("✅ Rate limiting validation completed")

        except Exception as e:
            self.results.append({
                "category": "Rate Limiting",
                "test": "Rate Limiting Implementation",
                "status": "ERROR",
                "details": f"Error validating rate limiting: {e}"
            })
            self.logger.error(f"❌ Rate limiting validation failed: {e}")

    def validate_configuration_security(self):
        """Validate overall configuration security."""
        self.logger.info("⚙️ Validating Configuration Security...")

        try:
            config = get_api_security_config()

            # Check environment variable support
            env_vars_supported = [
                "JWT_SECRET_KEY", "JWT_ALGORITHM", "JWT_ACCESS_EXPIRE_MINUTES",
                "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD",
                "RATE_LIMIT_ENABLED", "RATE_LIMIT_PER_MINUTE"
            ]

            # Check Redis configuration
            redis_config = config.get("redis", {})
            redis_configured = all(key in redis_config for key in ["host", "port", "db"])

            # Check security settings
            security_config = config.get("security", {})
            security_features = [
                security_config.get("require_https", False),
                security_config.get("csrf_protection", False),
                security_config.get("input_validation", False),
                security_config.get("sql_injection_protection", False),
                security_config.get("xss_protection", False)
            ]

            security_enabled = sum(security_features)

            if redis_configured and security_enabled >= 4:
                self.results.append({
                    "category": "Configuration Security",
                    "test": "Security Configuration",
                    "status": "PASS",
                    "details": f"Redis configured, {security_enabled}/5 security features enabled"
                })
            else:
                issues = []
                if not redis_configured:
                    issues.append("Redis not properly configured")
                if security_enabled < 4:
                    issues.append(f"Only {security_enabled}/5 security features enabled")

                self.results.append({
                    "category": "Configuration Security",
                    "test": "Security Configuration",
                    "status": "PARTIAL",
                    "details": f"Configuration issues: {'; '.join(issues)}"
                })

            self.logger.info("✅ Configuration security validation completed")

        except Exception as e:
            self.results.append({
                "category": "Configuration Security",
                "test": "Security Configuration",
                "status": "ERROR",
                "details": f"Error validating configuration security: {e}"
            })
            self.logger.error(f"❌ Configuration security validation failed: {e}")

    def validate_error_handling(self):
        """Validate secure error handling implementation."""
        self.logger.info("🚨 Validating Error Handling Security...")

        try:
            api_file = Path("/home/solon/Documents/xanadOS-Search_Destroy/app/api/security_api.py")

            if not api_file.exists():
                self.results.append({
                    "category": "Error Handling",
                    "test": "Error Handling Implementation",
                    "status": "FAIL",
                    "details": "API file not found"
                })
                return

            content = api_file.read_text()

            # Check for secure error handling patterns
            error_handling_components = {
                "Exception handlers": "@self.app.exception_handler",
                "Secure error responses": "Internal Server Error",
                "Error logging": "logging.error",
                "Generic error messages": "An unexpected error occurred",
                "Status code handling": "status_code",
                "Error sanitization": "prevent information disclosure"
            }

            implemented_handlers = []
            for component, pattern in error_handling_components.items():
                if pattern in content:
                    implemented_handlers.append(component)

            # Check for potential information disclosure
            dangerous_patterns = [
                "str(exc)", "traceback", ".__dict__", "repr(",
                "Exception:", "Error:", "Traceback"
            ]

            potential_disclosures = [pattern for pattern in dangerous_patterns if pattern in content]

            if len(implemented_handlers) >= 4 and len(potential_disclosures) <= 2:
                self.results.append({
                    "category": "Error Handling",
                    "test": "Error Handling Implementation",
                    "status": "PASS",
                    "details": f"{len(implemented_handlers)}/6 error handling components, minimal disclosure risk"
                })
            else:
                issues = []
                if len(implemented_handlers) < 4:
                    issues.append(f"Only {len(implemented_handlers)}/6 error handling components")
                if len(potential_disclosures) > 2:
                    issues.append(f"Potential information disclosure: {potential_disclosures}")

                self.results.append({
                    "category": "Error Handling",
                    "test": "Error Handling Implementation",
                    "status": "PARTIAL",
                    "details": f"Error handling issues: {'; '.join(issues)}"
                })

            self.logger.info("✅ Error handling validation completed")

        except Exception as e:
            self.results.append({
                "category": "Error Handling",
                "test": "Error Handling Implementation",
                "status": "ERROR",
                "details": f"Error validating error handling: {e}"
            })
            self.logger.error(f"❌ Error handling validation failed: {e}")

    def validate_api_security_headers(self):
        """Validate security headers implementation."""
        self.logger.info("🔒 Validating Security Headers Implementation...")

        try:
            api_file = Path("/home/solon/Documents/xanadOS-Search_Destroy/app/api/security_api.py")
            content = api_file.read_text() if api_file.exists() else ""

            # Check for security middleware
            security_middleware = {
                "CORS Middleware": "CORSMiddleware",
                "Trusted Host Middleware": "TrustedHostMiddleware",
                "Rate Limit Headers": "X-RateLimit-",
                "Request ID Headers": "X-Request-ID",
                "Response Time Headers": "X-Response-Time"
            }

            implemented_headers = []
            for header_type, pattern in security_middleware.items():
                if pattern in content:
                    implemented_headers.append(header_type)

            # Check for security configurations
            security_configs = {
                "CORS origin restrictions": "allow_origins",
                "Credential handling": "allow_credentials",
                "Trusted hosts": "allowed_hosts",
                "Security headers": "add_header"
            }

            configured_security = []
            for config_type, pattern in security_configs.items():
                if pattern in content:
                    configured_security.append(config_type)

            total_security_features = len(implemented_headers) + len(configured_security)

            if total_security_features >= 6:
                self.results.append({
                    "category": "Security Headers",
                    "test": "Security Headers Implementation",
                    "status": "PASS",
                    "details": f"Comprehensive security headers: {implemented_headers + configured_security}"
                })
            elif total_security_features >= 4:
                self.results.append({
                    "category": "Security Headers",
                    "test": "Security Headers Implementation",
                    "status": "PARTIAL",
                    "details": f"Basic security headers: {implemented_headers + configured_security}"
                })
            else:
                self.results.append({
                    "category": "Security Headers",
                    "test": "Security Headers Implementation",
                    "status": "FAIL",
                    "details": f"Insufficient security headers: {implemented_headers + configured_security}"
                })

            self.logger.info("✅ Security headers validation completed")

        except Exception as e:
            self.results.append({
                "category": "Security Headers",
                "test": "Security Headers Implementation",
                "status": "ERROR",
                "details": f"Error validating security headers: {e}"
            })
            self.logger.error(f"❌ Security headers validation failed: {e}")

    def run_comprehensive_validation(self):
        """Run all security validations."""
        self.logger.info("🚀 Starting Comprehensive Phase 2 Security Validation...")

        validations = [
            self.validate_jwt_security,
            self.validate_input_validation,
            self.validate_database_security,
            self.validate_rate_limiting,
            self.validate_configuration_security,
            self.validate_error_handling,
            self.validate_api_security_headers
        ]

        for validation in validations:
            try:
                validation()
                time.sleep(0.1)  # Small delay between validations
            except Exception as e:
                self.logger.error(f"Validation {validation.__name__} failed with exception: {e}")

        self.generate_comprehensive_report()

    def generate_comprehensive_report(self):
        """Generate comprehensive security validation report."""
        print("\n" + "=" * 100)
        print("🔒 COMPREHENSIVE PHASE 2 SECURITY VALIDATION REPORT")
        print("=" * 100)

        # Calculate statistics by category
        categories = {}
        for result in self.results:
            category = result.get("category", "Unknown")
            if category not in categories:
                categories[category] = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "ERROR": 0, "total": 0}

            status = result.get("status", "ERROR")
            categories[category][status] += 1
            categories[category]["total"] += 1

        # Overall statistics
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        partial = sum(1 for r in self.results if r.get("status") == "PARTIAL")
        failed = sum(1 for r in self.results if r.get("status") == "FAIL")
        errors = sum(1 for r in self.results if r.get("status") == "ERROR")

        print(f"\n📊 OVERALL SUMMARY:")
        print(f"   Total Security Tests: {total_tests}")
        print(f"   ✅ Passed: {passed} ({(passed/total_tests*100):.1f}%)")
        print(f"   🔶 Partial: {partial} ({(partial/total_tests*100):.1f}%)")
        print(f"   ❌ Failed: {failed} ({(failed/total_tests*100):.1f}%)")
        print(f"   💥 Errors: {errors} ({(errors/total_tests*100):.1f}%)")

        # Calculate security score
        security_score = (passed * 100 + partial * 70) / total_tests if total_tests > 0 else 0
        print(f"   🎯 Security Score: {security_score:.1f}%")

        # Category breakdown
        print(f"\n📋 SECURITY CATEGORIES:")
        for category, stats in categories.items():
            category_score = (stats["PASS"] * 100 + stats["PARTIAL"] * 70) / stats["total"] if stats["total"] > 0 else 0
            print(f"   {category}: {category_score:.1f}% ({stats['PASS']}P/{stats['PARTIAL']}Pa/{stats['FAIL']}F/{stats['ERROR']}E)")

        # Detailed results
        print(f"\n📋 DETAILED VALIDATION RESULTS:")
        current_category = None
        for result in self.results:
            if result["category"] != current_category:
                current_category = result["category"]
                print(f"\n   🔹 {current_category}:")

            status_icon = {
                "PASS": "✅", "PARTIAL": "🔶",
                "FAIL": "❌", "ERROR": "💥"
            }.get(result["status"], "❓")

            print(f"      {status_icon} {result['test']}: {result['status']}")
            print(f"         Details: {result['details']}")

        # Security recommendations
        print(f"\n🛡️ SECURITY RECOMMENDATIONS:")

        if security_score >= 90:
            print("   🎉 EXCELLENT: Your Phase 2 security implementation is robust!")
            print("   ✅ All critical security measures are properly implemented")
            print("   🚀 Ready for production deployment")
        elif security_score >= 75:
            print("   ✅ GOOD: Your security implementation is solid with minor improvements needed")
            print("   🔧 Address partial implementations for complete security")
            print("   📋 Review failed tests and implement missing features")
        elif security_score >= 60:
            print("   🔶 MODERATE: Security implementation needs significant improvement")
            print("   ⚠️ Critical security gaps exist that need immediate attention")
            print("   🛠️ Focus on failed tests and upgrade partial implementations")
        else:
            print("   ❌ CRITICAL: Security implementation has major deficiencies")
            print("   🚨 Immediate security improvements required before deployment")
            print("   🔧 Address all failed tests and implement comprehensive security")

        # Next steps
        if failed > 0 or errors > 0:
            print(f"\n🔧 IMMEDIATE ACTION REQUIRED:")
            print("   1. Fix all FAILED and ERROR test cases")
            print("   2. Address security gaps identified in detailed results")
            print("   3. Re-run validation after fixes")
            print("   4. Consider additional security hardening measures")

        if partial > 0:
            print(f"\n📈 IMPROVEMENT OPPORTUNITIES:")
            print("   1. Complete partial implementations")
            print("   2. Enhance security configurations")
            print("   3. Add missing security features")
            print("   4. Strengthen error handling and validation")

        print("\n" + "=" * 100)

        return security_score >= 75


def main():
    """Main validation function."""
    validator = ComprehensiveSecurityValidator()
    success = validator.run_comprehensive_validation()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
