#!/usr/bin/env python3
"""
Debug pkexec in the exact GUI context
"""
import os

import subprocess
import sys


def test_pkexec_gui_context():
    """Test pkexec exactly as the GUI would call it"""

    print("=== Debug pkexec in GUI Context ===")
    print(f"DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
    print(f"XAUTHORITY: {os.environ.get('XAUTHORITY', 'NOT SET')}")
    print(f"HOME: {os.environ.get('HOME', 'NOT SET')}")
    print(f"Running from: {os.getcwd()}")
    print(f"Python path: {sys.executable}")
    print()

    # Set up environment exactly like our wrapper does
    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"
    if "XAUTHORITY" not in env and "HOME" in env:
        env["XAUTHORITY"] = f"{env['HOME']}/.Xauthority"

    print("Environment setup:")
    print(f"  DISPLAY: {env.get('DISPLAY')}")
    print(f"  XAUTHORITY: {env.get('XAUTHORITY')}")
    print()

    # Test the exact command our wrapper uses
    cmd = [
        "pkexec",
        "rkhunter",
        "--check",
        "--sk",
        "--nocolors",
        "--no-mail-on-warning",
    ]

    print(f"Running: {' '.join(cmd)}")
    print("Note: This should show an authentication dialog...")
    print()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout for testing
            env=env,
            check=False,
        )

        print(f"Return code: {result.returncode}")

        if result.returncode == 0:
            ok_count = result.stdout.count("[ OK ]")
            print(f"✅ SUCCESS! Found {ok_count} tests")
            print("First few lines of output:")
            for line in result.stdout.split("\n")[:10]:
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"❌ FAILED with return code {result.returncode}")
            print("stderr:", result.stderr[:300])
            print("stdout:", result.stdout[:300])

            # Common failure reasons
            if result.returncode == 126:
                print("  → This usually means permission denied")
            elif result.returncode == 127:
                print("  → This usually means command not found")
            elif result.returncode == 1:
                print("  → This could be authentication cancelled or polkit failure")

    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT - Authentication dialog may have appeared but not completed")
        print("   If you saw a dialog, the GUI authentication is working")
    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    test_pkexec_gui_context()
