#!/usr/bin/env python3
"""
Test script to verify the improved RKHunter configuration validation and auto-fix
"""

import sys
import tempfile
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_config_validation_improvements():
    """Test the improved configuration validation with specific issue detection"""
    print("🔧 Testing Improved Configuration Validation")
    print("=" * 50)

    try:
        from core.rkhunter_optimizer import RKHunterOptimizer, RKHunterConfig

        # Create a test config file with known issues
        test_config_path = "/tmp/test_rkhunter_problematic.conf"

        # Write a configuration with various issues we want to detect
        problematic_config = """# Test RKHunter configuration with issues
LOGFILE=/tmp/rkhunter.log

# Obsolete option that should be flagged
WEB_CMD_TIMEOUT=300

# Regex patterns with escaping issues
ALLOWHIDDENDIR=/dev/.static/\\+
ALLOWHIDDENFILE=/usr/share/man/\\-whatis

# Egrep usage that should be flagged
GREP_CMD="/usr/bin/egrep"

# Valid configuration
UPDATE_MIRRORS=1
MIRRORS_MODE=0
AUTO_X_DETECT=1
"""

        with open(test_config_path, 'w') as f:
            f.write(problematic_config)

        print(f"✅ Created test config with intentional issues: {test_config_path}")

        # Test the optimizer with this problematic config
        optimizer = RKHunterOptimizer(config_path=test_config_path)

        print("🔍 Testing configuration validation...")

        # Test the validation method directly
        warnings = optimizer._validate_configuration()

        print(f"✅ Validation found {len(warnings)} issues:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

        # Test the auto-fix functionality
        print("\n🛠️ Testing auto-fix functionality...")
        fixes = optimizer._auto_fix_config_issues()

        print(f"✅ Auto-fix applied {len(fixes)} fixes:")
        for i, fix in enumerate(fixes, 1):
            print(f"   {i}. {fix}")

        # Check if the issues are now resolved
        print("\n🔍 Re-validating after auto-fix...")
        warnings_after = optimizer._validate_configuration()

        print(f"✅ Validation after fixes found {len(warnings_after)} remaining issues:")
        for i, warning in enumerate(warnings_after, 1):
            print(f"   {i}. {warning}")

        # Show the difference
        issues_fixed = len(warnings) - len(warnings_after)
        if issues_fixed > 0:
            print(f"\n🎉 SUCCESS: {issues_fixed} configuration issues were automatically fixed!")
        else:
            print(f"\n⚠️ No issues were automatically fixed")

        # Show the final config content
        print("\n📄 Final configuration after fixes:")
        with open(test_config_path, 'r') as f:
            content = f.read()
            print(content[:500] + "..." if len(content) > 500 else content)

        # Clean up
        os.unlink(test_config_path)

        return issues_fixed > 0

    except Exception as e:
        print(f"❌ Error during config validation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimization_with_improved_reporting():
    """Test the full optimization process with improved reporting"""
    print("\n" + "=" * 50)
    print("🚀 Testing Full Optimization with Improved Reporting")

    try:
        from core.rkhunter_optimizer import RKHunterOptimizer, RKHunterConfig

        # Create a test config with a known issue
        test_config_path = "/tmp/test_rkhunter_optimization.conf"

        config_with_issues = """# Test config for optimization
LOGFILE=/tmp/rkhunter.log
WEB_CMD_TIMEOUT=300
ALLOWHIDDENDIR=/tmp/\\+test
"""

        with open(test_config_path, 'w') as f:
            f.write(config_with_issues)

        # Create optimizer and config
        optimizer = RKHunterOptimizer(config_path=test_config_path)
        config = RKHunterConfig(
            update_mirrors=True,
            auto_update_db=True,
            performance_mode="balanced"
        )

        print("🔄 Running optimization with improved reporting...")

        # Run optimization
        report = optimizer.optimize_configuration(config)

        # Display results with focus on warnings and recommendations
        print(f"\n📊 Optimization Results:")
        print(f"   Config changes: {len(report.config_changes)}")
        print(f"   Performance improvements: {len(report.performance_improvements)}")
        print(f"   Warnings: {len(report.warnings)}")
        print(f"   Recommendations: {len(report.recommendations)}")

        print(f"\n⚠️ Detailed Warnings ({len(report.warnings)}):")
        for i, warning in enumerate(report.warnings, 1):
            print(f"   {i}. {warning}")

        print(f"\n💡 Recommendations ({len(report.recommendations)}):")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"   {i}. {rec}")

        # Check if we have specific, actionable warnings instead of vague ones
        specific_warnings = [w for w in report.warnings if "Unknown config option" in w or "Invalid backslash" in w or "obsolete" in w]
        vague_warnings = [w for w in report.warnings if w == "⚠️ Configuration syntax issues detected"]

        print(f"\n📈 Warning Quality Analysis:")
        print(f"   Specific, actionable warnings: {len(specific_warnings)}")
        print(f"   Vague, unhelpful warnings: {len(vague_warnings)}")

        success = len(specific_warnings) > 0 and len(vague_warnings) == 0

        if success:
            print(f"\n🎉 SUCCESS: Warnings are now specific and actionable!")
        else:
            print(f"\n⚠️ Still have vague warnings that need improvement")

        # Clean up
        os.unlink(test_config_path)

        return success

    except Exception as e:
        print(f"❌ Error during optimization test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 RKHunter Configuration Validation & Auto-Fix Test")
    print("=" * 60)

    success1 = test_config_validation_improvements()
    success2 = test_optimization_with_improved_reporting()

    print("\n" + "=" * 60)
    print("🏁 Final Results:")
    print(f"   Config Validation & Auto-Fix: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Improved Warning Reporting: {'✅ PASS' if success2 else '❌ FAIL'}")

    if success1 and success2:
        print("\n🎉🎉 GREAT SUCCESS! 🎉🎉")
        print("The RKHunter optimization now provides:")
        print("• Specific, actionable configuration warnings")
        print("• Automatic fixes for common issues")
        print("• Detailed recommendations for manual fixes")
        print("• Clear guidance on what each issue means")
        print("\nNo more vague 'Configuration syntax issues detected' warnings!")
    else:
        print("\n🔧 Some improvements still needed")
