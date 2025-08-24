#!/usr/bin/env python3
"""
Demo script for RKHunter availability detection - standalone version

This is archived and not part of the pytest suite. Run directly if needed.
"""
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_rkhunter_availability():
    """
    Check RKHunter availability using simple path checks.
    """
    logger.info("Checking RKHunter availability...")

    possible_paths = [
        '/usr/bin/rkhunter',
        '/usr/local/bin/rkhunter',
        '/opt/rkhunter/bin/rkhunter',
    ]

    rkhunter_path = None

    for path in possible_paths:
        if os.path.exists(path):
            rkhunter_path = path
            logger.info(f"Found RKHunter at {path}")
            break

    return rkhunter_path is not None, rkhunter_path


def main():
    print("== RKHunter Availability Demo ==")
    is_available, rkhunter_path = check_rkhunter_availability()
    print(f"Available: {is_available}")
    if rkhunter_path:
        print(f"Path: {rkhunter_path}")


if __name__ == "__main__":
    main()
