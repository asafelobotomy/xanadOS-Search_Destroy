#!/usr/bin/env python3
"""
Rate Limiting Configuration Validation Script
Validates that rate limiting configuration is properly set up.
"""

import json
import logging
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.utils.config import get_api_security_config


def validate_rate_limiting_config():
    """Validate rate limiting configuration."""
    print("🔒 RATE LIMITING CONFIGURATION VALIDATION")
    print("=" * 60)

    try:
        # Load configuration
        config = get_api_security_config()
        rate_config = config.get("rate_limiting", {})

        print("\n📋 CURRENT CONFIGURATION:")
        print(f"   Enabled: {rate_config.get('enabled', 'NOT SET')}")
        print(f"   Requests per minute: {rate_config.get('requests_per_minute', 'NOT SET')}")
        print(f"   Requests per hour: {rate_config.get('requests_per_hour', 'NOT SET')}")
        print(f"   Requests per day: {rate_config.get('requests_per_day', 'NOT SET')}")
        print(f"   Burst limit: {rate_config.get('burst_limit', 'NOT SET')}")
        print(f"   Whitelist IPs: {rate_config.get('whitelist_ips', 'NOT SET')}")
        print(f"   Blacklist IPs: {rate_config.get('blacklist_ips', 'NOT SET')}")

        # Validate required fields
        required_fields = [
            'enabled', 'requests_per_minute', 'requests_per_hour',
            'requests_per_day', 'burst_limit', 'whitelist_ips', 'blacklist_ips'
        ]

        missing_fields = [field for field in required_fields if field not in rate_config]

        print("\n✅ VALIDATION RESULTS:")
        if not missing_fields:
            print("   ✅ All required configuration fields present")

            # Validate values
            issues = []

            if not isinstance(rate_config.get('enabled'), bool):
                issues.append("'enabled' should be a boolean")

            numeric_fields = ['requests_per_minute', 'requests_per_hour', 'requests_per_day', 'burst_limit']
            for field in numeric_fields:
                if not isinstance(rate_config.get(field), int) or rate_config.get(field) <= 0:
                    issues.append(f"'{field}' should be a positive integer")

            list_fields = ['whitelist_ips', 'blacklist_ips']
            for field in list_fields:
                if not isinstance(rate_config.get(field), list):
                    issues.append(f"'{field}' should be a list")

            if issues:
                print("   ⚠️ Configuration issues found:")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print("   ✅ All configuration values are valid")
        else:
            print(f"   ❌ Missing required fields: {missing_fields}")

        # Check Redis configuration
        redis_config = config.get("redis", {})
        print("\n🔗 REDIS CONFIGURATION:")
        print(f"   Host: {redis_config.get('host', 'NOT SET')}")
        print(f"   Port: {redis_config.get('port', 'NOT SET')}")
        print(f"   Database: {redis_config.get('db', 'NOT SET')}")
        print(f"   SSL: {redis_config.get('ssl', 'NOT SET')}")

        # Check environment variable support
        print("\n🌍 ENVIRONMENT VARIABLE SUPPORT:")
        env_vars = [
            'RATE_LIMIT_ENABLED', 'RATE_LIMIT_PER_MINUTE', 'RATE_LIMIT_PER_HOUR',
            'RATE_LIMIT_PER_DAY', 'RATE_LIMIT_BURST', 'RATE_LIMIT_WHITELIST_IPS',
            'RATE_LIMIT_BLACKLIST_IPS', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB'
        ]

        set_vars = [var for var in env_vars if os.environ.get(var)]
        if set_vars:
            print(f"   ✅ Environment variables set: {set_vars}")
        else:
            print("   ℹ️ No rate limiting environment variables set (using defaults)")

        print("\n" + "=" * 60)

        if not missing_fields and not issues:
            print("🎉 Rate limiting configuration is valid and ready!")
            return True
        else:
            print("⚠️ Rate limiting configuration needs attention.")
            return False

    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def check_api_file_structure():
    """Check if the API files have the expected rate limiting code."""
    print("\n📁 API FILE STRUCTURE VALIDATION")
    print("=" * 60)

    api_file = "/home/solon/Documents/xanadOS-Search_Destroy/app/api/security_api.py"

    if not os.path.exists(api_file):
        print(f"❌ API file not found: {api_file}")
        return False

    try:
        with open(api_file, 'r') as f:
            content = f.read()

        # Check for key rate limiting components
        components = {
            'RateLimiter class': 'class RateLimiter:',
            'Rate limiting middleware': 'rate_limit_middleware',
            'Redis fallback': 'redis_available',
            'Burst protection': 'burst_limit',
            'Whitelist/Blacklist': 'whitelist_ips',
            'Rate limit endpoints': '/v1/rate-limit/'
        }

        print("\n🔍 CHECKING FOR RATE LIMITING COMPONENTS:")
        all_present = True

        for component, search_string in components.items():
            if search_string in content:
                print(f"   ✅ {component}: Found")
            else:
                print(f"   ❌ {component}: Missing")
                all_present = False

        if all_present:
            print("\n✅ All rate limiting components are present in the API file")
        else:
            print("\n⚠️ Some rate limiting components are missing")

        return all_present

    except Exception as e:
        print(f"❌ Error reading API file: {e}")
        return False


def main():
    """Main validation function."""
    print("🚀 Starting Rate Limiting Validation...")

    config_valid = validate_rate_limiting_config()
    structure_valid = check_api_file_structure()

    print("\n" + "=" * 60)
    print("📊 FINAL VALIDATION SUMMARY")
    print("=" * 60)

    if config_valid and structure_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Rate limiting implementation is ready for use")
        return True
    else:
        print("⚠️ SOME VALIDATIONS FAILED!")
        if not config_valid:
            print("❌ Configuration validation failed")
        if not structure_valid:
            print("❌ API structure validation failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
