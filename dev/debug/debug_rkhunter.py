#!/usr/bin/env python3
"""
Debug script to see what RKHunter actually outputs
"""
from core.rkhunter_wrapper import RKHunterWrapper

import os

import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

def debug_rkhunter_output():
    """Debug RKHunter output to see what's being captured"""
    print("Debugging RKHunter output...")

    wrapper = RKHunterWrapper()

    # Test basic wrapper functionality
    print(f"RKHunter available: {wrapper.is_available()}")

    if not wrapper.is_available():
        print("RKHunter is not available. Please install it first.")
        return False

    print("Running RKHunter scan with debug output...")

    # Enable debug logging
    import logging

    logging.basicConfig(level=logging.DEBUG)

    try:
        # Run a system scan to test authentication
        result = wrapper.scan_system()

        print(f"\n=== SCAN RESULT ===")
        print(f"Success: {result.success}")
        print(f"Tests run: {result.tests_run}")
        print(f"Total tests: {result.total_tests}")
        print(f"Warnings: {result.warnings_found}")
        print(f"Infections: {result.infections_found}")
        print(f"Skipped: {result.skipped_tests}")
        print(f"Error message: {result.error_message}")
        print(f"Scan summary: {result.scan_summary}")

        if result.findings:
            print(f"\n=== FINDINGS ({len(result.findings)}) ===")
            for i, finding in enumerate(result.findings):
                print(f"{i + 1}. {finding.test_name}: {finding.result.value} - {finding.description}")

        return True

    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback

        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_rkhunter_output()
