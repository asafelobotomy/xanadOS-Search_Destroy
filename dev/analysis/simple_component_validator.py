#!/usr/bin/env python3
"""
Simple Component Validation for xanadOS Search & Destroy
Tests the basic functionality of unified components:
- Import tests
- Basic initialization tests
- Component availability verification
"""
from pathlib import Path

import sys

import traceback

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test core imports and component availability"""
    print("🔍 Testing component imports...")

    results = {
        "core_imports": False,
        "security_engine": False,
        "performance_optimizer": False,
        "legacy_components": False,
        "errors": [],
    }

    try:
        # Test core module imports
        from app.core import (
            UNIFIED_PERFORMANCE_AVAILABLE,
            UNIFIED_SECURITY_AVAILABLE,
            ClamAVWrapper,
            FileScanner,
        )

        results["core_imports"] = True
        print("  ✅ Core module imports successful")

        # Test unified security engine
        if UNIFIED_SECURITY_AVAILABLE:
            from app.core.unified_security_engine import (
                ProtectionMode,
                ThreatLevel,
                UnifiedSecurityEngine,
            )

            results["security_engine"] = True
            print("  ✅ Unified Security Engine available")
        else:
            results["errors"].append("Unified Security Engine not available")
            print("  ⚠️  Unified Security Engine not available")

        # Test unified performance optimizer
        if UNIFIED_PERFORMANCE_AVAILABLE:
            from app.core.unified_performance_optimizer import (
                PerformanceMode,
                UnifiedPerformanceOptimizer,
            )

            results["performance_optimizer"] = True
            print("  ✅ Unified Performance Optimizer available")
        else:
            results["errors"].append("Unified Performance Optimizer not available")
            print("  ⚠️  Unified Performance Optimizer not available")

        # Test legacy components
        from app.core import DatabaseConnectionPool, MemoryOptimizer

        results["legacy_components"] = True
        print("  ✅ Legacy components available")

    except Exception as e:
        results["errors"].append(f"Import error: {str(e)}")
        print(f"  ❌ Import failed: {e}")

    return results

def test_basic_functionality():
    """Test basic component functionality"""
    print("\n🔧 Testing basic functionality...")

    results = {
        "clamav_wrapper": False,
        "file_scanner": False,
        "security_engine_init": False,
        "performance_optimizer_init": False,
        "errors": [],
    }

    # Test ClamAV wrapper
    try:
        from app.core import ClamAVWrapper

        wrapper = ClamAVWrapper()
        results["clamav_wrapper"] = True
        print("  ✅ ClamAV Wrapper initialization successful")
    except Exception as e:
        results["errors"].append(f"ClamAV Wrapper error: {str(e)}")
        print(f"  ❌ ClamAV Wrapper failed: {e}")

    # Test File Scanner
    try:
        from app.core import FileScanner

        scanner = FileScanner()
        results["file_scanner"] = True
        print("  ✅ File Scanner initialization successful")
    except Exception as e:
        results["errors"].append(f"File Scanner error: {str(e)}")
        print(f"  ❌ File Scanner failed: {e}")

    # Test Unified Security Engine (if available)
    try:
        from app.core import UNIFIED_SECURITY_AVAILABLE

        if UNIFIED_SECURITY_AVAILABLE:
            from app.core.unified_security_engine import UnifiedSecurityEngine

            # Try initialization with required parameters
            engine = UnifiedSecurityEngine(watch_paths=["/tmp"])
            results["security_engine_init"] = True
            print("  ✅ Unified Security Engine initialization successful")
        else:
            print("  ⚠️  Unified Security Engine not available for testing")
    except Exception as e:
        results["errors"].append(f"Security Engine error: {str(e)}")
        print(f"  ❌ Unified Security Engine failed: {e}")

    # Test Unified Performance Optimizer (if available)
    try:
        from app.core import UNIFIED_PERFORMANCE_AVAILABLE

        if UNIFIED_PERFORMANCE_AVAILABLE:
            from app.core.unified_performance_optimizer import UnifiedPerformanceOptimizer

            optimizer = UnifiedPerformanceOptimizer()
            results["performance_optimizer_init"] = True
            print("  ✅ Unified Performance Optimizer initialization successful")
        else:
            print("  ⚠️  Unified Performance Optimizer not available for testing")
    except Exception as e:
        results["errors"].append(f"Performance Optimizer error: {str(e)}")
        print(f"  ❌ Unified Performance Optimizer failed: {e}")

    return results

def test_archived_components():
    """Verify archived components are no longer imported"""
    print("\n📦 Verifying archived components...")

    archived_components = ["auto_updater", "real_time_protection", "performance_monitor"]

    results = {"properly_archived": [], "still_importable": [], "errors": []}

    for component in archived_components:
        try:
            # Try to import from core - should fail
            exec(f"from app.core.{component} import *")
            results["still_importable"].append(component)
            print(f"  ⚠️  {component} still importable from core (should be archived)")
        except ImportError:
            results["properly_archived"].append(component)
            print(f"  ✅ {component} properly archived")
        except Exception as e:
            results["errors"].append(f"{component}: {str(e)}")
            print(f"  ❌ {component} error: {e}")

    return results

def generate_summary(import_results, functionality_results, archive_results):
    """Generate validation summary"""
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    # Import summary
    total_import_tests = 4
    passed_imports = sum(
        [
            import_results["core_imports"],
            import_results["security_engine"],
            import_results["performance_optimizer"],
            import_results["legacy_components"],
        ]
    )

    print(f"Import Tests: {passed_imports}/{total_import_tests} passed")

    # Functionality summary
    total_func_tests = 4
    passed_func = sum(
        [
            functionality_results["clamav_wrapper"],
            functionality_results["file_scanner"],
            functionality_results["security_engine_init"],
            functionality_results["performance_optimizer_init"],
        ]
    )

    print(f"Functionality Tests: {passed_func}/{total_func_tests} passed")

    # Archive summary
    properly_archived = len(archive_results["properly_archived"])
    still_importable = len(archive_results["still_importable"])
    total_archived = properly_archived + still_importable

    print(f"Archive Tests: {properly_archived}/{total_archived} components properly archived")

    # Overall status
    total_tests = total_import_tests + total_func_tests + total_archived
    total_passed = passed_imports + passed_func + properly_archived

    print(f"\nOVERALL: {total_passed}/{total_tests} tests passed")

    # Recommendations
    print("\nRECOMMENDATIONS:")
    all_errors = (
        import_results["errors"] + functionality_results["errors"] + archive_results["errors"]
    )

    if all_errors:
        print("Issues to address:")
        for i, error in enumerate(all_errors[:5], 1):  # Show max 5 errors
            print(f"  {i}. {error}")
        if len(all_errors) > 5:
            print(f"  ... and {len(all_errors) - 5} more issues")

    if still_importable:
        print("Components still importable (should be archived):")
        for component in still_importable:
            print(f"  - {component}")

    if total_passed == total_tests:
        print("\n🎉 All validation tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests failed or had issues")
        return 1

def main():
    """Main validation function"""
    print("🚀 xanadOS Search & Destroy - Component Validation")
    print("=" * 60)

    # Run all validation tests
    import_results = test_imports()
    functionality_results = test_basic_functionality()
    archive_results = test_archived_components()

    # Generate summary and return exit code
    exit_code = generate_summary(import_results, functionality_results, archive_results)

    print(f"\nValidation completed with exit code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
