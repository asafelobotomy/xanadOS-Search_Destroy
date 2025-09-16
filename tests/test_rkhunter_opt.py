#!/usr/bin/env python3
"""Test script to investigate RKHunter optimization issues"""

import sys
import traceback
from pathlib import Path

# Add the app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_optimization():
    """Test RKHunter optimization functionality"""
    try:
        print("=== Testing RKHunter Optimization ===")

        # Import required modules
        from app.core.rkhunter_optimizer import RKHunterOptimizer, RKHunterConfig
        print("✅ Successfully imported RKHunter modules")

        # Create a test config
        config = RKHunterConfig(
            update_mirrors=True,
            mirrors_mode=0,
            auto_update_db=True,
            check_frequency="daily",
            enable_logging=True,
            log_level="info",
            custom_rules_enabled=False,
            custom_rules_path="",
            baseline_auto_update=True,
            performance_mode="balanced",
            network_timeout=300
        )
        print("✅ Created test configuration")

        # Create optimizer instance
        test_config_path = Path.home() / ".config" / "search-and-destroy" / "rkhunter_test.conf"
        optimizer = RKHunterOptimizer(config_path=str(test_config_path))
        print(f"✅ Created optimizer with config path: {test_config_path}")

        # Test getting current status first
        print("\n=== Testing Status Check ===")
        try:
            status = optimizer.get_current_status()
            print(f"✅ Status check successful:")
            print(f"   Version: {status.version}")
            print(f"   Database version: {status.database_version}")
            print(f"   Baseline exists: {status.baseline_exists}")
            print(f"   Issues found: {len(status.issues_found)}")
            if status.issues_found:
                print(f"   First issue: {status.issues_found[0]}")
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            traceback.print_exc()

        # Test optimization
        print("\n=== Testing Optimization ===")
        try:
            report = optimizer.optimize_configuration(config)
            print(f"✅ Optimization completed successfully!")
            print(f"   Config changes: {len(report.config_changes)}")
            print(f"   Performance improvements: {len(report.performance_improvements)}")
            print(f"   Warnings: {len(report.warnings)}")
            print(f"   Recommendations: {len(report.recommendations)}")

            if report.config_changes:
                print(f"\n   Sample changes:")
                for i, change in enumerate(report.config_changes[:3]):
                    print(f"     {i+1}. {change}")

            if report.performance_improvements:
                print(f"\n   Sample improvements:")
                for i, improvement in enumerate(report.performance_improvements[:3]):
                    print(f"     {i+1}. {improvement}")

            if report.warnings:
                print(f"\n   Sample warnings:")
                for i, warning in enumerate(report.warnings[:3]):
                    print(f"     {i+1}. {warning}")

            return report

        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            traceback.print_exc()
            return None

    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_optimization()
    if result:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
