#!/usr/bin/env python3
"""ML-Powered Threat Detection for xanadOS Search & Destroy.

Modern machine learning integration using TensorFlow for advanced threat detection.
"""

import asyncio
import logging
import os
import pickle
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from app.core.async_threat_detector import ThreatDetection, ThreatLevel, ThreatType
from app.utils.secure_crypto import secure_file_hash


# ML Model Constants
MALWARE_CONFIDENCE_THRESHOLD = 0.5
BEHAVIORAL_CONFIDENCE_THRESHOLD = 0.5
CRITICAL_THREAT_THRESHOLD = 0.9
HIGH_THREAT_THRESHOLD = 0.7
MEDIUM_THREAT_THRESHOLD = 0.5
FEATURE_VECTOR_SIZE = 1000
MAX_STRING_SEQUENCES = 100
MAX_STRING_LENGTH = 50
ANOMALY_CONFIDENCE_HIGH = 0.8
ANOMALY_CONFIDENCE_LOW = 0.2


class MLModelType(Enum):
    """Types of ML models available."""
    MALWARE_CLASSIFIER = "malware_classifier"
    BEHAVIORAL_ANALYZER = "behavioral_analyzer"
    ANOMALY_DETECTOR = "anomaly_detector"
    PATTERN_RECOGNIZER = "pattern_recognizer"


class MLThreatLevel(Enum):
    """ML-specific threat levels with confidence scores."""
    BENIGN = ("benign", 0.0)
    SUSPICIOUS = ("suspicious", 0.3)
    LIKELY_THREAT = ("likely_threat", 0.6)
    HIGH_CONFIDENCE_THREAT = ("high_confidence_threat", 0.8)
    CRITICAL_THREAT = ("critical_threat", 0.95)


@dataclass
class MLPrediction:
    """ML model prediction result."""
    model_type: MLModelType
    prediction_class: str
    confidence_score: float
    feature_importance: dict[str, float] | None = None
    model_version: str = "1.0"
    prediction_time: datetime | None = None


@dataclass
class FileFeatures:
    """Extracted features from a file for ML analysis."""
    file_path: str
    file_size: int
    file_entropy: float
    pe_features: dict[str, Any] | None = None
    string_features: list[str] | None = None
    opcode_features: list[str] | None = None
    api_calls: list[str] | None = None
    file_hash: str = ""
    magic_bytes: bytes | None = None
    creation_time: datetime | None = None
    modification_time: datetime | None = None


class MLThreatDetector:
    """
    Machine Learning-powered threat detector using TensorFlow and scikit-learn.

    Features:
    - Deep neural networks for malware classification
    - Behavioral pattern recognition using RNNs
    - Anomaly detection for zero-day threats
    - Feature extraction from PE files and executables
    - Real-time ML inference with async support
    """

    def __init__(
        self,
        models_dir: str = "models/",
        enable_gpu: bool = True,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
    ) -> None:
        """Initialize ML threat detector."""
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size

        # TensorFlow configuration
        if enable_gpu:
            self._configure_tensorflow_gpu()
        else:
            tf.config.set_visible_devices([], 'GPU')

        # Models
        self.malware_classifier: tf.keras.Model | None = None
        self.behavioral_analyzer: tf.keras.Model | None = None
        self.anomaly_detector: IsolationForest | None = None
        self.pattern_recognizer: tf.keras.Model | None = None

        # Feature extractors
        self.tfidf_vectorizer: TfidfVectorizer | None = None
        self.feature_scaler: StandardScaler | None = None

        # Model metadata
        self.model_versions: dict[str, str] = {}
        self.feature_dimensions: dict[str, int] = {}

        # Performance tracking
        self.predictions_made = 0
        self.ml_detections = 0
        self.avg_prediction_time = 0.0

        # Initialize models asynchronously
        self._initialization_task = asyncio.create_task(self._initialize_models_async())

        self.logger.info("ML threat detector initialized")

    def _configure_tensorflow_gpu(self) -> None:
        """Configure TensorFlow for optimal GPU usage with memory management."""
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    # Enable memory growth to prevent allocation of all GPU memory
                    tf.config.experimental.set_memory_growth(gpu, True)

                    # Set memory limit if specified (optional, for resource constraints)
                    # tf.config.experimental.set_memory_limit(gpu, 1024)  # 1GB limit

                self.logger.info("Configured %d GPU(s) for TensorFlow", len(gpus))
            else:
                self.logger.info("No GPUs found, using CPU")

            # Configure TensorFlow for memory efficiency
            tf.config.optimizer.set_jit(True)  # Enable XLA compilation
            tf.config.threading.set_inter_op_parallelism_threads(0)  # Use all available cores

        except RuntimeError as e:
            self.logger.error("Error configuring GPU: %s", e)

    async def _initialize_models_async(self) -> None:
        """Initialize all ML models asynchronously."""
        try:
            # Load or create models
            await self._load_or_create_malware_classifier_async()
            await self._load_or_create_behavioral_analyzer_async()
            await self._load_or_create_anomaly_detector_async()
            await self._load_or_create_pattern_recognizer_async()

            # Initialize feature extractors
            await self._initialize_feature_extractors_async()

            self.logger.info("ML models initialization completed")

        except (ImportError, ModuleNotFoundError) as e:
            self.logger.error("Missing ML dependencies: %s", e)
            raise
        except (OSError, IOError) as e:
            self.logger.error("Error accessing model files: %s", e)
        except RuntimeError as e:
            self.logger.error("Runtime error during ML initialization: %s", e)
        except Exception as e:
            self.logger.error("Unexpected error initializing ML models: %s", e)

    async def _load_or_create_malware_classifier_async(self) -> None:
        """Load or create the malware classification model."""
        try:
            model_path = self.models_dir / "malware_classifier.h5"

            if model_path.exists():
                # Load existing model
                loop = asyncio.get_event_loop()
                self.malware_classifier = await loop.run_in_executor(
                    None, tf.keras.models.load_model, str(model_path)
                )
                self.logger.info("Loaded existing malware classifier")
            else:
                # Create new model
                self.malware_classifier = self._create_malware_classifier_model()
                self.logger.info("Created new malware classifier")

            self.model_versions["malware_classifier"] = "1.0"

        except Exception as e:
            self.logger.error("Error with malware classifier: %s", e)

    def _create_malware_classifier_model(self) -> tf.keras.Model:
        """Create a deep neural network for malware classification."""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(512, activation='relu', input_shape=(1000,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')  # Binary classification
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )

        return model

    async def _load_or_create_behavioral_analyzer_async(self) -> None:
        """Load or create the behavioral analysis model."""
        try:
            model_path = self.models_dir / "behavioral_analyzer.h5"

            if model_path.exists():
                loop = asyncio.get_event_loop()
                self.behavioral_analyzer = await loop.run_in_executor(
                    None, tf.keras.models.load_model, str(model_path)
                )
                self.logger.info("Loaded existing behavioral analyzer")
            else:
                self.behavioral_analyzer = self._create_behavioral_analyzer_model()
                self.logger.info("Created new behavioral analyzer")

            self.model_versions["behavioral_analyzer"] = "1.0"

        except Exception as e:
            self.logger.error("Error with behavioral analyzer: %s", e)

    def _create_behavioral_analyzer_model(self) -> tf.keras.Model:
        """Create an LSTM model for behavioral sequence analysis."""
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(128, return_sequences=True, input_shape=(100, 50)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.LSTM(64, return_sequences=False),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        return model

    async def _load_or_create_anomaly_detector_async(self) -> None:
        """Load or create the anomaly detection model."""
        try:
            model_path = self.models_dir / "anomaly_detector.pkl"

            if model_path.exists():
                loop = asyncio.get_event_loop()
                with open(model_path, 'rb') as f:
                    self.anomaly_detector = await loop.run_in_executor(
                        None, pickle.load, f
                    )
                self.logger.info("Loaded existing anomaly detector")
            else:
                self.anomaly_detector = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
                self.logger.info("Created new anomaly detector")

            self.model_versions["anomaly_detector"] = "1.0"

        except Exception as e:
            self.logger.error("Error with anomaly detector: %s", e)

    async def _load_or_create_pattern_recognizer_async(self) -> None:
        """Load or create the pattern recognition model."""
        try:
            model_path = self.models_dir / "pattern_recognizer.h5"

            if model_path.exists():
                loop = asyncio.get_event_loop()
                self.pattern_recognizer = await loop.run_in_executor(
                    None, tf.keras.models.load_model, str(model_path)
                )
                self.logger.info("Loaded existing pattern recognizer")
            else:
                self.pattern_recognizer = self._create_pattern_recognizer_model()
                self.logger.info("Created new pattern recognizer")

            self.model_versions["pattern_recognizer"] = "1.0"

        except Exception as e:
            self.logger.error("Error with pattern recognizer: %s", e)

    def _create_pattern_recognizer_model(self) -> tf.keras.Model:
        """Create a CNN model for pattern recognition in binary data."""
        model = tf.keras.Sequential([
            tf.keras.layers.Conv1D(64, 3, activation='relu', input_shape=(1024, 1)),
            tf.keras.layers.MaxPooling1D(2),
            tf.keras.layers.Conv1D(128, 3, activation='relu'),
            tf.keras.layers.MaxPooling1D(2),
            tf.keras.layers.Conv1D(256, 3, activation='relu'),
            tf.keras.layers.GlobalAveragePooling1D(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        return model

    async def _initialize_feature_extractors_async(self) -> None:
        """Initialize feature extraction components."""
        try:
            # TF-IDF vectorizer for string analysis
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 3)
            )

            # Standard scaler for numerical features
            self.feature_scaler = StandardScaler()

            # Try to load existing fitted extractors
            await self._load_feature_extractors_async()

        except Exception as e:
            self.logger.error("Error initializing feature extractors: %s", e)

    async def _load_feature_extractors_async(self) -> None:
        """Load pre-fitted feature extractors if available."""
        try:
            tfidf_path = self.models_dir / "tfidf_vectorizer.pkl"
            scaler_path = self.models_dir / "feature_scaler.pkl"

            loop = asyncio.get_event_loop()

            if tfidf_path.exists():
                with open(tfidf_path, 'rb') as f:
                    self.tfidf_vectorizer = await loop.run_in_executor(
                        None, pickle.load, f
                    )

            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    self.feature_scaler = await loop.run_in_executor(
                        None, pickle.load, f
                    )

        except Exception as e:
            self.logger.error("Error loading feature extractors: %s", e)

    async def extract_file_features_async(self, file_path: str) -> FileFeatures:
        """Extract comprehensive features from a file for ML analysis."""
        try:
            # Basic file information
            stat_result = os.stat(file_path)
            file_size = stat_result.st_size

            if file_size > self.max_file_size:
                return FileFeatures(
                    file_path=file_path,
                    file_size=file_size,
                    file_entropy=0.0,
                    file_hash=await self._calculate_file_hash_async(file_path)
                )

            # Calculate file hash
            file_hash = await self._calculate_file_hash_async(file_path)

            # Calculate entropy
            entropy = await self._calculate_entropy_async(file_path)

            # Extract strings and patterns
            strings = await self._extract_strings_async(file_path)

            # Read magic bytes
            magic_bytes = await self._read_magic_bytes_async(file_path)

            # PE analysis (if applicable)
            pe_features = await self._extract_pe_features_async(file_path)

            return FileFeatures(
                file_path=file_path,
                file_size=file_size,
                file_entropy=entropy,
                pe_features=pe_features,
                string_features=strings,
                file_hash=file_hash,
                magic_bytes=magic_bytes,
                creation_time=datetime.fromtimestamp(stat_result.st_ctime),
                modification_time=datetime.fromtimestamp(stat_result.st_mtime)
            )

        except Exception as e:
            self.logger.error("Error extracting features from %s: %s", file_path, e)
            return FileFeatures(
                file_path=file_path,
                file_size=0,
                file_entropy=0.0
            )

    async def _calculate_file_hash_async(self, file_path: str) -> str:
        """Calculate file hash asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, secure_file_hash, file_path, 'sha256')

    async def _calculate_entropy_async(self, file_path: str) -> float:
        """Calculate file entropy asynchronously."""
        try:
            import math
            from collections import Counter

            def calc_entropy():
                with open(file_path, 'rb') as f:
                    # Read sample of file for entropy calculation
                    data = f.read(min(8192, os.path.getsize(file_path)))
                    if not data:
                        return 0.0

                    byte_counts = Counter(data)
                    entropy = 0.0
                    data_len = len(data)

                    for count in byte_counts.values():
                        probability = count / data_len
                        if probability > 0:
                            entropy -= probability * math.log2(probability)

                    return entropy

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, calc_entropy)

        except Exception as e:
            self.logger.error("Error calculating entropy for %s: %s", file_path, e)
            return 0.0

    async def _extract_strings_async(self, file_path: str) -> list[str]:
        """Extract printable strings from file."""
        try:
            def extract_strings():
                import re
                strings = []

                with open(file_path, 'rb') as f:
                    content = f.read(min(65536, os.path.getsize(file_path)))  # Read up to 64KB

                    # Extract ASCII strings (minimum length 4)
                    ascii_strings = re.findall(rb'[ -~]{4,}', content)
                    strings.extend([s.decode('ascii', errors='ignore') for s in ascii_strings])

                    # Extract Unicode strings
                    unicode_strings = re.findall(rb'(?:[\x20-\x7E]\x00){4,}', content)
                    for s in unicode_strings:
                        try:
                            decoded = s.decode('utf-16le', errors='ignore')
                            if decoded.strip():
                                strings.append(decoded)
                        except Exception:
                            pass

                return strings[:100]  # Limit to first 100 strings

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_strings)

        except Exception as e:
            self.logger.error("Error extracting strings from %s: %s", file_path, e)
            return []

    async def _read_magic_bytes_async(self, file_path: str) -> bytes | None:
        """Read magic bytes from file header."""
        try:
            def read_magic():
                with open(file_path, 'rb') as f:
                    return f.read(16)  # Read first 16 bytes

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, read_magic)

        except Exception as e:
            self.logger.error("Error reading magic bytes from %s: %s", file_path, e)
            return None

    async def _extract_pe_features_async(self, file_path: str) -> dict[str, Any] | None:
        """Extract PE (Portable Executable) features if applicable."""
        try:
            # Check if file is PE by magic bytes
            magic = await self._read_magic_bytes_async(file_path)
            if not magic or not magic.startswith(b'MZ'):
                return None

            # Basic PE analysis (would use pefile library in production)
            pe_features = {
                "is_pe": True,
                "has_mz_header": True,
                "file_type": "executable",
                # Would extract more detailed PE information here
                "sections": [],
                "imports": [],
                "exports": [],
            }

            return pe_features

        except Exception as e:
            self.logger.error("Error extracting PE features from %s: %s", file_path, e)
            return None

    async def predict_malware_async(self, features: FileFeatures) -> MLPrediction:
        """Predict if file is malware using the neural network classifier."""
        try:
            if not self.malware_classifier:
                raise ValueError("Malware classifier not initialized")

            # Convert features to numerical vector
            feature_vector = await self._features_to_vector_async(features)

            # Make prediction
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None,
                self.malware_classifier.predict,
                np.array([feature_vector])
            )

            confidence = float(prediction[0][0])
            is_malware = confidence > MALWARE_CONFIDENCE_THRESHOLD

            prediction_class = "malware" if is_malware else "benign"

            self.predictions_made += 1
            if is_malware:
                self.ml_detections += 1

            return MLPrediction(
                model_type=MLModelType.MALWARE_CLASSIFIER,
                prediction_class=prediction_class,
                confidence_score=confidence,
                model_version=self.model_versions.get("malware_classifier", "1.0"),
                prediction_time=datetime.now()
            )

        except Exception as e:
            self.logger.error("Error in malware prediction: %s", e)
            return MLPrediction(
                model_type=MLModelType.MALWARE_CLASSIFIER,
                prediction_class="unknown",
                confidence_score=0.0,
                prediction_time=datetime.now()
            )

    async def analyze_behavior_async(self, features: FileFeatures) -> MLPrediction:
        """Analyze behavioral patterns using LSTM model."""
        try:
            if not self.behavioral_analyzer:
                raise ValueError("Behavioral analyzer not initialized")

            # Convert strings to sequence features for LSTM
            sequence_features = await self._create_sequence_features_async(features)

            if sequence_features is None:
                return MLPrediction(
                    model_type=MLModelType.BEHAVIORAL_ANALYZER,
                    prediction_class="insufficient_data",
                    confidence_score=0.0,
                    prediction_time=datetime.now()
                )

            # Make prediction
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None,
                self.behavioral_analyzer.predict,
                np.array([sequence_features])
            )

            confidence = float(prediction[0][0])
            is_suspicious = confidence > BEHAVIORAL_CONFIDENCE_THRESHOLD

            prediction_class = "suspicious_behavior" if is_suspicious else "normal_behavior"

            return MLPrediction(
                model_type=MLModelType.BEHAVIORAL_ANALYZER,
                prediction_class=prediction_class,
                confidence_score=confidence,
                model_version=self.model_versions.get("behavioral_analyzer", "1.0"),
                prediction_time=datetime.now()
            )

        except Exception as e:
            self.logger.error("Error in behavioral analysis: %s", e)
            return MLPrediction(
                model_type=MLModelType.BEHAVIORAL_ANALYZER,
                prediction_class="error",
                confidence_score=0.0,
                prediction_time=datetime.now()
            )

    async def detect_anomaly_async(self, features: FileFeatures) -> MLPrediction:
        """Detect anomalies using Isolation Forest."""
        try:
            if not self.anomaly_detector:
                raise ValueError("Anomaly detector not initialized")

            # Convert features to numerical vector
            feature_vector = await self._features_to_vector_async(features)

            # Make prediction
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None,
                self.anomaly_detector.predict,
                np.array([feature_vector])
            )

            is_anomaly = prediction[0] == -1
            confidence = 0.8 if is_anomaly else 0.2

            prediction_class = "anomaly" if is_anomaly else "normal"

            return MLPrediction(
                model_type=MLModelType.ANOMALY_DETECTOR,
                prediction_class=prediction_class,
                confidence_score=confidence,
                model_version=self.model_versions.get("anomaly_detector", "1.0"),
                prediction_time=datetime.now()
            )

        except Exception as e:
            self.logger.error("Error in anomaly detection: %s", e)
            return MLPrediction(
                model_type=MLModelType.ANOMALY_DETECTOR,
                prediction_class="error",
                confidence_score=0.0,
                prediction_time=datetime.now()
            )

    async def _features_to_vector_async(self, features: FileFeatures) -> np.ndarray:
        """Convert file features to numerical vector for ML models."""
        try:
            # Basic numerical features
            numerical_features = [
                features.file_size,
                features.file_entropy,
                len(features.string_features) if features.string_features else 0,
                1 if features.pe_features else 0,
                len(features.magic_bytes) if features.magic_bytes else 0,
            ]

            # Pad to required length (1000 features for this example)
            while len(numerical_features) < FEATURE_VECTOR_SIZE:
                numerical_features.append(0.0)

            return np.array(numerical_features[:FEATURE_VECTOR_SIZE], dtype=np.float32)

        except Exception as e:
            self.logger.error("Error converting features to vector: %s", e)
            return np.zeros(FEATURE_VECTOR_SIZE, dtype=np.float32)

    async def _create_sequence_features_async(self, features: FileFeatures) -> np.ndarray | None:
        """Create sequence features for LSTM behavioral analysis."""
        try:
            if not features.string_features:
                return None

            # Convert strings to numerical sequences
            # This is a simplified version - would use more sophisticated encoding in production
            sequences = []

            for string in features.string_features[:MAX_STRING_SEQUENCES]:  # Use first 100 strings
                # Convert string to character codes
                char_codes = [ord(c) % 256 for c in string[:MAX_STRING_LENGTH]]  # Limit string length

                # Pad to fixed length
                while len(char_codes) < MAX_STRING_LENGTH:
                    char_codes.append(0)

                sequences.append(char_codes[:MAX_STRING_LENGTH])

            # Pad sequences to fixed count
            while len(sequences) < MAX_STRING_SEQUENCES:
                sequences.append([0] * MAX_STRING_LENGTH)

            return np.array(sequences[:MAX_STRING_SEQUENCES], dtype=np.float32)

        except Exception as e:
            self.logger.error("Error creating sequence features: %s", e)
            return None

    async def comprehensive_ml_analysis_async(self, file_path: str) -> list[MLPrediction]:
        """Perform comprehensive ML analysis using all available models."""
        try:
            start_time = datetime.now()

            # Extract features
            features = await self.extract_file_features_async(file_path)

            # Run all predictions concurrently
            predictions = await asyncio.gather(
                self.predict_malware_async(features),
                self.analyze_behavior_async(features),
                self.detect_anomaly_async(features),
                return_exceptions=True
            )

            # Filter out exceptions
            valid_predictions = [
                p for p in predictions
                if isinstance(p, MLPrediction)
            ]

            # Update performance metrics
            end_time = datetime.now()
            prediction_time = (end_time - start_time).total_seconds()
            self.avg_prediction_time = (
                (self.avg_prediction_time * (self.predictions_made - 1) + prediction_time)
                / self.predictions_made
            )

            return valid_predictions

        except Exception as e:
            self.logger.error("Error in comprehensive ML analysis for %s: %s", file_path, e)
            return []

    async def ml_to_threat_detection_async(
        self, file_path: str, ml_predictions: list[MLPrediction]
    ) -> ThreatDetection | None:
        """Convert ML predictions to standard threat detection format."""
        try:
            if not ml_predictions:
                return None

            # Aggregate predictions to determine overall threat level
            threat_scores = []
            threat_details = []

            for prediction in ml_predictions:
                if prediction.prediction_class in ['malware', 'suspicious_behavior', 'anomaly']:
                    threat_scores.append(prediction.confidence_score)
                    threat_details.append(f"{prediction.model_type.value}: {prediction.prediction_class}")

            if not threat_scores:
                return None

            # Calculate overall confidence
            overall_confidence = max(threat_scores)

            # Determine threat level
            if overall_confidence >= CRITICAL_THREAT_THRESHOLD:
                threat_level = ThreatLevel.CRITICAL
            elif overall_confidence >= HIGH_THREAT_THRESHOLD:
                threat_level = ThreatLevel.HIGH
            elif overall_confidence >= MEDIUM_THREAT_THRESHOLD:
                threat_level = ThreatLevel.MEDIUM
            else:
                threat_level = ThreatLevel.LOW

            # Get file info
            file_stat = os.stat(file_path)
            file_hash = await self._calculate_file_hash_async(file_path)

            return ThreatDetection(
                file_path=file_path,
                threat_name=f"ML Detection: {', '.join(threat_details)}",
                threat_type=ThreatType.MALWARE,  # Primary type
                threat_level=threat_level,
                detection_time=datetime.now(),
                file_hash=file_hash,
                file_size=file_stat.st_size,
                confidence_score=overall_confidence,
                additional_info={
                    "detection_method": "machine_learning",
                    "ml_predictions": [
                        {
                            "model": p.model_type.value,
                            "class": p.prediction_class,
                            "confidence": p.confidence_score,
                        }
                        for p in ml_predictions
                    ],
                    "overall_confidence": overall_confidence,
                }
            )

        except Exception as e:
            self.logger.error("Error converting ML predictions to threat detection: %s", e)
            return None

    async def get_ml_statistics_async(self) -> dict[str, Any]:
        """Get ML detector performance statistics."""
        return {
            "predictions_made": self.predictions_made,
            "ml_detections": self.ml_detections,
            "detection_rate": (
                self.ml_detections / self.predictions_made
                if self.predictions_made > 0 else 0.0
            ),
            "avg_prediction_time_seconds": self.avg_prediction_time,
            "models_loaded": {
                "malware_classifier": self.malware_classifier is not None,
                "behavioral_analyzer": self.behavioral_analyzer is not None,
                "anomaly_detector": self.anomaly_detector is not None,
                "pattern_recognizer": self.pattern_recognizer is not None,
            },
            "model_versions": self.model_versions,
            "tensorflow_version": tf.__version__,
            "gpu_available": len(tf.config.experimental.list_physical_devices('GPU')) > 0,
        }

    async def save_models_async(self) -> bool:
        """Save all trained models to disk."""
        try:
            loop = asyncio.get_event_loop()

            # Save TensorFlow models
            if self.malware_classifier:
                await loop.run_in_executor(
                    None,
                    self.malware_classifier.save,
                    str(self.models_dir / "malware_classifier.h5")
                )

            if self.behavioral_analyzer:
                await loop.run_in_executor(
                    None,
                    self.behavioral_analyzer.save,
                    str(self.models_dir / "behavioral_analyzer.h5")
                )

            if self.pattern_recognizer:
                await loop.run_in_executor(
                    None,
                    self.pattern_recognizer.save,
                    str(self.models_dir / "pattern_recognizer.h5")
                )

            # Save scikit-learn models
            if self.anomaly_detector:
                with open(self.models_dir / "anomaly_detector.pkl", 'wb') as f:
                    await loop.run_in_executor(None, pickle.dump, self.anomaly_detector, f)

            # Save feature extractors
            if self.tfidf_vectorizer:
                with open(self.models_dir / "tfidf_vectorizer.pkl", 'wb') as f:
                    await loop.run_in_executor(None, pickle.dump, self.tfidf_vectorizer, f)

            if self.feature_scaler:
                with open(self.models_dir / "feature_scaler.pkl", 'wb') as f:
                    await loop.run_in_executor(None, pickle.dump, self.feature_scaler, f)

            self.logger.info("All models saved successfully")
            return True

        except Exception as e:
            self.logger.error("Error saving models: %s", e)
            return False

    async def shutdown_async(self) -> None:
        """Shutdown ML detector and clean up resources."""
        try:
            # Save models before shutdown
            await self.save_models_async()

            # Clear models from memory
            del self.malware_classifier
            del self.behavioral_analyzer
            del self.anomaly_detector
            del self.pattern_recognizer
            del self.tfidf_vectorizer
            del self.feature_scaler

            # Clear TensorFlow session
            tf.keras.backend.clear_session()

            self.logger.info("ML threat detector shutdown completed")

        except Exception as e:
            self.logger.error("Error during ML detector shutdown: %s", e)


# Integration function for existing threat detector
async def enhance_threat_detector_with_ml(
    threat_detector: Any,
    ml_detector: MLThreatDetector
) -> None:
    """Enhance existing threat detector with ML capabilities."""
    try:
        # This would integrate ML predictions into the existing async threat detector
        # For demonstration purposes, we'll add ML as an additional detection method

        original_scan_method = threat_detector._perform_async_scan

        async def enhanced_scan_method(file_path: str, stat_result: Any):
            # Run original scan
            original_result = await original_scan_method(file_path, stat_result)

            # If no threat found by traditional methods, try ML
            if not original_result.is_threat:
                ml_predictions = await ml_detector.comprehensive_ml_analysis_async(file_path)
                ml_threat = await ml_detector.ml_to_threat_detection_async(file_path, ml_predictions)

                if ml_threat:
                    from app.core.async_threat_detector import ScanResult
                    return ScanResult(
                        file_path=file_path,
                        is_threat=True,
                        threat_detection=ml_threat
                    )

            return original_result

        # Replace the scan method with enhanced version
        threat_detector._perform_async_scan = enhanced_scan_method

    except Exception as e:
        logging.error("Error enhancing threat detector with ML: %s", e)


    async def cleanup_ml_resources_async(self) -> None:
        """Clean up ML resources and memory properly."""
        try:
            self.logger.info("Starting ML resource cleanup...")

            # Clear model references
            if self.malware_classifier:
                del self.malware_classifier
                self.malware_classifier = None

            if self.behavioral_analyzer:
                del self.behavioral_analyzer
                self.behavioral_analyzer = None

            if self.pattern_recognizer:
                del self.pattern_recognizer
                self.pattern_recognizer = None

            if self.anomaly_detector:
                del self.anomaly_detector
                self.anomaly_detector = None

            # Clear feature extractors
            if self.tfidf_vectorizer:
                del self.tfidf_vectorizer
                self.tfidf_vectorizer = None

            if self.feature_scaler:
                del self.feature_scaler
                self.feature_scaler = None

            # Clear TensorFlow session and backend
            tf.keras.backend.clear_session()
            if hasattr(tf.python.keras.backend, 'clear_session'):
                tf.python.keras.backend.clear_session()

            # Force garbage collection
            import gc
            gc.collect()

            # Reset performance tracking
            self.predictions_made = 0
            self.ml_detections = 0
            self.avg_prediction_time = 0.0

            self.logger.info("ML resource cleanup completed successfully")

        except Exception as e:
            self.logger.error("Error during ML resource cleanup: %s", e)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialization_task
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup_ml_resources_async()


# Convenience function for creating ML detector with context management
async def create_ml_threat_detector(**kwargs) -> MLThreatDetector:
    """Create and initialize ML threat detector with proper resource management."""
    detector = MLThreatDetector(**kwargs)
    await detector._initialization_task
    return detector
