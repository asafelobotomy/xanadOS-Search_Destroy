"""
ML-based threat detection module.

This module implements machine learning-based malware detection using:
- Static feature extraction from PE/ELF binaries
- Random Forest baseline classifier
- Transformer-based sequence models (BERT)
- Ensemble learning for robust predictions
- Model explainability (SHAP values)

Phase 3: Task 3.1 - ML-Based Threat Detection
"""

__version__ = "3.1.0-dev"
__author__ = "xanadOS Security Team"

from pathlib import Path

# Module exports
__all__ = [
    "FeatureExtractor",
    "ModelRegistry",
    "MalwareInferenceEngine",
]


# Lazy imports to avoid loading heavy ML dependencies unless needed
def __getattr__(name: str):
    """Lazy import ML components."""
    if name == "FeatureExtractor":
        from .feature_extractor import FeatureExtractor

        return FeatureExtractor
    elif name == "ModelRegistry":
        from .model_registry import ModelRegistry

        return ModelRegistry
    elif name == "MalwareInferenceEngine":
        from .inference import MalwareInferenceEngine

        return MalwareInferenceEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
