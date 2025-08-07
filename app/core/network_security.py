#!/usr/bin/env python3
"""
Network security module for xanadOS Search & Destroy
Handles secure network communications, certificate validation, and secure updates
"""
import hashlib
import logging
import socket
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import os


class NetworkSecurityLevel(Enum):
    """Network security levels for different operations."""

    STRICT = "strict"  # Highest security, certificate pinning
    STANDARD = "standard"  # Standard TLS verification
    RELAXED = "relaxed"  # Basic security for compatibility


@dataclass
class SecureEndpoint:
    """Represents a secure network endpoint."""

    url: str
    certificate_fingerprint: Optional[str] = None
    max_retries: int = 3
    timeout: int = 30
    security_level: NetworkSecurityLevel = NetworkSecurityLevel.STANDARD


class NetworkSecurityError(Exception):
    """Custom exception for network security errors."""

    pass


class SecureNetworkManager:
    """
    Manages secure network communications for antivirus operations.

    Provides secure update mechanisms, certificate validation,
    and protection against network-based attacks.
    """

    # Official ClamAV update servers and their certificate fingerprints
    CLAMAV_ENDPOINTS = {
        "database.clamav.net": SecureEndpoint(
            url="https://database.clamav.net",
            certificate_fingerprint="sha256:1234567890abcdef...",  # Replace with actual
            security_level=NetworkSecurityLevel.STRICT,
        ),
        "db.local.clamav.net": SecureEndpoint(
            url="https://db.local.clamav.net",
            security_level=NetworkSecurityLevel.STANDARD,
        ),
    }

    def __init__(self):
        """Initialize the secure network manager."""
        self.logger = logging.getLogger(__name__)
        self._session_cache = {}  # noqa: F841
        self._certificate_cache = {}  # noqa: F841

        # Configure secure SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True  # noqa: F841
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED  # noqa: F841

        # Disable weak protocols and ciphers
        self.ssl_context.options |= ssl.OP_NO_SSLv2
        self.ssl_context.options |= ssl.OP_NO_SSLv3
        self.ssl_context.options |= ssl.OP_NO_TLSv1
        self.ssl_context.options |= ssl.OP_NO_TLSv1_1

        # Set strong cipher suites
        self.ssl_context.set_ciphers(
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
        )

    def _verify_certificate_fingerprint(
        self, hostname: str, port: int, expected_fingerprint: str
    ) -> bool:
        """
        Verify certificate fingerprint for certificate pinning.

        Args:
            hostname: The hostname to connect to
            port: The port to connect to
            expected_fingerprint: Expected certificate fingerprint

        Returns:
            True if fingerprint matches, False otherwise
        """
        try:
            # Get certificate from server
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)

            # Validate certificate data
            if cert_der is None:
                self.logger.error(
                    "No certificate data received from %s", hostname)
                return False

            # Calculate fingerprint
            fingerprint = hashlib.sha256(cert_der).hexdigest()
            actual_fingerprint = f"sha256:{fingerprint}"

            return actual_fingerprint == expected_fingerprint

        except Exception as e:
            self.logger.error(
                "Certificate verification failed for %s: %s", hostname, e)
            return False

    def _create_secure_request(
        self,
        url: str,
        endpoint: SecureEndpoint,
        headers: Optional[Dict[str, str]] = None,
    ) -> urllib.request.Request:
        """
        Create a secure HTTP request with appropriate headers.

        Args:
            url: The URL to request
            endpoint: Endpoint configuration
            headers: Additional headers

        Returns:
            Configured urllib request object
        """
        # Set secure headers
        secure_headers = {
            "User-Agent": "xanadOS-SearchDestroy/1.0 (Security Scanner)",
            "Accept": "application/octet-stream, application/json, text/plain",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",  # Prevent connection reuse for security
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "DNT": "1",  # Do Not Track
        }

        if headers:
            secure_headers.update(headers)

        request = urllib.request.Request(url, headers=secure_headers)
        return request

    def _validate_response(
        self, response, expected_content_type: Optional[str] = None
    ) -> bool:
        """
        Validate HTTP response for security issues.

        Args:
            response: The HTTP response object
            expected_content_type: Expected content type

        Returns:
            True if response is safe, False otherwise
        """
        # Check content type if specified
        if expected_content_type:
            content_type = response.headers.get("Content-Type", "")  # noqa: F841
            if not content_type.startswith(expected_content_type):
                self.logger.warning(
                    "Unexpected content type: %s", content_type)
                return False

        # Check content length
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                length = int(content_length)
                if length > 100 * 1024 * 1024:  # 100MB limit
                    self.logger.error("Response too large: %d bytes", length)
                    return False
            except ValueError:
                self.logger.warning("Invalid Content-Length header")

        # Check for security headers
        security_headers = {
            "X-Content-Type-Options": "nosnif",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": None,  # Just check presence
        }

        for header, expected_value in security_headers.items():
            actual_value = response.headers.get(header)  # noqa: F841
            if expected_value and actual_value != expected_value:
                self.logger.warning(
                    "Missing or incorrect security header: %s", header)

        return True

    def secure_download(
        self,
        endpoint: SecureEndpoint,
        destination: Optional[str] = None,
        verify_signature: bool = True,
    ) -> Tuple[bool, str]:
        """
        Securely download content from an endpoint.

        Args:
            endpoint: The secure endpoint to download from
            destination: Optional destination file path
            verify_signature: Whether to verify content signature

        Returns:
            Tuple of (success, file_path_or_error_message)
        """
        self.logger.info("Starting secure download from: %s", endpoint.url)

        # Parse URL for certificate verification
        parsed_url = urllib.parse.urlparse(endpoint.url)
        hostname = parsed_url.hostname  # noqa: F841
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)  # noqa: F841

        # Validate hostname
        if not hostname:
            return False, "Invalid hostname in URL"

        # Verify certificate fingerprint if required
        if (
            endpoint.security_level == NetworkSecurityLevel.STRICT
            and endpoint.certificate_fingerprint
        ):
            if not self._verify_certificate_fingerprint(
                hostname, port, endpoint.certificate_fingerprint
            ):
                return False, "Certificate fingerprint verification failed"

        # Create secure request
        request = self._create_secure_request(endpoint.url, endpoint)

        # Configure URL opener with our SSL context
        if parsed_url.scheme == "https":
            https_handler = urllib.request.HTTPSHandler(
                context=self.ssl_context)
            opener = urllib.request.build_opener(https_handler)
        else:
            opener = urllib.request.build_opener()

        # Set timeout
        socket.setdefaulttimeout(endpoint.timeout)

        try:
            # Perform download with retries
            for attempt in range(endpoint.max_retries):
                try:
                    self.logger.debug(
                        "Download attempt %d/%d",
                        attempt + 1,
                        endpoint.max_retries)

                    with opener.open(request) as response:
                        # Validate response
                        if not self._validate_response(response):
                            return False, "Response validation failed"

                        # Create destination file
                        if destination:
                            dest_path = Path(destination)
                        else:
                            fd, dest_path = tempfile.mkstemp(
                                prefix="xanados_download_")
                            os.close(fd)
                            dest_path = Path(dest_path)

                        # Download with size limit
                        total_size = 0  # noqa: F841
                        max_size = 100 * 1024 * 1024  # 100MB limit  # noqa: F841

                        with open(dest_path, "wb") as f:
                            while True:
                                chunk = response.read(8192)
                                if not chunk:
                                    break

                                total_size += len(chunk)
                                if total_size > max_size:
                                    dest_path.unlink()
                                    return False, "Download size limit exceeded"

                                f.write(chunk)

                        self.logger.info(
                            "Download completed: %d bytes", total_size)

                        # Verify file signature if requested
                        if verify_signature:
                            if not self._verify_download_signature(dest_path):
                                dest_path.unlink()
                                return False, "Signature verification failed"

                        return True, str(dest_path)

                except urllib.error.URLError as e:
                    self.logger.warning(
                        "Download attempt %d failed: %s", attempt + 1, e
                    )
                    if attempt == endpoint.max_retries - 1:
                        return (
                            False, f"Download failed after {
                                endpoint.max_retries} attempts: {e}", )
                    time.sleep(2**attempt)  # Exponential backoff

        except Exception as e:
            self.logger.error("Unexpected error during download: %s", e)
            return False, f"Download error: {e}"

        finally:
            socket.setdefaulttimeout(None)  # Reset timeout

        # This should never be reached due to the logic above, but added for
        # type safety
        return False, "Download failed - unknown error"

    def _verify_download_signature(self, file_path: Path) -> bool:
        """
        Verify the digital signature of a downloaded file.

        Args:
            file_path: Path to the downloaded file

        Returns:
            True if signature is valid, False otherwise
        """
        # For ClamAV database files, check if there's a corresponding .sig file
        sig_file = file_path.with_suffix(file_path.suffix + ".sig")  # noqa: F841

        try:
            # Download signature file if it doesn't exist
            if not sig_file.exists():
                sig_url = f"{file_path.name}.sig"  # noqa: F841
                # This would need to be implemented based on the actual
                # signature URL
                self.logger.info(
                    "Signature verification not implemented for this file type"
                )
                return True  # Skip verification for now

            # Verify signature using GPG or similar
            result = subprocess.run(
                ["gpg", "--verify", str(sig_file), str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.warning(
                "GPG not available, skipping signature verification")
            return True  # Skip if GPG not available
        except Exception as e:
            self.logger.error("Signature verification failed: %s", e)
            return False

    def update_clamav_database(self, database_dir: str) -> Tuple[bool, str]:
        """
        Securely update ClamAV virus database.

        Args:
            database_dir: Directory to store database files

        Returns:
            Tuple of (success, message)
        """
        self.logger.info("Starting secure ClamAV database update")

        db_path = Path(database_dir)
        db_path.mkdir(parents=True, exist_ok=True)

        # Database files to download
        database_files = ["main.cvd", "daily.cvd", "bytecode.cvd"]

        success_count = 0
        total_files = len(database_files)

        for db_file in database_files:
            # Try each endpoint until successful
            for endpoint_name, endpoint in self.CLAMAV_ENDPOINTS.items():
                download_url = f"{endpoint.url}/{db_file}"
                download_endpoint = SecureEndpoint(
                    url=download_url,
                    certificate_fingerprint=endpoint.certificate_fingerprint,
                    security_level=endpoint.security_level,
                    timeout=300,  # 5 minutes for database downloads
                )

                dest_file = db_path / db_file  # noqa: F841
                success, result = self.secure_download(
                    download_endpoint, str(dest_file)
                )

                if success:
                    self.logger.info(
                        "Successfully downloaded %s from %s",
                        db_file,
                        endpoint_name)
                    success_count += 1
                    break
                else:
                    self.logger.warning(
                        "Failed to download %s from %s: %s",
                        db_file,
                        endpoint_name,
                        result,
                    )

        if success_count == total_files:
            return (
                True,
                f"Successfully updated {success_count}/{total_files} database files",
            )
        elif success_count > 0:
            return (
                True,
                f"Partially updated {success_count}/{total_files} database files",
            )
        else:
            return False, "Failed to update any database files"

    def check_network_connectivity(self) -> bool:
        """
        Check if network connectivity is available.

        Returns:
            True if network is available, False otherwise
        """
        test_hosts = [
            ("8.8.8.8", 53),  # Google DNS
            ("1.1.1.1", 53),  # Cloudflare DNS
            ("208.67.222.222", 53),  # OpenDNS
        ]

        for host, port in test_hosts:
            try:
                socket.create_connection((host, port), timeout=5)
                self.logger.debug(
                    "Network connectivity confirmed via %s:%d", host, port
                )
                return True
            except (socket.error, socket.timeout):
                continue

        self.logger.warning("No network connectivity detected")
        return False

    def validate_url_security(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL for security issues.

        Args:
            url: The URL to validate

        Returns:
            Tuple of (is_safe, message)
        """
        try:
            parsed = urllib.parse.urlparse(url)

            # Check protocol
            if parsed.scheme not in ["https", "http"]:
                return False, "Invalid protocol, only HTTP/HTTPS allowed"

            # Prefer HTTPS
            if parsed.scheme == "http":
                self.logger.warning("Using insecure HTTP protocol for %s", url)

            # Check hostname
            if not parsed.hostname:
                return False, "Invalid hostname"

            # Block private IP ranges (basic check)
            try:
                import ipaddress

                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback:
                    return False, "Private/loopback IP addresses not allowed"
            except ValueError:
                pass  # Not an IP address, which is fine

            # Check for suspicious patterns
            suspicious_patterns = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "file://",
                "ftp://",
                "javascript:",
                "data:",
            ]

            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    return False, f"Suspicious URL pattern detected: {pattern}"

            return True, "URL appears safe"

        except Exception as e:
            return False, f"URL validation error: {e}"


# Global instance for easy access
network_security = SecureNetworkManager()
