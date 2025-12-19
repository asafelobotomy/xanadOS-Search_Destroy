#!/usr/bin/env python3
"""
Model Registry for ML models with version management and metadata tracking.

Provides:
- Semantic versioning for models
- Model metadata storage (hyperparameters, metrics, training data)
- Model file integrity verification (SHA256 hashing)
- Experiment tracking and comparison
- Model rollback capabilities
"""

import hashlib
import json
import shutil
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import joblib


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""

    version: str  # Semantic version (e.g., "1.0.0")
    name: str  # Model name/identifier
    architecture: str  # Model type (e.g., "RandomForest", "CNN")
    created_at: str  # ISO timestamp
    author: str  # Creator username

    # Training configuration
    hyperparameters: dict[str, Any]
    training_data_hash: str  # SHA256 of training dataset
    feature_version: str  # Feature extractor version

    # Performance metrics
    metrics: dict[str, float]  # accuracy, precision, recall, f1, etc.

    # Model file information
    model_path: str  # Relative path to model file
    model_hash: str  # SHA256 of model file
    model_size_bytes: int

    # Additional metadata
    description: str = ""
    tags: list[str] = field(default_factory=list)
    experiment_id: Optional[str] = None  # wandb run ID

    # __post_init__ removed - using field(default_factory=list) for defaults

    @property
    def stage(self) -> str:
        """Determine model stage from model_path."""
        return "production" if "production" in self.model_path else "checkpoint"


class ModelRegistry:
    """
    Model registry for managing ML model versions.

    Features:
    - Semantic versioning
    - Model metadata tracking
    - File integrity verification
    - Experiment comparison
    - Model promotion (dev → staging → production)
    """

    def __init__(self, registry_dir: Path | str = "models"):
        """
        Initialize model registry.

        Args:
            registry_dir: Base directory for model storage
        """
        self.registry_dir = Path(registry_dir)
        self.metadata_dir = self.registry_dir / "metadata"
        self.checkpoints_dir = self.registry_dir / "checkpoints"
        self.production_dir = self.registry_dir / "production"

        # Create directory structure
        for d in [self.metadata_dir, self.checkpoints_dir, self.production_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def register_model(
        self, model: Any, metadata: ModelMetadata, stage: str = "checkpoint"
    ) -> Path:
        """
        Register a new model with metadata.

        Args:
            model: Trained model object (must be picklable)
            metadata: Model metadata
            stage: Storage stage ("checkpoint" or "production")

        Returns:
            Path to saved model file
        """
        # Validate stage
        if stage not in ["checkpoint", "production"]:
            raise ValueError(
                f"Invalid stage: {stage}. Must be 'checkpoint' or 'production'"
            )

        # Determine output directory
        if stage == "checkpoint":
            output_dir = self.checkpoints_dir / metadata.name
        else:
            output_dir = self.production_dir / metadata.name

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save model file
        model_filename = f"{metadata.name}_v{metadata.version}.pkl"
        model_path = output_dir / model_filename

        joblib.dump(model, model_path)

        # Compute model hash and size
        model_hash = self._compute_file_hash(model_path)
        model_size = model_path.stat().st_size

        # Update metadata with file information
        metadata.model_path = str(model_path.relative_to(self.registry_dir))
        metadata.model_hash = model_hash
        metadata.model_size_bytes = model_size

        # Set file permissions (owner read/write only)
        model_path.chmod(0o600)

        # Save metadata
        metadata_filename = f"{metadata.name}_v{metadata.version}.json"
        metadata_path = self.metadata_dir / metadata_filename

        with open(metadata_path, "w") as f:
            json.dump(asdict(metadata), f, indent=2)

        metadata_path.chmod(0o600)

        return model_path

    def load_model(
        self, name: str, version: str | None = None, verify_integrity: bool = True
    ) -> tuple[Any, ModelMetadata]:
        """
        Load a model by name and version.

        Args:
            name: Model name
            version: Model version (None = latest)
            verify_integrity: Whether to verify SHA256 hash

        Returns:
            Tuple of (model, metadata)
        """
        if version is None:
            version = self.get_latest_version(name)

        # Load metadata
        metadata_path = self.metadata_dir / f"{name}_v{version}.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Model metadata not found: {name} v{version}")

        with open(metadata_path) as f:
            metadata_dict = json.load(f)

        metadata = ModelMetadata(**metadata_dict)

        # Load model file
        model_path = self.registry_dir / metadata.model_path

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Verify integrity
        if verify_integrity:
            current_hash = self._compute_file_hash(model_path)
            if current_hash != metadata.model_hash:
                raise ValueError(
                    f"Model integrity check failed!\n"
                    f"Expected: {metadata.model_hash}\n"
                    f"Got: {current_hash}\n"
                    f"Model may have been tampered with."
                )

        # Load model
        model = joblib.load(model_path)

        return model, metadata

    def list_models(
        self, name: str | None = None, stage: str | None = None
    ) -> list[ModelMetadata]:
        """
        List all registered models.

        Args:
            name: Filter by model name (None = all)
            stage: Filter by stage ("checkpoint" or "production")

        Returns:
            List of model metadata objects
        """
        models = []

        for metadata_file in self.metadata_dir.glob("*.json"):
            with open(metadata_file) as f:
                metadata_dict = json.load(f)

            metadata = ModelMetadata(**metadata_dict)

            # Apply filters
            if name and metadata.name != name:
                continue

            if stage:
                if stage == "production" and "production" not in metadata.model_path:
                    continue
                if stage == "checkpoint" and "production" in metadata.model_path:
                    continue

            models.append(metadata)

        # Sort by creation time (newest first)
        models.sort(key=lambda m: m.created_at, reverse=True)

        return models

    def get_latest_version(self, name: str) -> str:
        """
        Get the latest version of a model.

        Args:
            name: Model name

        Returns:
            Version string (e.g., "1.2.0")
        """
        models = self.list_models(name=name)

        if not models:
            raise ValueError(f"No models found with name: {name}")

        # Parse semantic versions and find max
        versions = []
        for model in models:
            try:
                major, minor, patch = map(int, model.version.split("."))
                versions.append((major, minor, patch, model.version))
            except ValueError:
                continue  # Skip invalid versions

        if not versions:
            raise ValueError(f"No valid semantic versions found for: {name}")

        # Get max version
        versions.sort(reverse=True)
        return versions[0][3]

    def promote_to_production(
        self, name: str, version: str, backup_existing: bool = True
    ) -> Path:
        """
        Promote a checkpoint model to production.

        Args:
            name: Model name
            version: Model version to promote
            backup_existing: Whether to backup existing production model

        Returns:
            Path to production model
        """
        # Load checkpoint model
        model, metadata = self.load_model(name, version)

        # Backup existing production model if requested
        if backup_existing:
            try:
                prod_models = self.list_models(name=name, stage="production")
                if prod_models:
                    latest_prod = prod_models[0]
                    backup_dir = self.registry_dir / "backups" / name
                    backup_dir.mkdir(parents=True, exist_ok=True)

                    # Copy model file
                    src_path = self.registry_dir / latest_prod.model_path
                    dst_path = backup_dir / f"{name}_v{latest_prod.version}_backup.pkl"
                    shutil.copy2(src_path, dst_path)
            except Exception as e:
                # Log warning but continue
                print(f"Warning: Failed to backup existing model: {e}")

        # Save to production
        production_path = self.register_model(model, metadata, stage="production")

        return production_path

    def compare_models(self, name: str, version1: str, version2: str) -> dict[str, Any]:
        """
        Compare two model versions.

        Args:
            name: Model name
            version1: First version
            version2: Second version

        Returns:
            Comparison dictionary
        """
        _, metadata1 = self.load_model(name, version1, verify_integrity=False)
        _, metadata2 = self.load_model(name, version2, verify_integrity=False)

        comparison = {
            "name": name,
            "version1": version1,
            "version2": version2,
            "metrics_diff": {},
            "hyperparameters_diff": {},
            "size_diff_bytes": metadata2.model_size_bytes - metadata1.model_size_bytes,
            "created_at": {
                "version1": metadata1.created_at,
                "version2": metadata2.created_at,
            },
        }

        # Compare metrics
        all_metric_keys = set(metadata1.metrics.keys()) | set(metadata2.metrics.keys())
        for key in all_metric_keys:
            val1 = metadata1.metrics.get(key, 0.0)
            val2 = metadata2.metrics.get(key, 0.0)
            comparison["metrics_diff"][key] = {
                "version1": val1,
                "version2": val2,
                "diff": val2 - val1,
                "improvement_pct": ((val2 - val1) / val1 * 100) if val1 != 0 else 0.0,
            }

        # Compare hyperparameters
        all_hp_keys = set(metadata1.hyperparameters.keys()) | set(
            metadata2.hyperparameters.keys()
        )
        for key in all_hp_keys:
            val1: Any = metadata1.hyperparameters.get(key)
            val2: Any = metadata2.hyperparameters.get(key)
            if val1 != val2:
                comparison["hyperparameters_diff"][key] = {
                    "version1": val1,
                    "version2": val2,
                }

        return comparison

    def delete_model(self, name: str, version: str, confirm: bool = False):
        """
        Delete a model version (use with caution).

        Args:
            name: Model name
            version: Model version
            confirm: Must be True to actually delete
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete model")

        # Load metadata to get file path
        _, metadata = self.load_model(name, version, verify_integrity=False)

        # Delete model file
        model_path = self.registry_dir / metadata.model_path
        if model_path.exists():
            model_path.unlink()

        # Delete metadata file
        metadata_path = self.metadata_dir / f"{name}_v{version}.json"
        if metadata_path.exists():
            metadata_path.unlink()

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()
