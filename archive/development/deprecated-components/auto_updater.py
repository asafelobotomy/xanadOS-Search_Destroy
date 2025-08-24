#!/usr/bin/env python3
"""
Auto-update system for S&D - Search & Destroy
Checks for updates via GitHub releases and handles app updates
"""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import urllib.request
import urllib.error
import ssl


class AutoUpdater:
    """Handles automatic application updates via GitHub releases."""
    
    def __init__(self, current_version: str, config_path: Optional[str] = None):
        self.current_version = current_version
        
        # Load configuration
        config = self._load_config(config_path)
        self.repo_owner = config.get('repo_owner', 'asafelobotomy')
        self.repo_name = config.get('repo_name', 'xanadOS-Search_Destroy')
        self.branch = config.get('update_branch', 'stable')
        self.include_prereleases = config.get('include_prereleases', False)
        
        self.github_api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.update_check_file = Path.home() / ".local/share/search-and-destroy/last_update_check.json"
        
        # Create update directory if it doesn't exist
        self.update_check_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🔧 Auto-updater configured for {self.repo_owner}/{self.repo_name}:{self.branch}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load update configuration from file."""
        if config_path is None:
            # Default config path
            config_path = Path(__file__).parent.parent.parent / "config" / "update_config.json"
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ Could not load update config ({e}), using defaults")
            return {}
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """Make a secure HTTP request to GitHub API."""
        try:
            # Create SSL context with verification
            context = ssl.create_default_context()
            
            # Set User-Agent header to avoid rate limiting
            req = urllib.request.Request(url)
            req.add_header('User-Agent', f'S&D-Search-Destroy/{self.current_version}')
            
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                if response.status == 200:
                    return json.loads(response.read().decode())
                else:
                    print(f"GitHub API request failed with status: {response.status}")
                    return None
        except urllib.error.URLError as e:
            print(f"Network error checking for updates: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response from GitHub: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error checking for updates: {e}")
            return None
    
    def _version_compare(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2."""
        try:
            # Clean version strings (remove 'v' prefix, etc.)
            v1_clean = version1.lstrip('v').strip()
            v2_clean = version2.lstrip('v').strip()
            
            # Split into components
            v1_parts = [int(x) for x in v1_clean.split('.')]
            v2_parts = [int(x) for x in v2_clean.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            # Compare each component
            for a, b in zip(v1_parts, v2_parts):
                if a < b:
                    return -1
                elif a > b:
                    return 1
            return 0
        except (ValueError, AttributeError):
            # Fallback to string comparison if version format is invalid
            return -1 if version1 < version2 else (1 if version1 > version2 else 0)
    
    def check_for_updates(self, force_check: bool = False) -> Optional[Dict]:
        """Check for available updates. Returns update info if available."""
        # Check rate limiting unless forced
        if not force_check and not self._should_check_updates():
            return None
        
        print("🔍 Checking for application updates...")
        
        # Get latest release from GitHub
        latest_release = self._get_latest_release()
        if not latest_release:
            return None
        
        # Update last check time
        self._save_last_check_time()
        
        # Compare versions
        latest_version = latest_release.get('tag_name', '').lstrip('v')
        if not latest_version:
            print("❌ Could not determine latest version")
            return None
        
        comparison = self._version_compare(self.current_version, latest_version)
        
        if comparison < 0:
            # Current version is older
            update_info = {
                'available': True,
                'current_version': self.current_version,
                'latest_version': latest_version,
                'release_name': latest_release.get('name', f'Version {latest_version}'),
                'release_notes': latest_release.get('body', 'No release notes available'),
                'download_url': self._get_download_url(latest_release),
                'published_at': latest_release.get('published_at'),
                'prerelease': latest_release.get('prerelease', False)
            }
            print(f"✅ Update available: {self.current_version} → {latest_version}")
            return update_info
        else:
            print(f"✅ Application is up to date (v{self.current_version})")
            return {'available': False, 'current_version': self.current_version}
    
    def _should_check_updates(self) -> bool:
        """Check if enough time has passed since last update check."""
        try:
            if not self.update_check_file.exists():
                return True
            
            with open(self.update_check_file, 'r') as f:
                data = json.load(f)
            
            last_check = datetime.fromisoformat(data.get('last_check', '2000-01-01'))
            # Check for updates at most once per day
            return datetime.now() - last_check > timedelta(days=1)
        except (json.JSONDecodeError, KeyError, ValueError):
            return True
    
    def _save_last_check_time(self):
        """Save the current time as last update check time."""
        try:
            data = {'last_check': datetime.now().isoformat()}
            with open(self.update_check_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not save update check time: {e}")
    
    def get_last_check_time(self) -> Optional[str]:
        """Get the last update check time as a formatted string."""
        try:
            if not self.update_check_file.exists():
                return None
                
            with open(self.update_check_file, 'r') as f:
                data = json.load(f)
            
            last_check = datetime.fromisoformat(data.get('last_check', ''))
            return last_check.strftime("%Y-%m-%d %H:%M:%S")
        except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError):
            return None
    
    def _get_latest_release(self) -> Optional[Dict]:
        """Get the latest release information from GitHub stable branch."""
        # First, get all releases
        url = f"{self.github_api_url}/releases"
        releases = self._make_request(url)
        
        if not releases:
            return None
        
        # Filter releases to find ones available on the stable branch
        for release in releases:
            if release.get('prerelease', False) and not self.include_prereleases:
                continue  # Skip pre-releases unless configured to include them
            
            # Check if this release's tag exists on the stable branch
            tag_name = release.get('tag_name')
            if tag_name and self._is_tag_on_branch(tag_name, self.branch):
                return release
        
        # If no releases found on stable branch, fall back to latest release
        print(f"⚠️ No releases found on {self.branch} branch, using latest release")
        url = f"{self.github_api_url}/releases/latest"
        return self._make_request(url)
    
    def _is_tag_on_branch(self, tag_name: str, branch_name: str) -> bool:
        """Check if a tag exists on the specified branch."""
        try:
            # Get the commit SHA for the tag
            tag_url = f"{self.github_api_url}/git/refs/tags/{tag_name}"
            tag_data = self._make_request(tag_url)
            
            if not tag_data:
                return False
            
            tag_sha = tag_data.get('object', {}).get('sha')
            if not tag_sha:
                return False
            
            # Get commits from the branch
            branch_url = f"{self.github_api_url}/commits?sha={branch_name}"
            commits = self._make_request(branch_url)
            
            if not commits:
                return False
            
            # Check if the tag's commit SHA is in the branch's commit history
            branch_shas = [commit.get('sha') for commit in commits[:50]]  # Check last 50 commits
            return tag_sha in branch_shas
            
        except Exception as e:
            print(f"Error checking tag on branch: {e}")
            return True  # Default to True to avoid blocking updates
    
    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Extract download URL from release data, preferring stable branch."""
        assets = release_data.get('assets', [])
        
        # For stable branch, construct zipball URL from the stable branch
        tag_name = release_data.get('tag_name')
        if tag_name:
            # Use the stable branch zipball URL instead of the tag
            stable_zipball_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/refs/heads/{self.branch}.zip"
            return stable_zipball_url
        
        # Fallback to release zipball
        zipball_url = release_data.get('zipball_url')
        if zipball_url:
            return zipball_url
        
        # Fallback to first asset if available
        if assets:
            return assets[0].get('browser_download_url')
        
        return None
    
    def download_update(self, download_url: str, progress_callback=None) -> Optional[Path]:
        """Download the update file. Returns path to downloaded file."""
        try:
            print(f"📥 Downloading update from: {download_url}")
            
            # Create temporary file for download
            temp_dir = tempfile.mkdtemp(prefix="sd_update_")
            temp_path = Path(temp_dir) / "update.zip"
            
            # Download with progress tracking
            def reporthook(blocknum, blocksize, totalsize):
                if progress_callback and totalsize > 0:
                    percent = min(100, (blocknum * blocksize * 100) // totalsize)
                    progress_callback(percent)
            
            urllib.request.urlretrieve(download_url, temp_path, reporthook)
            
            print(f"✅ Update downloaded to: {temp_path}")
            return temp_path
            
        except Exception as e:
            print(f"❌ Failed to download update: {e}")
            return None
    
    def apply_update(self, update_file: Path, backup_current: bool = True) -> bool:
        """Apply the downloaded update. Returns True if successful."""
        try:
            print("🔄 Applying update...")
            
            # Get application root directory
            app_root = Path(__file__).parent.parent
            
            # Create backup if requested
            if backup_current:
                backup_path = self._create_backup(app_root)
                if backup_path:
                    print(f"📦 Backup created at: {backup_path}")
            
            # Extract update
            temp_extract_dir = tempfile.mkdtemp(prefix="sd_extract_")
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # Find the extracted directory (GitHub creates a subdirectory)
            extracted_items = list(Path(temp_extract_dir).iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                source_dir = extracted_items[0]
            else:
                source_dir = Path(temp_extract_dir)
            
            # Copy new files (preserve config and data)
            self._copy_update_files(source_dir, app_root)
            
            # Cleanup
            shutil.rmtree(temp_extract_dir)
            update_file.unlink()
            
            print("✅ Update applied successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply update: {e}")
            return False
    
    def _create_backup(self, app_root: Path) -> Optional[Path]:
        """Create a backup of the current application."""
        try:
            backup_dir = app_root.parent / f"search-destroy-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(app_root, backup_dir, ignore=shutil.ignore_patterns(
                '__pycache__', '*.pyc', '*.pyo', '.git', 'temp', 'logs'
            ))
            return backup_dir
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None
    
    def _copy_update_files(self, source_dir: Path, target_dir: Path):
        """Copy update files while preserving user data."""
        # Files/directories to preserve (don't overwrite)
        preserve_patterns = {
            'config.json', 'activity_logs.json', 'scan_reports', 'quarantine', 
            'logs', '__pycache__', '.git', 'temp'
        }
        
        for item in source_dir.rglob('*'):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(source_dir)
                target_path = target_dir / rel_path
                
                # Skip preserved files
                if any(pattern in str(rel_path) for pattern in preserve_patterns):
                    continue
                
                # Create parent directories
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, target_path)
    
    def get_update_settings(self) -> Dict:
        """Get current auto-update settings."""
        try:
            with open(self.update_check_file, 'r') as f:
                data = json.load(f)
                return data.get('settings', {
                    'auto_check': True,
                    'auto_download': False,
                    'auto_install': False,
                    'check_interval_days': 1
                })
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'auto_check': True,
                'auto_download': False, 
                'auto_install': False,
                'check_interval_days': 1
            }
    
    def save_update_settings(self, settings: Dict):
        """Save auto-update settings."""
        try:
            existing_data = {}
            if self.update_check_file.exists():
                with open(self.update_check_file, 'r') as f:
                    existing_data = json.load(f)
            
            existing_data['settings'] = settings
            
            with open(self.update_check_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save update settings: {e}")
    
    def restart_application(self):
        """Restart the application after update."""
        try:
            # Get the current script path
            app_root = Path(__file__).parent.parent
            main_script = app_root / "main.py"
            
            if main_script.exists():
                print("🔄 Restarting application...")
                
                # Start new process
                subprocess.Popen([
                    'python', str(main_script)
                ], cwd=str(app_root))
                
                # Exit current process
                import sys
                sys.exit(0)
            else:
                print("❌ Could not find main script for restart")
        except Exception as e:
            print(f"❌ Failed to restart application: {e}")


# Convenience functions for use in main application
def check_for_updates(current_version: str, force_check: bool = False) -> Optional[Dict]:
    """Convenience function to check for updates."""
    updater = AutoUpdater(current_version)
    return updater.check_for_updates(force_check)


def download_and_apply_update(update_info: Dict, progress_callback=None) -> bool:
    """Convenience function to download and apply an update."""
    if not update_info.get('available'):
        return False
    
    download_url = update_info.get('download_url')
    if not download_url:
        print("❌ No download URL available")
        return False
    
    current_version = update_info.get('current_version', '0.0.0')
    updater = AutoUpdater(current_version)
    
    # Download update
    update_file = updater.download_update(download_url, progress_callback)
    if not update_file:
        return False
    
    # Apply update
    success = updater.apply_update(update_file)
    if success:
        # Optionally restart
        try:
            updater.restart_application()
        except Exception as e:
            print(f"Update applied but restart failed: {e}")
    
    return success


class UpdateNotifier:
    """Handles update notifications and user interactions."""
    
    def __init__(self, updater, main_window):
        """
        Initialize the update notifier.
        
        Args:
            updater: AutoUpdater instance
            main_window: Main application window
        """
        self.updater = updater
        self.main_window = main_window
        self.last_check = None
        
    def check_for_updates_background(self):
        """Check for updates in the background without blocking UI."""
        try:
            from PyQt6.QtCore import QThread, pyqtSignal
            
            class UpdateCheckThread(QThread):
                update_found = pyqtSignal(dict)
                no_update = pyqtSignal()
                error_occurred = pyqtSignal(str)
                
                def __init__(self, updater):
                    super().__init__()
                    self.updater = updater
                    
                def run(self):
                    try:
                        update_info = self.updater.check_for_updates()
                        if update_info:
                            self.update_found.emit(update_info)
                        else:
                            self.no_update.emit()
                    except Exception as e:
                        self.error_occurred.emit(str(e))
            
            # Create and start the background check
            self.check_thread = UpdateCheckThread(self.updater)
            self.check_thread.update_found.connect(self.show_update_notification)
            self.check_thread.error_occurred.connect(self.handle_check_error)
            self.check_thread.start()
            
        except Exception as e:
            print(f"Error starting background update check: {e}")
            
    def show_update_notification(self, update_info):
        """Show update notification to user."""
        try:
            from gui.update_dialog import UpdateDialog
            
            # Check if this version should be skipped
            if self.updater.is_version_skipped(update_info.get('version')):
                return
                
            # Check if we should remind later
            if self.updater.should_remind_later(update_info.get('version')):
                return
                
            # Show the update dialog
            dialog = UpdateDialog(
                parent=self.main_window,
                update_info=update_info,
                updater=self.updater
            )
            dialog.show()
            
        except Exception as e:
            print(f"Error showing update notification: {e}")
            
    def handle_check_error(self, error_message):
        """Handle errors during update checking."""
        print(f"Update check failed: {error_message}")
        
    def check_for_updates_manual(self):
        """Manually check for updates (triggered by user)."""
        try:
            # Show immediate feedback
            if hasattr(self.main_window, 'show_status_message'):
                self.main_window.show_status_message("Checking for updates...")
                
            update_info = self.updater.check_for_updates()
            
            if update_info:
                self.show_update_notification(update_info)
            else:
                # Show "no updates" message using themed dialog
                if hasattr(self.main_window, 'show_themed_message_box'):
                    self.main_window.show_themed_message_box(
                        "information",
                        "No Updates Available",
                        f"You are running the latest version ({self.updater.current_version})."
                    )
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self.main_window,
                        "No Updates Available",
                        f"You are running the latest version ({self.updater.current_version})."
                    )
                
        except Exception as e:
            # Show error message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.main_window,
                "Update Check Failed",
                f"Failed to check for updates:\n{str(e)}"
            )
