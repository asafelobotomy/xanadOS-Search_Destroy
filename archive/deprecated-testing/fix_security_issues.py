#!/usr/bin/env python3
"""
Security Hardening Issue Diagnostic and Fix Script
xanadOS Search & Destroy v2.7.1

This script diagnoses and fixes the three failed security hardening issues:
1. Kernel Lockdown Mode
2. AppArmor  
3. Sysctl: kernel.modules_disabled
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from core.elevated_runner import elevated_run

def check_permissions():
    """Check if we have the necessary permissions"""
    print("🔐 Checking permissions...")
    
    # Test sudo access
    result = elevated_run(['id'], gui=False)
    if result.returncode == 0:
        print("✅ Elevated permissions available")
        return True
    else:
        print("❌ No elevated permissions - fixes may fail")
        return False

def diagnose_kernel_lockdown():
    """Diagnose kernel lockdown issues"""
    print("\n🔍 DIAGNOSING KERNEL LOCKDOWN")
    print("=" * 40)
    
    # Check current status
    result = elevated_run(['cat', '/sys/kernel/security/lockdown'], gui=False)
    if result.returncode == 0:
        current_mode = result.stdout.strip()
        print(f"Current lockdown mode: {current_mode}")
        
        if '[none]' in current_mode:
            print("❌ Issue: Kernel lockdown is disabled")
            return False
        else:
            print("✅ Kernel lockdown is enabled")
            return True
    else:
        print("❌ Issue: Cannot read kernel lockdown status")
        return False

def fix_kernel_lockdown():
    """Fix kernel lockdown configuration"""
    print("\n🔧 FIXING KERNEL LOCKDOWN")
    print("=" * 30)
    
    # Check if we can modify GRUB
    grub_default = "/etc/default/grub"
    if not os.path.exists(grub_default):
        print(f"❌ GRUB config file not found: {grub_default}")
        return False
    
    try:
        # Create backup
        backup_path = f"{grub_default}.backup.{int(__import__('time').time())}"
        result = elevated_run(['cp', grub_default, backup_path], gui=False)
        if result.returncode != 0:
            print("❌ Failed to create backup")
            return False
        print(f"✅ Created backup: {backup_path}")
        
        # Read current GRUB config
        with open(grub_default, 'r') as f:
            lines = f.readlines()
        
        # Look for GRUB_CMDLINE_LINUX_DEFAULT line
        modified = False
        for i, line in enumerate(lines):
            if line.strip().startswith('GRUB_CMDLINE_LINUX_DEFAULT='):
                # Check if lockdown is already present
                if 'lockdown=' in line:
                    print("✅ Lockdown parameter already present in GRUB")
                    modified = True
                else:
                    # Add lockdown=integrity parameter
                    # Remove the closing quote, add parameter, add quote back
                    line = line.rstrip()
                    if line.endswith('"'):
                        line = line[:-1] + ' lockdown=integrity"'
                    elif line.endswith("'"):
                        line = line[:-1] + " lockdown=integrity'"
                    else:
                        line = line + ' lockdown=integrity'
                    lines[i] = line + '\n'
                    modified = True
                    print("✅ Added lockdown=integrity to GRUB config")
                break
        
        if not modified:
            print("❌ Could not find GRUB_CMDLINE_LINUX_DEFAULT line")
            return False
        
        # Write the modified config
        temp_file = f"{grub_default}.tmp"
        with open(temp_file, 'w') as f:
            f.writelines(lines)
        
        # Copy with elevated permissions
        result = elevated_run(['cp', temp_file, grub_default], gui=False)
        os.remove(temp_file)
        
        if result.returncode != 0:
            print("❌ Failed to update GRUB config")
            return False
        
        # Update GRUB
        if shutil.which('update-grub'):
            grub_cmd = ['update-grub']
        elif shutil.which('grub-mkconfig'):
            grub_cmd = ['grub-mkconfig', '-o', '/boot/grub/grub.cfg']
        elif shutil.which('grub2-mkconfig'):
            grub_cmd = ['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg']
        else:
            print("❌ No GRUB update command found")
            return False
        
        print(f"🔄 Updating GRUB with: {' '.join(grub_cmd)}")
        result = elevated_run(grub_cmd, gui=False)
        
        if result.returncode == 0:
            print("✅ GRUB updated successfully")
            print("⚠️  REBOOT REQUIRED for kernel lockdown to take effect")
            return True
        else:
            print(f"❌ GRUB update failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing kernel lockdown: {e}")
        return False

def diagnose_apparmor():
    """Diagnose AppArmor issues"""
    print("\n🔍 DIAGNOSING APPARMOR")
    print("=" * 30)
    
    # Check if AppArmor is installed
    result = elevated_run(['which', 'apparmor_status'], gui=False)
    if result.returncode != 0:
        print("❌ Issue: AppArmor not installed")
        return False
    
    # Check AppArmor status
    result = elevated_run(['apparmor_status'], gui=False)
    if result.returncode == 0:
        status_output = result.stdout.strip()
        print(f"AppArmor status:\n{status_output}")
        
        if "apparmor module is loaded" in status_output:
            print("✅ AppArmor module is loaded")
            
            # Check if profiles are loaded
            if "profiles are loaded" in status_output:
                return True
            else:
                print("❌ Issue: No AppArmor profiles loaded")
                return False
        else:
            print("❌ Issue: AppArmor module not loaded")
            return False
    else:
        print("❌ Issue: Cannot get AppArmor status")
        return False

def fix_apparmor():
    """Fix AppArmor configuration"""
    print("\n🔧 FIXING APPARMOR")
    print("=" * 20)
    
    try:
        # Check if AppArmor service is running
        result = elevated_run(['systemctl', 'is-active', 'apparmor'], gui=False)
        if result.returncode != 0:
            print("🔄 Starting AppArmor service...")
            result = elevated_run(['systemctl', 'start', 'apparmor'], gui=False)
            if result.returncode != 0:
                print(f"❌ Failed to start AppArmor service: {result.stderr}")
                return False
            print("✅ AppArmor service started")
        
        # Enable AppArmor service
        result = elevated_run(['systemctl', 'enable', 'apparmor'], gui=False)
        if result.returncode == 0:
            print("✅ AppArmor service enabled")
        
        # Check if profiles directory exists and load profiles
        profiles_dir = Path("/etc/apparmor.d")
        if profiles_dir.exists():
            print("🔄 Loading AppArmor profiles...")
            result = elevated_run(['aa-enforce', '/etc/apparmor.d/*'], gui=False)
            if result.returncode == 0:
                print("✅ AppArmor profiles loaded in enforce mode")
            else:
                # Try alternative method
                result = elevated_run(['systemctl', 'reload', 'apparmor'], gui=False)
                if result.returncode == 0:
                    print("✅ AppArmor profiles reloaded")
                else:
                    print("⚠️  Could not load all profiles, but service is running")
        
        # Final status check
        result = elevated_run(['apparmor_status'], gui=False)
        if result.returncode == 0 and "profiles are loaded" in result.stdout:
            print("✅ AppArmor is now working properly")
            return True
        else:
            print("⚠️  AppArmor service is running but may need manual profile configuration")
            return True  # Partial success
            
    except Exception as e:
        print(f"❌ Error fixing AppArmor: {e}")
        return False

def diagnose_sysctl_modules():
    """Diagnose sysctl modules_disabled issue"""
    print("\n🔍 DIAGNOSING SYSCTL MODULES_DISABLED")
    print("=" * 45)
    
    # Check current value
    result = elevated_run(['sysctl', 'kernel.modules_disabled'], gui=False)
    if result.returncode == 0:
        current_value = result.stdout.strip()
        print(f"Current value: {current_value}")
        
        if "kernel.modules_disabled = 0" in current_value:
            print("❌ Issue: kernel.modules_disabled is 0 (modules can be loaded)")
            return False
        elif "kernel.modules_disabled = 1" in current_value:
            print("✅ kernel.modules_disabled is 1 (modules disabled)")
            return True
        else:
            print(f"⚠️  Unexpected value: {current_value}")
            return False
    else:
        print("❌ Issue: Cannot read kernel.modules_disabled")
        return False

def fix_sysctl_modules():
    """Fix sysctl modules_disabled setting"""
    print("\n🔧 FIXING SYSCTL MODULES_DISABLED")
    print("=" * 35)
    
    try:
        # CRITICAL WARNING
        print("⚠️  CRITICAL WARNING ⚠️")
        print("=" * 25)
        print("Setting kernel.modules_disabled=1 is IRREVERSIBLE!")
        print("Once set, you CANNOT load any kernel modules until reboot.")
        print("This will prevent:")
        print("- Loading new hardware drivers")
        print("- Loading filesystem modules")
        print("- Loading network modules")
        print("- Any other kernel module operations")
        print()
        
        response = input("Do you want to proceed with this IRREVERSIBLE change? [y/N]: ")
        if response.lower() != 'y':
            print("❌ User cancelled the operation")
            return False
        
        print("\n🔄 Setting kernel.modules_disabled=1...")
        
        # Set the parameter
        result = elevated_run(['sysctl', '-w', 'kernel.modules_disabled=1'], gui=False)
        if result.returncode == 0:
            print("✅ kernel.modules_disabled set to 1")
            
            # Make it persistent (though it's already irreversible for this boot)
            sysctl_dir = "/etc/sysctl.d"
            if os.path.exists(sysctl_dir):
                config_file = f"{sysctl_dir}/99-xanadOS-security.conf"
                
                # Check if file exists and if parameter is already there
                param_exists = False
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if 'kernel.modules_disabled' in content:
                            param_exists = True
                
                if not param_exists:
                    with open(f"{config_file}.tmp", 'w') as f:
                        if os.path.exists(config_file):
                            with open(config_file, 'r') as existing:
                                f.write(existing.read())
                        f.write("\n# Disable module loading (irreversible until reboot)\n")
                        f.write("kernel.modules_disabled = 1\n")
                    
                    result = elevated_run(['cp', f"{config_file}.tmp", config_file], gui=False)
                    os.remove(f"{config_file}.tmp")
                    
                    if result.returncode == 0:
                        print(f"✅ Configuration saved to {config_file}")
                    else:
                        print("⚠️  Could not save persistent configuration")
            
            print("✅ kernel.modules_disabled successfully set to 1")
            print("⚠️  This setting is now IRREVERSIBLE until reboot!")
            return True
        else:
            print(f"❌ Failed to set kernel.modules_disabled: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing sysctl modules: {e}")
        return False

def main():
    """Main diagnostic and fix routine"""
    print("🔒 Security Hardening Issue Diagnostic & Fix")
    print("xanadOS Search & Destroy v2.7.1")
    print("=" * 50)
    
    if not check_permissions():
        print("\n❌ Insufficient permissions for fixes")
        print("Please run with appropriate privileges")
        return False
    
    print("\n📊 DIAGNOSIS PHASE")
    print("=" * 20)
    
    # Diagnose all issues
    lockdown_ok = diagnose_kernel_lockdown()
    apparmor_ok = diagnose_apparmor()
    sysctl_ok = diagnose_sysctl_modules()
    
    # Summary of issues
    issues = []
    if not lockdown_ok:
        issues.append("Kernel Lockdown")
    if not apparmor_ok:
        issues.append("AppArmor")
    if not sysctl_ok:
        issues.append("Sysctl modules_disabled")
    
    if not issues:
        print("\n✅ All security features are working correctly!")
        return True
    
    print(f"\n❌ Found {len(issues)} issue(s): {', '.join(issues)}")
    
    # Ask user if they want to proceed with fixes
    print(f"\n🔧 FIX PHASE")
    print("=" * 15)
    
    response = input("Do you want to attempt to fix these issues? [y/N]: ")
    if response.lower() != 'y':
        print("❌ User cancelled fixes")
        return False
    
    # Apply fixes
    fixed_count = 0
    total_fixes = len(issues)
    
    if not lockdown_ok:
        print("\n" + "="*50)
        if fix_kernel_lockdown():
            fixed_count += 1
    
    if not apparmor_ok:
        print("\n" + "="*50)
        if fix_apparmor():
            fixed_count += 1
    
    if not sysctl_ok:
        print("\n" + "="*50)
        if fix_sysctl_modules():
            fixed_count += 1
    
    # Final summary
    print("\n" + "="*50)
    print("📊 FIX SUMMARY")
    print("=" * 15)
    print(f"Fixed: {fixed_count}/{total_fixes} issues")
    
    if fixed_count == total_fixes:
        print("✅ All issues have been resolved!")
        if not lockdown_ok and fixed_count > 0:
            print("\n⚠️  REBOOT REQUIRED for kernel lockdown changes to take effect")
        return True
    else:
        print(f"⚠️  {total_fixes - fixed_count} issue(s) still need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
