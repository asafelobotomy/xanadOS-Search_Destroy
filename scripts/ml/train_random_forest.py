#!/usr/bin/env python3
"""
Train Random Forest baseline model for malware detection.

Uses 318-dimensional static features extracted from PE/ELF binaries.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from rich.console import Console
from rich.table import Table

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.model_registry import ModelRegistry, ModelMetadata
from app.ml.experiment_logger import ExperimentLogger, ExperimentLog
from app.ml.training_utils import (
    load_features,
    compute_dataset_hash,
    get_class_weights,
    compute_metrics,
    get_feature_importance,
    print_training_summary,
)
from app.ml.feature_extractor import get_feature_names

console = Console()


def train_random_forest(
    n_estimators: int = 500,
    max_depth: int | None = None,
    min_samples_split: int = 2,
    random_state: int = 42,
):
    """
    Train Random Forest model.

    Args:
        n_estimators: Number of trees
        max_depth: Maximum tree depth (None = unlimited)
        min_samples_split: Minimum samples to split node
        random_state: Random seed for reproducibility
    """
    console.print("\n[bold cyan]🌲 Random Forest Baseline Training")
    console.print(f"[cyan]Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load features
    console.print("[cyan]📥 Loading features...")
    X_train, y_train = load_features("train")
    X_val, y_val = load_features("val")
    X_test, y_test = load_features("test")

    console.print(
        f"[green]✅ Train: {X_train.shape[0]} samples, {X_train.shape[1]} features"
    )
    console.print(f"[green]✅ Val:   {X_val.shape[0]} samples")
    console.print(f"[green]✅ Test:  {X_test.shape[0]} samples\n")

    # Compute dataset hash for reproducibility
    train_data_hash = compute_dataset_hash(X_train, y_train)
    console.print(f"[cyan]🔒 Training data hash: {train_data_hash[:16]}...\n")

    # Display class distribution
    train_malware = np.sum(y_train)
    train_benign = len(y_train) - train_malware

    console.print("[cyan]📊 Class distribution:")
    console.print(
        f"  • Malware: {train_malware} ({train_malware/len(y_train)*100:.1f}%)"
    )
    console.print(f"  • Benign:  {train_benign} ({train_benign/len(y_train)*100:.1f}%)")
    console.print(f"  • Ratio:   1:{train_benign/train_malware:.1f} (malware:benign)\n")

    # Compute class weights to handle imbalance
    class_weights = get_class_weights(y_train)
    console.print("[cyan]⚖️  Class weights (balanced):")
    console.print(f"  • Benign:  {class_weights[0]:.3f}")
    console.print(f"  • Malware: {class_weights[1]:.3f}\n")

    # Initialize model
    console.print("[cyan]🏗️  Initializing Random Forest...")
    console.print(f"  • Trees: {n_estimators}")
    console.print(f"  • Max depth: {max_depth if max_depth else 'Unlimited'}")
    console.print(f"  • Min samples split: {min_samples_split}")
    console.print(f"  • Class weight: balanced\n")

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,  # Use all CPU cores
        verbose=1,
    )

    # Train model
    console.print("[bold cyan]🚀 Training model...\n")
    import time

    start_time = time.time()

    model.fit(X_train, y_train)

    training_time = time.time() - start_time
    console.print(f"\n[green]✅ Training complete in {training_time:.2f} seconds\n")

    # Evaluate on all splits
    console.print("[cyan]📊 Evaluating model...\n")

    # Train metrics
    y_train_pred = model.predict(X_train)
    y_train_prob = model.predict_proba(X_train)[:, 1]
    train_metrics = compute_metrics(y_train, y_train_pred, y_train_prob)

    # Validation metrics
    y_val_pred = model.predict(X_val)
    y_val_prob = model.predict_proba(X_val)[:, 1]
    val_metrics = compute_metrics(y_val, y_val_pred, y_val_prob)

    # Test metrics
    y_test_pred = model.predict(X_test)
    y_test_prob = model.predict_proba(X_test)[:, 1]
    test_metrics = compute_metrics(y_test, y_test_pred, y_test_prob)

    # Print summary
    print_training_summary(
        "Random Forest Baseline",
        train_metrics,
        val_metrics,
        test_metrics,
        training_time,
    )

    # Feature importance
    console.print("[cyan]📈 Top 10 Most Important Features:\n")
    feature_names = get_feature_names()
    top_features = get_feature_importance(model, feature_names, top_k=10)

    importance_table = Table(show_header=True, header_style="bold cyan")
    importance_table.add_column("Rank", justify="right", width=6)
    importance_table.add_column("Feature", width=30)
    importance_table.add_column("Importance", justify="right", width=12)

    for i, (feature, importance) in enumerate(top_features, 1):
        importance_table.add_row(str(i), feature, f"{importance:.6f}")

    console.print(importance_table)
    console.print()

    # Save model using registry
    console.print("[cyan]💾 Saving model to registry...")

    registry = ModelRegistry()

    metadata = ModelMetadata(
        version="1.0.0",
        name="malware_detector_rf",
        architecture="RandomForest",
        created_at=datetime.utcnow().isoformat(),
        author="xanadOS",
        hyperparameters={
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "class_weight": "balanced",
            "random_state": random_state,
        },
        training_data_hash=train_data_hash,
        feature_version="1.0.0",
        metrics={
            "test_accuracy": test_metrics["accuracy"],
            "test_precision": test_metrics["precision"],
            "test_recall": test_metrics["recall"],
            "test_f1": test_metrics["f1"],
            "test_auc": test_metrics.get("auc", 0.0),
            "val_accuracy": val_metrics["accuracy"],
        },
        model_path="",  # Will be set by registry
        model_hash="",  # Will be set by registry
        model_size_bytes=0,  # Will be set by registry
        description=f"Random Forest baseline with {n_estimators} trees, trained on {len(X_train)} samples",
        tags=["baseline", "random-forest", "v1.0.0"],
    )

    model_path = registry.register_model(model, metadata, stage="checkpoint")
    console.print(f"[green]✅ Model saved: {model_path}\n")

    # Log experiment
    console.print("[cyan]📝 Logging experiment...")

    logger = ExperimentLogger()

    experiment = ExperimentLog(
        experiment_id="",  # Will be generated
        name=f"rf_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        created_at=datetime.utcnow().isoformat(),
        model_architecture="RandomForest",
        hyperparameters={
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "class_weight": "balanced",
            "random_state": random_state,
        },
        feature_version="1.0.0",
        dataset_hash=train_data_hash,
        metrics={
            "train_accuracy": train_metrics["accuracy"],
            "train_precision": train_metrics["precision"],
            "train_recall": train_metrics["recall"],
            "train_f1": train_metrics["f1"],
            "val_accuracy": val_metrics["accuracy"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
            "val_f1": val_metrics["f1"],
            "test_accuracy": test_metrics["accuracy"],
            "test_precision": test_metrics["precision"],
            "test_recall": test_metrics["recall"],
            "test_f1": test_metrics["f1"],
            "test_auc": test_metrics.get("auc", 0.0),
            "test_specificity": test_metrics["specificity"],
        },
        training_time_seconds=training_time,
        python_version="3.13",
        dependencies={"scikit-learn": "1.7.2", "numpy": "2.3.3"},
        model_path=str(model_path),
        tags=["baseline", "random-forest"],
        notes=f"Baseline Random Forest trained on {len(X_train)} samples with class balancing",
    )

    experiment_id = logger.log_experiment(experiment)
    console.print(f"[green]✅ Experiment logged: {experiment_id}\n")

    # Final summary
    console.print("[bold green]" + "=" * 70)
    console.print("[bold green]  ✅ TRAINING COMPLETE!")
    console.print("[bold green]" + "=" * 70 + "\n")

    console.print(f"[cyan]📊 Final Test Results:")
    console.print(
        f"  • Accuracy:  {test_metrics['accuracy']:.4f} ({test_metrics['accuracy']*100:.2f}%)"
    )
    console.print(f"  • Precision: {test_metrics['precision']:.4f}")
    console.print(f"  • Recall:    {test_metrics['recall']:.4f}")
    console.print(f"  • F1 Score:  {test_metrics['f1']:.4f}")
    console.print(f"  • AUC:       {test_metrics.get('auc', 0.0):.4f}\n")

    if test_metrics["accuracy"] >= 0.90:
        console.print("[bold green]🎯 TARGET ACHIEVED: 90%+ accuracy!")
    else:
        console.print(
            f"[yellow]⚠️  Below target: {test_metrics['accuracy']*100:.2f}% < 90%"
        )

    console.print(f"\n[cyan]💾 Model: {model_path}")
    console.print(f"[cyan]📝 Experiment: {experiment_id}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Train Random Forest baseline for malware detection"
    )
    parser.add_argument(
        "--trees",
        type=int,
        default=500,
        help="Number of trees in forest (default: 500)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum tree depth (default: unlimited)",
    )
    parser.add_argument(
        "--min-samples-split",
        type=int,
        default=2,
        help="Minimum samples to split node (default: 2)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)"
    )

    args = parser.parse_args()

    train_random_forest(
        n_estimators=args.trees,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        random_state=args.seed,
    )


if __name__ == "__main__":
    main()
