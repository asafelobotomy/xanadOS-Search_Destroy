#!/usr/bin/env python3
"""
Firewall Detection and Status Module
=====================================
Detects and monitors various Linux firewall systems and their status.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .elevated_runner import elevated_run
from .secure_subprocess import run_secure
from app.utils.config import DATA_DIR
import glob
import re
import tempfile


class FirewallActivityTracker:
    """Tracks firewall state changes through activity monitoring."""

    def __init__(self):
        self.activity_file = Path.home() / ".local/share/search-and-destroy/firewall_activity.json"
        self.activity_file.parent.mkdir(parents=True, exist_ok=True)
        self._last_known_state = None

    def get_cached_status(self) -> Optional[Dict[str, Any]]:
        """Get last known firewall status from activity cache."""
        try:
            if self.activity_file.exists():
                with open(self.activity_file, "r") as f:
                    data = json.load(f)
                    # Return cached status if it's less than 5 minutes old
                    if time.time() - data.get("timestamp", 0) < 300:  # 5 minutes
                        return data.get("status")
        except (json.JSONDecodeError, IOError):
            pass
        return None

    def update_status(self, status: Dict[str, Any]):
        """Update cached firewall status."""
        try:
            data = {"status": status, "timestamp": time.time()}
            with open(self.activity_file, "w") as f:
                json.dump(data, f)
        except IOError:
            pass

    def record_activity(self, action: str, firewall_type: str, success: bool = True):
        """Record firewall activity for tracking."""
        try:
            {
                "action": action,
                "firewall_type": firewall_type,
                "success": success,
                "timestamp": time.time(),
            }

            # Also update the main activity tracking
            try:
                activity_log_file = DATA_DIR / "activity_log.json"

                if activity_log_file.exists():
                    with open(activity_log_file, "r") as f:
                        activity_log = json.load(f)
                else:
                    activity_log = []

                activity_log.append(
                    {
                        "timestamp": time.time(),
                        "message": f"🔥 Firewall {action} via S&D application",
                        "type": "firewall_activity",
                    }
                )

                # Keep only last 100 entries
                activity_log = activity_log[-100:]

                with open(activity_log_file, "w") as f:
                    json.dump(activity_log, f)
            except (ImportError, IOError):
                pass

        except IOError:
            pass


class FirewallDetector:
    """Detects and monitors firewall status on Linux systems."""

    def __init__(self):
        self.activity_tracker = FirewallActivityTracker()
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
                result = run_secure(
                    [
                        "systemctl",
                        "list-unit-files",
                        f"{fw_info['service_name']}.service",
                    ],
                    timeout=5,
                    capture_output=True,
                    text=True,
                )
                return result.returncode == 0 and fw_info["service_name"] in result.stdout
            except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
                pass

        return True

    def get_firewall_status(self) -> Dict[str, str | bool | None]:
        """
        Get comprehensive firewall status information using non-invasive methods.

        This method prioritizes cached activity data and system service status
        over privileged commands to avoid authentication prompts.

        Returns:
            Dictionary with status information including:
            - is_active: bool
            - firewall_name: str
            - firewall_type: str
            - status_text: str
            - error: str (if any)
            - method: str (how status was determined)
        """
        # First, check if we have recent cached status from activity tracking
        cached_status = self.activity_tracker.get_cached_status()
        if cached_status:
            cached_status["method"] = "activity_cache"
            return cached_status

        fw_type, fw_name = self.detect_firewall()

        status_info = {
            "is_active": False,
            "firewall_name": fw_name,
            "firewall_type": fw_type,
            "status_text": "Inactive",
            "error": None,
            "method": "system_check",
        }

        if not fw_type:
            status_info["status_text"] = "Not detected"
            status_info["method"] = "not_detected"
            return status_info

        try:
            # Get status based on firewall type using non-invasive methods only
            if fw_type == "ufw":
                status_info.update(self._get_ufw_status())
            elif fw_type == "firewalld":
                status_info.update(self._get_firewalld_status())
            elif fw_type == "iptables":
                status_info.update(self._get_iptables_status())
            elif fw_type == "nftables":
                status_info.update(self._get_nftables_status())

            # Cache the result for future use
            self.activity_tracker.update_status(status_info)

        except (OSError, subprocess.SubprocessError) as e:
            status_info["error"] = str(e)
            status_info["status_text"] = "Error checking status"
            status_info["method"] = "error"

        return status_info

    def _get_ufw_status(self) -> Dict[str, str | bool]:
        """Get UFW firewall status using non-invasive methods."""
        try:
            # Use enhanced non-invasive status checking
            return self._get_ufw_status_non_invasive()

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check UFW: {str(e)}"}

    def _get_ufw_status_non_invasive(self) -> Dict[str, str | bool]:
        """Get UFW firewall status without requiring elevated privileges."""

        # Method 1: Check systemctl service status (most reliable, no sudo needed)
        try:
            result = run_secure(
                ["systemctl", "is-active", "ufw"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return {"is_active": True, "status_text": "Active"}
        except (subprocess.SubprocessError, OSError):
            pass

        # Method 2: Check if UFW is enabled via systemctl is-enabled
        try:
            result = run_secure(
                ["systemctl", "is-enabled", "ufw"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            enabled_states = ["enabled", "static", "enabled-runtime"]
            if result.returncode == 0 and result.stdout.strip() in enabled_states:
                return {"is_active": True, "status_text": "Active"}
        except (subprocess.SubprocessError, OSError):
            pass

        # Method 3: Check UFW configuration files (read-only, no sudo needed for most systems)
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

        # Method 4: Check for UFW rule files (indicates UFW has been configured)
        # NOTE: This method has been improved to avoid false positives.
        # Simply having rule files doesn't mean UFW is active - UFW can be
        # disabled even with rule files present. Only check /var/lib/ paths
        # as they're more likely to indicate actual active configuration.
        ufw_rule_paths = ["/var/lib/ufw/user.rules", "/var/lib/ufw/user6.rules"]
        for rule_path in ufw_rule_paths:
            try:
                if (
                    os.path.exists(rule_path) and os.path.getsize(rule_path) > 500
                ):  # Significantly larger rule file
                    # Additional check: look for actual user rules, not just template
                    with open(rule_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Only consider active if there are actual user-defined rules
                    if (
                        "### tuple ###" in content
                        or "-A ufw-user-" in content
                        and "allow" in content.lower()
                    ):
                        return {"is_active": True, "status_text": "Active"}
            except (PermissionError, IOError):
                continue

        # Method 5: Check netfilter/iptables rules indirectly via /proc (last resort)
        # NOTE: Removed this method as it was incorrectly detecting UFW as active
        # just because iptables modules are loaded. The presence of "filter" table
        # only means kernel modules are available, not that UFW is configured/active.

        # If all methods fail, assume inactive
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
            ufw_status_paths = ["/var/lib/ufw/user.rules", "/var/lib/ufw/user6.rules"]

            for status_path in ufw_status_paths:
                try:
                    if os.path.exists(status_path) and os.path.getsize(status_path) > 0:
                        return {"is_active": True, "status_text": "Active"}
                except (PermissionError, IOError):
                    continue

            # Method 3: Check systemctl status (original fallback)
            result = run_secure(
                ["systemctl", "is-active", "ufw"],
                timeout=5,
                capture_output=True,
                text=True,
            )

            is_active = result.stdout.strip() == "active"

            return {
                "is_active": is_active,
                "status_text": "Active" if is_active else "Inactive",
            }
        except (subprocess.SubprocessError, OSError, IOError):
            return {"is_active": False, "status_text": "Inactive"}

    def _get_firewalld_status(self) -> Dict[str, str | bool]:
        """Get firewalld status using non-invasive methods."""
        try:
            # Method 1: Check systemctl service status (most reliable, no sudo needed)
            result = run_secure(
                ["systemctl", "is-active", "firewalld"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return {"is_active": True, "status_text": "Active"}

            # Method 2: Try the original firewall-cmd --state (may work without sudo
            # on some systems)
            result = run_secure(
                ["firewall-cmd", "--state"], timeout=10, capture_output=True, text=True
            )
            if result.returncode == 0:
                is_active = "running" in result.stdout.lower()
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }

            # Method 3: Fallback - assume inactive if service check failed
            return {"is_active": False, "status_text": "Inactive"}

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check firewalld: {str(e)}"}

    def _get_iptables_status(self) -> Dict[str, str | bool]:
        """Get iptables status using non-invasive methods."""
        try:
            # Method 1: Check if iptables service is active via systemctl
            result = run_secure(
                ["systemctl", "is-active", "iptables"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return {"is_active": True, "status_text": "Active"}

            # Method 2: Try iptables -L (may work without sudo on some systems)
            result = run_secure(
                ["iptables", "-L", "-n"], timeout=10, capture_output=True, text=True
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
                has_policies = "policy DROP" in result.stdout or "policy REJECT" in result.stdout
                is_active = rule_count > 0 or has_policies
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }

            # Method 3: Check /proc/net/ip_tables_names for loaded modules
            try:
                if os.path.exists("/proc/net/ip_tables_names"):
                    with open("/proc/net/ip_tables_names", "r") as f:
                        tables = f.read()
                    if "filter" in tables or "nat" in tables:
                        return {"is_active": True, "status_text": "Active"}
            except (PermissionError, IOError):
                pass

            return {"is_active": False, "status_text": "Inactive"}

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check iptables: {str(e)}"}

    def _get_nftables_status(self) -> Dict[str, str | bool]:
        """Get nftables status using non-invasive methods."""
        try:
            # Method 1: Check systemctl service status
            result = run_secure(
                ["systemctl", "is-active", "nftables"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return {"is_active": True, "status_text": "Active"}

            # Method 2: Try nft list tables (may work without sudo on some systems)
            result = run_secure(
                ["nft", "list", "tables"], timeout=10, capture_output=True, text=True
            )
            if result.returncode == 0:
                # If there are any tables, nftables is considered active
                is_active = bool(result.stdout.strip())
                return {
                    "is_active": is_active,
                    "status_text": "Active" if is_active else "Inactive",
                }

            return {"is_active": False, "status_text": "Inactive"}

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Failed to check nftables: {str(e)}"}

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
            result = None
            if fw_type == "ufw":
                result = self._toggle_ufw(enable)

                # If UFW failed with kernel module issues, provide diagnostic info
                if not result["success"] and "error" in result:
                    error_msg = result["error"].lower()
                    if (
                        "can't initialize iptables" in error_msg
                        or "table does not exist" in error_msg
                        or "perhaps iptables" in error_msg
                        or "unable to initialize table" in error_msg
                        or "problem running ufw-init" in error_msg
                    ):
                        # Add diagnostic information
                        diagnosis = self._diagnose_kernel_modules()
                        if diagnosis["success"]:
                            result["diagnosis"] = diagnosis["diagnosis"]
                            result["message"] += " - Kernel module issue detected"
            elif fw_type == "firewalld":
                result = self._toggle_firewalld(enable)
            elif fw_type == "iptables":
                result = self._toggle_iptables(enable)
            elif fw_type == "nftables":
                result = self._toggle_nftables(enable)
            else:
                result = {
                    "success": False,
                    "message": f"Firewall control not implemented for {fw_name}",
                    "error": f"No control method available for {fw_type}",
                }

            # Record activity for successful operations
            if result and result.get("success"):
                action = "enabled" if enable else "disabled"
                self.activity_tracker.record_activity(action, fw_type, True)

                # Update cached status immediately
                updated_status = {
                    "is_active": enable,
                    "firewall_name": fw_name,
                    "firewall_type": fw_type,
                    "status_text": "Active" if enable else "Inactive",
                    "error": None,
                    "method": "user_action",
                }
                self.activity_tracker.update_status(updated_status)
            else:
                # Record failed attempt
                action = "enable" if enable else "disable"
                self.activity_tracker.record_activity(f"failed_to_{action}", fw_type, False)

            return result

        except (OSError, subprocess.SubprocessError, PermissionError) as e:
            return {
                "success": False,
                "message": f"Failed to {'enable' if enable else 'disable'} firewall",
                "error": str(e),
            }

    def _get_admin_cmd_prefix(self) -> list:
        """Get the appropriate command prefix for admin privileges.

        Note: This method is deprecated. Use elevated_run() instead for better
        privilege escalation with GUI sudo priority order.
        """
        # Legacy method - kept for compatibility with module loading code
        # New firewall toggle methods should use elevated_run() directly
        if shutil.which("sudo"):
            return ["sudo"]
        else:
            return []

    def _attempt_module_load(self) -> Dict[str, str | bool]:
        """Attempt to load required iptables kernel modules for UFW with cross-kernel compatibility."""
        required_modules = ["iptable_filter", "iptable_nat", "ip_tables", "x_tables"]

        try:
            admin_cmd = self._get_admin_cmd_prefix()
            if not admin_cmd:
                return {
                    "success": False,
                    "message": "Cannot load kernel modules - no admin privileges",
                }

            env = os.environ.copy()
            loaded_modules = []
            failed_modules = []
            cross_kernel_attempts = []

            # First, try standard module loading
            for module in required_modules:
                cmd = admin_cmd + ["modprobe", module]

                try:
                    result = run_secure(cmd, timeout=30, allow_root=True)

                    if result.returncode == 0:
                        loaded_modules.append(module)
                        print(f"🔍 DEBUG: Successfully loaded module: {module}")
                    else:
                        failed_modules.append(module)
                        print(f"🔍 DEBUG: Failed to load module {module}: {result.stderr}")

                except subprocess.TimeoutExpired:
                    failed_modules.append(module)
                    print(f"🔍 DEBUG: Timeout loading module: {module}")

            # If some modules failed, try cross-kernel loading
            if failed_modules:
                cross_kernel_result = self._try_cross_kernel_modules(failed_modules, admin_cmd, env)
                loaded_modules.extend(cross_kernel_result.get("loaded", []))
                cross_kernel_attempts = cross_kernel_result.get("attempts", [])

                # Remove successfully loaded modules from failed list
                failed_modules = [
                    m for m in failed_modules if m not in cross_kernel_result.get("loaded", [])
                ]

            if loaded_modules:
                message = f"Loaded kernel modules: {', '.join(loaded_modules)}"
                if cross_kernel_attempts:
                    message += f" (including cross-kernel compatibility for: {
                        ', '.join(cross_kernel_attempts)
                    })"
                return {
                    "success": True,
                    "message": message,
                    "loaded": loaded_modules,
                    "failed": failed_modules,
                    "cross_kernel": cross_kernel_attempts,
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to load any required kernel modules",
                    "failed": failed_modules,
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error attempting to load kernel modules: {str(e)}",
            }

    def _try_cross_kernel_modules(
        self, failed_modules: list, admin_cmd: list, env: dict
    ) -> Dict[str, list]:
        """Attempt to load modules from compatible kernel versions."""
        loaded = []
        attempts = []

        try:
            # Get available kernel module directories
            module_base = "/lib/modules"
            available_kernels = []

            if os.path.exists(module_base):
                available_kernels = [
                    d
                    for d in os.listdir(module_base)
                    if os.path.isdir(os.path.join(module_base, d))
                ]
                available_kernels.sort(reverse=True)  # Try newer kernels first

            current_kernel = os.uname().release
            print(f"🔍 DEBUG: Current kernel: {current_kernel}")
            print(f"🔍 DEBUG: Available kernel modules: {available_kernels}")

            # Try each compatible kernel
            for kernel_version in available_kernels:
                if kernel_version == current_kernel:
                    continue  # Skip current kernel, already tried

                # Check if this kernel has the modules we need
                kernel_path = os.path.join(module_base, kernel_version)

                for module in failed_modules[:]:  # Use slice to allow modification
                    if module in loaded:
                        continue

                    # Look for the module file in this kernel's directory
                    module_found = self._find_module_in_kernel(kernel_path, module)

                    if module_found:
                        # Try to load using insmod with full path
                        cmd = admin_cmd + ["insmod", module_found]

                        try:
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=30,
                                check=False,
                                env=env,
                            )

                            if result.returncode == 0:
                                loaded.append(module)
                                attempts.append(f"{module} from {kernel_version}")
                                print(
                                    f"🔍 DEBUG: Cross-kernel loaded {module} from {kernel_version}"
                                )
                            else:
                                print(
                                    f"🔍 DEBUG: Cross-kernel failed {module} from {kernel_version}: {result.stderr}"
                                )

                        except subprocess.TimeoutExpired:
                            print(
                                f"🔍 DEBUG: Timeout cross-kernel loading {module} from {kernel_version}"
                            )

        except Exception as e:
            print(f"🔍 DEBUG: Error in cross-kernel loading: {e}")

        return {"loaded": loaded, "attempts": attempts}

    def _find_module_in_kernel(self, kernel_path: str, module_name: str) -> str | None:
        """Find a specific module file in a kernel directory."""
        try:
            # Common paths where netfilter modules are located
            search_paths = [
                f"kernel/net/ipv4/netfilter/{module_name}.ko*",
                f"kernel/net/netfilter/{module_name}.ko*",
                f"kernel/net/{module_name}.ko*",
            ]

            for pattern in search_paths:
                full_pattern = os.path.join(kernel_path, pattern)

                matches = glob.glob(full_pattern)

                if matches:
                    # Return the first match (could be .ko or .ko.zst)
                    return matches[0]

            return None

        except Exception as e:
            print(f"🔍 DEBUG: Error finding module {module_name} in {kernel_path}: {e}")
            return None

    def _diagnose_kernel_modules(self) -> Dict[str, str | bool]:
        """Diagnose kernel module status for firewall functionality."""
        try:
            # Get kernel version
            kernel_version = "Unknown"
            try:
                with open("/proc/version", "r") as f:
                    kernel_info = f.read().strip()
                    # Extract version info

                    match = re.search(r"Linux version ([^\s]+)", kernel_info)
                    if match:
                        kernel_version = match.group(1)
            except Exception:
                pass

            # Check if required modules are loaded
            loaded_modules = []
            missing_modules = []
            required_modules = [
                "iptable_filter",
                "iptable_nat",
                "ip_tables",
                "x_tables",
            ]

            try:
                with open("/proc/modules", "r") as f:
                    proc_modules = f.read()

                for module in required_modules:
                    if module in proc_modules:
                        loaded_modules.append(module)
                    else:
                        missing_modules.append(module)
            except Exception:
                missing_modules = required_modules  # Assume all missing if we can't read

            # Check available module directories
            module_dirs = []
            try:
                base_path = "/lib/modules"
                if os.path.exists(base_path):
                    module_dirs = [
                        d
                        for d in os.listdir(base_path)
                        if os.path.isdir(os.path.join(base_path, d))
                    ]
                    module_dirs.sort()
            except Exception:
                pass

            return {
                "success": True,
                "kernel_version": kernel_version,
                "loaded_modules": loaded_modules,
                "missing_modules": missing_modules,
                "available_module_dirs": module_dirs,
                "diagnosis": self._generate_module_diagnosis(
                    kernel_version, loaded_modules, missing_modules, module_dirs
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error diagnosing kernel modules: {str(e)}",
            }

    def _generate_module_diagnosis(
        self, kernel_version: str, loaded: list, missing: list, dirs: list
    ) -> str:
        """Generate a human-readable diagnosis of the kernel module situation."""
        if not missing:
            return "All required iptables modules are loaded and available."

        diagnosis = f"Kernel version: {kernel_version}\n"

        if loaded:
            diagnosis += f"Loaded modules: {', '.join(loaded)}\n"

        if missing:
            diagnosis += f"Missing modules: {', '.join(missing)}\n"

        if dirs:
            diagnosis += f"Available module directories: {', '.join(dirs[-3:])}\n"  # Show last 3

            # Check if current kernel matches available modules
            current_in_dirs = any(kernel_version in d for d in dirs)
            if not current_in_dirs:
                diagnosis += f"⚠️  Current kernel ({kernel_version}) modules may not be available.\n"

                # Check for compatible kernels
                compatible_kernels = []
                base_version = kernel_version.split("-")[
                    0
                ]  # e.g., "6.15.8" from "6.15.8-zen1-2-zen"

                for d in dirs:
                    if base_version[:4] in d:  # Match major.minor version (e.g., "6.15")
                        compatible_kernels.append(d)

                if compatible_kernels:
                    diagnosis += (
                        f"📦 Compatible kernels available: {', '.join(compatible_kernels)}\n"
                    )
                    diagnosis += "💡 Solutions:\n"
                    diagnosis += "   • Reboot to use a newer kernel\n"
                    diagnosis += "   • The main firewall toggle will attempt alternative methods\n"
                    diagnosis += "   • Install kernel modules for current kernel\n"
                else:
                    diagnosis += "💡 Solutions:\n"
                    diagnosis += "   • Update system and reboot: sudo pacman -Syu && sudo reboot\n"
                    diagnosis += "   • The main firewall toggle provides alternative protection\n"
                    diagnosis += "   • Manually install iptables modules\n"
            else:
                diagnosis += "✅ Kernel modules should be available but may need loading.\n"
                diagnosis += "💡 Try: sudo modprobe iptable_filter iptable_nat\n"
        else:
            diagnosis += "❌ No kernel module directories found in /lib/modules\n"
            diagnosis += "💡 Solution: Reinstall kernel packages\n"

        return diagnosis

    def _try_alternative_firewall_method(self, enable: bool) -> Dict[str, str | bool]:
        """Try alternative firewall methods when UFW fails due to kernel issues."""
        try:
            admin_cmd = self._get_admin_cmd_prefix()
            if not admin_cmd:
                return {
                    "success": False,
                    "message": "Cannot use alternative firewall - no admin privileges",
                }

            env = os.environ.copy()

            # Method 1: Try direct iptables commands (basic firewall rules)
            if enable:
                # Enable basic firewall protection with iptables
                iptables_rules = [
                    # Set default policies
                    ["iptables", "-P", "INPUT", "DROP"],
                    ["iptables", "-P", "FORWARD", "DROP"],
                    ["iptables", "-P", "OUTPUT", "ACCEPT"],
                    # Allow loopback
                    ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
                    # Allow established connections
                    [
                        "iptables",
                        "-A",
                        "INPUT",
                        "-m",
                        "state",
                        "--state",
                        "ESTABLISHED,RELATED",
                        "-j",
                        "ACCEPT",
                    ],
                    # Allow SSH (port 22) - important to not lock out user
                    [
                        "iptables",
                        "-A",
                        "INPUT",
                        "-p",
                        "tcp",
                        "--dport",
                        "22",
                        "-j",
                        "ACCEPT",
                    ],
                ]

                successful_rules = 0
                for rule in iptables_rules:
                    cmd = admin_cmd + rule
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            check=False,
                            env=env,
                        )

                        if result.returncode == 0:
                            successful_rules += 1
                            print(f"🔍 DEBUG: Applied iptables rule: {' '.join(rule)}")
                        else:
                            print(
                                f"🔍 DEBUG: Failed iptables rule: {' '.join(rule)} - {result.stderr}"
                            )

                    except subprocess.TimeoutExpired:
                        print(f"🔍 DEBUG: Timeout applying rule: {' '.join(rule)}")

                if successful_rules >= 4:  # At least basic rules applied
                    return {
                        "success": True,
                        "message": f"Basic firewall enabled using iptables ({successful_rules}/{len(iptables_rules)} rules applied)",
                        "method": "iptables_direct",
                    }
            else:
                # Disable firewall by flushing iptables rules
                flush_commands = [
                    ["iptables", "-F"],  # Flush all rules
                    ["iptables", "-X"],  # Delete all chains
                    [
                        "iptables",
                        "-P",
                        "INPUT",
                        "ACCEPT",
                    ],  # Set default policies to ACCEPT
                    ["iptables", "-P", "FORWARD", "ACCEPT"],
                    ["iptables", "-P", "OUTPUT", "ACCEPT"],
                ]

                successful_flushes = 0
                for cmd_args in flush_commands:
                    cmd = admin_cmd + cmd_args
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            check=False,
                            env=env,
                        )

                        if result.returncode == 0:
                            successful_flushes += 1
                            print(f"🔍 DEBUG: Applied iptables flush: {' '.join(cmd_args)}")
                        else:
                            print(
                                f"🔍 DEBUG: Failed iptables flush: {' '.join(cmd_args)} - {result.stderr}"
                            )

                    except subprocess.TimeoutExpired:
                        print(f"🔍 DEBUG: Timeout flushing: {' '.join(cmd_args)}")

                if successful_flushes >= 3:  # At least basic flush worked
                    return {
                        "success": True,
                        "message": f"Firewall disabled using iptables ({successful_flushes}/{len(flush_commands)} commands applied)",
                        "method": "iptables_direct",
                    }

            # Method 2: Try systemd-based firewall if iptables direct fails
            return self._try_systemd_firewall_service(enable, admin_cmd, env)

        except Exception as e:
            return {
                "success": False,
                "message": f"Alternative firewall methods failed: {str(e)}",
            }

    def _try_systemd_firewall_service(
        self, enable: bool, admin_cmd: list, env: dict
    ) -> Dict[str, str | bool]:
        """Try to use systemd to manage firewall services as a last resort."""
        try:
            # Check if we can use systemd to manage networking/firewall

            if enable:
                # Try to start basic network security services
                services_to_try = ["ufw", "iptables", "netfilter-persistent"]

                for service in services_to_try:
                    cmd = admin_cmd + ["systemctl", "start", service]
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            check=False,
                            env=env,
                        )

                        if result.returncode == 0:
                            return {
                                "success": True,
                                "message": f"Firewall enabled via systemd service: {service}",
                                "method": f"systemd_{service}",
                            }
                        else:
                            print(f"🔍 DEBUG: Failed to start {service}: {result.stderr}")

                    except subprocess.TimeoutExpired:
                        print(f"🔍 DEBUG: Timeout starting service: {service}")
            else:
                # Try to stop firewall services
                services_to_try = ["ufw", "iptables"]

                for service in services_to_try:
                    cmd = admin_cmd + ["systemctl", "stop", service]
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            check=False,
                            env=env,
                        )

                        if result.returncode == 0:
                            return {
                                "success": True,
                                "message": f"Firewall disabled via systemd service: {service}",
                                "method": f"systemd_{service}",
                            }
                        else:
                            print(f"🔍 DEBUG: Failed to stop {service}: {result.stderr}")

                    except subprocess.TimeoutExpired:
                        print(f"🔍 DEBUG: Timeout stopping service: {service}")

            return {
                "success": False,
                "message": "All alternative firewall methods failed",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Systemd firewall fallback failed: {str(e)}",
            }

    def _toggle_ufw(self, enable: bool) -> Dict[str, str | bool]:
        """Toggle UFW firewall with enhanced error handling for kernel module issues."""
        print(f"🔍 DEBUG: _toggle_ufw called with enable={enable}")
        try:
            # Use elevated_run for consistent privilege escalation with GUI sudo priority
            cmd_args = ["ufw", "--force", "enable" if enable else "disable"]

            # Debug: Print the command being executed
            print(f"DEBUG: Executing firewall command: ufw {' '.join(cmd_args[1:])}")

            print("🔍 DEBUG: About to run elevated_run...")
            # Use elevated_run with GUI preference (same as RKHunter and ClamAV)
            result = elevated_run(
                cmd_args,
                timeout=300,  # Longer timeout for firewall operations
                capture_output=True,
                text=True,
                gui=True,  # Enable GUI sudo preference
            )

            # Debug: Print result details
            print(f"DEBUG: Command exit code: {result.returncode}")
            print(f"DEBUG: Command stdout: {result.stdout}")
            print(f"DEBUG: Command stderr: {result.stderr}")
            print("🔍 DEBUG: elevated_run completed")

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

                # Handle iptables kernel module issues specifically
                if (
                    "can't initialize iptables" in error_output.lower()
                    or "table does not exist" in error_output.lower()
                    or "perhaps iptables or your kernel needs to be upgraded"
                    in error_output.lower()
                    or "unable to initialize table" in error_output.lower()
                    or "problem running ufw-init" in error_output.lower()
                ):
                    # Try to load required kernel modules using old method (for compatibility)
                    module_load_result = self._attempt_module_load()
                    if module_load_result["success"]:
                        # Retry UFW command after loading modules
                        print("🔍 DEBUG: Retrying UFW command after loading kernel modules...")
                        retry_result = elevated_run(
                            cmd_args,
                            timeout=300,
                            capture_output=True,
                            text=True,
                            gui=True,
                        )

                        if retry_result.returncode == 0:
                            action = "enabled" if enable else "disabled"
                            return {
                                "success": True,
                                "message": f"UFW firewall {action} successfully (after loading kernel modules)",
                            }
                        else:
                            # Even after module loading, UFW still fails - try alternative approach
                            print(
                                "🔍 DEBUG: UFW still failing after module loading, trying alternative approach"
                            )
                            alt_result = self._try_alternative_firewall_method(enable)
                            if alt_result["success"]:
                                return alt_result

                return {
                    "success": False,
                    "message": f"Failed to {'enable' if enable else 'disable'} UFW",
                    "error": error_output or f"Command exited with code {result.returncode}",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Authentication timed out",
                "error": "Authentication dialog timed out after 300 seconds",
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
            # Use elevated_run for consistent privilege escalation
            cmd_args = ["systemctl", "start" if enable else "stop", "firewalld"]

            result = elevated_run(cmd_args, timeout=60, capture_output=True, text=True, gui=True)

            if result.returncode == 0:
                action = "started" if enable else "stopped"
                return {"success": True, "message": f"firewalld {action} successfully"}
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
                    "message": f"Failed to {'start' if enable else 'stop'} firewalld",
                    "error": error_output or f"Command exited with code {result.returncode}",
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
        """Toggle iptables using enhanced GUI authentication."""
        try:
            if enable:
                # Enable basic iptables rules - drop all incoming except established
                commands = [
                    ["iptables", "-P", "INPUT", "DROP"],
                    ["iptables", "-P", "FORWARD", "DROP"],
                    ["iptables", "-P", "OUTPUT", "ACCEPT"],
                    ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
                    [
                        "iptables",
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
                    ["iptables", "-P", "INPUT", "ACCEPT"],
                    ["iptables", "-P", "FORWARD", "ACCEPT"],
                    ["iptables", "-P", "OUTPUT", "ACCEPT"],
                    ["iptables", "-F"],  # Flush all rules
                    ["iptables", "-X"],  # Delete user-defined chains
                ]

            # Execute commands using elevated_run with GUI authentication
            for cmd in commands:
                result = elevated_run(cmd, timeout=60, capture_output=True, text=True, gui=True)

                if result.returncode != 0:
                    error_output = result.stderr.strip() or result.stdout.strip()

                    # Check for authentication cancellation
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
                        "message": f"Failed to {'enable' if enable else 'disable'} iptables",
                        "error": error_output or f"iptables command failed: {' '.join(cmd)}",
                    }

            action = "enabled" if enable else "disabled"
            return {"success": True, "message": f"iptables {action} successfully"}

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Authentication timed out",
                "error": "Authentication dialog timed out after 60 seconds",
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "success": False,
                "message": "iptables command failed",
                "error": f"iptables not found or not executable: {str(e)}",
            }

    def _toggle_nftables(self, enable: bool) -> Dict[str, str | bool]:
        """Toggle nftables using enhanced GUI authentication."""
        try:
            if enable:
                # Enable basic nftables rules using elevated_run
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
                # Note: For stdin input, we need to use a different approach with elevated_run
                # We'll create a temporary file or use a different method

                with tempfile.NamedTemporaryFile(mode="w", suffix=".nft", delete=False) as f:
                    f.write(nft_rules)
                    temp_file = f.name

                try:
                    result = elevated_run(
                        ["nft", "-f", temp_file],
                        timeout=60,
                        capture_output=True,
                        text=True,
                        gui=True,
                    )
                finally:
                    # Clean up temp file

                    try:
                        os.unlink(temp_file)
                    except BaseException:
                        pass
            else:
                # Disable nftables - flush all rules using elevated_run
                result = elevated_run(
                    ["nft", "flush", "ruleset"],
                    timeout=60,
                    capture_output=True,
                    text=True,
                    gui=True,
                )

            if result.returncode == 0:
                action = "enabled" if enable else "disabled"
                return {
                    "success": True,
                    "message": f"nftables firewall {action} successfully",
                }
            else:
                error_output = result.stderr.strip() or result.stdout.strip()

                # Check for authentication cancellation
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
                    "message": f"Failed to {'enable' if enable else 'disable'} nftables",
                    "error": error_output or f"Command exited with code {result.returncode}",
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
