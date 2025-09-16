#!/usr/bin/env python3
"""
Enhanced RKHunter Detection System
Optimized for security, usability, and compatibility across Linux distributions
Based on comprehensive research of default permissions and best practices
"""

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


@dataclass
class RKHunterDetectionResult:
    """Comprehensive RKHunter detection result"""

    available: bool
    binary_path: Optional[str]
    binary_permissions: Optional[str]
    config_path: Optional[str]
    config_readable: bool
    version: Optional[str]
    install_method: str
    distribution_type: str
    issues: List[str]
    solutions: List[str]
    status_message: str
    confidence_level: str  # 'high', 'medium', 'low'


class EnhancedRKHunterDetector:
    """
    Enhanced RKHunter detection system with multi-method approach
    Handles various permission scenarios across Linux distributions
    """

    def __init__(self):
        self.binary_paths = [
            '/usr/bin/rkhunter',
            '/usr/local/bin/rkhunter',
            '/usr/sbin/rkhunter',
            '/opt/rkhunter/bin/rkhunter'
        ]

        self.config_paths = [
            # User-specific configs (highest priority)
            str(Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf'),
            str(Path.home() / '.rkhunter.conf'),
            # System configs
            '/etc/rkhunter.conf',
            '/usr/local/etc/rkhunter.conf',
            '/etc/rkhunter/rkhunter.conf'
        ]

        self.distribution_detection = self._detect_distribution()

    def detect_comprehensive(self) -> RKHunterDetectionResult:
        """
        Perform comprehensive RKHunter detection using multiple methods
        """
        result = RKHunterDetectionResult(
            available=False,
            binary_path=None,
            binary_permissions=None,
            config_path=None,
            config_readable=False,
            version=None,
            install_method='unknown',
            distribution_type=self.distribution_detection,
            issues=[],
            solutions=[],
            status_message='',
            confidence_level='low'
        )

        # Method 1: Binary detection and permission analysis
        binary_info = self._detect_binary()
        result.binary_path = binary_info['path']
        result.binary_permissions = binary_info['permissions']

        # Method 2: Availability through multiple approaches
        availability = self._check_availability_multi_method()
        result.available = availability['available']
        result.version = availability['version']
        result.install_method = availability['install_method']

        # Method 3: Configuration detection
        config_info = self._detect_configuration()
        result.config_path = config_info['path']
        result.config_readable = config_info['readable']

        # Method 4: Issue analysis and solutions
        issues_analysis = self._analyze_issues(result)
        result.issues = issues_analysis['issues']
        result.solutions = issues_analysis['solutions']

        # Method 5: Generate user-friendly status
        status_info = self._generate_status_message(result)
        result.status_message = status_info['message']
        result.confidence_level = status_info['confidence']

        return result

    def _detect_distribution(self) -> str:
        """Detect Linux distribution for distribution-specific handling"""
        try:
            # Check for distribution-specific files
            if os.path.exists('/etc/arch-release'):
                return 'arch'
            elif os.path.exists('/etc/debian_version'):
                return 'debian'
            elif os.path.exists('/etc/redhat-release'):
                return 'redhat'
            elif os.path.exists('/etc/fedora-release'):
                return 'fedora'

            # Fallback: check /etc/os-release
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'arch' in content:
                        return 'arch'
                    elif 'ubuntu' in content or 'debian' in content:
                        return 'debian'
                    elif 'centos' in content or 'rhel' in content:
                        return 'redhat'
                    elif 'fedora' in content:
                        return 'fedora'

            return 'unknown'
        except Exception:
            return 'unknown'

    def _detect_binary(self) -> Dict[str, Optional[str]]:
        """Detect RKHunter binary and analyze permissions"""
        for binary_path in self.binary_paths:
            if os.path.exists(binary_path):
                try:
                    stat_info = os.stat(binary_path)
                    permissions = oct(stat_info.st_mode)[-3:]

                    return {
                        'path': binary_path,
                        'permissions': permissions,
                        'exists': True,
                        'executable': os.access(binary_path, os.X_OK)
                    }
                except OSError:
                    continue

        return {'path': None, 'permissions': None, 'exists': False, 'executable': False}

    def _check_availability_multi_method(self) -> Dict[str, Union[bool, str]]:
        """Check availability using multiple detection methods"""
        methods = {
            'which_command': self._check_via_which(),
            'direct_execution': self._check_via_execution(),
            'package_manager': self._check_via_package_manager(),
            'file_existence': self._check_via_file_existence()
        }

        # Determine overall availability
        available = any(method['available'] for method in methods.values())

        # Get best version information
        version = None
        install_method = 'unknown'

        for method_name, method_result in methods.items():
            if method_result['available'] and method_result.get('version'):
                version = method_result['version']
                install_method = method_result.get('install_method', method_name)
                break

        return {
            'available': available,
            'version': version,
            'install_method': install_method,
            'methods': methods
        }

    def _check_via_which(self) -> Dict[str, Union[bool, str]]:
        """Check availability via 'which' command"""
        try:
            result = subprocess.run(
                ['which', 'rkhunter'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return {
                    'available': True,
                    'path': result.stdout.strip(),
                    'install_method': 'package'
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass

        return {'available': False}

    def _check_via_execution(self) -> Dict[str, Union[bool, str]]:
        """Check availability via direct execution"""
        try:
            result = subprocess.run(
                ['rkhunter', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and 'Rootkit Hunter' in result.stdout:
                # Parse version from output
                version = 'Rootkit Hunter'
                for line in result.stdout.split('\n'):
                    if 'version' in line.lower() or 'hunter' in line.lower():
                        version = line.strip()
                        break

                return {
                    'available': True,
                    'version': version,
                    'install_method': 'accessible'
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass

        return {'available': False}

    def _check_via_package_manager(self) -> Dict[str, Union[bool, str]]:
        """Check installation via package managers"""
        package_managers = [
            (['pacman', '-Q', 'rkhunter'], 'pacman'),
            (['dpkg', '-l', 'rkhunter'], 'dpkg'),
            (['rpm', '-q', 'rkhunter'], 'rpm'),
            (['yum', 'list', 'installed', 'rkhunter'], 'yum'),
            (['apt', 'list', '--installed', 'rkhunter'], 'apt')
        ]

        for cmd, manager in package_managers:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and 'rkhunter' in result.stdout:
                    return {
                        'available': True,
                        'version': f'Installed via {manager}',
                        'install_method': manager
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                continue

        return {'available': False}

    def _check_via_file_existence(self) -> Dict[str, Union[bool, str]]:
        """Check via direct file existence"""
        binary_info = self._detect_binary()
        if binary_info['exists']:
            return {
                'available': True,
                'path': binary_info['path'],
                'permissions': binary_info['permissions'],
                'executable': binary_info['executable'],
                'install_method': 'file_system'
            }

        return {'available': False}

    def _detect_configuration(self) -> Dict[str, Union[bool, str, None]]:
        """Detect accessible configuration file"""
        for config_path in self.config_paths:
            expanded_path = os.path.expanduser(config_path)
            if os.path.exists(expanded_path):
                readable = os.access(expanded_path, os.R_OK)
                return {
                    'path': expanded_path,
                    'readable': readable,
                    'exists': True
                }

        return {'path': None, 'readable': False, 'exists': False}

    def _analyze_issues(self, result: RKHunterDetectionResult) -> Dict[str, List[str]]:
        """Analyze issues and provide solutions"""
        issues = []
        solutions = []

        # Check for Arch Linux permission anomaly
        if (result.distribution_type == 'arch' and
            result.binary_permissions == '700'):
            issues.append("RKHunter has restrictive permissions (Arch Linux anomaly)")
            solutions.append("Fix with: sudo chmod 755 /usr/bin/rkhunter")

        # Check for inaccessible configuration
        if not result.config_readable and result.config_path:
            issues.append("Configuration file exists but is not readable")
            solutions.append("Create user config: mkdir -p ~/.config/search-and-destroy && cp /etc/rkhunter.conf ~/.config/search-and-destroy/ 2>/dev/null")

        # Check for missing configuration
        if not result.config_path:
            issues.append("No accessible configuration file found")
            solutions.append("Create user-specific configuration file")

        # Check for binary not executable
        if result.binary_path and not os.access(result.binary_path, os.X_OK):
            issues.append("RKHunter binary is not executable by current user")
            if result.binary_permissions == '700':
                solutions.append("Fix permissions: sudo chmod 755 " + result.binary_path)
            else:
                solutions.append("Run with sudo for elevated privileges")

        # Check for not installed
        if not result.available:
            issues.append("RKHunter is not installed")
            if result.distribution_type == 'arch':
                solutions.append("Install with: sudo pacman -S rkhunter")
            elif result.distribution_type in ['debian', 'ubuntu']:
                solutions.append("Install with: sudo apt install rkhunter")
            elif result.distribution_type in ['redhat', 'fedora']:
                solutions.append("Install with: sudo yum install rkhunter (via EPEL)")
            else:
                solutions.append("Install using your distribution's package manager")

        return {'issues': issues, 'solutions': solutions}

    def _generate_status_message(self, result: RKHunterDetectionResult) -> Dict[str, str]:
        """Generate user-friendly status message"""
        if not result.available:
            return {
                'message': '❌ RKHunter is not installed on this system',
                'confidence': 'high'
            }

        if result.issues:
            severity = 'high' if any('not executable' in issue for issue in result.issues) else 'medium'
            if severity == 'high':
                return {
                    'message': '⚠️ RKHunter is installed but has access issues',
                    'confidence': 'high'
                }
            else:
                return {
                    'message': '⚡ RKHunter is available with minor configuration issues',
                    'confidence': 'medium'
                }

        return {
            'message': '✅ RKHunter is properly installed and accessible',
            'confidence': 'high'
        }

    def create_user_config(self) -> Optional[str]:
        """Create user-accessible configuration file"""
        user_config_dir = Path.home() / '.config' / 'search-and-destroy'
        user_config_path = user_config_dir / 'rkhunter.conf'

        if user_config_path.exists():
            return str(user_config_path)

        # Create directory
        user_config_dir.mkdir(parents=True, exist_ok=True)

        # Try to copy system config
        system_configs = ['/etc/rkhunter.conf', '/usr/local/etc/rkhunter.conf']
        for system_config in system_configs:
            if os.path.exists(system_config):
                try:
                    shutil.copy2(system_config, user_config_path)
                    return str(user_config_path)
                except (PermissionError, IOError):
                    continue

        # Create minimal config if copy fails
        minimal_config = """# User-specific RKHunter configuration
# Generated by xanadOS Search & Destroy

# Update settings
UPDATE_MIRRORS=1
MIRRORS_MODE=0
WEB_CMD=""

# Security settings
ALLOW_SSH_ROOT_USER=no

# Whitelist common false positives
ALLOWHIDDENDIR="/dev/.udev"
ALLOWHIDDENDIR="/dev/.static"
ALLOWHIDDENDIR="/dev/.initramfs"

# Package manager integration (Debian-based systems)
PKGMGR=DPKG

# Disable problematic checks that often cause false positives
DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"
"""

        try:
            with open(user_config_path, 'w') as f:
                f.write(minimal_config)
            return str(user_config_path)
        except IOError:
            return None

    def get_installation_suggestions(self) -> Dict[str, str]:
        """Get distribution-specific installation suggestions"""
        suggestions = {
            'arch': 'sudo pacman -S rkhunter',
            'debian': 'sudo apt update && sudo apt install rkhunter',
            'ubuntu': 'sudo apt update && sudo apt install rkhunter',
            'redhat': 'sudo yum install epel-release && sudo yum install rkhunter',
            'fedora': 'sudo dnf install rkhunter',
            'centos': 'sudo yum install epel-release && sudo yum install rkhunter'
        }

        return {
            'command': suggestions.get(self.distribution_detection, 'Use your package manager to install rkhunter'),
            'distribution': self.distribution_detection,
            'notes': self._get_installation_notes()
        }

    def _get_installation_notes(self) -> List[str]:
        """Get distribution-specific installation notes"""
        notes = []

        if self.distribution_detection == 'arch':
            notes.append("After installation, fix permissions: sudo chmod 755 /usr/bin/rkhunter")
        elif self.distribution_detection in ['redhat', 'centos']:
            notes.append("EPEL repository required for RKHunter")
        elif self.distribution_detection in ['debian', 'ubuntu']:
            notes.append("Run 'sudo rkhunter --propupd' after installation")

        return notes


def main():
    """Demo/test the enhanced detection system"""
    detector = EnhancedRKHunterDetector()
    result = detector.detect_comprehensive()

    print("🔍 Enhanced RKHunter Detection Results")
    print("=" * 50)
    print(f"Status: {result.status_message}")
    print(f"Available: {result.available}")
    print(f"Binary Path: {result.binary_path}")
    print(f"Binary Permissions: {result.binary_permissions}")
    print(f"Config Path: {result.config_path}")
    print(f"Config Readable: {result.config_readable}")
    print(f"Version: {result.version}")
    print(f"Install Method: {result.install_method}")
    print(f"Distribution: {result.distribution_type}")
    print(f"Confidence: {result.confidence_level}")

    if result.issues:
        print(f"\n⚠️ Issues Found:")
        for issue in result.issues:
            print(f"  - {issue}")

    if result.solutions:
        print(f"\n💡 Solutions:")
        for solution in result.solutions:
            print(f"  - {solution}")

    # Test user config creation
    if not result.config_readable:
        print(f"\n🔧 Creating user configuration...")
        user_config = detector.create_user_config()
        if user_config:
            print(f"✅ Created: {user_config}")
        else:
            print(f"❌ Failed to create user configuration")


if __name__ == "__main__":
    main()
