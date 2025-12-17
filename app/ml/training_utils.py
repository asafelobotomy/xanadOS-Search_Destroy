#!/usr/bin/env python3
"""
Training utilities for ML model development.

Provides helper functions for:
- Loading feature datasets
- Computing dataset hashes for reproducibility
- Handling class imbalance
- Training/validation/test splitting
- Metric calculation
"""

import hashlib
import time
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.utils.class_weight import compute_class_weight


def load_features(
    split: str = "train", features_dir: Path | str = "data/features"
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load feature vectors from .npz files.

    Args:
        split: Dataset split ("train", "val", or "test")
        features_dir: Base features directory

    Returns:
        Tuple of (X, y) where:
        - X: Feature matrix (n_samples, n_features)
        - y: Labels (n_samples,) where 0=benign, 1=malware
    """
    features_dir = Path(features_dir)
    split_dir = features_dir / split

    # Load malware features
    malware_dir = split_dir / "malware"
    malware_features = []

    for npz_file in malware_dir.glob("*.npz"):
        features = np.load(npz_file)["features"]
        malware_features.append(features)

    # Load benign features
    benign_dir = split_dir / "benign"
    benign_features = []

    for npz_file in benign_dir.glob("*.npz"):
        features = np.load(npz_file)["features"]
        benign_features.append(features)

    # Combine into arrays
    X_malware = np.array(malware_features, dtype=np.float32)
    X_benign = np.array(benign_features, dtype=np.float32)

    # Create labels (1 = malware, 0 = benign)
    y_malware = np.ones(len(X_malware), dtype=np.int32)
    y_benign = np.zeros(len(X_benign), dtype=np.int32)

    # Concatenate
    X = np.vstack([X_malware, X_benign])
    y = np.concatenate([y_malware, y_benign])

    # Shuffle (with fixed seed for reproducibility)
    rng = np.random.RandomState(42)
    shuffle_idx = rng.permutation(len(X))

    X = X[shuffle_idx]
    y = y[shuffle_idx]

    return X, y


def compute_dataset_hash(X: np.ndarray, y: np.ndarray) -> str:
    """
    Compute SHA256 hash of dataset for reproducibility tracking.

    Args:
        X: Feature matrix
        y: Labels

    Returns:
        SHA256 hex digest
    """
    # Combine X and y into single array
    data = np.column_stack([X, y.reshape(-1, 1)])

    # Compute hash
    sha256 = hashlib.sha256()
    sha256.update(data.tobytes())

    return sha256.hexdigest()


def get_class_weights(y: np.ndarray) -> dict[int, float]:
    """
    Compute class weights for handling imbalance.

    Args:
        y: Labels array

    Returns:
        Dictionary mapping class -> weight
    """
    classes = np.unique(y)
    weights = compute_class_weight("balanced", classes=classes, y=y)

    return {cls: weight for cls, weight in zip(classes, weights)}


def compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None
) -> dict[str, float]:
    """
    Compute comprehensive classification metrics.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_prob: Predicted probabilities (optional, for AUC)

    Returns:
        Dictionary of metrics
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }

    # Add AUC if probabilities provided
    if y_prob is not None:
        try:
            metrics["auc"] = roc_auc_score(y_true, y_prob)
        except ValueError:
            # Skip if only one class present
            pass

    # Add confusion matrix components
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    metrics.update(
        {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
            "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0.0,
        }
    )

    return metrics


def time_training(func):
    """Decorator to time training functions."""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time

        return result, elapsed_time

    return wrapper


def get_feature_importance(
    model, feature_names: list[str], top_k: int = 20
) -> list[tuple[str, float]]:
    """
    Get feature importance from trained model.

    Args:
        model: Trained model with feature_importances_ attribute
        feature_names: List of feature names
        top_k: Number of top features to return

    Returns:
        List of (feature_name, importance) tuples, sorted by importance
    """
    if not hasattr(model, "feature_importances_"):
        raise ValueError("Model does not have feature_importances_ attribute")

    importances = model.feature_importances_

    # Create (name, importance) pairs
    feature_importance_pairs = list(zip(feature_names, importances))

    # Sort by importance (descending)
    feature_importance_pairs.sort(key=lambda x: x[1], reverse=True)

    return feature_importance_pairs[:top_k]


def print_training_summary(
    model_name: str,
    train_metrics: dict[str, float],
    val_metrics: dict[str, float],
    test_metrics: dict[str, float],
    training_time: float,
):
    """
    Print formatted training summary.

    Args:
        model_name: Name of trained model
        train_metrics: Training set metrics
        val_metrics: Validation set metrics
        test_metrics: Test set metrics
        training_time: Training time in seconds
    """
    print(f"\n{'='*70}")
    print(f"  {model_name} Training Summary")
    print(f"{'='*70}\n")

    print(f"Training Time: {training_time:.2f} seconds\n")

    # Metrics table
    print(f"{'Metric':<20} {'Train':<12} {'Val':<12} {'Test':<12}")
    print(f"{'-'*20} {'-'*12} {'-'*12} {'-'*12}")

    # Show main metrics
    for metric in ["accuracy", "precision", "recall", "f1", "auc"]:
        if metric in test_metrics:
            train_val = train_metrics.get(metric, 0.0)
            val_val = val_metrics.get(metric, 0.0)
            test_val = test_metrics.get(metric, 0.0)

            print(
                f"{metric.capitalize():<20} "
                f"{train_val:<12.4f} "
                f"{val_val:<12.4f} "
                f"{test_val:<12.4f}"
            )

    print(f"\n{'='*70}\n")
