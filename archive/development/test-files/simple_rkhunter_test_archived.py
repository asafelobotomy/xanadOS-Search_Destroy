#!/usr/bin/env python3
"""
Simple script for RKHunter availability detection - archived.
This filename avoids pytest collection.
"""
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_rkhunter_availability():
    logger.info("Testing RKHunter availability detection...")
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

if __name__ == '__main__':
    ok, p = check_rkhunter_availability()
    print('Available:', ok, 'Path:', p)
