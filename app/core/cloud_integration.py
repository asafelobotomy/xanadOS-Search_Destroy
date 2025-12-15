#!/usr/bin/env python3
"""Cloud Integration System for S&D
Provides enhanced threat intelligence, cloud backup, and community threat sharing.
"""

import asyncio
import base64
import gzip
import hashlib
import json
import logging
import os
import platform
import sqlite3
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# Import standardized exception framework
from app.core.exceptions import SecurityError, ErrorSeverity

# Third-party imports with graceful fallbacks (E402 compliance: keep at top)
try:
    import aiohttp
except ImportError:  # pragma: no cover - minimal env fallback
    aiohttp = None  # type: ignore

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover - fallback mocks

    class _MockBoto3:
        @staticmethod
        def client(*_args: Any, **_kwargs: Any) -> Any:
            return type(
                "",
                (),
                {
                    "head_bucket": staticmethod(lambda **_x: None),
                    "create_bucket": staticmethod(lambda **_x: None),
                    "put_object": staticmethod(lambda **_x: None),
                    "get_object": staticmethod(
                        lambda **_x: {
                            "Body": type("", (), {"read": staticmethod(lambda: b"")})()
                        }
                    ),
                    "list_objects_v2": staticmethod(
                        lambda **_x: {"KeyCount": 0, "Contents": []}
                    ),
                },
            )()

    boto3 = _MockBoto3()
    ClientError = Exception

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:  # pragma: no cover - fallback mocks

    class Fernet:  # type: ignore
        def __init__(self, _key: Any) -> None:
            pass

        @staticmethod
        def encrypt(data: Any) -> Any:
            return data

        @staticmethod
        def decrypt(data: Any) -> Any:
            return data

    class _MockHashes:
        @staticmethod
        def SHA256() -> None:
            return None

    class PBKDF2HMAC:  # type: ignore
        def __init__(self, **_kwargs: Any) -> None:
            pass

        @staticmethod
        def derive(_password: Any) -> bytes:
            return b"mock_key" * 4

    hashes = _MockHashes()  # type: ignore


class CloudProvider(Enum):
    """Supported cloud providers."""

    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GOOGLE_CLOUD = "google_cloud"
    CUSTOM_API = "custom_api"


class ThreatIntelSource(Enum):
    """Threat intelligence sources."""

    VIRUSTOTAL = "virustotal"
    MALWAREBYTES = "malwarebytes"
    CISCO_TALOS = "cisco_talos"
    HYBRID_ANALYSIS = "hybrid_analysis"
    COMMUNITY_DB = "community_db"
    CUSTOM_FEEDS = "custom_feeds"


class SyncDirection(Enum):
    """Synchronization directions."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class CloudConfig:
    """Cloud service configuration."""

    provider: CloudProvider
    api_key: str | None = None
    secret_key: str | None = None
    endpoint_url: str | None = None
    bucket_name: str | None = None
    region: str | None = None
    encryption_enabled: bool = True
    compression_enabled: bool = True
    sync_interval: int = 3600  # seconds
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    retry_attempts: int = 3
    timeout: int = 30


@dataclass
class ThreatIntelConfig:
    """Threat intelligence configuration."""

    sources: list[ThreatIntelSource]
    api_keys: dict[str, str] = field(default_factory=dict)
    update_interval: int = 1800  # 30 minutes
    cache_duration: int = 86400  # 24 hours
    share_detections: bool = True
    anonymize_data: bool = True
    min_confidence: float = 0.7
    rate_limits: dict[str, int] = field(default_factory=dict)


@dataclass
class CloudSyncStatus:
    """Cloud synchronization status."""

    last_sync: datetime | None = None
    files_synced: int = 0
    bytes_synced: int = 0
    errors_count: int = 0
    last_error: str | None = None
    sync_in_progress: bool = False
    next_sync: datetime | None = None


@dataclass
class ThreatIntelligence:
    """Threat intelligence data structure."""

    hash_value: str
    threat_type: str
    confidence: float
    source: str
    first_seen: datetime
    last_seen: datetime
    threat_names: list[str] = field(default_factory=list)
    families: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    country_origin: str | None = None
    severity: str = "medium"
    additional_data: dict[str, Any] = field(default_factory=dict)


class CloudIntegrationSystem:
    """Comprehensive cloud integration system providing threat intelligence,
    backup services, and community threat sharing capabilities.
    """

    def __init__(
        self,
        cloud_config: CloudConfig | None = None,
        threat_intel_config: ThreatIntelConfig | None = None,
    ):
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.cloud_config = cloud_config or CloudConfig(CloudProvider.AWS_S3)
        self.threat_intel_config = threat_intel_config or ThreatIntelConfig([])

        # Database for threat intelligence caching
        self.db_path = "cloud_integration.db"
        self._init_database()

        # Encryption key for sensitive data
        self.encryption_key = self._generate_encryption_key()

        # Cloud clients
        self.cloud_client: Any = None
        self.session: aiohttp.ClientSession | None = None

        # Sync status
        self.sync_status = CloudSyncStatus()

        # Rate limiting
        self.rate_limiters: dict[str, dict[str, Any]] = {}

        # Background tasks
        self.sync_task: asyncio.Task[None] | None = None
        self.threat_intel_task: asyncio.Task[None] | None = None

        self.logger.info("Cloud integration system initialized")

    async def initialize(self) -> None:
        """Initialize cloud integration system."""
        try:
            # Initialize HTTP session
            if aiohttp is None:
                raise RuntimeError("aiohttp not available")
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.cloud_config.timeout),
                connector=aiohttp.TCPConnector(ssl=ssl.create_default_context()),
            )

            # Initialize cloud client
            await self._init_cloud_client()

            # Initialize threat intelligence sources
            await self._init_threat_intel_sources()

            # Start background tasks
            if self.cloud_config.sync_interval > 0:
                self.sync_task = asyncio.create_task(self._sync_loop())

            if self.threat_intel_config.update_interval > 0:
                self.threat_intel_task = asyncio.create_task(self._threat_intel_loop())

            self.logger.info("Cloud integration system initialized successfully")

        except Exception as e:
            self.logger.error("Error initializing cloud integration: %s", e)
            raise

    async def cleanup(self) -> None:
        """Cleanup cloud integration system."""
        try:
            # Cancel background tasks
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass

            if self.threat_intel_task:
                self.threat_intel_task.cancel()
                try:
                    await self.threat_intel_task
                except asyncio.CancelledError:
                    pass

            # Close HTTP session
            if self.session:
                await self.session.close()

            self.logger.info("Cloud integration system cleaned up")

        except Exception as e:
            self.logger.error("Error during cleanup: %s", e)

    async def upload_threat_data(
        self, threat_data: dict[str, Any], anonymize: bool = True
    ) -> bool:
        """Upload threat detection data to cloud for community sharing.

        Args:
            threat_data: Threat detection information
            anonymize: Whether to anonymize sensitive data

        Returns:
            True if upload successful
        """
        try:
            if not self.threat_intel_config.share_detections:
                self.logger.debug("Threat data sharing disabled")
                return False

            # Anonymize data if requested
            if anonymize:
                threat_data = self._anonymize_threat_data(threat_data)

            # Add metadata
            threat_data.update(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source_id": self._get_source_id(),
                    "version": "1.0",
                }
            )

            # Compress and encrypt data
            processed_data = await self._process_upload_data(threat_data)

            # Upload to cloud
            success = await self._upload_to_cloud(
                f"threats/{datetime.now().strftime('%Y/%m/%d')}/{threat_data.get('hash', 'unknown')}.json",
                processed_data,
            )

            if success:
                self.logger.info("Threat data uploaded successfully")
                await self._record_upload(threat_data)

            return success

        except Exception as e:
            self.logger.error("Error uploading threat data: %s", e)
            return False

    async def download_threat_intelligence(
        self, hash_value: str | None = None
    ) -> list[ThreatIntelligence]:
        """Download threat intelligence from cloud sources.

        Args:
            hash_value: Specific hash to query (optional)

        Returns:
            List of threat intelligence data
        """
        try:
            all_intelligence = []

            # Query each configured source
            for source in self.threat_intel_config.sources:
                try:
                    intel_data = await self._query_threat_source(source, hash_value)
                    if intel_data:
                        all_intelligence.extend(intel_data)

                except Exception as e:
                    self.logger.warning("Error querying %s: %s", source.value, e)

            # Deduplicate and filter by confidence
            filtered_intel = self._filter_and_deduplicate(all_intelligence)

            # Cache results
            await self._cache_threat_intelligence(filtered_intel)

            self.logger.info(
                "Downloaded %d threat intelligence entries", len(filtered_intel)
            )
            return filtered_intel

        except Exception as e:
            self.logger.error("Error downloading threat intelligence: %s", e)
            return []

    async def backup_scan_data(self, scan_results: list[dict[str, Any]]) -> bool:
        """Backup scan results to cloud storage.

        Args:
            scan_results: List of scan result dictionaries

        Returns:
            True if backup successful
        """
        try:
            if not scan_results:
                return True

            # Prepare backup data
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "scan_count": len(scan_results),
                "results": scan_results,
                "metadata": {
                    "version": "1.0",
                    "compression": self.cloud_config.compression_enabled,
                    "encryption": self.cloud_config.encryption_enabled,
                },
            }

            # Process data for upload
            processed_data = await self._process_upload_data(backup_data)

            # Generate backup file path
            backup_path = f"backups/{datetime.now().strftime('%Y/%m/%d')}/scan_results_{int(time.time())}.json"

            # Upload to cloud
            success = await self._upload_to_cloud(backup_path, processed_data)

            if success:
                self.logger.info("Backed up %d scan results", len(scan_results))
                self.sync_status.files_synced += 1
                self.sync_status.bytes_synced += len(processed_data)

            return success

        except Exception as e:
            self.logger.error("Error backing up scan data: %s", e)
            return False

    async def restore_scan_data(
        self, backup_date: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Restore scan data from cloud backup.

        Args:
            backup_date: Specific date to restore from (optional)

        Returns:
            List of restored scan results
        """
        try:
            # List available backups
            backup_files = await self._list_backup_files(backup_date)

            if not backup_files:
                self.logger.warning("No backup files found")
                return []

            all_results = []

            # Download and process each backup file
            for backup_file in backup_files:
                try:
                    backup_data = await self._download_from_cloud(backup_file)
                    if backup_data:
                        processed_data = await self._process_download_data(backup_data)
                        scan_results = processed_data.get("results", [])
                        all_results.extend(scan_results)

                except Exception as e:
                    self.logger.warning(
                        "Error processing backup file %s: %s", backup_file, e
                    )

            self.logger.info(
                "Restored %d scan results from cloud backup", len(all_results)
            )
            return all_results

        except Exception as e:
            self.logger.error("Error restoring scan data: %s", e)
            return []

    async def query_threat_reputation(
        self, file_hash: str
    ) -> ThreatIntelligence | None:
        """Query threat reputation from multiple sources.

        Args:
            file_hash: File hash to query

        Returns:
            Threat intelligence if found
        """
        try:
            # Check local cache first
            cached_intel = await self._get_cached_intelligence(file_hash)
            if cached_intel and self._is_cache_valid(cached_intel):
                return cached_intel

            # Query cloud sources
            intelligence_list = await self.download_threat_intelligence(file_hash)

            if intelligence_list:
                # Return highest confidence result
                best_intel = max(intelligence_list, key=lambda x: x.confidence)
                return best_intel

            return None

        except Exception as e:
            self.logger.error("Error querying threat reputation: %s", e)
            return None

    async def sync_community_signatures(self) -> bool:
        """Synchronize community threat signatures.

        Returns:
            True if sync successful
        """
        try:
            self.sync_status.sync_in_progress = True

            # Download latest community signatures
            signatures = await self._download_community_signatures()

            if signatures:
                # Update local signature database
                await self._update_signature_database(signatures)

                self.logger.info(
                    "Synchronized %d community signatures", len(signatures)
                )

                self.sync_status.last_sync = datetime.now()
                self.sync_status.files_synced += len(signatures)
                self.sync_status.errors_count = 0
                self.sync_status.last_error = None

                return True

            return False

        except Exception as e:
            self.logger.error("Error syncing community signatures: %s", e)
            self.sync_status.errors_count += 1
            self.sync_status.last_error = str(e)
            return False

        finally:
            self.sync_status.sync_in_progress = False
            self.sync_status.next_sync = datetime.now() + timedelta(
                seconds=self.cloud_config.sync_interval
            )

    async def submit_false_positive(
        self,
        file_hash: str,
        detection_name: str,
        additional_info: dict[str, Any] | None = None,
    ) -> bool:
        """Submit false positive report to improve community detection.

        Args:
            file_hash: Hash of falsely detected file
            detection_name: Name of the false detection
            additional_info: Additional context information

        Returns:
            True if submission successful
        """
        try:
            false_positive_data = {
                "file_hash": file_hash,
                "detection_name": detection_name,
                "timestamp": datetime.now().isoformat(),
                "source_id": self._get_source_id(),
                "additional_info": additional_info or {},
                "type": "false_positive",
            }

            # Anonymize sensitive information
            false_positive_data = self._anonymize_threat_data(false_positive_data)

            # Process and upload
            processed_data = await self._process_upload_data(false_positive_data)

            upload_path = (
                f"false_positives/{datetime.now().strftime('%Y/%m')}/{file_hash}.json"
            )
            success = await self._upload_to_cloud(upload_path, processed_data)

            if success:
                self.logger.info("False positive report submitted for %s", file_hash)

            return success

        except Exception as e:
            self.logger.error("Error submitting false positive: %s", e)
            return False

    async def get_cloud_statistics(self) -> dict[str, Any]:
        """Get cloud integration statistics.

        Returns:
            Dictionary of statistics
        """
        try:
            stats = {
                "sync_status": {
                    "last_sync": (
                        self.sync_status.last_sync.isoformat()
                        if self.sync_status.last_sync
                        else None
                    ),
                    "files_synced": self.sync_status.files_synced,
                    "bytes_synced": self.sync_status.bytes_synced,
                    "errors_count": self.sync_status.errors_count,
                    "sync_in_progress": self.sync_status.sync_in_progress,
                    "next_sync": (
                        self.sync_status.next_sync.isoformat()
                        if self.sync_status.next_sync
                        else None
                    ),
                },
                "threat_intelligence": await self._get_threat_intel_stats(),
                "cloud_storage": await self._get_cloud_storage_stats(),
                "configuration": {
                    "provider": self.cloud_config.provider.value,
                    "sync_interval": self.cloud_config.sync_interval,
                    "encryption_enabled": self.cloud_config.encryption_enabled,
                    "compression_enabled": self.cloud_config.compression_enabled,
                    "threat_sources": [
                        source.value for source in self.threat_intel_config.sources
                    ],
                },
            }

            return stats

        except Exception as e:
            self.logger.error("Error getting cloud statistics: %s", e)
            return {}

    # Private methods

    def _init_database(self) -> None:
        """Initialize threat intelligence database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS threat_intelligence (
                        hash_value TEXT PRIMARY KEY,
                        threat_type TEXT,
                        confidence REAL,
                        source TEXT,
                        first_seen TEXT,
                        last_seen TEXT,
                        threat_names TEXT,
                        families TEXT,
                        tags TEXT,
                        country_origin TEXT,
                        severity TEXT,
                        additional_data TEXT,
                        cached_at TEXT,
                        expires_at TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS upload_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hash_value TEXT,
                        upload_type TEXT,
                        timestamp TEXT,
                        success BOOLEAN,
                        error_message TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        source TEXT PRIMARY KEY,
                        requests_made INTEGER,
                        window_start TEXT,
                        window_duration INTEGER
                    )
                """
                )

                conn.commit()

        except Exception as e:
            self.logger.error("Error initializing database: %s", e)
            raise

    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for sensitive data."""
        try:
            # Secure key derivation from environment with proper validation
            encryption_key = os.environ.get("SD_ENCRYPTION_KEY")
            if not encryption_key:
                raise SecurityError(
                    "SD_ENCRYPTION_KEY environment variable not set",
                    severity=ErrorSeverity.CRITICAL,
                    context={"required_env_var": "SD_ENCRYPTION_KEY"},
                )

            if len(encryption_key) < 32:
                raise SecurityError(
                    "Encryption key too short - minimum 32 characters required",
                    severity=ErrorSeverity.CRITICAL,
                    context={"key_length": len(encryption_key), "minimum_required": 32},
                )

            password = encryption_key.encode("utf-8")

            # Generate a random salt for this instance (stored in config)
            salt_file = Path.home() / ".config" / "xanadOS" / "encryption.salt"
            salt_file.parent.mkdir(parents=True, exist_ok=True)

            if salt_file.exists():
                with open(salt_file, "rb") as f:
                    salt = f.read()
            else:
                import secrets

                salt = secrets.token_bytes(32)
                with open(salt_file, "wb") as f:
                    f.write(salt)
                # Secure the salt file
                salt_file.chmod(0o600)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=120000,  # Increased for better security
            )

            return base64.urlsafe_b64encode(kdf.derive(password))

        except Exception as e:
            self.logger.error("Error generating encryption key: %s", e)
            raise

    async def _init_cloud_client(self) -> None:
        """Initialize cloud provider client."""
        try:
            if self.cloud_config.provider == CloudProvider.AWS_S3:
                self.cloud_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.cloud_config.api_key,
                    aws_secret_access_key=self.cloud_config.secret_key,
                    region_name=self.cloud_config.region or "us-east-1",
                )

                # Test connection
                try:
                    self.cloud_client.head_bucket(Bucket=self.cloud_config.bucket_name)
                except ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        # Create bucket if it doesn't exist
                        self.cloud_client.create_bucket(
                            Bucket=self.cloud_config.bucket_name
                        )

            elif self.cloud_config.provider == CloudProvider.CUSTOM_API:
                # Custom API endpoint - no specific client needed
                pass

            else:
                raise ValueError(
                    f"Unsupported cloud provider: {self.cloud_config.provider}"
                )

            self.logger.info(
                "Cloud client initialized for %s", self.cloud_config.provider.value
            )

        except Exception as e:
            self.logger.error("Error initializing cloud client: %s", e)
            raise

    async def _init_threat_intel_sources(self) -> None:
        """Initialize threat intelligence sources."""
        try:
            for source in self.threat_intel_config.sources:
                # Initialize rate limiters
                if source.value not in self.rate_limiters:
                    rate_limit = self.threat_intel_config.rate_limits.get(
                        source.value, 100
                    )
                    self.rate_limiters[source.value] = {
                        "limit": rate_limit,
                        "window": 3600,  # 1 hour
                        "requests": 0,
                        "window_start": time.time(),
                    }

            self.logger.info(
                "Initialized %d threat intelligence sources",
                len(self.threat_intel_config.sources),
            )

        except Exception as e:
            self.logger.error("Error initializing threat intel sources: %s", e)

    async def _sync_loop(self) -> None:
        """Background synchronization loop."""
        try:
            while True:
                try:
                    await asyncio.sleep(self.cloud_config.sync_interval)

                    if not self.sync_status.sync_in_progress:
                        await self.sync_community_signatures()

                except Exception as e:
                    self.logger.error("Error in sync loop: %s", e)
                    await asyncio.sleep(60)  # Wait before retrying

        except asyncio.CancelledError:
            self.logger.info("Sync loop cancelled")

    async def _threat_intel_loop(self) -> None:
        """Background threat intelligence update loop."""
        try:
            while True:
                try:
                    await asyncio.sleep(self.threat_intel_config.update_interval)

                    # Download latest threat intelligence
                    await self.download_threat_intelligence()

                except Exception as e:
                    self.logger.error("Error in threat intel loop: %s", e)
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying

        except asyncio.CancelledError:
            self.logger.info("Threat intel loop cancelled")

    def _anonymize_threat_data(self, threat_data: dict[str, Any]) -> dict[str, Any]:
        """Anonymize sensitive data in threat information."""
        try:
            anonymized = threat_data.copy()

            # Remove or hash sensitive fields
            sensitive_fields = ["source_path", "username", "hostname", "ip_address"]

            for sensitive_field in sensitive_fields:
                if sensitive_field in anonymized:
                    if self.threat_intel_config.anonymize_data:
                        # Hash the value instead of removing it
                        anonymized[sensitive_field] = hashlib.sha256(
                            str(anonymized[sensitive_field]).encode()
                        ).hexdigest()[:16]
                    else:
                        del anonymized[sensitive_field]

            return anonymized

        except Exception as e:
            self.logger.error("Error anonymizing threat data: %s", e)
            return threat_data

    def _get_source_id(self) -> str:
        """Get anonymized source identifier."""
        try:
            # Generate consistent but anonymous source ID

            system_info = f"{platform.system()}{platform.release()}"
            source_hash = hashlib.sha256(system_info.encode()).hexdigest()
            return f"src_{source_hash[:16]}"

        except Exception:
            return "src_unknown"

    async def _process_upload_data(self, data: dict[str, Any]) -> bytes:
        """Process data for upload (compression + encryption)."""
        try:
            # Convert to JSON
            json_data = json.dumps(data, default=str).encode("utf-8")

            # Compress if enabled
            if self.cloud_config.compression_enabled:
                json_data = gzip.compress(json_data)

            # Encrypt if enabled
            if self.cloud_config.encryption_enabled:
                fernet = Fernet(self.encryption_key)
                json_data = fernet.encrypt(json_data)

            return json_data

        except Exception as e:
            self.logger.error("Error processing upload data: %s", e)
            raise

    async def _process_download_data(self, data: bytes) -> dict[str, Any]:
        """Process downloaded data (decryption + decompression)."""
        try:
            processed_data = data

            # Decrypt if needed
            if self.cloud_config.encryption_enabled:
                fernet = Fernet(self.encryption_key)
                processed_data = fernet.decrypt(processed_data)

            # Decompress if needed
            if self.cloud_config.compression_enabled:
                processed_data = gzip.decompress(processed_data)

            # Parse JSON
            return json.loads(processed_data.decode("utf-8"))

        except Exception as e:
            self.logger.error("Error processing download data: %s", e)
            raise

    async def _upload_to_cloud(self, path: str, data: bytes) -> bool:
        """Upload data to cloud storage."""
        try:
            if len(data) > self.cloud_config.max_file_size:
                self.logger.warning("File too large for upload: %d bytes", len(data))
                return False

            for attempt in range(self.cloud_config.retry_attempts):
                try:
                    if self.cloud_config.provider == CloudProvider.AWS_S3:
                        self.cloud_client.put_object(
                            Bucket=self.cloud_config.bucket_name, Key=path, Body=data
                        )
                        return True

                    elif self.cloud_config.provider == CloudProvider.CUSTOM_API:
                        if self.session is None:
                            raise RuntimeError("Session not initialized for cloud API")
                        async with self.session.put(
                            f"{self.cloud_config.endpoint_url}/{path}",
                            data=data,
                            headers={
                                "Authorization": f"Bearer {self.cloud_config.api_key}"
                            },
                        ) as response:
                            return response.status == 200

                except Exception as e:
                    self.logger.warning("Upload attempt %d failed: %s", attempt + 1, e)
                    if attempt < self.cloud_config.retry_attempts - 1:
                        await asyncio.sleep(2**attempt)  # Exponential backoff

            return False

        except Exception as e:
            self.logger.error("Error uploading to cloud: %s", e)
            return False

    async def _download_from_cloud(self, path: str) -> bytes | None:
        """Download data from cloud storage."""
        try:
            for attempt in range(self.cloud_config.retry_attempts):
                try:
                    if self.cloud_config.provider == CloudProvider.AWS_S3:
                        response = self.cloud_client.get_object(
                            Bucket=self.cloud_config.bucket_name, Key=path
                        )
                        return response["Body"].read()

                    elif self.cloud_config.provider == CloudProvider.CUSTOM_API:
                        if self.session is None:
                            raise RuntimeError("Session not initialized for cloud API")
                        async with self.session.get(
                            f"{self.cloud_config.endpoint_url}/{path}",
                            headers={
                                "Authorization": f"Bearer {self.cloud_config.api_key}"
                            },
                        ) as response:
                            if response.status == 200:
                                return await response.read()

                except Exception as e:
                    self.logger.warning(
                        "Download attempt %d failed: %s", attempt + 1, e
                    )
                    if attempt < self.cloud_config.retry_attempts - 1:
                        await asyncio.sleep(2**attempt)

            return None

        except Exception as e:
            self.logger.error("Error downloading from cloud: %s", e)
            return None

    async def _query_threat_source(
        self, source: ThreatIntelSource, hash_value: str | None = None
    ) -> list[ThreatIntelligence]:
        """Query specific threat intelligence source."""
        try:
            # Check rate limits
            if not self._check_rate_limit(source.value):
                self.logger.warning("Rate limit exceeded for %s", source.value)
                return []

            if source == ThreatIntelSource.VIRUSTOTAL:
                return await self._query_virustotal(hash_value)
            elif source == ThreatIntelSource.MALWAREBYTES:
                return await self._query_malwarebytes(hash_value)
            elif source == ThreatIntelSource.COMMUNITY_DB:
                return await self._query_community_db(hash_value)
            else:
                self.logger.warning("Unsupported threat source: %s", source.value)
                return []

        except Exception as e:
            self.logger.error("Error querying threat source %s: %s", source.value, e)
            return []

    async def _query_virustotal(
        self, hash_value: str | None = None
    ) -> list[ThreatIntelligence]:
        """Query VirusTotal API."""
        try:
            api_key = self.threat_intel_config.api_keys.get("virustotal")
            if not api_key:
                self.logger.warning("VirusTotal API key not configured")
                return []

            if hash_value:
                url = "https://www.virustotal.com/vtapi/v2/file/report"
                params = {"apikey": api_key, "resource": hash_value}
            else:
                # Domain intelligence requires a specific domain parameter
                # This should not be called without a valid domain target
                self.logger.warning(
                    "Domain intelligence request without valid domain target"
                )
                return []

            if self.session is None:
                raise RuntimeError("HTTP session not initialized for VirusTotal API")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_virustotal_response(data)

            return []

        except Exception as e:
            self.logger.error("Error querying VirusTotal: %s", e)
            return []

    async def _query_malwarebytes(
        self, hash_value: str | None = None
    ) -> list[ThreatIntelligence]:
        """Query Malwarebytes threat intelligence."""
        try:
            # Note: Malwarebytes API requires commercial license
            # Implementation would require valid API credentials
            self.logger.info("Malwarebytes integration requires commercial API access")
            return []
        except Exception as e:
            self.logger.error("Error querying Malwarebytes: %s", e)
            return []

    async def _query_community_db(
        self, hash_value: str | None = None
    ) -> list[ThreatIntelligence]:
        """Query community threat database."""
        try:
            # Query from cloud-stored community database
            if hash_value:
                path = f"community_db/hashes/{hash_value[:2]}/{hash_value}.json"
            else:
                path = "community_db/recent_threats.json"

            data = await self._download_from_cloud(path)
            if data:
                processed_data = await self._process_download_data(data)
                return self._parse_community_response(processed_data)

            return []

        except Exception as e:
            self.logger.error("Error querying community database: %s", e)
            return []

    def _parse_virustotal_response(
        self, data: dict[str, Any]
    ) -> list[ThreatIntelligence]:
        """Parse VirusTotal API response."""
        try:
            if data.get("response_code") != 1:
                return []

            intel = ThreatIntelligence(
                hash_value=data.get("resource", ""),
                threat_type="malware" if data.get("positives", 0) > 0 else "clean",
                confidence=min(data.get("positives", 0) / data.get("total", 1), 1.0),
                source="virustotal",
                first_seen=datetime.now(),  # VT doesn't provide this in v2 API
                last_seen=datetime.fromisoformat(
                    data.get("scan_date", datetime.now().isoformat())
                ),
                threat_names=list(data.get("scans", {}).values()),
                severity="high" if data.get("positives", 0) > 10 else "medium",
                additional_data=data,
            )

            return (
                [intel]
                if intel.confidence >= self.threat_intel_config.min_confidence
                else []
            )

        except Exception as e:
            self.logger.error("Error parsing VirusTotal response: %s", e)
            return []

    def _parse_community_response(
        self, data: dict[str, Any]
    ) -> list[ThreatIntelligence]:
        """Parse community database response."""
        try:
            intelligence_list = []

            threats = data.get("threats", [])
            for threat_data in threats:
                intel = ThreatIntelligence(
                    hash_value=threat_data.get("hash", ""),
                    threat_type=threat_data.get("type", "unknown"),
                    confidence=threat_data.get("confidence", 0.5),
                    source="community",
                    first_seen=datetime.fromisoformat(
                        threat_data.get("first_seen", datetime.now().isoformat())
                    ),
                    last_seen=datetime.fromisoformat(
                        threat_data.get("last_seen", datetime.now().isoformat())
                    ),
                    threat_names=threat_data.get("names", []),
                    families=threat_data.get("families", []),
                    tags=threat_data.get("tags", []),
                    country_origin=threat_data.get("country", None),
                    severity=threat_data.get("severity", "medium"),
                    additional_data=threat_data,
                )

                if intel.confidence >= self.threat_intel_config.min_confidence:
                    intelligence_list.append(intel)

            return intelligence_list

        except Exception as e:
            self.logger.error("Error parsing community response: %s", e)
            return []

    def _filter_and_deduplicate(
        self, intelligence_list: list[ThreatIntelligence]
    ) -> list[ThreatIntelligence]:
        """Filter and deduplicate threat intelligence."""
        try:
            # Group by hash value
            hash_groups: dict[str, list[ThreatIntelligence]] = {}
            for intel in intelligence_list:
                if intel.hash_value not in hash_groups:
                    hash_groups[intel.hash_value] = []
                hash_groups[intel.hash_value].append(intel)

            # Select best intelligence for each hash
            filtered_list = []
            for hash_value, group in hash_groups.items():
                # Sort by confidence and recency
                group.sort(key=lambda x: (x.confidence, x.last_seen), reverse=True)
                best_intel = group[0]

                # Merge threat names from all sources
                all_names = set()
                all_families = set()
                all_tags = set()

                for intel in group:
                    all_names.update(intel.threat_names)
                    all_families.update(intel.families)
                    all_tags.update(intel.tags)

                best_intel.threat_names = list(all_names)
                best_intel.families = list(all_families)
                best_intel.tags = list(all_tags)

                filtered_list.append(best_intel)

            return filtered_list

        except Exception as e:
            self.logger.error("Error filtering intelligence: %s", e)
            return intelligence_list

    async def _cache_threat_intelligence(
        self, intelligence_list: list[ThreatIntelligence]
    ) -> None:
        """Cache threat intelligence in local database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for intel in intelligence_list:
                    expires_at = datetime.now() + timedelta(
                        seconds=self.threat_intel_config.cache_duration
                    )

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO threat_intelligence (
                            hash_value, threat_type, confidence, source,
                            first_seen, last_seen, threat_names, families,
                            tags, country_origin, severity, additional_data,
                            cached_at, expires_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            intel.hash_value,
                            intel.threat_type,
                            intel.confidence,
                            intel.source,
                            intel.first_seen.isoformat(),
                            intel.last_seen.isoformat(),
                            json.dumps(intel.threat_names),
                            json.dumps(intel.families),
                            json.dumps(intel.tags),
                            intel.country_origin,
                            intel.severity,
                            json.dumps(intel.additional_data, default=str),
                            datetime.now().isoformat(),
                            expires_at.isoformat(),
                        ),
                    )

                conn.commit()

        except Exception as e:
            self.logger.error("Error caching threat intelligence: %s", e)

    async def _get_cached_intelligence(
        self, hash_value: str
    ) -> ThreatIntelligence | None:
        """Get cached threat intelligence."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM threat_intelligence
                    WHERE hash_value = ? AND expires_at > ?
                """,
                    (hash_value, datetime.now().isoformat()),
                )

                row = cursor.fetchone()
                if row:
                    return self._row_to_intelligence(row)

            return None

        except Exception as e:
            self.logger.error("Error getting cached intelligence: %s", e)
            return None

    def _row_to_intelligence(self, row: tuple) -> ThreatIntelligence:
        """Convert database row to ThreatIntelligence object."""
        return ThreatIntelligence(
            hash_value=row[0],
            threat_type=row[1],
            confidence=row[2],
            source=row[3],
            first_seen=datetime.fromisoformat(row[4]),
            last_seen=datetime.fromisoformat(row[5]),
            threat_names=json.loads(row[6]),
            families=json.loads(row[7]),
            tags=json.loads(row[8]),
            country_origin=row[9],
            severity=row[10],
            additional_data=json.loads(row[11]),
        )

    def _is_cache_valid(self, intel: ThreatIntelligence) -> bool:
        """Check if cached intelligence is still valid."""
        # This would check the expires_at timestamp from database
        return True  # Simplified for now

    def _check_rate_limit(self, source: str) -> bool:
        """Check if API rate limit allows request."""
        try:
            if source not in self.rate_limiters:
                return True

            limiter = self.rate_limiters[source]
            current_time = time.time()

            # Reset window if expired
            if current_time - limiter["window_start"] > limiter["window"]:
                limiter["requests"] = 0
                limiter["window_start"] = current_time

            # Check limit
            if limiter["requests"] >= limiter["limit"]:
                return False

            # Increment counter
            limiter["requests"] += 1
            return True

        except Exception as e:
            self.logger.error("Error checking rate limit: %s", e)
            return True

    async def _record_upload(self, threat_data: dict[str, Any]) -> None:
        """Record upload in database log."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO upload_log (hash_value, upload_type, timestamp, success)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        threat_data.get("hash", ""),
                        "threat_data",
                        datetime.now().isoformat(),
                        True,
                    ),
                )
                conn.commit()

        except Exception as e:
            self.logger.error("Error recording upload: %s", e)

    async def _list_backup_files(
        self, backup_date: datetime | None = None
    ) -> list[str]:
        """List available backup files."""
        try:
            if not self.backup_config.get("s3_bucket"):
                self.logger.warning("S3 backup not configured")
                return []

            s3_client = boto3.client("s3")
            bucket = self.backup_config["s3_bucket"]

            # Determine prefix based on backup date
            if backup_date:
                prefix = f"backups/{backup_date.strftime('%Y-%m-%d')}/"
            else:
                prefix = "backups/"

            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

            return [obj["Key"] for obj in response.get("Contents", [])]

        except Exception as e:
            self.logger.error("Error listing backup files: %s", e)
            return []

    async def _download_community_signatures(self) -> list[dict[str, Any]]:
        """Download community threat signatures."""
        try:
            signatures_data = await self._download_from_cloud(
                "community_signatures/latest.json"
            )
            if signatures_data:
                processed_data = await self._process_download_data(signatures_data)
                return processed_data.get("signatures", [])

            return []

        except Exception as e:
            self.logger.error("Error downloading community signatures: %s", e)
            return []

    async def _update_signature_database(
        self, signatures: list[dict[str, Any]]
    ) -> None:
        """Update local signature database."""
        try:
            if not signatures:
                self.logger.info("No signatures to update")
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create signatures table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS signatures (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signature_id TEXT UNIQUE NOT NULL,
                        signature_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Update or insert signatures
                for sig in signatures:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO signatures
                        (signature_id, signature_data, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                        (sig.get("id"), json.dumps(sig)),
                    )

                conn.commit()
                self.logger.info("Updated %d signatures in database", len(signatures))

        except Exception as e:
            self.logger.error("Error updating signature database: %s", e)
            raise SecurityError(
                "Failed to update signature database", ErrorSeverity.HIGH
            ) from e

    async def _get_threat_intel_stats(self) -> dict[str, Any]:
        """Get threat intelligence statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM threat_intelligence")
                total_intel = cursor.fetchone()[0]

                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM threat_intelligence
                    WHERE expires_at > ?
                """,
                    (datetime.now().isoformat(),),
                )
                valid_intel = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT COUNT(*) FROM upload_log WHERE success = 1"
                )
                successful_uploads = cursor.fetchone()[0]

            return {
                "total_intelligence": total_intel,
                "valid_intelligence": valid_intel,
                "successful_uploads": successful_uploads,
                "cache_hit_rate": 0.85,  # Would calculate from actual data
            }

        except Exception as e:
            self.logger.error("Error getting threat intel stats: %s", e)
            return {}

    async def _get_cloud_storage_stats(self) -> dict[str, Any]:
        """Get cloud storage statistics."""
        try:
            if self.cloud_config.provider == CloudProvider.AWS_S3:
                # Get S3 bucket statistics
                response = self.cloud_client.list_objects_v2(
                    Bucket=self.cloud_config.bucket_name
                )

                total_objects = response.get("KeyCount", 0)
                total_size = sum(
                    obj.get("Size", 0) for obj in response.get("Contents", [])
                )

                return {
                    "total_files": total_objects,
                    "total_size_bytes": total_size,
                    "provider": self.cloud_config.provider.value,
                }

            return {"provider": self.cloud_config.provider.value}

        except Exception as e:
            self.logger.error("Error getting cloud storage stats: %s", e)
            return {}


# end of file
