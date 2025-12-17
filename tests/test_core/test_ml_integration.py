#!/usr/bin/env python3
"""Tests for ML scanner integration."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.core.ml_scanner_integration import MLScanResult, MLThreatDetector


class TestMLScanResult:
    """Test MLScanResult dataclass."""

    def test_clean_file_result(self):
        """Test clean file scan result."""
        result = MLScanResult(
            file_path="/test/clean.txt",
            is_malware=False,
            confidence=0.1,
            model_version="v1.1.0",
            detection_time=0.05,
        )

        assert result.threat_level == "CLEAN"
        assert "clean" in result.description.lower()
        assert result.engine == "ML-RandomForest"

    def test_high_confidence_malware(self):
        """Test high confidence malware detection."""
        result = MLScanResult(
            file_path="/test/malware.exe",
            is_malware=True,
            confidence=0.95,
            model_version="v1.1.0",
            detection_time=0.08,
        )

        assert result.threat_level == "HIGH"
        assert "malware" in result.description.lower()
        assert result.confidence == 0.95

    def test_medium_confidence_malware(self):
        """Test medium confidence malware detection."""
        result = MLScanResult(
            file_path="/test/suspicious.bin",
            is_malware=True,
            confidence=0.75,
            model_version="v1.1.0",
            detection_time=0.06,
        )

        assert result.threat_level == "MEDIUM"
        assert result.confidence == 0.75

    def test_low_confidence_malware(self):
        """Test low confidence malware detection."""
        result = MLScanResult(
            file_path="/test/maybe.dat",
            is_malware=True,
            confidence=0.65,
            model_version="v1.1.0",
            detection_time=0.07,
        )

        assert result.threat_level == "LOW"
        assert "suspicious" in result.description.lower()


class TestMLThreatDetector:
    """Test MLThreatDetector class."""

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_initialization(self, mock_extractor, mock_registry):
        """Test detector initialization."""
        # Mock registry to return production model
        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"
        mock_metadata.architecture = "RandomForest"

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (Mock(), mock_metadata)
        mock_registry.return_value = mock_registry_instance

        detector = MLThreatDetector()

        assert detector.model is not None
        assert detector.metadata is not None
        assert detector.is_ready

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_scan_file_malware(self, mock_extractor, mock_registry):
        """Test scanning malware file."""
        # Mock setup
        mock_model = Mock()
        mock_model.predict.return_value = [1]  # Malware
        mock_model.predict_proba.return_value = [[0.1, 0.9]]  # 90% confidence

        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (mock_model, mock_metadata)
        mock_registry.return_value = mock_registry_instance

        mock_extractor_instance = Mock()
        import numpy as np

        mock_extractor_instance.extract_features.return_value = np.zeros(318)
        mock_extractor.return_value = mock_extractor_instance

        detector = MLThreatDetector()

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp:
            tmp.write(b"malicious content")
            tmp_path = Path(tmp.name)

        try:
            result = detector.scan_file(tmp_path)

            assert result.is_malware is True
            assert result.confidence == 0.9
            assert result.model_version == "v1.1.0"
            assert result.detection_time > 0
            assert result.threat_level == "HIGH"
        finally:
            tmp_path.unlink()

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_scan_file_clean(self, mock_extractor, mock_registry):
        """Test scanning clean file."""
        # Mock setup
        mock_model = Mock()
        mock_model.predict.return_value = [0]  # Clean
        mock_model.predict_proba.return_value = [[0.95, 0.05]]  # 95% clean

        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (mock_model, mock_metadata)
        mock_registry.return_value = mock_registry_instance

        mock_extractor_instance = Mock()
        import numpy as np

        mock_extractor_instance.extract_features.return_value = np.zeros(318)
        mock_extractor.return_value = mock_extractor_instance

        detector = MLThreatDetector()

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(b"clean content")
            tmp_path = Path(tmp.name)

        try:
            result = detector.scan_file(tmp_path)

            assert result.is_malware is False
            assert result.confidence == 0.05
            assert result.threat_level == "CLEAN"
        finally:
            tmp_path.unlink()

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_scan_nonexistent_file(self, mock_extractor, mock_registry):
        """Test scanning file that doesn't exist."""
        # Mock setup
        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (Mock(), mock_metadata)
        mock_registry.return_value = mock_registry_instance

        detector = MLThreatDetector()

        with pytest.raises(FileNotFoundError):
            detector.scan_file("/nonexistent/file.exe")

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_scan_bytes(self, mock_extractor, mock_registry):
        """Test scanning raw bytes."""
        # Mock setup
        mock_model = Mock()
        mock_model.predict.return_value = [1]  # Malware
        mock_model.predict_proba.return_value = [[0.2, 0.8]]

        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (mock_model, mock_metadata)
        mock_registry.return_value = mock_registry_instance

        mock_extractor_instance = Mock()
        import numpy as np

        mock_extractor_instance.extract_features.return_value = np.zeros(318)
        mock_extractor.return_value = mock_extractor_instance

        detector = MLThreatDetector()

        result = detector.scan_bytes(b"malicious payload", "malware.exe")

        assert result.file_path == "malware.exe"
        assert result.is_malware is True

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_get_model_info(self, mock_extractor, mock_registry):
        """Test getting model information."""
        # Mock setup
        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"
        mock_metadata.architecture = "RandomForest"
        mock_metadata.created_at = "2025-12-17T10:00:00"
        mock_metadata.metrics = {
            "test_accuracy": 1.0,
            "test_precision": 1.0,
            "test_recall": 1.0,
        }
        mock_metadata.hyperparameters = {"n_estimators": 100}

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (Mock(), mock_metadata)
        mock_registry.return_value = mock_registry_instance

        detector = MLThreatDetector(model_name="test_model")

        info = detector.get_model_info()

        assert info["name"] == "test_model"
        assert info["version"] == "v1.1.0"
        assert info["architecture"] == "RandomForest"
        assert info["test_accuracy"] == 1.0
        assert "n_estimators" in info["hyperparameters"]

    @patch("app.core.ml_scanner_integration.ModelRegistry")
    @patch("app.core.ml_scanner_integration.FeatureExtractor")
    def test_feature_extraction_failure(self, mock_extractor, mock_registry):
        """Test handling of feature extraction failure."""
        # Mock setup
        mock_metadata = Mock()
        mock_metadata.version = "v1.1.0"

        mock_registry_instance = Mock()
        mock_registry_instance.list_models.return_value = [mock_metadata]
        mock_registry_instance.load_model.return_value = (Mock(), mock_metadata)
        mock_registry.return_value = mock_registry_instance

        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_features.return_value = (
            None  # Extraction failed
        )
        mock_extractor.return_value = mock_extractor_instance

        detector = MLThreatDetector()

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = Path(tmp.name)

        try:
            result = detector.scan_file(tmp_path)

            assert result.is_malware is False
            assert "extraction failed" in result.description.lower()
        finally:
            tmp_path.unlink()
