#!/usr/bin/env python3
"""
Python SDK for xanadOS ML Inference API

Provides a simple client for interacting with the ML inference API.
"""

import hashlib
import logging
import time
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PredictionResult(BaseModel):
    """Client-side prediction result."""

    model_config = {"protected_namespaces": ()}  # Allow model_ fields

    file_hash: str
    is_malware: bool
    confidence: float
    threat_level: str
    model_version: str
    scan_time_ms: float
    engine: str = "ML-RandomForest"


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    version: str
    stage: str
    architecture: str
    created_at: str
    test_accuracy: float
    test_precision: float
    test_recall: float


class MLScannerClient:
    """
    Client for xanadOS ML Inference API.

    Example:
        >>> client = MLScannerClient("http://localhost:8000", api_key="your-key")
        >>> result = client.scan_file("/path/to/file.exe")
        >>> if result.is_malware:
        ...     print(f"Malware detected! Confidence: {result.confidence:.1%}")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize ML scanner client.

        Args:
            base_url: API base URL (default: http://localhost:8000)
            api_key: API key for authentication (optional)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # HTTP client with retry logic
        self.client = httpx.Client(timeout=timeout, headers=self._get_headers())

        # Async client
        self.async_client = httpx.AsyncClient(
            timeout=timeout, headers=self._get_headers()
        )

    def _get_headers(self) -> dict:
        """Get request headers including API key."""
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    def health_check(self) -> dict:
        """
        Check API health status.

        Returns:
            dict: Health status information

        Raises:
            httpx.HTTPError: If request fails
        """
        response = self.client.get(f"{self.base_url}/api/ml/health")
        response.raise_for_status()
        return response.json()

    async def health_check_async(self) -> dict:
        """Async version of health_check."""
        response = await self.async_client.get(f"{self.base_url}/api/ml/health")
        response.raise_for_status()
        return response.json()

    def scan_file(self, file_path: str | Path) -> PredictionResult:
        """
        Scan file for malware.

        Args:
            file_path: Path to file to scan

        Returns:
            PredictionResult: Scan results

        Raises:
            FileNotFoundError: If file doesn't exist
            httpx.HTTPError: If API request fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}

            response = self.client.post(f"{self.base_url}/api/ml/predict", files=files)

        response.raise_for_status()
        return PredictionResult(**response.json())

    async def scan_file_async(self, file_path: str | Path) -> PredictionResult:
        """Async version of scan_file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}

            response = await self.async_client.post(
                f"{self.base_url}/api/ml/predict", files=files
            )

        response.raise_for_status()
        return PredictionResult(**response.json())

    def scan_bytes(self, content: bytes, filename: str = "sample") -> PredictionResult:
        """
        Scan raw bytes for malware.

        Args:
            content: File content as bytes
            filename: Filename for the upload (default: "sample")

        Returns:
            PredictionResult: Scan results

        Raises:
            httpx.HTTPError: If API request fails
        """
        files = {"file": (filename, content, "application/octet-stream")}

        response = self.client.post(f"{self.base_url}/api/ml/predict", files=files)

        response.raise_for_status()
        return PredictionResult(**response.json())

    async def scan_bytes_async(
        self, content: bytes, filename: str = "sample"
    ) -> PredictionResult:
        """Async version of scan_bytes."""
        files = {"file": (filename, content, "application/octet-stream")}

        response = await self.async_client.post(
            f"{self.base_url}/api/ml/predict", files=files
        )

        response.raise_for_status()
        return PredictionResult(**response.json())

    def list_models(self) -> list[ModelInfo]:
        """
        List available ML models.

        Returns:
            list[ModelInfo]: Available models

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = self.client.get(f"{self.base_url}/api/ml/models")
        response.raise_for_status()

        data = response.json()
        return [ModelInfo(**model) for model in data["models"]]

    async def list_models_async(self) -> list[ModelInfo]:
        """Async version of list_models."""
        response = await self.async_client.get(f"{self.base_url}/api/ml/models")
        response.raise_for_status()

        data = response.json()
        return [ModelInfo(**model) for model in data["models"]]

    def reload_model(self, version: str) -> dict:
        """
        Reload API with specified model version.

        Args:
            version: Model version to load (e.g., "v1.1.0")

        Returns:
            dict: Reload status

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = self.client.post(f"{self.base_url}/api/ml/models/{version}/reload")
        response.raise_for_status()
        return response.json()

    async def reload_model_async(self, version: str) -> dict:
        """Async version of reload_model."""
        response = await self.async_client.post(
            f"{self.base_url}/api/ml/models/{version}/reload"
        )
        response.raise_for_status()
        return response.json()

    def scan_directory(
        self, directory: str | Path, recursive: bool = True, max_files: int = 1000
    ) -> list[PredictionResult]:
        """
        Scan all files in a directory.

        Args:
            directory: Directory path to scan
            recursive: Scan subdirectories (default: True)
            max_files: Maximum files to scan (default: 1000)

        Returns:
            list[PredictionResult]: Scan results for all files
        """
        directory = Path(directory)

        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        # Collect files
        pattern = "**/*" if recursive else "*"
        files = [f for f in directory.glob(pattern) if f.is_file()][:max_files]

        # Scan each file
        results = []
        for file_path in files:
            try:
                result = self.scan_file(file_path)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to scan {file_path}: {e}")

        return results

    async def scan_directory_async(
        self, directory: str | Path, recursive: bool = True, max_files: int = 1000
    ) -> list[PredictionResult]:
        """Async version of scan_directory."""
        import asyncio

        directory = Path(directory)

        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        # Collect files
        pattern = "**/*" if recursive else "*"
        files = [f for f in directory.glob(pattern) if f.is_file()][:max_files]

        # Scan files concurrently
        tasks = [self.scan_file_async(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        return [r for r in results if isinstance(r, PredictionResult)]

    def close(self):
        """Close HTTP clients."""
        self.client.close()

    async def aclose(self):
        """Close async HTTP client."""
        await self.async_client.aclose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
