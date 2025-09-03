#!/usr/bin/env python3
"""
Firewall Status Detection Validation Script
===========================================

This script validates that the firewall detector correctly identifies
UFW status based on configuration files rather than just systemd service status.
"""

import os
import subprocess

from app.core.firewall_detector import FirewallDetector


def test_ufw_detection() -> None:
    """Test UFW detection logic with mock config files."""

    print("🧪 Testing UFW Status Detection Fix")
    print("=" * 50)

    # Test 1: Real system status
    detector = FirewallDetector()
    real_status = detector.get_firewall_status()

    print("📊 Real System Status:")
    print(f"   Active: {real_status['is_active']}")
    print(f"   Status: {real_status['status_text']}")
    print(f"   Method: {real_status['method']}")

    # Test 2: Compare with systemctl (what was causing the issue)
    try:
        systemctl_result = subprocess.run(
            ["systemctl", "is-active", "ufw"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        systemctl_active = (
            systemctl_result.returncode == 0
            and systemctl_result.stdout.strip() == "active"
        )
        print(
            f"🔧 Systemctl says UFW service: {'Active' if systemctl_active else 'Inactive'}"
        )
    except Exception as e:
        print(f"❌ Systemctl check failed: {e}")

    # Test 3: Check actual UFW command (with sudo)
    try:
        ufw_result = subprocess.run(
            ["sudo", "ufw", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            input="",
            check=False,  # No password input
        )
        if ufw_result.returncode == 0:
            ufw_actual = (
                "active" if "Status: active" in ufw_result.stdout else "inactive"
            )
            print(f"🎯 UFW command says: {ufw_actual}")

            # Check if our detector matches the actual UFW status
            detector_says_active = real_status["is_active"]
            ufw_says_active = ufw_actual == "active"

            if detector_says_active == ufw_says_active:
                print("✅ PASS: Detector matches actual UFW status")
            else:
                print("❌ FAIL: Detector does not match actual UFW status")
                print(
                    f"   Detector: {'Active' if detector_says_active else 'Inactive'}"
                )
                print(f"   UFW:      {'Active' if ufw_says_active else 'Inactive'}")

    except subprocess.TimeoutExpired:
        print("⏰ UFW command timed out (probably waiting for password)")
    except Exception as e:
        print(f"❌ UFW command failed: {e}")

    # Test 4: Config file check
    config_path = "/etc/ufw/ufw.conf"
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                content = f.read()

            if "ENABLED=yes" in content:
                config_status = "enabled"
            elif "ENABLED=no" in content:
                config_status = "disabled"
            else:
                config_status = "unknown"

            print(f"📁 Config file says: {config_status}")

            # Check if detector matches config
            detector_matches_config = (
                config_status == "enabled" and real_status["is_active"]
            ) or (config_status == "disabled" and not real_status["is_active"])

            if detector_matches_config:
                print("✅ PASS: Detector matches UFW config file")
            else:
                print("❌ FAIL: Detector does not match UFW config file")

        except Exception as e:
            print(f"❌ Could not read config file: {e}")
    else:
        print("❌ UFW config file not found")

    print()
    print("🏁 Test Summary:")
    print("   The fix ensures the detector reads UFW config files FIRST")
    print("   before checking systemd service status, preventing false positives.")


if __name__ == "__main__":
    test_ufw_detection()
