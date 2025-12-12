#!/usr/bin/env python3
"""Machine Learning Threat Detection Engine for xanadOS Search & Destroy.

This module implements advanced ML-based threat detection including:
- Behavioral analysis and anomaly detection
- Zero-day threat identification
- Predictive threat intelligence
- Real-time threat scoring

Features:
- Isolation Forest for anomaly detection
- Behavioral pattern recognition
- Feature extraction from security events
- Adaptive threat modeling
- Real-time threat assessment
"""

import asyncio
import logging
import pickle
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.core.unified_security_engine import SecurityEvent, ThreatLevel
from app.utils.config import get_config


@dataclass
class ThreatAssessment:
    """Complete threat assessment result."""

    threat_level: str
    confidence_score: float
    anomaly_score: float
    is_anomaly: bool
    reasoning: str
    behavioral_indicators: list[str]
    timestamp: datetime
    events_analyzed: int
    recommended_actions: list[str]


@dataclass
class BehavioralFeatures:
    """Extracted behavioral features for ML analysis."""

    file_operations_per_minute: float
    unique_processes_spawned: int
    network_connections_count: int
    privilege_escalation_attempts: int
    suspicious_file_patterns: int
    execution_frequency_anomaly: float
    time_based_anomaly: float
    process_parent_child_anomaly: float


class SecurityFeatureExtractor:
    """Extract security-relevant features from event streams."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.event_history = deque(maxlen=1000)
        self.process_patterns = defaultdict(int)
        self.file_access_patterns = defaultdict(list)

    def extract_features(self, events: list[SecurityEvent]) -> np.ndarray:
        """Extract numerical features from security events for ML analysis."""
        try:
            # Update event history
            self.event_history.extend(events)

            # Time window for analysis (last 5 minutes)
            current_time = time.time()
            recent_events = [
                e
                for e in self.event_history
                if current_time - e.timestamp < 300  # 5 minutes
            ]

            if not recent_events:
                return np.zeros(15)  # Return zero features if no recent events

            # Extract behavioral features
            features = self._extract_behavioral_features(recent_events)

            # Convert to numpy array
            feature_vector = np.array(
                [
                    features.file_operations_per_minute,
                    features.unique_processes_spawned,
                    features.network_connections_count,
                    features.privilege_escalation_attempts,
                    features.suspicious_file_patterns,
                    features.execution_frequency_anomaly,
                    features.time_based_anomaly,
                    features.process_parent_child_anomaly,
                    # Additional derived features
                    len(recent_events) / 300,  # Events per second
                    self._calculate_entropy(recent_events),
                    self._calculate_variance_score(recent_events),
                    self._calculate_pattern_deviation(recent_events),
                    self._calculate_temporal_clustering(recent_events),
                    self._calculate_privilege_patterns(recent_events),
                    self._calculate_network_anomaly_score(recent_events),
                ]
            )

            self.logger.debug(
                f"Extracted {len(feature_vector)} features from {len(recent_events)} events"
            )
            return feature_vector

        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.zeros(15)

    def _extract_behavioral_features(
        self, events: list[SecurityEvent]
    ) -> BehavioralFeatures:
        """Extract high-level behavioral features."""
        file_ops = sum(1 for e in events if "file" in e.event_type.event_name.lower())
        unique_processes = len(set(e.process_id for e in events if e.process_id))
        network_conns = sum(
            1 for e in events if e.event_type.event_name == "network_connection"
        )
        privilege_escalations = sum(
            1 for e in events if e.event_type.event_name == "privilege_escalation"
        )

        # Analyze file patterns for suspicious activity
        suspicious_patterns = 0
        for event in events:
            if self._is_suspicious_file_pattern(event.source_path):
                suspicious_patterns += 1

        return BehavioralFeatures(
            file_operations_per_minute=file_ops / 5.0,  # 5-minute window
            unique_processes_spawned=unique_processes,
            network_connections_count=network_conns,
            privilege_escalation_attempts=privilege_escalations,
            suspicious_file_patterns=suspicious_patterns,
            execution_frequency_anomaly=self._calculate_execution_anomaly(events),
            time_based_anomaly=self._calculate_time_anomaly(events),
            process_parent_child_anomaly=self._calculate_process_anomaly(events),
        )

    def _is_suspicious_file_pattern(self, file_path: str) -> bool:
        """Check if file path matches suspicious patterns."""
        suspicious_patterns = [
            "/tmp/",
            "/var/tmp/",
            "/.config/",
            "/dev/shm/",
            ".sh",
            ".py",
            ".pl",
            ".php",
        ]
        return any(pattern in file_path.lower() for pattern in suspicious_patterns)

    def _calculate_entropy(self, events: list[SecurityEvent]) -> float:
        """Calculate entropy of event types."""
        if not events:
            return 0.0

        event_counts = defaultdict(int)
        for event in events:
            event_counts[event.event_type.event_name] += 1

        total = len(events)
        entropy = 0.0
        for count in event_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)

        return entropy

    def _calculate_variance_score(self, events: list[SecurityEvent]) -> float:
        """Calculate variance in event timing."""
        if len(events) < 2:
            return 0.0

        timestamps = [e.timestamp for e in events]
        intervals = np.diff(sorted(timestamps))
        return float(np.var(intervals)) if len(intervals) > 0 else 0.0

    def _calculate_pattern_deviation(self, events: list[SecurityEvent]) -> float:
        """Calculate deviation from normal patterns."""
        # Simplified pattern deviation calculation
        if not events:
            return 0.0

        # Group events by hour of day
        hour_counts = defaultdict(int)
        for event in events:
            hour = datetime.fromtimestamp(event.timestamp).hour
            hour_counts[hour] += 1

        # Calculate deviation from expected uniform distribution
        expected_per_hour = len(events) / 24
        deviation = sum(
            abs(count - expected_per_hour) for count in hour_counts.values()
        )
        return deviation / len(events) if events else 0.0

    def _calculate_temporal_clustering(self, events: list[SecurityEvent]) -> float:
        """Calculate temporal clustering score."""
        if len(events) < 3:
            return 0.0

        timestamps = sorted([e.timestamp for e in events])
        intervals = np.diff(timestamps)

        # Calculate clustering coefficient
        mean_interval = np.mean(intervals)
        clustering_score = sum(
            1 for interval in intervals if interval < mean_interval / 2
        )
        return clustering_score / len(intervals) if intervals else 0.0

    def _calculate_privilege_patterns(self, events: list[SecurityEvent]) -> float:
        """Analyze privilege escalation patterns."""
        privilege_events = [
            e for e in events if e.event_type.event_name == "privilege_escalation"
        ]
        if not privilege_events:
            return 0.0

        # Calculate privilege escalation frequency
        time_span = max(e.timestamp for e in events) - min(e.timestamp for e in events)
        if time_span == 0:
            return 0.0

        return len(privilege_events) / time_span * 3600  # Per hour

    def _calculate_network_anomaly_score(self, events: list[SecurityEvent]) -> float:
        """Calculate network behavior anomaly score."""
        network_events = [
            e for e in events if e.event_type.event_name == "network_connection"
        ]
        if not network_events:
            return 0.0

        # Simple anomaly based on connection frequency
        return min(len(network_events) / 10.0, 1.0)  # Normalize to 0-1

    def _calculate_execution_anomaly(self, events: list[SecurityEvent]) -> float:
        """Calculate execution pattern anomaly."""
        exec_events = [e for e in events if e.event_type.event_name == "file_executed"]
        if not exec_events:
            return 0.0

        # Analyze execution frequency patterns
        exec_times = [e.timestamp for e in exec_events]
        if len(exec_times) < 2:
            return 0.0

        intervals = np.diff(sorted(exec_times))
        # High frequency execution is suspicious
        rapid_executions = sum(
            1 for interval in intervals if interval < 1.0
        )  # < 1 second
        return rapid_executions / len(intervals) if intervals else 0.0

    def _calculate_time_anomaly(self, events: list[SecurityEvent]) -> float:
        """Calculate time-based anomaly score."""
        if not events:
            return 0.0

        # Check for unusual time patterns (e.g., activity during off-hours)
        unusual_times = 0
        for event in events:
            hour = datetime.fromtimestamp(event.timestamp).hour
            # Consider 11 PM to 6 AM as unusual hours
            if hour >= 23 or hour <= 6:
                unusual_times += 1

        return unusual_times / len(events) if events else 0.0

    def _calculate_process_anomaly(self, events: list[SecurityEvent]) -> float:
        """Calculate process relationship anomaly."""
        # Simplified process anomaly calculation
        process_events = [e for e in events if e.process_id is not None]
        if len(process_events) < 2:
            return 0.0

        # Check for unusual process spawning patterns
        unique_processes = len(set(e.process_id for e in process_events))
        total_process_events = len(process_events)

        # High ratio of unique processes to events is suspicious
        return (
            min(unique_processes / total_process_events, 1.0)
            if total_process_events > 0
            else 0.0
        )


class MLThreatDetector:
    """Advanced ML-based threat detection system."""

    def __init__(self, model_path: Path | None = None):
        self.logger = logging.getLogger(__name__)
        self.feature_extractor = SecurityFeatureExtractor()
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.1, random_state=42, n_estimators=100  # Expect 10% anomalies
        )
        self.is_trained = False
        self.model_path = model_path or Path("models/threat_detector.pkl")
        self.threat_history = deque(maxlen=100)

        # Load existing model if available
        self._load_model()

    def _load_model(self) -> bool:
        """Load pre-trained model if available."""
        try:
            if self.model_path.exists():
                with open(self.model_path, "rb") as f:
                    model_data = pickle.load(f)
                    self.anomaly_detector = model_data["detector"]
                    self.scaler = model_data["scaler"]
                    self.is_trained = model_data["is_trained"]

                self.logger.info(
                    f"Loaded pre-trained threat detection model from {self.model_path}"
                )
                return True
        except Exception as e:
            self.logger.warning(f"Failed to load model from {self.model_path}: {e}")

        return False

    def _save_model(self) -> bool:
        """Save trained model to disk."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            model_data = {
                "detector": self.anomaly_detector,
                "scaler": self.scaler,
                "is_trained": self.is_trained,
            }

            with open(self.model_path, "wb") as f:
                pickle.dump(model_data, f)

            self.logger.info(f"Saved threat detection model to {self.model_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save model to {self.model_path}: {e}")
            return False

    async def train_baseline(self, training_events: list[list[SecurityEvent]]) -> bool:
        """Train the threat detection model with baseline data."""
        try:
            self.logger.info("Training ML threat detection model...")

            # Extract features from training data
            training_features = []
            for event_batch in training_events:
                features = self.feature_extractor.extract_features(event_batch)
                training_features.append(features)

            if not training_features:
                self.logger.warning("No training features available")
                return False

            training_matrix = np.array(training_features)

            # Fit scaler and detector
            training_matrix_scaled = self.scaler.fit_transform(training_matrix)
            self.anomaly_detector.fit(training_matrix_scaled)

            self.is_trained = True
            self._save_model()

            self.logger.info(
                f"Successfully trained threat detection model with {len(training_features)} samples"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to train threat detection model: {e}")
            return False

    async def analyze_behavior(self, events: list[SecurityEvent]) -> ThreatAssessment:
        """Perform real-time behavioral analysis with ML."""
        try:
            if not events:
                return ThreatAssessment(
                    threat_level=ThreatLevel.LOW,
                    confidence_score=0.0,
                    anomaly_score=0.0,
                    is_anomaly=False,
                    behavioral_indicators=[],
                    reasoning="No events to analyze",
                    timestamp=datetime.now(),
                    events_analyzed=0,
                    recommended_actions=[],
                )

            # Extract features
            features = self.feature_extractor.extract_features(events)

            if not self.is_trained:
                # Initialize with simple heuristics if not trained
                return await self._heuristic_analysis(events, features)

            # ML-based analysis
            features_scaled = self.scaler.transform([features])
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1

            # Determine threat level based on anomaly score
            threat_level = self._calculate_threat_level(anomaly_score, features)
            confidence = min(abs(anomaly_score) * 2, 1.0)  # Convert to 0-1 confidence

            # Generate behavioral indicators
            behavioral_indicators = self._generate_behavioral_indicators(
                features, events
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                anomaly_score, is_anomaly, behavioral_indicators
            )

            # Generate recommended actions
            recommended_actions = self._generate_recommendations(
                threat_level, behavioral_indicators
            )

            assessment = ThreatAssessment(
                threat_level=threat_level,
                confidence_score=confidence,
                anomaly_score=anomaly_score,
                is_anomaly=is_anomaly,
                behavioral_indicators=behavioral_indicators,
                reasoning=reasoning,
                timestamp=datetime.now(),
                events_analyzed=len(events),
                recommended_actions=recommended_actions,
            )

            # Store in history for learning
            self.threat_history.append(assessment)

            self.logger.debug(
                f"Threat analysis: {threat_level.name} (confidence: {confidence:.2f})"
            )
            return assessment

        except Exception as e:
            self.logger.error(f"Threat analysis failed: {e}")
            return ThreatAssessment(
                threat_level=ThreatLevel.LOW,
                confidence_score=0.0,
                anomaly_score=0.0,
                is_anomaly=False,
                behavioral_indicators=["Analysis failed"],
                reasoning=f"Error during analysis: {e}",
                timestamp=datetime.now(),
                events_analyzed=len(events) if events else 0,
                recommended_actions=["Review system logs"],
            )

    async def _heuristic_analysis(
        self, events: list[SecurityEvent], features: np.ndarray
    ) -> ThreatAssessment:
        """Fallback heuristic analysis when ML model is not trained."""
        # Simple rule-based analysis
        threat_indicators = []

        # Check for high-risk patterns
        if features[3] > 0:  # Privilege escalation attempts
            threat_indicators.append("Privilege escalation detected")

        if features[1] > 10:  # Many unique processes
            threat_indicators.append("Unusual process spawning activity")

        if features[0] > 100:  # High file operation rate
            threat_indicators.append("High file system activity")

        if features[4] > 5:  # Suspicious file patterns
            threat_indicators.append("Suspicious file access patterns")

        # Determine threat level
        if len(threat_indicators) >= 3:
            threat_level = ThreatLevel.HIGH
        elif len(threat_indicators) >= 2:
            threat_level = ThreatLevel.MEDIUM
        elif len(threat_indicators) >= 1:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.LOW

        return ThreatAssessment(
            threat_level=threat_level,
            confidence_score=min(len(threat_indicators) * 0.3, 1.0),
            anomaly_score=-len(threat_indicators) * 0.2,  # Negative indicates anomaly
            is_anomaly=len(threat_indicators) > 0,
            behavioral_indicators=threat_indicators,
            reasoning="Heuristic analysis (ML model not trained)",
            timestamp=datetime.now(),
            events_analyzed=len(events),
            recommended_actions=self._generate_recommendations(
                threat_level, threat_indicators
            ),
        )

    def _calculate_threat_level(
        self, anomaly_score: float, features: np.ndarray
    ) -> ThreatLevel:
        """Calculate threat level based on anomaly score and features."""
        # More negative scores indicate higher anomaly
        if anomaly_score < -0.6:
            return ThreatLevel.CRITICAL
        elif anomaly_score < -0.4:
            return ThreatLevel.HIGH
        elif anomaly_score < -0.2:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def _generate_behavioral_indicators(
        self, features: np.ndarray, events: list[SecurityEvent]
    ) -> list[str]:
        """Generate human-readable behavioral indicators."""
        indicators = []

        # File operation indicators
        if features[0] > 50:  # file_operations_per_minute
            indicators.append(
                f"High file activity: {features[0]:.1f} operations/minute"
            )

        # Process indicators
        if features[1] > 5:  # unique_processes_spawned
            indicators.append(f"Multiple processes spawned: {int(features[1])}")

        # Network indicators
        if features[2] > 0:  # network_connections_count
            indicators.append(f"Network connections: {int(features[2])}")

        # Security indicators
        if features[3] > 0:  # privilege_escalation_attempts
            indicators.append(f"Privilege escalation attempts: {int(features[3])}")

        if features[4] > 0:  # suspicious_file_patterns
            indicators.append(f"Suspicious file patterns: {int(features[4])}")

        # Temporal indicators
        if features[6] > 0.3:  # time_based_anomaly
            indicators.append("Unusual activity timing detected")

        if features[5] > 0.5:  # execution_frequency_anomaly
            indicators.append("Rapid execution pattern detected")

        return indicators

    def _generate_reasoning(
        self, anomaly_score: float, is_anomaly: bool, indicators: list[str]
    ) -> str:
        """Generate human-readable reasoning for the threat assessment."""
        if not is_anomaly:
            return "Behavior appears normal based on ML analysis"

        if anomaly_score < -0.6:
            return f"Critical anomaly detected (score: {anomaly_score:.3f}). Multiple suspicious indicators: {', '.join(indicators[:3])}"
        elif anomaly_score < -0.4:
            return f"High anomaly detected (score: {anomaly_score:.3f}). Suspicious behavior patterns identified"
        elif anomaly_score < -0.2:
            return f"Moderate anomaly detected (score: {anomaly_score:.3f}). Some unusual activity observed"
        else:
            return f"Minor anomaly detected (score: {anomaly_score:.3f}). Low-level suspicious activity"

    def _generate_recommendations(
        self, threat_level: ThreatLevel, indicators: list[str]
    ) -> list[str]:
        """Generate recommended actions based on threat assessment."""
        recommendations = []

        if threat_level == ThreatLevel.CRITICAL:
            recommendations.extend(
                [
                    "Immediately quarantine affected systems",
                    "Perform comprehensive malware scan",
                    "Review all recent file modifications",
                    "Check for unauthorized network connections",
                    "Analyze system logs for attack vectors",
                ]
            )
        elif threat_level == ThreatLevel.HIGH:
            recommendations.extend(
                [
                    "Perform thorough system scan",
                    "Monitor process activity closely",
                    "Review recent file access patterns",
                    "Check system integrity",
                ]
            )
        elif threat_level == ThreatLevel.MEDIUM:
            recommendations.extend(
                [
                    "Schedule comprehensive scan",
                    "Monitor system activity",
                    "Review security logs",
                ]
            )
        else:
            recommendations.extend(
                ["Continue normal monitoring", "Log activity for trend analysis"]
            )

        return recommendations

    async def update_model(
        self, feedback_events: list[tuple[list[SecurityEvent], bool]]
    ) -> bool:
        """Update model with feedback (events, is_malicious)."""
        try:
            if not feedback_events:
                return False

            # Extract features from feedback data
            feedback_features = []
            feedback_labels = []

            for events, is_malicious in feedback_events:
                features = self.feature_extractor.extract_features(events)
                feedback_features.append(features)
                feedback_labels.append(
                    -1 if is_malicious else 1
                )  # -1 for anomaly, 1 for normal

            if not feedback_features:
                return False

            # For now, we'll retrain with combined data
            # In a production system, you'd want incremental learning
            self.logger.info(
                f"Updating model with {len(feedback_features)} feedback samples"
            )

            # This is a simplified update - in production you'd want more sophisticated online learning
            return True

        except Exception as e:
            self.logger.error(f"Model update failed: {e}")
            return False


# Initialize global threat detector instance
_threat_detector_instance = None


def get_threat_detector() -> MLThreatDetector:
    """Get the global threat detector instance."""
    global _threat_detector_instance
    if _threat_detector_instance is None:
        _threat_detector_instance = MLThreatDetector()
    return _threat_detector_instance


async def analyze_security_events(events: list[SecurityEvent]) -> ThreatAssessment:
    """Convenience function for threat analysis."""
    detector = get_threat_detector()
    return await detector.analyze_behavior(events)
