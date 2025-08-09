#!/usr/bin/env python3
"""
Firewall Detection and Status Module
=====================================
Detects and monitors various Linux firewall systems and their status.
"""

import os
import shutil
import subprocess
from typing import Any, Dict, Optional, Tuple


class FirewallDetector:
    """Detects and monitors firewall status on Linux systems."""

    def __init__(self):
        self.supported_firewalls = {
            "ufw": {
                "name": "UFW (Uncomplicated Firewall)",
                "check_cmd": ["ufw", "status"],
                "service_name": "ufw",
            },
            "firewalld": {
                "name": "firewalld",
                "check_cmd": ["firewall-cmd", "--state"],
                "service_name": "firewalld",
            },
            "iptables": {
                "name": "iptables",
                "check_cmd": ["iptables", "-L", "-n"],
                "service_name": "iptables",
            },
            "nftables": {
                "name": "nftables",
                "check_cmd": ["nft", "list", "tables"],
                "service_name": "nftables",
            },
        }

    def detect_firewall(self) -> Tuple[Optional[str], str]:
        """
        Detect which firewall is installed and active.

        Returns:
            Tuple of (firewall_type, firewall_name) or (None, "No firewall detected")
        """
        # Check each supported firewall
        for fw_type, fw_info in self.supported_firewalls.items():
            if self._is_firewall_available(fw_type):
                return fw_type, fw_info["name"]

        return None, "No firewall detected"

    def _is_firewall_available(self, firewall_type: str) -> bool:
        """Check if a specific firewall is available on the system."""
        fw_info = self.supported_firewalls.get(firewall_type)
        if not fw_info:
            return False

        # Check if the command exists
        cmd = fw_info["check_cmd"][0]
        if not shutil.which(cmd):
            return False

        # For systemd systems, also check if service exists
        if self._has_systemd():
            try:
                result = subprocess.run(
                    [
                        "systemctl",
                        "list-unit-files",
                        f"{fw_info['service_name']}.service",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                return (result.returncode ==
                        0 and fw_info["service_name"] in result.stdout)
            except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
                pass

        return True

    def get_firewall_status(self) -> Dict[str, str | bool | None]:
        """
        Get comprehensive firewall status information.

        Returns:
            Dictionary with status information including:
            - is_active: bool
            - firewall_name: str
            - firewall_type: str
            - status_text: str
            - error: str (if any)
        """
        fw_type, fw_name = self.detect_firewall()

        status_info = {
            "is_active": False,
            "firewall_name": fw_name,
            "firewall_type": fw_type,
            "status_text": "Inactive",
            "error": None,
        }

        if not fw_type:
            status_info["status_text"] = "Not detected"
            return status_info

        try:
            # Get status based on firewall type
            if fw_type == "ufw":
                status_info.update(self._get_ufw_status())
            elif fw_type == "firewalld":
                status_info.update(self._get_firewalld_status())
            elif fw_type == "iptables":
                status_info.update(self._get_iptables_status())
            elif fw_type == "nftables":
                status_info.update(self._get_nftables_status())

        except (OSError, subprocess.SubprocessError) as e:
            status_info["error"] = str(e)
            status_info["status_text"] = "Error checking status"

        return status_info

    def _get_ufw_status(self) -> Dict[str, str | bool]:
        """Get UFW firewall status."""
        try:
            # First try without sudo (some systems allow status check without
            # root)
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            # If that fails, try with sudo
            if result.returncode != 0:
                result = subprocess.run(
                    ["sudo", "-n", "ufw", "status"],  # -n = non-interactive
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

            if result.returncode == 0:
                output = result.stdout.lower()
                is_active = "status: active" in output
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }
            else:
                # If sudo also fails, try to detect from service status
                return self._get_ufw_service_status()

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check UFW: {str(e)}"}

        return {"is_active": False, "status_text": "Inactive"}

    def _get_ufw_service_status(self) -> Dict[str, str | bool]:
        """Get UFW status via alternative methods as fallback."""
        try:
            # Method 1: Check UFW configuration file for enabled status
            ufw_config_paths = ["/etc/ufw/ufw.conf", "/etc/default/ufw"]

            for config_path in ufw_config_paths:
                try:
                    if os.path.exists(config_path):
                        with open(config_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Look for ENABLED=yes in the config
                        if "ENABLED=yes" in content:
                            return {"is_active": True, "status_text": "Active"}
                except (PermissionError, IOError):
                    continue

            # Method 2: Try to check if UFW status file exists and indicates
            # enabled
            ufw_status_paths = [
                "/var/lib/ufw/user.rules",
                "/var/lib/ufw/user6.rules"]

            for status_path in ufw_status_paths:
                try:
                    if os.path.exists(status_path) and os.path.getsize(
                            status_path) > 0:
                        return {"is_active": True, "status_text": "Active"}
                except (PermissionError, IOError):
                    continue

            # Method 3: Check systemctl status (original fallback)
            result = subprocess.run(
                ["systemctl", "is-active", "ufw"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            is_active = result.stdout.strip() == "active"

            return {
                "is_active": is_active,
                "status_text": "Active" if is_active else "Inactive",
            }
        except (subprocess.SubprocessError, OSError, IOError) as e:
            return {"is_active": False, "status_text": "Inactive"}

    def _get_firewalld_status(self) -> Dict[str, str | bool]:
        """Get firewalld status."""
        try:
            result = subprocess.run(
                ["firewall-cmd", "--state"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if result.returncode == 0:
                is_active = "running" in result.stdout.lower()
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check firewalld: {str(e)}"}

        return {"is_active": False, "status_text": "Inactive"}

    def _get_iptables_status(self) -> Dict[str, str | bool]:
        """Get iptables status."""
        try:
            result = subprocess.run(
                ["iptables", "-L", "-n"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if result.returncode == 0:
                # Check if there are any rules beyond the default chains
                lines = result.stdout.strip().split("\n")
                rule_count = len(
                    [
                        line
                        for line in lines
                        if line.strip()
                        and not line.startswith("Chain")
                        and not line.startswith("target")
                    ]
                )

                # Check for non-ACCEPT policies or actual rules
                has_policies = (
                    "policy DROP" in result.stdout or "policy REJECT" in result.stdout)
                is_active = rule_count > 0 or has_policies
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check iptables: {str(e)}"}

        return {"is_active": False, "status_text": "Inactive"}

    def _get_nftables_status(self) -> Dict[str, str | bool]:
        """Get nftables status."""
        try:
            result = subprocess.run(
                ["nft", "list", "tables"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if result.returncode == 0:
                # If there are any tables, nftables is considered active
                is_active = bool(result.stdout.strip())
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check nftables: {str(e)}"}

        return {"is_active": False, "status_text": "Inactive"}

    def _has_systemd(self) -> bool:
        """Check if the system uses systemd."""
        return os.path.exists("/run/systemd/system")

    def toggle_firewall(self, enable: bool) -> Dict[str, str | bool]:
        """
        Enable or disable the detected firewall.

        Args:
            enable: True to enable firewall, False to disable

        Returns:
            Dictionary with operation result:
            - success: bool
            - message: str
            - error: str (if any)
        """
        fw_type, fw_name = self.detect_firewall()

        if not fw_type:
            return {
                "success": False,
                "message": "No firewall detected",
                "error": "Cannot control firewall - no supported firewall found",
            }

        try:
            if fw_type == "ufw":
                return self._toggle_ufw(enable)
            elif fw_type == "firewalld":
                return self._toggle_firewalld(enable)
            elif fw_type == "iptables":
                return self._toggle_iptables(enable)
            elif fw_type == "nftables":
                return self._toggle_nftables(enable)
            else:
                return {
                    "success": False,
                    "message": f"Firewall control not implemented for {fw_name}",
                    "error": f"No control method available for {fw_type}",
                }

        except (OSError, subprocess.SubprocessError, PermissionError) as e:
            return {
                "success": False,
                "message": f'Failed to {
                    "enable" if enable else "disable"} firewall',
                "error": str(e),
            }

    def _get_admin_cmd_prefix(self) -> list:
        """Get the appropriate command prefix for admin privileges."""
        # Try pkexec first (better for GUI apps), then fall back to sudo
        if shutil.which("pkexec"):
            # Check if we're in a GUI environment
            display = os.environ.get("DISPLAY")
            if display:
                # We're in a GUI environment - pkexec should work
                return ["pkexec"]
            else:
                # No GUI environment, use sudo if available
                if shutil.which("sudo"):
                    return ["sudo"]
                else:
                    return ["pkexec"]  # Try anyway
        elif shutil.which("sudo"):
            return ["sudo"]
        else:
            return []

    def _toggle_ufw(self, enable: bool) -> Dict[str, str | bool]:
        """Toggle UFW firewall."""
        print(f"🔍 DEBUG: _toggle_ufw called with enable={enable}")
        try:
            admin_cmd = self._get_admin_cmd_prefix()
            print(f"🔍 DEBUG: Admin command: {admin_cmd}")
            if not admin_cmd:
                return {
                    "success": False,
                    "message": "Administrative privileges not available",
                    "error": "Neither pkexec nor sudo found on system",
                }

            # UFW requires admin privileges
            cmd = admin_cmd + ["ufw", "--force",
                               "enable" if enable else "disable"]
            
            # Debug: Print the command being executed
            print(f"DEBUG: Executing firewall command: {' '.join(cmd)}")
            
            # Prepare environment for GUI authentication
            env = os.environ.copy()  # Keep all current environment variables
            print(f"🔍 DEBUG: Original environment DISPLAY: {env.get('DISPLAY', 'Not set')}")
            print(f"🔍 DEBUG: Original environment XAUTHORITY: {env.get('XAUTHORITY', 'Not set')}")
            
            # Ensure GUI environment variables are set for pkexec authentication
            if admin_cmd[0] == "pkexec":
                print("🔍 DEBUG: Using pkexec, setting up GUI environment...")
                # Make sure DISPLAY and XAUTHORITY are available for pkexec GUI
                if "DISPLAY" not in env and "DISPLAY" in os.environ:
                    env["DISPLAY"] = os.environ["DISPLAY"]
                if "XAUTHORITY" not in env and "XAUTHORITY" in os.environ:
                    env["XAUTHORITY"] = os.environ["XAUTHORITY"]
                # Also ensure other common GUI environment variables
                for var in ["WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR"]:
                    if var not in env and var in os.environ:
                        env[var] = os.environ[var]
                        print(f"🔍 DEBUG: Set {var} = {env[var]}")
            
            print("🔍 DEBUG: About to run subprocess...")
            # Use the same approach as update_virus_definitions for better GUI compatibility
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # Longer timeout like update_definitions (was 60)
                check=False,
                env=env,  # Use the prepared environment
            )
            
            # Debug: Print result details
            print(f"DEBUG: Command exit code: {result.returncode}")
            print(f"DEBUG: Command stdout: {result.stdout}")
            print(f"DEBUG: Command stderr: {result.stderr}")
            print(f"🔍 DEBUG: Subprocess completed")

            if result.returncode == 0:
                action = "enabled" if enable else "disabled"
                return {
                    "success": True,
                    "message": f"UFW firewall {action} successfully",
                }
            else:
                error_output = result.stderr.strip() or result.stdout.strip()
                # Check for common authentication cancellation messages
                if (
                    "request dismissed" in error_output.lower()
                    or "cancelled" in error_output.lower()
                ):
                    return {
                        "success": False,
                        "message": "Authentication cancelled by user",
                        "error": "User cancelled the authentication dialog",
                    }
                return {
                    "success": False,
                    "message": f'Failed to {
                        "enable" if enable else "disable"} UFW',
                    "error": error_output or f"Command exited with code {
                        result.returncode}",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Authentication timed out",
                "error": "Authentication dialog timed out after 60 seconds",
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "success": False,
                "message": "UFW command failed",
                "error": f"UFW not found or not executable: {str(e)}",
            }

    def _toggle_firewalld(self, enable: bool) -> Dict[str, str | bool]:
        """Toggle firewalld."""
        try:
            admin_cmd = self._get_admin_cmd_prefix()
            if not admin_cmd:
                return {
                    "success": False,
                    "message": "Administrative privileges not available",
                    "error": "Neither pkexec nor sudo found on system",
                }

            # Prepare environment for GUI authentication
            env = os.environ.copy()
            if admin_cmd[0] == "pkexec":
                for var in ["DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR"]:
                    if var not in env and var in os.environ:
                        env[var] = os.environ[var]

            if enable:
                # Start firewalld service
                result = subprocess.run(
                    admin_cmd + ["systemctl", "start", "firewalld"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                    env=env,
                )
            else:
                # Stop firewalld service
                result = subprocess.run(
                    admin_cmd + ["systemctl", "stop", "firewalld"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                    env=env,
                )

            if result.returncode == 0:
                action = "started" if enable else "stopped"
                return {
                    "success": True,
                    "message": f"firewalld {action} successfully"}
            else:
                error_output = result.stderr.strip() or result.stdout.strip()
                if (
                    "request dismissed" in error_output.lower()
                    or "cancelled" in error_output.lower()
                ):
                    return {
                        "success": False,
                        "message": "Authentication cancelled by user",
                        "error": "User cancelled the authentication dialog",
                    }
                return {
                    "success": False,
                    "message": f'Failed to {
                        "start" if enable else "stop"} firewalld',
                    "error": error_output or f"Command exited with code {
                        result.returncode}",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Authentication timed out",
                "error": "Authentication dialog timed out after 60 seconds",
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "success": False,
                "message": "firewalld command failed",
                "error": f"systemctl not found or not executable: {str(e)}",
            }

    def _toggle_iptables(self, enable: bool) -> Dict[str, str | bool]:
        """Toggle iptables (basic implementation)."""
        try:
            admin_cmd = self._get_admin_cmd_prefix()
            if not admin_cmd:
                return {
                    "success": False,
                    "message": "Administrative privileges not available",
                    "error": "Neither pkexec nor sudo found on system",
                }

            # Prepare environment for GUI authentication
            env = os.environ.copy()
            if admin_cmd[0] == "pkexec":
                for var in ["DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR"]:
                    if var not in env and var in os.environ:
                        env[var] = os.environ[var]

            if enable:
                # Enable basic iptables rules - drop all incoming except
                # established
                commands = [admin_cmd + ["iptables",
                                         "-P",
                                         "INPUT",
                                         "DROP"],
                            admin_cmd + ["iptables",
                                         "-P",
                                         "FORWARD",
                                         "DROP"],
                            admin_cmd + ["iptables",
                                         "-P",
                                         "OUTPUT",
                                         "ACCEPT"],
                            admin_cmd + ["iptables",
                                         "-A",
                                         "INPUT",
                                         "-i",
                                         "lo",
                                         "-j",
                                         "ACCEPT"],
                            admin_cmd + ["iptables",
                                         "-A",
                                         "INPUT",
                                         "-m",
                                         "conntrack",
                                         "--ctstate",
                                         "ESTABLISHED,RELATED",
                                         "-j",
                                         "ACCEPT",
                                         ],
                            ]
            else:
                # Disable iptables - set all policies to ACCEPT and flush rules
                commands = [
                    admin_cmd + ["iptables", "-P", "INPUT", "ACCEPT"],
                    admin_cmd + ["iptables", "-P", "FORWARD", "ACCEPT"],
                    admin_cmd + ["iptables", "-P", "OUTPUT", "ACCEPT"],
                    admin_cmd + ["iptables", "-F"],  # Flush all rules
                    # Delete user-defined chains
                    admin_cmd + ["iptables", "-X"],
                ]

            # Execute commands
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                    env=env,
                )
                if result.returncode != 0:
                    error_output = result.stderr.strip() or result.stdout.strip()
                    if (
                        "request dismissed" in error_output.lower()
                        or "cancelled" in error_output.lower()
                    ):
                        return {
                            "success": False,
                            "message": "Authentication cancelled by user",
                            "error": "User cancelled the authentication dialog",
                        }
                    return {
                        "success": False,
                        "message": f'iptables command failed: {" ".join(cmd[len(admin_cmd):])}',
                        "error": error_output
                        or f"Command exited with code {result.returncode}",
                    }

            action = "enabled" if enable else "disabled"
            return {
                "success": True,
                "message": f"iptables firewall {action} successfully",
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Authentication timed out",
                "error": "Authentication dialog timed out",
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "success": False,
                "message": "iptables command failed",
                "error": f"iptables not found or not executable: {str(e)}",
            }

    def _toggle_nftables(self, enable: bool) -> Dict[str, str | bool]:
        """Toggle nftables (basic implementation)."""
        try:
            admin_cmd = self._get_admin_cmd_prefix()
            if not admin_cmd:
                return {
                    "success": False,
                    "message": "Administrative privileges not available",
                    "error": "Neither pkexec nor sudo found on system",
                }

            # Prepare environment for GUI authentication
            env = os.environ.copy()
            if admin_cmd[0] == "pkexec":
                for var in ["DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR"]:
                    if var not in env and var in os.environ:
                        env[var] = os.environ[var]

            if enable:
                # Enable basic nftables rules
                nft_rules = """
                table inet filter {
                    chain input {
                        type filter hook input priority 0; policy drop;
                        iif lo accept
                        ct state established,related accept
                    }
                    chain forward {
                        type filter hook forward priority 0; policy drop;
                    }
                    chain output {
                        type filter hook output priority 0; policy accept;
                    }
                }
                """
                result = subprocess.run(
                    admin_cmd + ["nft", "-f", "-"],
                    input=nft_rules,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                    env=env,
                )
            else:
                # Disable nftables - flush all rules
                result = subprocess.run(
                    admin_cmd + ["nft", "flush", "ruleset"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                    env=env,
                )

            if result.returncode == 0:
                action = "enabled" if enable else "disabled"
                return {
                    "success": True,
                    "message": f"nftables firewall {action} successfully",
                }
            else:
                error_output = result.stderr.strip() or result.stdout.strip()
                if (
                    "request dismissed" in error_output.lower()
                    or "cancelled" in error_output.lower()
                ):
                    return {
                        "success": False,
                        "message": "Authentication cancelled by user",
                        "error": "User cancelled the authentication dialog",
                    }
                return {
                    "success": False,
                    "message": f'Failed to {
                        "enable" if enable else "disable"} nftables',
                    "error": error_output or f"Command exited with code {
                        result.returncode}",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Authentication timed out",
                "error": "Authentication dialog timed out",
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "success": False,
                "message": "nftables command failed",
                "error": f"nft not found or not executable: {str(e)}",
            }


# Global instance for easy access
firewall_detector = FirewallDetector()


def get_firewall_status() -> Dict[str, str | bool | None]:
    """Convenience function to get firewall status."""
    return firewall_detector.get_firewall_status()


def toggle_firewall(enable: bool) -> Dict[str, str | bool]:
    """Convenience function to toggle firewall."""
    return firewall_detector.toggle_firewall(enable)


if __name__ == "__main__":
    # Test the firewall detection
    status = get_firewall_status()
    print("Firewall Status:")
    print(f"  Name: {status['firewall_name']}")
    print(f"  Type: {status['firewall_type']}")
    print(f"  Active: {status['is_active']}")
    print(f"  Status: {status['status_text']}")
    if status["error"]:
        print(f"  Error: {status['error']}")
