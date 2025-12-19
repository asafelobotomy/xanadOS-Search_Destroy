#!/usr/bin/env python3
"""
ML-based malware detection integration.

Provides ML threat detection using the production Random Forest model,
integrated with the existing UnifiedScannerEngine.
"""

import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.ml.model_registry import ModelRegistry
from app.ml.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


@dataclass
class MLScanResult:
    """Result from ML-based malware scan."""

    file_path: str
    is_malware: bool
    confidence: float  # 0.0-1.0
    model_version: str
    detection_time: float  # seconds
    engine: str = "ML-RandomForest"
    threat_level: str = "UNKNOWN"
    description: str = ""

    def __post_init__(self):
        """Set threat level and description based on detection."""
        # Only set description if not already provided
        if self.description:
            # Description explicitly set (e.g., error cases), don't override
            return

        if self.is_malware:
            if self.confidence >= 0.9:
                self.threat_level = "HIGH"
                self.description = (
                    f"ML model detected malware with {self.confidence:.1%} confidence"
                )
            elif self.confidence >= 0.7:
                self.threat_level = "MEDIUM"
                self.description = f"ML model detected potential malware ({self.confidence:.1%} confidence)"
            else:
                self.threat_level = "LOW"
                self.description = f"ML model flagged file as suspicious ({self.confidence:.1%} confidence)"
        else:
            self.threat_level = "CLEAN"
            self.description = f"ML model classified as clean ({1-self.confidence:.1%} confidence benign)"


class MLThreatDetector:
    """
    ML-based malware detection using production model.

    Features:
    - Loads production model from registry
    - Extracts features from files
    - Returns standardized scan results
    - Thread-safe for concurrent scanning
    - Automatic model reloading on version change
    """

    def __init__(
        self,
        model_name: str = "malware_detector_rf",
        model_version: Optional[str] = None,
    ):
        """
        Initialize ML threat detector.

        Args:
            model_name: Name of model in registry (default: malware_detector_rf)
            model_version: Specific version to load, or None for production
        """
        self.model_name = model_name
        self.model_version = model_version
        self.registry = ModelRegistry()
        self.feature_extractor = FeatureExtractor()

        # Load model (types set for model registry tuple unpacking)
        self.model: Any = None
        self.metadata: ModelMetadata | None = None
        self._load_model()

        logger.info(
            f"MLThreatDetector initialized with {self.model_name} v{self.metadata.version}"
        )

    def _load_model(self):
        """Load production model from registry."""
        try:
            if self.model_version:
                # Load specific version
                self.model, self.metadata = self.registry.load_model(
                    self.model_name, self.model_version
                )
                logger.info(f"Loaded model {self.model_name} v{self.model_version}")
            else:
                # Load production model
                production_models = self.registry.list_models(
                    name=self.model_name, stage="production"
                )

                if not production_models:
                    # Fallback to latest checkpoint
                    logger.warning("No production model found, using latest checkpoint")
                    all_models = self.registry.list_models(name=self.model_name)

                    if not all_models:
                        raise RuntimeError(f"No models found for {self.model_name}")

                    latest = all_models[0]  # Already sorted by creation time
                    self.model, self.metadata = self.registry.load_model(
                        self.model_name, latest.version
                    )
                else:
                    # Use production model
                    prod_metadata = production_models[0]
                    self.model, self.metadata = self.registry.load_model(
                        self.model_name, prod_metadata.version
                    )

                logger.info(
                    f"Loaded production model {self.model_name} v{self.metadata.version}"
                )

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            raise RuntimeError(f"ML model loading failed: {e}")

    def reload_model(self):
        """Reload model from registry (e.g., after model update)."""
        logger.info(f"Reloading model {self.model_name}...")
        self._load_model()

    def scan_file(self, file_path: Path | str) -> MLScanResult:
        """
        Scan file for malware using ML model.

        Args:
            file_path: Path to file to scan

        Returns:
            MLScanResult with detection details

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If scanning fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = time.time()

        try:
            # Extract features
            features = self.feature_extractor.extract_features(file_path)

            if features is None:
                logger.warning(f"Feature extraction failed for {file_path}")
                return MLScanResult(
                    file_path=str(file_path),
                    is_malware=False,
                    confidence=0.0,
                    model_version=self.metadata.version,
                    detection_time=time.time() - start_time,
                    description="Feature extraction failed",
                )

            # Reshape for prediction (model expects 2D array)
            features_reshaped = features.reshape(1, -1)

            # Predict
            prediction = self.model.predict(features_reshaped)[0]
            probability = self.model.predict_proba(features_reshaped)[0]

            # probability[0] = benign, probability[1] = malware
            malware_confidence = float(probability[1])

            detection_time = time.time() - start_time

            result = MLScanResult(
                file_path=str(file_path),
                is_malware=bool(prediction),
                confidence=malware_confidence,
                model_version=self.metadata.version,
                detection_time=detection_time,
            )

            logger.debug(
                f"Scanned {file_path.name}: {'MALWARE' if result.is_malware else 'CLEAN'} "
                f"({result.confidence:.1%} confidence, {detection_time*1000:.1f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"ML scan failed for {file_path}: {e}")
            raise RuntimeError(f"ML scanning error: {e}")

    def scan_bytes(self, file_bytes: bytes, file_name: str = "unknown") -> MLScanResult:
        """
        Scan raw bytes for malware.

        Args:
            file_bytes: Raw file content
            file_name: Name for logging/reporting

        Returns:
            MLScanResult with detection details
        """
        import tempfile

        # Write to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            result = self.scan_file(tmp_path)
            # Update path to original name
            result.file_path = file_name
            return result
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)

    def get_model_info(self) -> dict:
        """Get information about loaded model."""
        return {
            "name": self.model_name,
            "version": self.metadata.version,
            "architecture": self.metadata.architecture,
            "created_at": self.metadata.created_at,
            "test_accuracy": self.metadata.metrics.get("test_accuracy", 0.0),
            "test_precision": self.metadata.metrics.get("test_precision", 0.0),
            "test_recall": self.metadata.metrics.get("test_recall", 0.0),
            "hyperparameters": self.metadata.hyperparameters,
        }

    @property
    def is_ready(self) -> bool:
        """Check if detector is ready to scan."""
        return self.model is not None and self.metadata is not None
