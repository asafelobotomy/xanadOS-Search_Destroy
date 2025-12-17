#!/usr/bin/env python3
"""
Hyperparameter tuning for Random Forest malware detector.

Uses RandomizedSearchCV to explore hyperparameter space efficiently.
"""

import argparse
import sys
from datetime import datetime, UTC
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.model_registry import ModelRegistry, ModelMetadata
from app.ml.experiment_logger import ExperimentLogger, ExperimentLog
from app.ml.training_utils import (
    load_features,
    compute_dataset_hash,
    compute_metrics,
    get_feature_importance,
    print_training_summary,
)
from app.ml.feature_extractor import get_feature_names

console = Console()


def tune_random_forest(n_iter: int = 50, cv_folds: int = 5, random_state: int = 42):
    """
    Hyperparameter tuning using RandomizedSearchCV.

    Args:
        n_iter: Number of random combinations to try
        cv_folds: Number of cross-validation folds
        random_state: Random seed
    """
    console.print("\n[bold cyan]🔧 Random Forest Hyperparameter Tuning")
    console.print(f"[cyan]Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load features
    console.print("[cyan]📥 Loading features...")
    X_train, y_train = load_features("train")
    X_val, y_val = load_features("val")
    X_test, y_test = load_features("test")

    # Combine train + val for tuning (more data = better estimates)
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])

    console.print(
        f"[green]✅ Train+Val: {X_train_val.shape[0]} samples, {X_train_val.shape[1]} features"
    )
    console.print(f"[green]✅ Test:      {X_test.shape[0]} samples\n")

    # Compute dataset hash
    train_data_hash = compute_dataset_hash(X_train_val, y_train_val)

    # Define hyperparameter search space
    param_distributions = {
        "n_estimators": [100, 300, 500, 700, 1000],
        "max_depth": [10, 20, 30, 40, None],
        "min_samples_split": [2, 5, 10, 20],
        "min_samples_leaf": [1, 2, 4, 8],
        "max_features": ["sqrt", "log2", None],
        "bootstrap": [True, False],
        "class_weight": ["balanced"],  # Always use balanced
    }

    console.print("[cyan]🔍 Hyperparameter search space:")
    for param, values in param_distributions.items():
        if param != "class_weight":
            console.print(f"  • {param}: {values}")
    console.print()

    # Initialize base model
    base_model = RandomForestClassifier(
        random_state=random_state,
        n_jobs=1,  # RandomizedSearchCV will parallelize across CV folds
    )

    # Setup cross-validation
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

    # Setup RandomizedSearchCV
    console.print(f"[cyan]⚙️  Initializing RandomizedSearchCV...")
    console.print(f"  • Iterations: {n_iter}")
    console.print(f"  • CV folds: {cv_folds}")
    console.print(f"  • Scoring: accuracy")
    console.print(f"  • Parallel jobs: -1 (all cores)\n")

    random_search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_distributions,
        n_iter=n_iter,
        cv=cv,
        scoring="accuracy",
        n_jobs=-1,
        random_state=random_state,
        verbose=2,
        return_train_score=True,
    )

    # Run tuning
    console.print("[bold cyan]🚀 Starting hyperparameter search...\n")
    console.print("[yellow]This may take several minutes...\n")

    import time

    start_time = time.time()

    random_search.fit(X_train_val, y_train_val)

    tuning_time = time.time() - start_time
    console.print(f"\n[green]✅ Tuning complete in {tuning_time:.2f} seconds\n")

    # Get best parameters
    best_params = random_search.best_params_
    best_cv_score = random_search.best_score_

    console.print("[bold cyan]🏆 Best Hyperparameters Found:\n")

    params_table = Table(show_header=True, header_style="bold cyan")
    params_table.add_column("Parameter", width=20)
    params_table.add_column("Value", width=20)

    for param, value in sorted(best_params.items()):
        params_table.add_row(param, str(value))

    console.print(params_table)
    console.print(
        f"\n[cyan]📊 Best CV Accuracy: {best_cv_score:.4f} ({best_cv_score*100:.2f}%)\n"
    )

    # Get best model
    best_model = random_search.best_estimator_

    # Evaluate on test set
    console.print("[cyan]📊 Evaluating best model on test set...\n")

    # Train metrics (on full train+val)
    y_train_val_pred = best_model.predict(X_train_val)
    y_train_val_prob = best_model.predict_proba(X_train_val)[:, 1]
    train_metrics = compute_metrics(y_train_val, y_train_val_pred, y_train_val_prob)

    # Test metrics
    y_test_pred = best_model.predict(X_test)
    y_test_prob = best_model.predict_proba(X_test)[:, 1]
    test_metrics = compute_metrics(y_test, y_test_pred, y_test_prob)

    # Print comparison with baseline
    console.print("[bold cyan]" + "=" * 70)
    console.print("[bold cyan]  📊 RESULTS COMPARISON")
    console.print("[bold cyan]" + "=" * 70 + "\n")

    comparison_table = Table(show_header=True, header_style="bold cyan")
    comparison_table.add_column("Metric", width=20)
    comparison_table.add_column("Baseline (500 trees)", justify="right", width=20)
    comparison_table.add_column("Tuned Model", justify="right", width=20)
    comparison_table.add_column("Improvement", justify="right", width=15)

    baseline_metrics = {
        "accuracy": 0.9889,
        "precision": 1.0000,
        "recall": 0.9333,
        "f1": 0.9655,
        "auc": 1.0000,
    }

    for metric in ["accuracy", "precision", "recall", "f1", "auc"]:
        baseline_val = baseline_metrics.get(metric, 0.0)
        tuned_val = test_metrics.get(metric, 0.0)
        improvement = tuned_val - baseline_val

        improvement_str = (
            f"+{improvement:.4f}" if improvement >= 0 else f"{improvement:.4f}"
        )
        if improvement > 0:
            improvement_str = f"[green]{improvement_str}"
        elif improvement < 0:
            improvement_str = f"[red]{improvement_str}"
        else:
            improvement_str = f"[yellow]{improvement_str}"

        comparison_table.add_row(
            metric.capitalize(),
            f"{baseline_val:.4f}",
            f"{tuned_val:.4f}",
            improvement_str,
        )

    console.print(comparison_table)
    console.print()

    # Feature importance
    console.print("[cyan]📈 Top 10 Most Important Features (Tuned Model):\n")
    feature_names = get_feature_names()
    top_features = get_feature_importance(best_model, feature_names, top_k=10)

    importance_table = Table(show_header=True, header_style="bold cyan")
    importance_table.add_column("Rank", justify="right", width=6)
    importance_table.add_column("Feature", width=30)
    importance_table.add_column("Importance", justify="right", width=12)

    for i, (feature, importance) in enumerate(top_features, 1):
        importance_table.add_row(str(i), feature, f"{importance:.6f}")

    console.print(importance_table)
    console.print()

    # Save model if improved or user confirms
    should_save = test_metrics["accuracy"] >= baseline_metrics["accuracy"]

    if should_save:
        console.print(
            "[green]🎯 Performance improved or maintained! Saving tuned model...\n"
        )

        # Save model
        registry = ModelRegistry()

        metadata = ModelMetadata(
            version="1.1.0",
            name="malware_detector_rf",
            architecture="RandomForest",
            created_at=datetime.now(UTC).isoformat(),
            author="xanadOS",
            hyperparameters=best_params,
            training_data_hash=train_data_hash,
            feature_version="1.0.0",
            metrics={
                "test_accuracy": test_metrics["accuracy"],
                "test_precision": test_metrics["precision"],
                "test_recall": test_metrics["recall"],
                "test_f1": test_metrics["f1"],
                "test_auc": test_metrics.get("auc", 0.0),
                "cv_accuracy": best_cv_score,
            },
            model_path="",
            model_hash="",
            model_size_bytes=0,
            description=f"Hyperparameter-tuned Random Forest (CV acc: {best_cv_score:.4f})",
            tags=["tuned", "random-forest", "v1.1.0"],
        )

        model_path = registry.register_model(best_model, metadata, stage="checkpoint")
        console.print(f"[green]✅ Model saved: {model_path}\n")

        # Log experiment
        logger = ExperimentLogger()

        experiment = ExperimentLog(
            experiment_id="",
            name=f"rf_tuned_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(UTC).isoformat(),
            model_architecture="RandomForest",
            hyperparameters=best_params,
            feature_version="1.0.0",
            dataset_hash=train_data_hash,
            metrics={
                "train_val_accuracy": train_metrics["accuracy"],
                "test_accuracy": test_metrics["accuracy"],
                "test_precision": test_metrics["precision"],
                "test_recall": test_metrics["recall"],
                "test_f1": test_metrics["f1"],
                "test_auc": test_metrics.get("auc", 0.0),
                "cv_accuracy": best_cv_score,
            },
            training_time_seconds=tuning_time,
            python_version="3.13",
            dependencies={"scikit-learn": "1.7.2", "numpy": "2.3.3"},
            model_path=str(model_path),
            tags=["tuned", "random-forest", "hyperparameter-search"],
            notes=f"RandomizedSearchCV with {n_iter} iterations, {cv_folds}-fold CV",
        )

        experiment_id = logger.log_experiment(experiment)
        console.print(f"[green]✅ Experiment logged: {experiment_id}\n")
    else:
        console.print("[yellow]⚠️  Performance not improved. Model not saved.\n")

    # Final summary
    console.print("[bold green]" + "=" * 70)
    console.print("[bold green]  ✅ HYPERPARAMETER TUNING COMPLETE!")
    console.print("[bold green]" + "=" * 70 + "\n")

    console.print(f"[cyan]📊 Final Test Results:")
    console.print(
        f"  • Accuracy:  {test_metrics['accuracy']:.4f} ({test_metrics['accuracy']*100:.2f}%)"
    )
    console.print(f"  • Precision: {test_metrics['precision']:.4f}")
    console.print(f"  • Recall:    {test_metrics['recall']:.4f}")
    console.print(f"  • F1 Score:  {test_metrics['f1']:.4f}")
    console.print(f"  • AUC:       {test_metrics.get('auc', 0.0):.4f}\n")

    console.print(f"[cyan]⏱️  Total tuning time: {tuning_time:.2f} seconds")
    console.print(f"[cyan]🔍 Combinations tried: {n_iter}")
    console.print(f"[cyan]🏆 Best CV score: {best_cv_score:.4f}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Hyperparameter tuning for Random Forest malware detector"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of random combinations to try (default: 50)",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Number of cross-validation folds (default: 5)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)"
    )

    args = parser.parse_args()

    tune_random_forest(
        n_iter=args.iterations, cv_folds=args.cv_folds, random_state=args.seed
    )


if __name__ == "__main__":
    main()
