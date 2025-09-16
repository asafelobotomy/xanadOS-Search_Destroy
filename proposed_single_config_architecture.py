#!/usr/bin/env python3
"""
Proposed Architecture: Single RKHunter Config with Smart Permission Handling

This demonstrates how we could eliminate the dual-config complexity
by focusing on the system config with intelligent permission management.
"""

from pathlib import Path
import os
import subprocess
import logging

class SmartRKHunterManager:
    """
    Proposed architecture that uses only the system RKHunter config
    with intelligent permission handling and sudo escalation when needed.
    """

    def __init__(self):
        self.system_config_path = "/etc/rkhunter.conf"
        self.logger = logging.getLogger(__name__)

    def can_read_system_config(self) -> bool:
        """Check if we can read the system config without sudo"""
        return (
            Path(self.system_config_path).exists() and
            os.access(self.system_config_path, os.R_OK)
        )

    def can_write_system_config(self) -> bool:
        """Check if we can write to system config without sudo"""
        return (
            Path(self.system_config_path).exists() and
            os.access(self.system_config_path, os.W_OK)
        )

    def fix_arch_permissions_if_needed(self) -> bool:
        """
        Detect and fix Arch Linux permission anomaly
        Returns True if permissions were fixed or were already correct
        """
        if not Path(self.system_config_path).exists():
            return False

        # Check current permissions
        stat_info = os.stat(self.system_config_path)
        current_perms = oct(stat_info.st_mode)[-3:]

        if current_perms == "600":  # Arch Linux anomaly
            self.logger.info("Detected Arch Linux permission anomaly, fixing...")
            try:
                # Fix the permission anomaly - this is a one-time system fix
                subprocess.run([
                    "sudo", "chmod", "644", self.system_config_path
                ], check=True, capture_output=True)
                self.logger.info("✅ Fixed RKHunter config permissions")
                return True
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to fix permissions: {e}")
                return False

        return True  # Permissions are already correct

    def detect_fixable_issues(self) -> dict:
        """
        Detect issues in the SYSTEM config, requesting sudo if needed
        This eliminates the user/system config confusion
        """
        issues = {}

        # First, try to fix permission issues
        if not self.can_read_system_config():
            if not self.fix_arch_permissions_if_needed():
                # If we still can't read after fixing permissions,
                # we need elevated access for this operation
                self.logger.warning("System config requires elevated access to read")
                return {"requires_sudo": {
                    "description": "🔒 System configuration requires administrator access",
                    "detail": "RKHunter configuration optimization needs elevated privileges",
                    "fix_action": "The app will request sudo access when needed",
                    "impact": "Ensures system-wide RKHunter optimization"
                }}

        # Now we can read the system config directly
        try:
            with open(self.system_config_path, 'r') as f:
                content = f.read()

            # Check for actual fixable issues in the REAL config file
            line_num = 0
            for line in content.splitlines():
                line_num += 1

                # Check for obsolete WEB_CMD_TIMEOUT option
                if line.strip().startswith('WEB_CMD_TIMEOUT'):
                    issues[f"obsolete_web_cmd_timeout_{line_num}"] = {
                        "description": "🔧 Obsolete 'WEB_CMD_TIMEOUT' setting found",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Remove this obsolete configuration option",
                        "impact": "Eliminates configuration warnings",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_system_config()
                    }

                # Check for egrep commands (should use grep -E)
                if 'egrep' in line and not line.strip().startswith('#'):
                    issues[f"egrep_deprecated_{line_num}"] = {
                        "description": "📅 Deprecated 'egrep' command found",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Replace 'egrep' with 'grep -E'",
                        "impact": "Uses modern grep syntax",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_system_config()
                    }

                # Check for regex escaping issues
                if '\\+' in line and not line.strip().startswith('#'):
                    issues[f"regex_plus_escape_{line_num}"] = {
                        "description": "🔍 Invalid regex escaping for '+' character",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Remove unnecessary backslash before '+'",
                        "impact": "Fixes regex pattern matching",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_system_config()
                    }

        except Exception as e:
            self.logger.error(f"Error reading system config: {e}")
            return {"error": {
                "description": "❌ Unable to read system configuration",
                "detail": str(e),
                "fix_action": "Check file permissions and path",
                "impact": "Cannot optimize RKHunter configuration"
            }}

        return issues

    def apply_fixes_with_sudo(self, selected_fixes: list) -> list:
        """
        Apply fixes to the SYSTEM config, using sudo when needed
        This ensures all fixes go to the real config file that RKHunter uses
        """
        applied_fixes = []

        try:
            # Read current content
            with open(self.system_config_path, 'r') as f:
                lines = f.readlines()

            # Apply fixes (this would need sudo for write access)
            for fix_id in selected_fixes:
                if "obsolete_web_cmd_timeout" in fix_id:
                    # Remove WEB_CMD_TIMEOUT lines
                    lines = [line for line in lines if not line.strip().startswith('WEB_CMD_TIMEOUT')]
                    applied_fixes.append("✅ Removed obsolete WEB_CMD_TIMEOUT setting")

                elif "egrep_deprecated" in fix_id:
                    # Replace egrep with grep -E
                    for i, line in enumerate(lines):
                        if 'egrep' in line and not line.strip().startswith('#'):
                            lines[i] = line.replace('egrep', 'grep -E')
                    applied_fixes.append("✅ Updated deprecated egrep commands to grep -E")

                elif "regex_plus_escape" in fix_id:
                    # Fix regex escaping
                    for i, line in enumerate(lines):
                        if '\\+' in line and not line.strip().startswith('#'):
                            lines[i] = line.replace('\\+', '+')
                    applied_fixes.append("✅ Fixed regex escaping issues")

            # Write back to system config (requires sudo if not writable)
            if self.can_write_system_config():
                with open(self.system_config_path, 'w') as f:
                    f.writelines(lines)
            else:
                # Use sudo to write to system config
                temp_content = ''.join(lines)
                result = subprocess.run([
                    "sudo", "tee", self.system_config_path
                ], input=temp_content, text=True, capture_output=True)

                if result.returncode != 0:
                    raise Exception(f"Sudo write failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"Error applying fixes: {e}")
            applied_fixes.append(f"❌ Error applying fixes: {e}")

        return applied_fixes

def main():
    """Demonstrate the proposed single-config architecture"""
    print("=== Proposed Single-Config RKHunter Architecture ===")

    manager = SmartRKHunterManager()

    print(f"System config: {manager.system_config_path}")
    print(f"Can read: {manager.can_read_system_config()}")
    print(f"Can write: {manager.can_write_system_config()}")

    # Detect issues in the REAL system config
    issues = manager.detect_fixable_issues()
    print(f"\nFound {len(issues)} issues in system config:")
    for issue_id, issue in issues.items():
        sudo_req = " (requires sudo)" if issue.get("requires_sudo", False) else ""
        print(f"  • {issue['description']}{sudo_req}")

    print("\n✅ Benefits of this approach:")
    print("  • Single source of truth (system config)")
    print("  • No configuration divergence")
    print("  • Clear sudo requirements")
    print("  • Fixes go to the config RKHunter actually uses")
    print("  • Handles Arch Linux permissions properly")

if __name__ == "__main__":
    main()
