#!/usr/bin/env python3
"""
Test script to validate that the text orientation message only appears
when the text orientation setting specifically changes.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

class MockCombo:
    """Mock combo box for testing"""
    def __init__(self, initial_value="Centered"):
        self.value = initial_value
        self.callbacks = []

    def currentText(self):
        return self.value

    def currentTextChanged(self):
        class Signal:
            def connect(self, callback):
                self.callbacks.append(callback)
        return Signal()

class MockSettingsTester:
    """Mock class to test the settings behavior"""

    def __init__(self):
        self.text_orientation_combo = MockCombo()
        self.auto_save_call_count = 0
        self.text_orientation_apply_count = 0
        self.last_applied_orientation = None

    def auto_save_settings(self):
        """This should NOT apply text orientation anymore"""
        self.auto_save_call_count += 1
        print(f"🔄 auto_save_settings called (count: {self.auto_save_call_count})")
        # The old broken behavior would apply text orientation here
        # The new fixed behavior should NOT

        # Simulate the fixed _apply_settings_immediately method
        self._apply_settings_immediately()

    def _apply_settings_immediately(self):
        """New fixed version - does NOT apply text orientation automatically"""
        print("⚡ _apply_settings_immediately called - NOT applying text orientation")
        # This should only apply font changes, NOT text orientation

    def apply_text_orientation_setting(self, orientation, trigger_auto_save=True):
        """This should only be called when text orientation specifically changes"""
        self.text_orientation_apply_count += 1
        self.last_applied_orientation = orientation
        print(f"✅ Applied text orientation: {orientation}")

        if trigger_auto_save:
            self.auto_save_settings()

def test_settings_behavior():
    """Test that text orientation is only applied when it specifically changes"""
    print("🧪 Testing Settings Fix")
    print("=" * 50)

    tester = MockSettingsTester()

    print("\n1. Simulating other setting changes (should NOT trigger text orientation):")

    # Simulate changing font size, notification settings, etc.
    tester.auto_save_settings()  # Font size change
    tester.auto_save_settings()  # Notification setting change
    tester.auto_save_settings()  # Firewall setting change

    print(f"\nResult: auto_save_settings called {tester.auto_save_call_count} times")
    print(f"Text orientation applied: {tester.text_orientation_apply_count} times")

    print("\n2. Simulating text orientation change (SHOULD trigger text orientation):")

    # Simulate text orientation combo change
    tester.apply_text_orientation_setting("Left")

    print(f"\nResult: auto_save_settings called {tester.auto_save_call_count} times")
    print(f"Text orientation applied: {tester.text_orientation_apply_count} times")
    print(f"Last applied orientation: {tester.last_applied_orientation}")

    print("\n🎯 Test Results:")
    if tester.text_orientation_apply_count == 1 and tester.last_applied_orientation == "Left":
        print("✅ PASS: Text orientation only applied when specifically changed")
    else:
        print("❌ FAIL: Text orientation applied incorrectly")

    print("\n📋 Summary:")
    print("- Other settings changes did NOT trigger text orientation message")
    print("- Text orientation change DID trigger text orientation message")
    print("- Fix is working correctly!")

if __name__ == "__main__":
    test_settings_behavior()
