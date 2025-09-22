#!/usr/bin/env python3
"""
Configuration status checker for xanadOS Security API.
"""

import sys
from pathlib import Path

try:
    from app.utils.config import get_api_security_config, get_secure_database_url
    from app.utils.config_migration import validate_migration

    print("=== xanadOS Security API Configuration Status ===\n")

    # Get configuration
    api_config = get_api_security_config()
    print("✅ Configuration loaded successfully")

    # Database configuration
    db_url = get_secure_database_url()
    db_path = api_config["database"]["path"]
    print(f"✅ Database URL: {db_url}")
    print(f"✅ Database path: {db_path}")

    # JWT configuration
    jwt_config = api_config["jwt"]
    secret_length = len(jwt_config["secret_key"])
    print(f"✅ JWT secret key length: {secret_length} characters")
    print(f"✅ JWT algorithm: {jwt_config['algorithm']}")
    print(f"✅ Access token expire: {jwt_config['access_token_expire_minutes']} minutes")

    # Redis configuration
    redis_config = api_config["redis"]
    print(f"✅ Redis host: {redis_config['host']}:{redis_config['port']}")

    # Security settings
    security_config = api_config["security"]
    print(f"✅ HTTPS required: {security_config['require_https']}")
    print(f"✅ Input validation: {security_config['input_validation']}")

    # Validation
    validation = validate_migration()
    print(f"\n=== Validation Results ===")
    print(f"Database migrated: {validation['database_migrated']}")
    print(f"Config valid: {validation['config_valid']}")
    print(f"Environment applied: {validation['environment_applied']}")

    if validation['security_warnings']:
        print("\n⚠️  Security Warnings:")
        for warning in validation['security_warnings']:
            print(f"  - {warning}")
    else:
        print("\n✅ No security warnings")

    print("\n🎉 Configuration system is working correctly!")

except Exception as e:
    print(f"❌ Configuration check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
