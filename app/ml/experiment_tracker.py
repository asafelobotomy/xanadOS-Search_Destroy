#!/usr/bin/env python3
"""
Experiment tracking integration with wandb (Weights & Biases).

Provides a unified interface for tracking ML experiments, metrics, and artifacts.
"""

import os
from pathlib import Path
from typing import Optional, Any

try:
    import wandb

    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False


class ExperimentTracker:
    """
    Wrapper for wandb experiment tracking.

    Features:
    - Automatic experiment initialization
    - Metric logging with step tracking
    - Artifact tracking (models, datasets, configs)
    - Hyperparameter logging
    - Graceful degradation if wandb unavailable
    """

    def __init__(
        self,
        project_name: str = "xanadOS-malware-detection",
        entity: Optional[str] = None,
        offline: bool = False,
    ):
        """
        Initialize experiment tracker.

        Args:
            project_name: wandb project name
            entity: wandb entity (username/organization)
            offline: Whether to run in offline mode
        """
        self.project_name = project_name
        self.entity = entity
        self.offline = offline
        self.run = None
        self.enabled = WANDB_AVAILABLE

        if not WANDB_AVAILABLE:
            print("⚠️  wandb not available - experiment tracking disabled")
            print("   Install with: uv pip install wandb")

    def start_run(
        self,
        name: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> Optional[str]:
        """
        Start a new experiment run.

        Args:
            name: Run name
            config: Hyperparameters and configuration
            tags: Tags for organizing runs
            notes: Optional notes about the experiment

        Returns:
            Run ID (or None if wandb unavailable)
        """
        if not self.enabled:
            return None

        # Set offline mode if requested
        if self.offline:
            os.environ["WANDB_MODE"] = "offline"

        self.run = wandb.init(
            project=self.project_name,
            entity=self.entity,
            name=name,
            config=config,
            tags=tags,
            notes=notes,
            reinit=True,  # Allow multiple runs in same process
        )

        return self.run.id if self.run else None

    def log_metrics(self, metrics: dict[str, float], step: Optional[int] = None):
        """
        Log metrics for current step.

        Args:
            metrics: Dictionary of metric name -> value
            step: Training step/epoch (auto-increments if None)
        """
        if not self.enabled or self.run is None:
            return

        wandb.log(metrics, step=step)

    def log_hyperparameters(self, hyperparameters: dict[str, Any]):
        """
        Log hyperparameters (can be called after run starts).

        Args:
            hyperparameters: Dictionary of hyperparameter values
        """
        if not self.enabled or self.run is None:
            return

        wandb.config.update(hyperparameters)

    def log_artifact(
        self,
        artifact_path: Path | str,
        artifact_type: str,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log an artifact (model, dataset, config file, etc.).

        Args:
            artifact_path: Path to artifact file/directory
            artifact_type: Type of artifact ("model", "dataset", "config")
            name: Artifact name (defaults to filename)
            metadata: Additional metadata
        """
        if not self.enabled or self.run is None:
            return

        artifact_path = Path(artifact_path)

        if name is None:
            name = artifact_path.stem

        artifact = wandb.Artifact(
            name=name, type=artifact_type, metadata=metadata or {}
        )

        if artifact_path.is_dir():
            artifact.add_dir(str(artifact_path))
        else:
            artifact.add_file(str(artifact_path))

        self.run.log_artifact(artifact)

    def log_model(
        self,
        model_path: Path | str,
        model_name: str,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log a trained model as an artifact.

        Args:
            model_path: Path to saved model file
            model_name: Model name
            metadata: Model metadata (hyperparameters, metrics, etc.)
        """
        self.log_artifact(
            artifact_path=model_path,
            artifact_type="model",
            name=model_name,
            metadata=metadata,
        )

    def log_dataset(
        self,
        dataset_path: Path | str,
        dataset_name: str,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Log a dataset as an artifact.

        Args:
            dataset_path: Path to dataset directory
            dataset_name: Dataset name
            metadata: Dataset metadata (size, splits, etc.)
        """
        self.log_artifact(
            artifact_path=dataset_path,
            artifact_type="dataset",
            name=dataset_name,
            metadata=metadata,
        )

    def log_confusion_matrix(
        self,
        y_true: list[int],
        y_pred: list[int],
        class_names: Optional[list[str]] = None,
    ):
        """
        Log a confusion matrix visualization.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Names of classes (e.g., ["benign", "malware"])
        """
        if not self.enabled or self.run is None:
            return

        if class_names is None:
            class_names = ["benign", "malware"]

        wandb.log(
            {
                "confusion_matrix": wandb.plot.confusion_matrix(
                    probs=None, y_true=y_true, preds=y_pred, class_names=class_names
                )
            }
        )

    def log_roc_curve(
        self,
        y_true: list[int],
        y_scores: list[float],
        class_names: Optional[list[str]] = None,
    ):
        """
        Log ROC curve visualization.

        Args:
            y_true: True binary labels
            y_scores: Predicted probabilities for positive class
            class_names: Names of classes
        """
        if not self.enabled or self.run is None:
            return

        if class_names is None:
            class_names = ["benign", "malware"]

        wandb.log(
            {"roc_curve": wandb.plot.roc_curve(y_true, y_scores, labels=class_names)}
        )

    def finish(self):
        """Finish the current run."""
        if not self.enabled or self.run is None:
            return

        wandb.finish()
        self.run = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - finish run."""
        self.finish()
