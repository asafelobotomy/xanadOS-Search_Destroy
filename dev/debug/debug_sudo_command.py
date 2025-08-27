#!/usr/bin/env python3
"""
Debug the exact sudo command that's failing
"""
import os

import subprocess


def debug_wrapper_sudo_command():
    """Test the exact command the wrapper is trying to run"""
    print("Testing the exact wrapper sudo command...")

    # Set up environment like the wrapper does
    env = os.environ.copy()
    env["SUDO_ASKPASS"] = "/usr/bin/ksshaskpass"

    # This is the exact command from the wrapper logs with secure tmpdir
    cmd = [
        "sudo",
        "-A",
        "/usr/bin/rkhunter",
        "--check",
        "--sk",
        "--nocolors",
        "--no-mail-on-warning",
        "--configfile",
        "/etc/rkhunter.con",
        "--tmpdir",
        "/var/lib/rkhunter/tmp",
    ]

    print(f"Running: {' '.join(cmd)}")
    print(f"SUDO_ASKPASS: {env.get('SUDO_ASKPASS')}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            env=env,
        )

        print(f"Return code: {result.returncode}")
        print(f"stdout length: {len(result.stdout)}")
        print(f"stderr length: {len(result.stderr)}")

        # Show first few lines of output
        if result.stdout:
            lines = result.stdout.split("\n")[:10]
            print("First 10 lines of stdout:")
            for line in lines:
                print(f"  {line}")

        if result.stderr:
            lines = result.stderr.split("\n")[:10]
            print("First 10 lines of stderr:")
            for line in lines:
                print(f"  {line}")

        return result.returncode == 0

    except Exception as e:
        print(f"Exception: {e}")
        return False


if __name__ == "__main__":
    success = debug_wrapper_sudo_command()
    print(f"\nCommand succeeded: {success}")
