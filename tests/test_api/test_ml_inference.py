#!/usr/bin/env python3
"""Tests for ML Inference API."""

import io
from unittest.mock import Mock, patch, MagicMock

import pytest


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    # Mock dependencies before importing
    with (
        patch("app.core.ml_scanner_integration.ModelRegistry"),
        patch("app.core.ml_scanner_integration.FeatureExtractor"),
    ):

        from fastapi.testclient import TestClient
        from app.api.ml_inference import app

        return TestClient(app)


@pytest.fixture
def mock_ml_detector():
    """Create mock ML detector."""
    detector = Mock()
    detector.metadata = Mock()
    detector.metadata.version = "v1.1.0"
    return detector


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/api/ml/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "ml_enabled" in data
        assert "uptime_seconds" in data

    def test_health_check_rate_limit(self, client):
        """Test health check respects rate limits."""
        # Make many requests (should not hit rate limit for health check)
        for _ in range(30):
            response = client.get("/api/ml/health")
            assert response.status_code == 200


class TestPredictEndpoint:
    """Test prediction endpoint."""

    @patch("app.api.ml_inference.ml_detector")
    def test_predict_file_success(self, mock_detector, client):
        """Test successful file prediction."""
        # Mock scan result
        from app.core.ml_scanner_integration import MLScanResult

        mock_result = MLScanResult(
            file_path="/tmp/test.exe",
            is_malware=True,
            confidence=0.95,
            model_version="v1.1.0",
            detection_time=0.05,
        )

        mock_detector.scan_file.return_value = mock_result

        # Create test file
        file_content = b"malicious content"
        files = {
            "file": (
                "malware.exe",
                io.BytesIO(file_content),
                "application/octet-stream",
            )
        }

        response = client.post("/api/ml/predict", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["is_malware"] is True
        assert data["confidence"] == 0.95
        assert data["threat_level"] == "HIGH"
        assert data["model_version"] == "v1.1.0"

    @patch("app.api.ml_inference.ml_detector")
    def test_predict_clean_file(self, mock_detector, client):
        """Test prediction for clean file."""
        from app.core.ml_scanner_integration import MLScanResult

        mock_result = MLScanResult(
            file_path="/tmp/test.txt",
            is_malware=False,
            confidence=0.05,
            model_version="v1.1.0",
            detection_time=0.03,
        )

        mock_detector.scan_file.return_value = mock_result

        file_content = b"clean content"
        files = {"file": ("clean.txt", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/ml/predict", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["is_malware"] is False
        assert data["threat_level"] == "CLEAN"

    def test_predict_no_file(self, client):
        """Test prediction without file."""
        response = client.post("/api/ml/predict")

        assert response.status_code == 422  # Validation error

    @patch("app.api.ml_inference.ml_detector", None)
    def test_predict_ml_unavailable(self, client):
        """Test prediction when ML detector unavailable."""
        file_content = b"test content"
        files = {
            "file": ("test.bin", io.BytesIO(file_content), "application/octet-stream")
        }

        response = client.post("/api/ml/predict", files=files)

        assert response.status_code == 503
        assert "not available" in response.json()["detail"].lower()

    @patch("app.api.ml_inference.ml_detector")
    def test_predict_file_too_large(self, mock_detector, client):
        """Test prediction with file exceeding size limit."""
        # Create file larger than 100MB
        large_content = b"x" * (101 * 1024 * 1024)
        files = {
            "file": ("large.bin", io.BytesIO(large_content), "application/octet-stream")
        }

        response = client.post("/api/ml/predict", files=files)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()


class TestModelsEndpoint:
    """Test models management endpoints."""

    @patch("app.api.ml_inference.model_registry")
    def test_list_models_success(self, mock_registry, client):
        """Test successful model listing."""
        # Mock model metadata
        mock_model1 = Mock()
        mock_model1.name = "malware_detector_rf"
        mock_model1.version = "v1.1.0"
        mock_model1.stage = "production"
        mock_model1.architecture = "RandomForest"
        mock_model1.created_at = "2025-12-17T10:00:00"
        mock_model1.metrics = {
            "test_accuracy": 1.0,
            "test_precision": 1.0,
            "test_recall": 1.0,
        }

        mock_model2 = Mock()
        mock_model2.name = "malware_detector_rf"
        mock_model2.version = "v1.0.0"
        mock_model2.stage = "checkpoint"
        mock_model2.architecture = "RandomForest"
        mock_model2.created_at = "2025-12-16T10:00:00"
        mock_model2.metrics = {
            "test_accuracy": 0.9889,
            "test_precision": 1.0,
            "test_recall": 0.9333,
        }

        mock_registry.list_models.return_value = [mock_model1, mock_model2]

        response = client.get("/api/ml/models")

        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert len(data["models"]) == 2
        assert data["production_model"] == "v1.1.0"

        # Check first model
        assert data["models"][0]["version"] == "v1.1.0"
        assert data["models"][0]["stage"] == "production"
        assert data["models"][0]["test_accuracy"] == 1.0

    @patch("app.api.ml_inference.MLThreatDetector")
    def test_reload_model_success(self, mock_detector_class, client):
        """Test successful model reload."""
        mock_detector = Mock()
        mock_detector.get_model_info.return_value = {
            "version": "v1.0.0",
            "architecture": "RandomForest",
        }

        mock_detector_class.return_value = mock_detector

        response = client.post("/api/ml/models/v1.0.0/reload")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "model_info" in data


class TestAuthentication:
    """Test API authentication."""

    @patch("app.api.ml_inference.load_config")
    def test_auth_disabled(self, mock_config, client):
        """Test requests when auth is disabled."""
        mock_config.return_value = {"api": {"require_auth": False}}

        response = client.get("/api/ml/health")
        assert response.status_code == 200

    @patch("app.api.ml_inference.load_config")
    def test_auth_required_no_key(self, mock_config, client):
        """Test request without API key when auth required."""
        mock_config.return_value = {
            "api": {"require_auth": True, "api_keys": ["test-key-123"]}
        }

        response = client.get("/api/ml/models")
        assert response.status_code == 401

    @patch("app.api.ml_inference.load_config")
    def test_auth_required_invalid_key(self, mock_config, client):
        """Test request with invalid API key."""
        mock_config.return_value = {
            "api": {"require_auth": True, "api_keys": ["valid-key"]}
        }

        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/api/ml/models", headers=headers)
        assert response.status_code == 403

    @patch("app.api.ml_inference.load_config")
    @patch("app.api.ml_inference.model_registry")
    def test_auth_required_valid_key(self, mock_registry, mock_config, client):
        """Test request with valid API key."""
        mock_config.return_value = {
            "api": {"require_auth": True, "api_keys": ["valid-key-123"]}
        }

        mock_registry.list_models.return_value = []

        headers = {"X-API-Key": "valid-key-123"}
        response = client.get("/api/ml/models", headers=headers)
        assert response.status_code == 200
