#!/usr/bin/env python3
"""
Configuration migration utilities for xanadOS Security API.

This module provides utilities to migrate existing configurations
and handle the transition from hardcoded to configurable settings.
"""

import logging
import os
import shutil
from pathlib import Path

from app.utils.config import (
    get_config,
    save_config,
    get_api_security_config,
    DATA_DIR,
    CONFIG_DIR,
    APP_NAME,
)


def migrate_hardcoded_database():
    """Migrate from hardcoded database location to secure location.

    Returns:
        bool: True if migration was successful or not needed
    """
    try:
        # Check for old hardcoded database file
        old_db_path = Path("security_api.db")

        if old_db_path.exists():
            # Get new secure location
            api_config = get_api_security_config()
            new_db_path = Path(api_config["database"]["path"])

            # Ensure secure directory exists
            new_db_path.parent.mkdir(parents=True, exist_ok=True)

            if not new_db_path.exists():
                # Move old database to secure location
                shutil.move(str(old_db_path), str(new_db_path))

                # Set secure permissions
                if os.name == "posix":
                    new_db_path.chmod(0o600)

                logging.getLogger(APP_NAME).info(
                    f"Migrated database from {old_db_path} to {new_db_path}"
                )
            else:
                # Remove old database (new one exists)
                old_db_path.unlink()
                logging.getLogger(APP_NAME).info(
                    f"Removed old database file: {old_db_path}"
                )

        return True

    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Database migration failed: {e}")
        return False


def migrate_environment_variables():
    """Update configuration with environment variables if present.

    Returns:
        bool: True if migration was successful
    """
    try:
        config = get_config()
        api_config = config.get("api_security", {})

        # Environment variable mappings
        env_mappings = {
            "JWT_SECRET_KEY": ("jwt", "secret_key"),
            "JWT_ALGORITHM": ("jwt", "algorithm"),
            "JWT_ACCESS_EXPIRE_MINUTES": ("jwt", "access_token_expire_minutes"),
            "JWT_REFRESH_EXPIRE_DAYS": ("jwt", "refresh_token_expire_days"),
            "JWT_ISSUER": ("jwt", "issuer"),
            "JWT_AUDIENCE": ("jwt", "audience"),
            "REDIS_HOST": ("redis", "host"),
            "REDIS_PORT": ("redis", "port"),
            "REDIS_DB": ("redis", "db"),
            "REDIS_PASSWORD": ("redis", "password"),
            "REDIS_SSL": ("redis", "ssl"),
            "API_REQUIRE_HTTPS": ("security", "require_https"),
            "API_MAX_REQUEST_SIZE_MB": ("security", "max_request_size_mb"),
            "API_ENABLE_CORS": ("security", "enable_cors"),
        }

        updated = False

        for env_var, (section, key) in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Ensure section exists
                if section not in api_config:
                    api_config[section] = {}

                # Convert value to appropriate type
                if key in [
                    "port",
                    "db",
                    "access_token_expire_minutes",
                    "refresh_token_expire_days",
                    "max_request_size_mb",
                ]:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                elif key in ["ssl", "require_https", "enable_cors"]:
                    env_value = env_value.lower() in ("true", "1", "yes", "on")

                # Update configuration
                api_config[section][key] = env_value
                updated = True

                logging.getLogger(APP_NAME).info(
                    f"Updated {section}.{key} from environment variable {env_var}"
                )

        if updated:
            config["api_security"] = api_config
            save_config(config)

        return True

    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Environment variable migration failed: {e}")
        return False


def validate_migration():
    """Validate that migration was successful.

    Returns:
        Dict[str, Any]: Validation results
    """
    results = {
        "database_migrated": False,
        "config_valid": False,
        "environment_applied": False,
        "security_warnings": [],
    }

    try:
        # Check database location
        api_config = get_api_security_config()
        db_path = Path(api_config["database"]["path"])

        if db_path.exists() and str(db_path).startswith(str(DATA_DIR)):
            results["database_migrated"] = True

        # Check configuration validity
        required_sections = ["database", "redis", "jwt", "security"]
        if all(section in api_config for section in required_sections):
            results["config_valid"] = True

        # Check environment variables
        env_vars = [
            "JWT_SECRET_KEY",
            "REDIS_HOST",
            "REDIS_PASSWORD",
            "API_REQUIRE_HTTPS",
            "API_ALLOWED_ORIGINS",
        ]

        env_found = any(os.environ.get(var) for var in env_vars)
        if env_found:
            results["environment_applied"] = True

        # Security warnings
        jwt_config = api_config.get("jwt", {})
        secret_key = jwt_config.get("secret_key", "")

        if len(secret_key) < 32:
            results["security_warnings"].append("JWT secret key is too short")

        if not api_config.get("security", {}).get("require_https", True):
            results["security_warnings"].append("HTTPS is not required")

        redis_config = api_config.get("redis", {})
        if not redis_config.get("password") and redis_config.get("host") != "localhost":
            results["security_warnings"].append(
                "Redis has no password for remote connection"
            )

    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Migration validation failed: {e}")

    return results


def run_full_migration():
    """Run complete configuration migration process.

    Returns:
        Dict[str, Any]: Migration results
    """
    logging.getLogger(APP_NAME).info("Starting configuration migration...")

    results = {
        "database_migration": migrate_hardcoded_database(),
        "environment_migration": migrate_environment_variables(),
        "validation": validate_migration(),
    }

    # Generate new secure configuration
    try:
        api_config = get_api_security_config()
        results["config_generated"] = True

        # Log important information
        logging.getLogger(APP_NAME).info(
            f"Database location: {api_config['database']['path']}"
        )
        logging.getLogger(APP_NAME).info(
            f"Redis configuration: {api_config['redis']['host']}:{api_config['redis']['port']}"
        )

        # Security warnings
        validation = results["validation"]
        if validation["security_warnings"]:
            for warning in validation["security_warnings"]:
                logging.getLogger(APP_NAME).warning(f"Security: {warning}")

    except Exception as e:
        results["config_generated"] = False
        logging.getLogger(APP_NAME).error(f"Configuration generation failed: {e}")

    logging.getLogger(APP_NAME).info("Configuration migration completed")
    return results


if __name__ == "__main__":
    # Run migration when script is executed directly
    import sys

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    results = run_full_migration()

    print("=== Configuration Migration Results ===")
    for key, value in results.items():
        if key == "validation":
            print(f"{key}:")
            for subkey, subvalue in value.items():
                print(f"  {subkey}: {subvalue}")
        else:
            print(f"{key}: {value}")

    # Exit with error code if critical migrations failed
    if not (results["database_migration"] and results["config_generated"]):
        sys.exit(1)
