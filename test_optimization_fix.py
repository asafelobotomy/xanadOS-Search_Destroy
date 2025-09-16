#!/usr/bin/env python3
"""
Test script to verify the optimization results fix
"""
import sys
from pathlib import Path
sys.path.append('.')

from app.core.rkhunter_optimizer import RKHunterOptimizer

def test_optimization_detection():
    """Test the optimization detection logic"""
    print("=== Testing RKHunter Optimization Detection ===")

    # Use user config path like the GUI does
    user_config_path = str(Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf')
    print(f"User config path: {user_config_path}")
    print(f"User config exists: {Path(user_config_path).exists()}")

    optimizer = RKHunterOptimizer(config_path=user_config_path)
    print(f"Optimizer config path: {optimizer.config_path}")

    # Test detect_fixable_issues (user config)
    print("\n1. Testing detect_fixable_issues() - User Config Check:")
    try:
        user_issues = optimizer.detect_fixable_issues()
        print(f"   Found {len(user_issues)} fixable issues in user config")
        if isinstance(user_issues, dict):
            issue_list = list(user_issues.keys())[:3]
        else:
            issue_list = user_issues[:3]
        for i, issue in enumerate(issue_list, 1):
            print(f"   {i}. {issue}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test _validate_configuration (system config)
    print("\n2. Testing _validate_configuration() - System Config Check:")
    try:
        system_warnings = optimizer._validate_configuration()
        print(f"   Found {len(system_warnings)} warnings in system config")
        for i, warning in enumerate(system_warnings[:3], 1):
            print(f"   {i}. {warning}")
    except Exception as e:
        print(f"   Error: {e}")

    # Show the difference
    print("\n3. Analysis:")
    print("   - detect_fixable_issues() checks user config at ~/.config/search-and-destroy/rkhunter.conf")
    print("   - _validate_configuration() runs 'rkhunter --config-check' on system config")
    print("   - This explains why we can have 'no user issues' but 'system warnings'")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_optimization_detection()
