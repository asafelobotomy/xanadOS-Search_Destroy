#!/usr/bin/env python3
"""Test script to verify the gui parameter fix."""

from unittest.mock import MagicMock, patch


# Test if the gui parameter is properly filtered
def test_elevated_popen_gui_param():
    """Test that gui parameter doesn't cause issues."""
    # Mock the elevated_popen_gui function
    with patch("app.core.gui_auth_manager.elevated_popen_gui") as mock_popen_gui:
        mock_process = MagicMock()
        mock_popen_gui.return_value = mock_process

        try:
            from app.core.elevated_runner import elevated_popen

            # This should not raise an exception about 'gui' parameter
            elevated_popen(["echo", "test"], gui=True)

            # Verify the mock was called without the gui parameter
            args, kwargs = mock_popen_gui.call_args
            print(f"elevated_popen_gui called with kwargs: {list(kwargs.keys())}")

            if "gui" in kwargs:
                print("ERROR: gui parameter was passed through incorrectly")
                return False
            else:
                print("SUCCESS: gui parameter was filtered out correctly")
                return True

        except Exception as e:
            print(f"ERROR: Exception occurred: {e}")
            return False


if __name__ == "__main__":
    success = test_elevated_popen_gui_param()
    if success:
        print("✅ GUI parameter fix is working correctly")
    else:
        print("❌ GUI parameter fix needs more work")
