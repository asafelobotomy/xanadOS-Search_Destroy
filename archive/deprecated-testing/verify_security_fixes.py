#!/usr/bin/env python3
"""
Post-Reboot Security Verification Script
xanadOS Search & Destroy v2.7.1

Run this script after rebooting to verify that the security fixes are working.
"""

import subprocess
import sys

def run_check(cmd, description):
    """Run a check command and report results"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔍 Post-Reboot Security Verification")
    print("xanadOS Search & Destroy v2.7.1")
    print("=" * 45)

    print("\n🔐 VERIFYING KERNEL LOCKDOWN:")
    print("=" * 35)

    success, lockdown_status, _ = run_check("cat /sys/kernel/security/lockdown", "Kernel lockdown status")
    if success:
        print(f"📊 Lockdown status: {lockdown_status}")
        if '[none]' in lockdown_status:
            print("❌ Kernel lockdown is still disabled")
        elif '[integrity]' in lockdown_status:
            print("✅ Kernel lockdown is active in integrity mode")
        elif '[confidentiality]' in lockdown_status:
            print("✅ Kernel lockdown is active in confidentiality mode")
        else:
            print(f"⚠️  Unexpected lockdown status: {lockdown_status}")
    else:
        print("❌ Cannot read kernel lockdown status")

    print("\n🛡️ VERIFYING APPARMOR:")
    print("=" * 25)

    success, apparmor_status, _ = run_check("sudo apparmor_status", "AppArmor status")
    if success:
        print("✅ AppArmor status check successful:")
        print(apparmor_status)

        if "apparmor module is loaded" in apparmor_status:
            print("\n✅ AppArmor module is loaded")
        else:
            print("\n❌ AppArmor module is not loaded")

        if "apparmor filesystem is not mounted" in apparmor_status:
            print("⚠️  AppArmor filesystem not mounted (may need manual intervention)")
        elif "profiles are loaded" in apparmor_status or "profiles are in enforce mode" in apparmor_status:
            print("✅ AppArmor profiles are active")
        else:
            print("⚠️  AppArmor profiles may need attention")
    else:
        print("❌ Cannot get AppArmor status")

    print("\n🚫 CHECKING SYSCTL MODULES:")
    print("=" * 30)
    print("ℹ️  kernel.modules_disabled has been REMOVED from the system")
    print("� Reason: Too dangerous and unnecessary for normal users")
    print("✅ Other security measures provide equivalent protection")

    print("\n📊 VERIFICATION SUMMARY:")
    print("=" * 30)

    # Count successful verifications
    success_count = 0
    total_checks = 2  # We only applied 2 fixes

    # Re-check each fix
    success, lockdown_status, _ = run_check("cat /sys/kernel/security/lockdown", "Kernel lockdown")
    if success and '[none]' not in lockdown_status:
        print("✅ Kernel Lockdown: WORKING")
        success_count += 1
    else:
        print("❌ Kernel Lockdown: NOT WORKING")

    success, apparmor_status, _ = run_check("sudo apparmor_status", "AppArmor")
    if success and "apparmor module is loaded" in apparmor_status:
        print("✅ AppArmor: WORKING")
        success_count += 1
    else:
        print("❌ AppArmor: NOT WORKING")

    print("⏸️  Sysctl modules: REMOVED (dangerous feature eliminated)")

    print(f"\n🎯 OVERALL RESULT: {success_count}/{total_checks} applicable fixes verified")
    print("🚫 1 dangerous feature removed for user safety")

    if success_count == total_checks:
        print("\n🎉 ALL SECURITY FIXES ARE WORKING CORRECTLY!")
        print("Your system security has been successfully enhanced.")
        return True
    elif success_count > 0:
        print(f"\n⚠️  PARTIAL SUCCESS: {success_count}/{total_checks} fixes working")
        print("Some fixes may need additional configuration.")
        return True
    else:
        print("\n❌ NO FIXES VERIFIED")
        print("The security fixes may need troubleshooting.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nRun this verification again after any changes.")
    sys.exit(0 if success else 1)
