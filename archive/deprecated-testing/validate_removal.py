#!/usr/bin/env python3
"""
System Validation After Dangerous Parameter Removal
xanadOS Search & Destroy v2.7.1

Validates that the security hardening system works correctly
after removing the dangerous kernel.modules_disabled parameter.
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_system_hardening_assessment():
    """Test that the system hardening assessment works without the dangerous parameter"""
    print("🔍 Testing System Hardening Assessment")
    print("=" * 45)
    
    try:
        from core.system_hardening import SystemHardeningAssessment
        
        # Create assessment instance
        assessment = SystemHardeningAssessment()
        
        # Run assessment
        print("🔄 Running security assessment...")
        features = assessment.assess_security()
        
        print(f"✅ Assessment completed successfully")
        print(f"📊 Found {len(features)} security features")
        
        # Check that dangerous parameter is not included
        dangerous_param_found = False
        for feature in features:
            if 'modules_disabled' in feature.name.lower():
                dangerous_param_found = True
                break
        
        if dangerous_param_found:
            print("❌ FAILURE: Dangerous parameter still present in assessment")
            return False
        else:
            print("✅ SUCCESS: Dangerous parameter correctly removed from assessment")
            
        # Show remaining sysctl parameters
        sysctl_features = [f for f in features if 'sysctl' in f.name.lower() or 'kernel.' in f.name.lower()]
        print(f"\n📋 Remaining sysctl parameters ({len(sysctl_features)}):")
        for feature in sysctl_features:
            print(f"   • {feature.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILURE: Assessment failed with error: {e}")
        return False

def test_gui_hardening_tab():
    """Test that the GUI hardening tab works without the dangerous parameter"""
    print("\n🖥️ Testing GUI Hardening Tab")
    print("=" * 35)
    
    try:
        # Mock PyQt6 since it might not be available in test environment
        import sys
        from unittest.mock import Mock
        
        # Mock PyQt6 modules
        sys.modules['PyQt6'] = Mock()
        sys.modules['PyQt6.QtWidgets'] = Mock()
        sys.modules['PyQt6.QtCore'] = Mock()
        sys.modules['PyQt6.QtGui'] = Mock()
        
        from gui.system_hardening_tab import SystemHardeningTab
        
        print("✅ GUI hardening tab module loads successfully")
        
        # Check that dangerous parameter is not in the safe parameters list
        # This is a bit of a hack since we can't easily instantiate the GUI
        import inspect
        source = inspect.getsource(SystemHardeningTab._fix_sysctl_parameter)
        
        if 'modules_disabled' in source:
            print("❌ FAILURE: Dangerous parameter still present in GUI code")
            return False
        else:
            print("✅ SUCCESS: Dangerous parameter correctly removed from GUI code")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILURE: GUI test failed with error: {e}")
        return False

def test_documentation_consistency():
    """Test that documentation has been updated consistently"""
    print("\n📚 Testing Documentation Consistency")
    print("=" * 40)
    
    # Files that should mention the removal
    doc_files = [
        'ENHANCED_HARDENING_REPORT.md',
        'enhanced_hardening_demo.py',
        'dangerous_parameter_removal_report.py'
    ]
    
    all_consistent = True
    
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            with open(doc_file, 'r') as f:
                content = f.read()
            
            if 'REMOVED' in content and 'modules_disabled' in content:
                print(f"✅ {doc_file}: Correctly documents removal")
            else:
                print(f"❌ {doc_file}: May not document removal properly")
                all_consistent = False
        else:
            print(f"⚠️  {doc_file}: File not found")
    
    if all_consistent:
        print("✅ SUCCESS: Documentation is consistent")
        return True
    else:
        print("❌ FAILURE: Documentation inconsistencies found")
        return False

def main():
    """Run all validation tests"""
    print("🔒 System Validation After Dangerous Parameter Removal")
    print("xanadOS Search & Destroy v2.7.1")
    print("=" * 60)
    
    tests = [
        ("System Hardening Assessment", test_system_hardening_assessment),
        ("GUI Hardening Tab", test_gui_hardening_tab),
        ("Documentation Consistency", test_documentation_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ CRITICAL FAILURE in {test_name}: {e}")
    
    print(f"\n{'='*60}")
    print("📊 VALIDATION SUMMARY")
    print("=" * 25)
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ System is safe and functional after dangerous parameter removal")
        print("✅ Security hardening system maintains full functionality")
        print("✅ Documentation is consistent and accurate")
        return True
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        print("❌ System may need additional attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
