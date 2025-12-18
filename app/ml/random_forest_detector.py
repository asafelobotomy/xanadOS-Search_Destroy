#!/usr/bin/env python3
"""
Random Forest ML Detector for malware detection.

Uses trained scikit-learn Random Forest model for real-time threat detection.
Integrates with UnifiedScannerEngine for production scanning.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from app.ml.feature_extractor import FeatureExtractor
from app.ml.model_registry import ModelRegistry


@dataclass
class MLScanResult:
    """Result from ML-based scan."""

    file_path: str
    is_malware: bool
    confidence: float
    prediction_time: float
    model_version: str
    features_extracted: bool = True
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RandomForestDetector:
    """
    Production Random Forest malware detector.

    Uses trained scikit-learn model for real-time scanning.
    """

    def __init__(
        self,
        model_version: str = "1.0.0",
        models_dir: str = "models/checkpoints/malware_detector_rf",
        confidence_threshold: float = 0.5,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
    ):
        """
        Initialize Random Forest detector.

        Args:
            model_version: Version of model to load (e.g., "1.0.0")
            models_dir: Directory containing trained models
            confidence_threshold: Minimum confidence to classify as malware
            max_file_size: Maximum file size to process
        """
        self.logger = logging.getLogger(__name__)

        self.model_version = model_version
        self.models_dir = Path(models_dir)
        self.confidence_threshold = confidence_threshold
        self.max_file_size = max_file_size

        # Components
        self.model = None
        self.feature_extractor = FeatureExtractor(max_file_size=max_file_size)
        self.registry = ModelRegistry()

        # Statistics
        self.scans_performed = 0
        self.malware_detected = 0
        self.total_scan_time = 0.0

        # Load model
        self._load_model()

        self.logger.info(
            f"Random Forest detector initialized (model v{self.model_version})"
        )

    def _load_model(self) -> None:
        """Load trained Random Forest model from registry."""
        try:
            model_path = (
                self.models_dir / f"malware_detector_rf_v{self.model_version}.pkl"
            )

            if not model_path.exists():
                raise FileNotFoundError(
                    f"Model not found: {model_path}\n"
                    f"Run: python scripts/ml/train_random_forest.py"
                )

            # Load model
            self.model = joblib.load(model_path)

            self.logger.info(f"Model loaded successfully: {model_path}")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

    def scan_file(self, file_path: str | Path) -> MLScanResult:
        """
        Scan a file using Random Forest model.

        Args:
            file_path: Path to file to scan

        Returns:
            MLScanResult with detection results
        """
        file_path = Path(file_path)
        start_time = time.time()

        try:
            # Extract features
            features = self.feature_extractor.extract(file_path)

            if features is None:
                return MLScanResult(
                    file_path=str(file_path),
                    is_malware=False,
                    confidence=0.0,
                    prediction_time=time.time() - start_time,
                    model_version=self.model_version,
                    features_extracted=False,
                    error="Feature extraction failed",
                )

            # Predict
            prediction = self.model.predict(features.reshape(1, -1))[0]
            confidence = self.model.predict_proba(features.reshape(1, -1))[0][1]

            # Update statistics
            self.scans_performed += 1
            if prediction == 1:
                self.malware_detected += 1

            scan_time = time.time() - start_time
            self.total_scan_time += scan_time

            return MLScanResult(
                file_path=str(file_path),
                is_malware=bool(
                    prediction == 1 and confidence >= self.confidence_threshold
                ),
                confidence=float(confidence),
                prediction_time=scan_time,
                model_version=self.model_version,
            )

        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
            return MLScanResult(
                file_path=str(file_path),
                is_malware=False,
                confidence=0.0,
                prediction_time=time.time() - start_time,
                model_version=self.model_version,
                features_extracted=False,
                error=str(e),
            )

    def get_statistics(self) -> dict:
        """
        Get detector statistics.

        Returns:
            Dictionary of statistics
        """
        avg_scan_time = (
            self.total_scan_time / self.scans_performed
            if self.scans_performed > 0
            else 0.0
        )

        return {
            "model_version": self.model_version,
            "scans_performed": self.scans_performed,
            "malware_detected": self.malware_detected,
            "detection_rate": (
                self.malware_detected / self.scans_performed
                if self.scans_performed > 0
                else 0.0
            ),
            "total_scan_time": self.total_scan_time,
            "avg_scan_time": avg_scan_time,
            "confidence_threshold": self.confidence_threshold,
        }

    def reset_statistics(self) -> None:
        """Reset scan statistics."""
        self.scans_performed = 0
        self.malware_detected = 0
        self.total_scan_time = 0.0

        self.logger.info("Statistics reset")
