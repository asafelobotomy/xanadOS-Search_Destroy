#!/usr/bin/env python3
"""
JSON-based experiment logger for reproducibility.

Provides local experiment logging independent of external services.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class ExperimentLog:
    """Log entry for a single experiment."""

    experiment_id: str  # Unique ID
    name: str  # Experiment name
    created_at: str  # ISO timestamp

    # Configuration
    model_architecture: str
    hyperparameters: dict[str, Any]
    feature_version: str
    dataset_hash: str  # SHA256 of training data

    # Training results
    metrics: dict[str, float]
    training_time_seconds: float

    # Environment
    python_version: str
    dependencies: dict[str, str]  # package -> version

    # Artifacts
    model_path: Optional[str] = None
    checkpoint_paths: list[str] = field(default_factory=list)

    # Metadata
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if self.checkpoint_paths is None:
            self.checkpoint_paths = []
        if self.tags is None:
            self.tags = []


class ExperimentLogger:
    """
    Local experiment logger using JSON files.

    Features:
    - Structured experiment logging
    - Reproducibility tracking (datasets, hyperparameters, environment)
    - Experiment comparison
    - Search and filtering
    """

    def __init__(self, log_dir: Path | str = "models/experiments"):
        """
        Initialize experiment logger.

        Args:
            log_dir: Directory for experiment logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.log_dir / "experiment_index.json"
        self._load_index()

    def _load_index(self):
        """Load experiment index."""
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {
                "experiments": [],
                "last_updated": datetime.utcnow().isoformat(),
            }

    def _save_index(self):
        """Save experiment index."""
        self.index["last_updated"] = datetime.utcnow().isoformat()

        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    def log_experiment(self, experiment: ExperimentLog) -> str:
        """
        Log a new experiment.

        Args:
            experiment: Experiment log entry

        Returns:
            Experiment ID
        """
        # Generate experiment ID if not provided
        if not experiment.experiment_id:
            experiment.experiment_id = self._generate_experiment_id(experiment.name)

        # Save experiment log
        log_filename = f"{experiment.experiment_id}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, "w") as f:
            json.dump(asdict(experiment), f, indent=2)

        # Update index
        self.index["experiments"].append(
            {
                "experiment_id": experiment.experiment_id,
                "name": experiment.name,
                "created_at": experiment.created_at,
                "model_architecture": experiment.model_architecture,
                "tags": experiment.tags,
            }
        )

        self._save_index()

        return experiment.experiment_id

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentLog]:
        """
        Retrieve an experiment by ID.

        Args:
            experiment_id: Experiment ID

        Returns:
            ExperimentLog or None if not found
        """
        log_path = self.log_dir / f"{experiment_id}.json"

        if not log_path.exists():
            return None

        with open(log_path) as f:
            data = json.load(f)

        return ExperimentLog(**data)

    def list_experiments(
        self,
        tags: Optional[list[str]] = None,
        architecture: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        List experiments with optional filtering.

        Args:
            tags: Filter by tags (any match)
            architecture: Filter by model architecture
            limit: Maximum number of results

        Returns:
            List of experiment summaries
        """
        experiments = self.index["experiments"]

        # Apply filters
        if tags:
            experiments = [
                e for e in experiments if any(tag in e.get("tags", []) for tag in tags)
            ]

        if architecture:
            experiments = [
                e for e in experiments if e.get("model_architecture") == architecture
            ]

        # Sort by creation time (newest first)
        experiments.sort(key=lambda e: e.get("created_at", ""), reverse=True)

        # Apply limit
        if limit:
            experiments = experiments[:limit]

        return experiments

    def compare_experiments(self, experiment_ids: list[str]) -> dict[str, Any]:
        """
        Compare multiple experiments.

        Args:
            experiment_ids: List of experiment IDs to compare

        Returns:
            Comparison dictionary
        """
        experiments = [self.get_experiment(eid) for eid in experiment_ids]

        # Filter out None values
        experiments = [e for e in experiments if e is not None]

        if not experiments:
            return {"error": "No valid experiments found"}

        comparison = {
            "experiment_ids": experiment_ids,
            "experiment_names": [e.name for e in experiments],
            "metrics": {},
            "hyperparameters": {},
            "training_time": {
                e.experiment_id: e.training_time_seconds for e in experiments
            },
        }

        # Compare metrics
        all_metric_keys: set[str] = set()
        for exp in experiments:
            all_metric_keys.update(exp.metrics.keys())

        for key in all_metric_keys:
            comparison["metrics"][key] = {
                exp.experiment_id: exp.metrics.get(key, None) for exp in experiments
            }

        # Compare hyperparameters
        all_hp_keys: set[str] = set()
        for exp in experiments:
            all_hp_keys.update(exp.hyperparameters.keys())

        for key in all_hp_keys:
            comparison["hyperparameters"][key] = {
                exp.experiment_id: exp.hyperparameters.get(key, None)
                for exp in experiments
            }

        return comparison

    def get_best_experiment(
        self,
        metric: str = "accuracy",
        maximize: bool = True,
        tags: Optional[list[str]] = None,
    ) -> Optional[ExperimentLog]:
        """
        Find the best experiment based on a metric.

        Args:
            metric: Metric name to optimize
            maximize: Whether higher is better
            tags: Filter by tags

        Returns:
            Best experiment or None
        """
        experiments_list = self.list_experiments(tags=tags)

        if not experiments_list:
            return None

        # Load full experiments and filter by metric
        valid_experiments = []
        for exp_summary in experiments_list:
            exp = self.get_experiment(exp_summary["experiment_id"])
            if exp and metric in exp.metrics:
                valid_experiments.append(exp)

        if not valid_experiments:
            return None

        # Find best
        best = max(
            valid_experiments, key=lambda e: e.metrics[metric] * (1 if maximize else -1)
        )

        return best

    @staticmethod
    def _generate_experiment_id(name: str) -> str:
        """Generate unique experiment ID."""
        timestamp = datetime.utcnow().isoformat()
        unique_string = f"{name}_{timestamp}"

        hash_obj = hashlib.sha256(unique_string.encode())
        return hash_obj.hexdigest()[:16]
