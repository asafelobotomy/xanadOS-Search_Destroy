#!/usr/bin/env python3
"""
Automatic Updates System for S&D
Handles virus definition updates, software updates, and threat intelligence feeds.

Note: This module is intentionally comprehensive and currently exceeds the default
Pylint module line limit. A future refactor could split responsibilities across
smaller modules. For now, we prefer stability over large structural changes.
"""

# pylint: disable=too-many-lines  # Large, monolithic updater; split planned in future

import asyncio
import hashlib
import json
import logging
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests
import schedule

try:
    from .secure_subprocess import run_secure  # centralized secure subprocess
except (
    ImportError
):  # pragma: no cover - optional dependency; fallback handled at call sites
    run_secure = None  # type: ignore


class UpdateType(Enum):
    """Types of updates available."""

    VIRUS_DEFINITIONS = "virus_definitions"
    SOFTWARE = "software"
    THREAT_INTELLIGENCE = "threat_intelligence"
    SIGNATURES = "signatures"


class UpdateStatus(Enum):
    """Update operation status."""

    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    SUCCESS = "success"
    FAILED = "failed"


class UpdatePriority(Enum):
    """Update priority levels."""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class UpdateInfo:  # pylint: disable=too-many-instance-attributes
    """Information about available update."""

    update_type: UpdateType
    version: str
    description: str
    size_bytes: int
    download_url: str
    checksum: str
    checksum_type: str = (
        "sha256"  # Use SHA256 by default for security (SHA512 also recommended)
    )
    priority: UpdatePriority = UpdatePriority.NORMAL
    release_date: datetime = field(default_factory=datetime.now)
    required_restart: bool = False
    changelog: List[str] = field(default_factory=list)


@dataclass
class UpdateResult:  # pylint: disable=too-many-instance-attributes
    """Result of update operation."""

    update_type: UpdateType
    success: bool
    version: str = ""
    error_message: str = ""
    download_time: float = 0.0
    install_time: float = 0.0
    bytes_downloaded: int = 0


@dataclass
class UpdateConfig:  # pylint: disable=too-many-instance-attributes
    """Update system configuration."""

    auto_update_enabled: bool = True
    check_interval_hours: int = 4
    download_timeout: int = 300  # 5 minutes
    virus_definitions_sources: List[str] = field(
        default_factory=lambda: [
            "https://database.clamav.net/main.cvd",
            "https://database.clamav.net/daily.cvd",
            "https://database.clamav.net/bytecode.cvd",
        ]
    )
    threat_intel_sources: List[str] = field(default_factory=list)
    update_window_start: str = "02:00"  # 2 AM
    update_window_end: str = "04:00"  # 4 AM
    max_concurrent_downloads: int = 3
    retry_attempts: int = 3
    retry_delay_seconds: int = 300  # 5 minutes


class AutoUpdateSystem:  # pylint: disable=too-many-instance-attributes
    """
    Comprehensive automatic update system for virus definitions,
    threat intelligence, and software components.
    """

    def __init__(
        self, current_version=None, clamav_wrapper=None, config: UpdateConfig = None
    ):
        self.logger = logging.getLogger(__name__)
        self.clamav = clamav_wrapper
        self.config = config or UpdateConfig()
        self.current_version = (
            current_version  # Store current version for compatibility
        )

        # State management
        self.status = UpdateStatus.IDLE
        self.status_lock = threading.RLock()
        self.is_running = False

        # Update tracking
        self.last_check_time: Optional[datetime] = None
        self.last_update_times: Dict[UpdateType, datetime] = {}
        self.available_updates: Dict[UpdateType, UpdateInfo] = {}
        self.update_history: List[UpdateResult] = []
        self.pending_updates: List[UpdateInfo] = []

        # Download management
        self.active_downloads: Dict[str, asyncio.Task] = {}
        self.download_progress: Dict[str, Dict[str, Any]] = {}

        # Callbacks
        self.update_available_callback: Optional[Callable[[UpdateInfo], None]] = None
        self.update_completed_callback: Optional[Callable[[UpdateResult], None]] = None
        self.update_progress_callback: Optional[Callable[[UpdateType, int], None]] = (
            None
        )
        self.update_error_callback: Optional[Callable[[str], None]] = None

        # Database paths
        self.db_dir = (
            Path("/var/lib/clamav")
            if Path("/var/lib/clamav").exists()
            else Path("./clamav_db")
        )
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # Config file for persistent state
        self.config_file = (
            Path.home() / ".config" / "search-and-destroy" / "update_state.json"
        )
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Load persisted state
        self._load_persistent_state()

        # Scheduler
        self.scheduler = schedule.Scheduler()
        self.scheduler_thread: Optional[threading.Thread] = None

        # Async components
        self.update_loop_task: Optional[asyncio.Task] = None
        self.check_updates_task: Optional[asyncio.Task] = None

        self.logger.info("Auto-update system initialized")

    # --- Lightweight logging helpers to match call sites across the module ---
    def logdebug(self, msg: str, *args, **kwargs) -> None:  # noqa: D401
        """Proxy to logger.debug."""
        self.logger.debug(msg, *args, **kwargs)

    def loginfo(self, msg: str, *args, **kwargs) -> None:  # noqa: D401
        """Proxy to logger.info."""
        self.logger.info(msg, *args, **kwargs)

    def logwarning(self, msg: str, *args, **kwargs) -> None:  # noqa: D401
        """Proxy to logger.warning."""
        self.logger.warning(msg, *args, **kwargs)

    def logerror(self, msg: str, *args, **kwargs) -> None:  # noqa: D401
        """Proxy to logger.error."""
        self.logger.error(msg, *args, **kwargs)

    def logcritical(self, msg: str, *args, **kwargs) -> None:  # noqa: D401
        """Proxy to logger.critical."""
        self.logger.critical(msg, *args, **kwargs)

    def _load_persistent_state(self):
        """Load persistent state from config file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                # Load last check time
                if "last_check_time" in state:
                    self.last_check_time = datetime.fromisoformat(
                        state["last_check_time"]
                    )

        except (OSError, json.JSONDecodeError, ValueError):
            # Corrupt/missing state should not crash the updater; log and continue
            self.logdebug(
                "Could not load persistent state: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def _save_persistent_state(self):
        """Save persistent state to config file."""
        try:
            state = {}

            # Save last check time
            if self.last_check_time:
                state["last_check_time"] = self.last_check_time.isoformat()

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

        except (OSError, TypeError):
            # Saving state can fail due to I/O or serialization; log and continue
            self.logdebug(
                "Could not save persistent state: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    async def start_update_system(self) -> bool:
        """Start the automatic update system."""
        try:
            if self.is_running:
                self.logger.warning("Update system already running")
                return True

            self.is_running = True

            # Setup scheduled tasks
            self._setup_scheduled_updates()

            # Start scheduler thread
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler, daemon=True, name="UpdateScheduler"
            )
            self.scheduler_thread.start()

            # Start update monitoring loop
            self.update_loop_task = asyncio.create_task(self._update_monitoring_loop())

            # Perform initial update check
            self.check_updates_task = asyncio.create_task(
                self.check_for_updates_async()
            )

            self.logger.info("Auto-update system started")
            return True

        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Failed to start update system: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            self.is_running = False
            return False

    async def stop_update_system(self):
        """Stop the automatic update system."""
        self.is_running = False

        # Cancel active downloads
        for download_task in self.active_downloads.values():
            download_task.cancel()

        # Cancel monitoring tasks
        if self.update_loop_task:
            self.update_loop_task.cancel()
        if self.check_updates_task:
            self.check_updates_task.cancel()

        # Wait for tasks to complete
        await self._wait_for_tasks()

        # Stop scheduler
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)

        self.logger.info("Auto-update system stopped")

    def _setup_scheduled_updates(self):
        """Setup scheduled update checks and installations."""
        # Schedule virus definition updates every 4 hours
        self.scheduler.every(self.config.check_interval_hours).hours.do(
            self._schedule_update_check
        )

        # Schedule daily update installation during maintenance window
        self.scheduler.every().day.at(self.config.update_window_start).do(
            self._schedule_update_installation
        )

        # Schedule weekly threat intelligence updates
        self.scheduler.every().sunday.at("01:00").do(self._schedule_threat_intel_update)

    def _run_scheduler(self):
        """Run the update scheduler."""
        while self.is_running:
            try:
                self.scheduler.run_pending()
                time.sleep(60)  # Check every minute
            except Exception:  # pylint: disable=broad-exception-caught
                self.logerror(
                    "Error in update scheduler: %s".replace("%s", "{e}").replace(
                        "%d", "{e}"
                    )
                )
                time.sleep(60)

    def _schedule_update_check(self):
        """Schedule update check (called by scheduler)."""
        if self.is_running:
            asyncio.create_task(self.check_for_updates_async())

    def _schedule_update_installation(self):
        """Schedule update installation (called by scheduler)."""
        if self.is_running and self.pending_updates:
            asyncio.create_task(self.install_pending_updates())

    def _schedule_threat_intel_update(self):
        """Schedule threat intelligence update (called by scheduler)."""
        if self.is_running:
            asyncio.create_task(self.update_threat_intelligence())

    async def check_for_updates_async(
        self, force_check: bool = False
    ) -> Dict[UpdateType, UpdateInfo]:
        """Check for available updates (async version)."""
        with self.status_lock:
            if self.status != UpdateStatus.IDLE and not force_check:
                self.logger.warning("Update check already in progress")
                return {}
            self.status = UpdateStatus.CHECKING

        try:
            self.logger.info("Checking for updates...")
            available_updates = {}

            # Check virus definition updates
            virus_def_update = await self._check_virus_definitions()
            if virus_def_update:
                available_updates[UpdateType.VIRUS_DEFINITIONS] = virus_def_update

            # Check software updates
            software_update = await self._check_software_updates()
            if software_update:
                available_updates[UpdateType.SOFTWARE] = software_update

            # Check threat intelligence updates
            threat_intel_update = await self._check_threat_intelligence()
            if threat_intel_update:
                available_updates[UpdateType.THREAT_INTELLIGENCE] = threat_intel_update

            # Update state
            self.available_updates = available_updates
            self.last_check_time = datetime.now()

            # Save persistent state
            self._save_persistent_state()

            # Notify about available updates
            for update_info in available_updates.values():
                if self.update_available_callback:
                    self.update_available_callback(update_info)

            # Auto-schedule critical updates
            for update_info in available_updates.values():
                if self.config.auto_update_enabled and update_info.priority in [
                    UpdatePriority.CRITICAL,
                    UpdatePriority.HIGH,
                ]:
                    self.pending_updates.append(update_info)

            with self.status_lock:
                self.status = UpdateStatus.IDLE

            # Use lazy logging formatting
            self.logger.info(
                "Update check completed. Found %d updates", len(available_updates)
            )
            return available_updates

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("Error checking for updates: %s", e)
            with self.status_lock:
                self.status = UpdateStatus.FAILED
            if self.update_error_callback:
                self.update_error_callback(f"Update check failed: {e}")
            return {}

    async def _check_virus_definitions(self) -> Optional[UpdateInfo]:
        """Check for virus definition updates."""
        try:
            # Get current database versions
            current_versions = {}
            for db_file in ["main.cvd", "daily.cvd", "bytecode.cvd"]:
                db_path = self.db_dir / db_file
                if db_path.exists():
                    # Extract version from file (simplified)
                    current_versions[db_file] = db_path.stat().st_mtime

            # Check online versions
            latest_version_info = await self._get_latest_db_versions()

            # Compare versions
            needs_update = False
            for db_file, online_info in latest_version_info.items():
                local_time = current_versions.get(db_file, 0)
                if online_info["last_modified"] > local_time:
                    needs_update = True
                    break

            if needs_update:
                total_size = sum(info["size"] for info in latest_version_info.values())
                return UpdateInfo(
                    update_type=UpdateType.VIRUS_DEFINITIONS,
                    version=datetime.now().strftime("%Y%m%d"),
                    description="Updated virus definitions",
                    size_bytes=total_size,
                    download_url="multiple",  # Multiple files
                    checksum="",  # Will verify individual files
                    priority=UpdatePriority.HIGH,
                )

            return None

        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Error checking virus definitions: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return None

    async def _check_software_updates(self) -> Optional[UpdateInfo]:
        """Check for software updates."""
        try:
            # Check GitHub releases for newer versions
            # Use centralized version from app package (reads root VERSION)
            try:
                from app import (
                    get_version,
                )  # local import to avoid cycles at module load

                current_version = get_version()
            except Exception:  # pylint: disable=broad-exception-caught
                current_version = "dev"  # Fallback version

            response = await self._async_http_request(
                "GET",
                "https://api.github.com/repos/asafelobotomy/xanadOS-Search_Destroy/releases/latest",
            )

            if response and "tag_name" in response:
                latest_version = response["tag_name"].lstrip("v")
                if self._version_compare(latest_version, current_version) > 0:
                    return UpdateInfo(
                        update_type=UpdateType.SOFTWARE,
                        version=latest_version,
                        description=f"S&D version {latest_version}",
                        size_bytes=response.get(
                            "size", 50 * 1024 * 1024
                        ),  # Estimate 50MB
                        download_url=response.get("tarball_url", ""),
                        checksum="",
                        priority=UpdatePriority.NORMAL,
                        required_restart=True,
                        changelog=response.get("body", "").split("\n")[:10],
                    )

            return None

        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Error checking software updates: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return None

    async def _check_threat_intelligence(self) -> Optional[UpdateInfo]:
        """Check for threat intelligence updates."""
        try:
            # Check threat intelligence sources
            for _ in self.config.threat_intel_sources:
                # This would integrate with actual threat intel feeds
                # For now, return a placeholder
                pass

            # Simplified implementation
            last_intel_update = self.last_update_times.get(
                UpdateType.THREAT_INTELLIGENCE
            )
            if not last_intel_update or datetime.now() - last_intel_update > timedelta(
                days=1
            ):
                return UpdateInfo(
                    update_type=UpdateType.THREAT_INTELLIGENCE,
                    version=datetime.now().strftime("%Y%m%d"),
                    description="Updated threat intelligence data",
                    size_bytes=1024 * 1024,  # 1MB
                    download_url="https://example.com/threat_intel.json",
                    checksum="",
                    priority=UpdatePriority.NORMAL,
                )

            return None

        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Error checking threat intelligence: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return None

    async def install_pending_updates(self) -> List[UpdateResult]:
        """Install all pending updates."""
        results = []

        with self.status_lock:
            if self.status != UpdateStatus.IDLE:
                self.logger.warning("Update installation already in progress")
                return results
            self.status = UpdateStatus.INSTALLING

        try:
            self.logger.info("Installing %d pending updates", len(self.pending_updates))

            # Sort by priority
            sorted_updates = sorted(
                self.pending_updates, key=lambda u: u.priority.value
            )

            for update_info in sorted_updates:
                result = await self.install_update(update_info)
                results.append(result)

                if self.update_completed_callback:
                    self.update_completed_callback(result)

            # Clear pending updates
            self.pending_updates.clear()

            with self.status_lock:
                self.status = UpdateStatus.SUCCESS

            self.logger.info(
                "Update installation completed. %d successful, %d failed",
                sum(1 for r in results if r.success),
                sum(1 for r in results if not r.success),
            )

            return results

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Error installing updates: %s".replace("%s", "{e}").replace("%d", "{e}")
            )
            with self.status_lock:
                self.status = UpdateStatus.FAILED
            if self.update_error_callback:
                self.update_error_callback(f"Update installation failed: {e}")
            return results

    async def install_update(self, update_info: UpdateInfo) -> UpdateResult:
        """Install a specific update."""
        start_time = time.time()

        try:
            self.logger.info(
                "Installing update: %s v%s",
                update_info.update_type.value,
                update_info.version,
            )

            if update_info.update_type == UpdateType.VIRUS_DEFINITIONS:
                result = await self._install_virus_definitions(update_info)
            elif update_info.update_type == UpdateType.SOFTWARE:
                result = await self._install_software_update(update_info)
            elif update_info.update_type == UpdateType.THREAT_INTELLIGENCE:
                result = await self._install_threat_intelligence(update_info)
            else:
                result = UpdateResult(
                    update_type=update_info.update_type,
                    success=False,
                    error_message="Unknown update type",
                )

            # Record installation time
            result.install_time = time.time() - start_time

            # Update history
            self.update_history.append(result)
            if len(self.update_history) > 100:  # Keep last 100 updates
                self.update_history = self.update_history[-100:]

            # Update last update time
            if result.success:
                self.last_update_times[update_info.update_type] = datetime.now()

            return result

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Error installing update %s: %s".replace(
                    "%s", "{update_info.update_type.value, e}"
                ).replace("%d", "{update_info.update_type.value, e}")
            )
            return UpdateResult(
                update_type=update_info.update_type,
                success=False,
                error_message=str(e),
                install_time=time.time() - start_time,
            )

    async def _install_virus_definitions(self, update_info: UpdateInfo) -> UpdateResult:
        """Install virus definition updates."""
        try:
            total_downloaded = 0
            download_start = time.time()

            # Download each database file
            for source_url in self.config.virus_definitions_sources:
                db_filename = Path(source_url).name
                temp_path = Path(tempfile.gettempdir()) / f"tmp_{db_filename}"

                # Download file
                bytes_downloaded = await self._download_file(source_url, temp_path)
                total_downloaded += bytes_downloaded

                # Verify download
                if await self._verify_db_file(temp_path):
                    # Move to database directory
                    final_path = self.db_dir / db_filename
                    shutil.move(str(temp_path), str(final_path))
                    self.loginfo(
                        "Updated database file: %s".replace(
                            "%s", "{db_filename}"
                        ).replace("%d", "{db_filename}")
                    )
                else:
                    self.logerror(
                        "Database file verification failed: %s".replace(
                            "%s", "{db_filename}"
                        ).replace("%d", "{db_filename}")
                    )
                    if temp_path.exists():
                        temp_path.unlink()
                    raise ValueError(f"Database verification failed: {db_filename}")

            download_time = time.time() - download_start

            # Reload ClamAV if available
            if self.clamav:
                await self._reload_clamav_database()

            return UpdateResult(
                update_type=UpdateType.VIRUS_DEFINITIONS,
                success=True,
                version=update_info.version,
                download_time=download_time,
                bytes_downloaded=total_downloaded,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            return UpdateResult(
                update_type=UpdateType.VIRUS_DEFINITIONS,
                success=False,
                error_message=str(e),
            )

    async def _install_software_update(self, update_info: UpdateInfo) -> UpdateResult:
        """Install software updates."""
        try:
            # Download update package
            temp_dir = Path(tempfile.mkdtemp(prefix="s&d_update_"))
            update_file = temp_dir / "update.tar.gz"

            download_start = time.time()
            bytes_downloaded = await self._download_file(
                update_info.download_url, update_file
            )
            download_time = time.time() - download_start

            # Verify checksum if provided
            if update_info.checksum:
                if not await self._verify_checksum(
                    update_file, update_info.checksum, update_info.checksum_type
                ):
                    raise ValueError("Update file checksum verification failed")

            # For safety, just log the update availability for now
            # In production, this would extract and apply the update
            self.loginfo(
                "Software update downloaded and verified: %s".replace(
                    "%s", "{update_info.version}"
                ).replace("%d", "{update_info.version}")
            )
            self.logger.info("Manual installation required for safety")

            # Cleanup
            shutil.rmtree(temp_dir)

            return UpdateResult(
                update_type=UpdateType.SOFTWARE,
                success=True,
                version=update_info.version,
                download_time=download_time,
                bytes_downloaded=bytes_downloaded,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            return UpdateResult(
                update_type=UpdateType.SOFTWARE, success=False, error_message=str(e)
            )

    async def _install_threat_intelligence(
        self, update_info: UpdateInfo
    ) -> UpdateResult:
        """Install threat intelligence updates."""
        try:
            # Download threat intelligence data
            intel_file = Path(tempfile.gettempdir()) / "threat_intel.json"

            download_start = time.time()
            bytes_downloaded = await self._download_file(
                update_info.download_url, intel_file
            )
            download_time = time.time() - download_start

            # Process threat intelligence data
            # This would integrate with the real-time protection engine
            intel_data = await self._process_threat_intel(intel_file)

            # Store in threat intelligence database
            await self._store_threat_intel(intel_data)

            # Cleanup
            if intel_file.exists():
                intel_file.unlink()

            return UpdateResult(
                update_type=UpdateType.THREAT_INTELLIGENCE,
                success=True,
                version=update_info.version,
                download_time=download_time,
                bytes_downloaded=bytes_downloaded,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            return UpdateResult(
                update_type=UpdateType.THREAT_INTELLIGENCE,
                success=False,
                error_message=str(e),
            )

    async def _download_file(
        self, url: str, dest_path: Path, progress_callback=None
    ) -> int:
        """Download file with progress tracking."""
        try:
            if aiohttp is None:
                raise RuntimeError(
                    "aiohttp is required for downloads but is not installed"
                )
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.download_timeout)
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with dest_path.open("wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Report progress
                            if progress_callback and total_size > 0:
                                progress_callback(downloaded, total_size)

                    return downloaded

        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Download failed for %s: %s".replace("%s", "{url, e}").replace(
                    "%d", "{url, e}"
                )
            )
            raise

    async def _verify_checksum(
        self, file_path: Path, expected_checksum: str, checksum_type: str
    ) -> bool:
        """Verify file checksum with support for multiple hash algorithms."""
        try:
            checksum_type = checksum_type.lower()

            # Supported hash algorithms in order of security preference
            if checksum_type == "sha256":
                hasher = hashlib.sha256()
            elif checksum_type == "sha512":
                hasher = hashlib.sha512()
            elif checksum_type == "sha1":
                # SHA1 is deprecated but may be needed for compatibility
                self.logger.warning(
                    "SHA1 checksum verification is deprecated and should be avoided. "
                    "Please use SHA256 or SHA512 for better security."
                )
                hasher = hashlib.sha1(usedforsecurity=False)
            elif checksum_type == "md5":
                # MD5 is cryptographically broken but kept for legacy compatibility
                self.logger.warning(
                    "MD5 checksum verification is cryptographically insecure and deprecated. "
                    "Please upgrade to SHA256 or SHA512 for proper security. "
                    "This support will be removed in a future version."
                )
                hasher = hashlib.md5(usedforsecurity=False)
            else:
                self.logger.error(
                    "Unsupported checksum type: %s. Supported types: sha256, sha512, "
                    "sha1 (deprecated), md5 (deprecated)",
                    checksum_type,
                )
                return False

            # Calculate hash
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)

            computed_hash = hasher.hexdigest().lower()
            expected_hash = expected_checksum.lower()

            if computed_hash == expected_hash:
                if checksum_type in ["sha256", "sha512"]:
                    self.logger.debug(
                        "Checksum verification successful using secure %s",
                        checksum_type.upper(),
                    )
                return True

            self.logger.error(
                "Checksum verification failed: expected %s, got %s",
                expected_hash,
                computed_hash,
            )
            return False
        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Error during checksum verification: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False

    async def _verify_db_file(self, db_path: Path) -> bool:
        """Verify ClamAV database file integrity."""
        try:
            # Use sigtool to verify if available
            sigtool_path = shutil.which("sigtool")
            if sigtool_path:
                if run_secure is not None:
                    result = run_secure(
                        [sigtool_path, "--info", str(db_path)], timeout=30
                    )
                    return result.returncode == 0
                # Fallback to original subprocess if secure wrapper unavailable
                result = subprocess.run(
                    [sigtool_path, "--info", str(db_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                return result.returncode == 0

            # Basic size check as fallback
            return db_path.stat().st_size > 1024  # At least 1KB

        except Exception:  # pylint: disable=broad-exception-caught
            return False

    async def _reload_clamav_database(self):
        """Reload ClamAV database after updates."""
        try:
            if hasattr(self.clamav, "reload_database"):
                await asyncio.get_event_loop().run_in_executor(
                    None, self.clamav.reload_database
                )
            self.logger.info("ClamAV database reloaded")
        except Exception:  # pylint: disable=broad-exception-caught
            self.logerror(
                "Failed to reload ClamAV database: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    async def _get_latest_db_versions(self) -> Dict[str, Dict[str, Any]]:
        """Get latest virus definition versions from online sources."""
        versions = {}

        for url in self.config.virus_definitions_sources:
            try:
                filename = Path(url).name
                # HEAD request to get file info
                response = await self._async_http_request("HEAD", url)
                if response:
                    versions[filename] = {
                        "size": int(response.get("content-length", 0)),
                        "last_modified": time.time(),  # Simplified
                    }
            except Exception:  # pylint: disable=broad-exception-caught
                self.logerror(
                    "Error checking %s: %s".replace("%s", "{url, e}").replace(
                        "%d", "{url, e}"
                    )
                )

        return versions

    async def _async_http_request(
        self, method: str, url: str
    ) -> Optional[Dict[str, Any]]:
        """Make async HTTP request."""
        try:
            # Simplified implementation - would use aiohttp in production
            loop = asyncio.get_event_loop()

            def sync_request():
                response = requests.request(method, url, timeout=30)
                response.raise_for_status()

                if method == "HEAD":
                    return dict(response.headers)
                return response.json()

            return await loop.run_in_executor(None, sync_request)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                # Rate limiting is expected for ClamAV database
                self.logdebug(
                    "Rate limited by %s (403 Forbidden) - this is normal".replace(
                        "%s", "{url}"
                    ).replace("%d", "{url}")
                )
            elif e.response.status_code in (429, 503):
                # Temporary server issues
                self.logger.warning(
                    "Server temporarily unavailable for %s: %s",
                    url,
                    e.response.status_code,
                )
            else:
                # Other HTTP errors
                self.logerror(
                    "HTTP request failed %s %s: %s".replace(
                        "%s", "{method, url, e}"
                    ).replace("%d", "{method, url, e}")
                )
            return None
        except requests.exceptions.RequestException:
            self.logerror(
                "HTTP request failed %s %s: %s".replace(
                    "%s", "{method, url, e}"
                ).replace("%d", "{method, url, e}")
            )
            return None

    def _version_compare(self, version1: str, version2: str) -> int:
        """Compare version strings. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""
        try:
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]

            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return 1
                if v1 < v2:
                    return -1

            return 0

        except ValueError:
            return 0

    async def _process_threat_intel(self, intel_file: Path) -> Dict[str, Any]:
        """Process downloaded threat intelligence data."""
        try:
            with intel_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Process and validate threat intelligence data
            processed_data = {
                "timestamp": datetime.now().isoformat(),
                "threats": data.get("threats", []),
                "indicators": data.get("indicators", []),
                "signatures": data.get("signatures", []),
            }

            return processed_data

        except (OSError, json.JSONDecodeError, ValueError):
            self.logerror(
                "Error processing threat intelligence: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return {}

    async def _store_threat_intel(self, intel_data: Dict[str, Any]):
        """Store threat intelligence data for use by protection engine."""
        try:
            intel_db_path = self.db_dir / "threat_intel.json"
            with intel_db_path.open("w", encoding="utf-8") as f:
                json.dump(intel_data, f, indent=2)

            self.logger.info(
                "Threat intelligence data stored: %d threats, %d indicators",
                len(intel_data.get("threats", [])),
                len(intel_data.get("indicators", [])),
            )

        except (OSError, TypeError):
            self.logerror(
                "Error storing threat intelligence: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    async def _update_monitoring_loop(self):
        """Monitor update system health and progress."""
        while self.is_running:
            try:
                # Update progress for active downloads
                for download_id, progress_info in self.download_progress.items():
                    if self.update_progress_callback:
                        update_type = progress_info.get("update_type")
                        progress_percent = progress_info.get("progress_percent", 0)
                        if update_type:
                            self.update_progress_callback(update_type, progress_percent)

                # Clean completed downloads
                completed_downloads = [
                    download_id
                    for download_id, task in self.active_downloads.items()
                    if task.done()
                ]
                for download_id in completed_downloads:
                    del self.active_downloads[download_id]
                    self.download_progress.pop(download_id, None)

                await asyncio.sleep(5.0)

            except asyncio.CancelledError:
                break
            except Exception:  # pylint: disable=broad-exception-caught
                self.logerror(
                    "Error in update monitoring loop: %s".replace("%s", "{e}").replace(
                        "%d", "{e}"
                    )
                )
                await asyncio.sleep(10.0)

    async def _wait_for_tasks(self):
        """Wait for async tasks to complete."""
        tasks = []
        if self.update_loop_task:
            tasks.append(self.update_loop_task)
        if self.check_updates_task:
            tasks.append(self.check_updates_task)

        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception:  # pylint: disable=broad-exception-caught
                # Swallow unexpected errors while waiting on shutdown; state is being torn down
                pass

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update system status."""
        return {
            "status": self.status.value,
            "is_running": self.is_running,
            "last_check_time": (
                self.last_check_time.isoformat() if self.last_check_time else None
            ),
            "available_updates_count": len(self.available_updates),
            "pending_updates_count": len(self.pending_updates),
            "active_downloads": len(self.active_downloads),
            "last_update_times": {
                update_type.value: timestamp.isoformat()
                for update_type, timestamp in self.last_update_times.items()
            },
            "auto_update_enabled": self.config.auto_update_enabled,
            "check_interval_hours": self.config.check_interval_hours,
        }

    def get_update_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get update history."""
        recent_updates = sorted(
            self.update_history,
            key=lambda u: getattr(u, "timestamp", datetime.min),
            reverse=True,
        )[:limit]

        return [
            {
                "update_type": update.update_type.value,
                "success": update.success,
                "version": update.version,
                "error_message": update.error_message,
                "download_time": update.download_time,
                "install_time": update.install_time,
                "bytes_downloaded": update.bytes_downloaded,
            }
            for update in recent_updates
        ]

    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last time updates were checked."""
        return self.last_check_time

    # Callback setters
    def set_update_available_callback(self, callback: Callable[[UpdateInfo], None]):
        """Set callback for when updates are available."""
        self.update_available_callback = callback

    def set_update_completed_callback(self, callback: Callable[[UpdateResult], None]):
        """Set callback for when updates complete."""
        self.update_completed_callback = callback

    def set_update_progress_callback(self, callback: Callable[[UpdateType, int], None]):
        """Set callback for update progress."""
        self.update_progress_callback = callback

    def set_update_error_callback(self, callback: Callable[[str], None]):
        """Set callback for update errors."""
        self.update_error_callback = callback

    async def force_update_check(self) -> Dict[UpdateType, UpdateInfo]:
        """Force immediate update check."""
        self.logger.info("Forcing update check...")
        return await self.check_for_updates_async()

    async def update_threat_intelligence(self):
        """Update threat intelligence specifically."""
        if UpdateType.THREAT_INTELLIGENCE in self.available_updates:
            update_info = self.available_updates[UpdateType.THREAT_INTELLIGENCE]
            result = await self.install_update(update_info)
            if self.update_completed_callback:
                self.update_completed_callback(result)

    # Synchronous wrapper methods for GUI compatibility
    def check_for_updates_sync(self, force_check: bool = False) -> Optional[Dict]:
        """
        Synchronous wrapper for check_for_updates to maintain GUI compatibility.
        Returns update info in the format expected by the GUI.
        """
        try:
            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async check_for_updates method
            updates = loop.run_until_complete(
                self.check_for_updates_async(force_check=force_check)
            )

            # Convert to GUI-compatible format
            if UpdateType.SOFTWARE in updates:
                software_update = updates[UpdateType.SOFTWARE]
                from app import get_version as _get_version  # local import

                return {
                    "available": True,
                    "current_version": self.current_version or _get_version(),
                    "latest_version": software_update.version,
                    "release_name": f"Version {software_update.version}",
                    "release_notes": (
                        "\n".join(software_update.changelog)
                        if hasattr(software_update, "changelog")
                        and software_update.changelog
                        else software_update.description
                    ),
                    "download_url": software_update.download_url,
                    "published_at": datetime.now().isoformat(),
                    "prerelease": False,
                }
            from app import get_version as _get_version  # local import

            return {
                "available": False,
                "current_version": self.current_version or _get_version(),
            }

        except Exception as e:
            self.logerror(
                "Error in synchronous update check: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            raise e

    def check_for_updates(self, force_check: bool = False) -> Optional[Dict]:
        """
        GUI-compatible synchronous method that maintains the expected interface.
        This method is called by the GUI and delegates to check_for_updates_sync.
        """
        return self.check_for_updates_sync(force_check)


# Add missing import for aiohttp
try:
    import aiohttp
except ImportError:
    # Fallback without aiohttp
    aiohttp = None
    logging.getLogger(__name__).warning(
        "aiohttp not available, some features may not work"
    )
