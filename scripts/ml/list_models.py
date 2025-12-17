#!/usr/bin/env python3
"""
List all models in the registry with their status.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.model_registry import ModelRegistry

console = Console()


def list_all_models():
    """List all registered models."""
    registry = ModelRegistry()

    console.print("\n[bold cyan]📦 Model Registry Status\n")

    # Get all models
    all_models = registry.list_models(name="malware_detector_rf")

    if not all_models:
        console.print("[yellow]No models found in registry\n")
        return

    # Create table
    table = Table(show_header=True, header_style="bold cyan", title="Registered Models")
    table.add_column("Version", width=10)
    table.add_column("Stage", width=12)
    table.add_column("Architecture", width=15)
    table.add_column("Test Acc", justify="right", width=10)
    table.add_column("Precision", justify="right", width=10)
    table.add_column("Recall", justify="right", width=10)
    table.add_column("F1", justify="right", width=10)
    table.add_column("Created", width=20)

    for model in all_models:
        # Determine stage
        stage = "PRODUCTION" if "production" in model.model_path else "Checkpoint"
        stage_style = "[bold green]" if stage == "PRODUCTION" else "[cyan]"

        # Get metrics
        test_acc = model.metrics.get("test_accuracy", 0.0)
        test_prec = model.metrics.get("test_precision", 0.0)
        test_recall = model.metrics.get("test_recall", 0.0)
        test_f1 = model.metrics.get("test_f1", 0.0)

        table.add_row(
            f"v{model.version}",
            f"{stage_style}{stage}",
            model.architecture,
            f"{test_acc:.4f}",
            f"{test_prec:.4f}",
            f"{test_recall:.4f}",
            f"{test_f1:.4f}",
            model.created_at.split("T")[0],
        )

    console.print(table)
    console.print(f"\n[cyan]Total models: {len(all_models)}")

    # Production summary
    prod_models = [m for m in all_models if "production" in m.model_path]
    if prod_models:
        console.print(f"[green]✅ Production models: {len(prod_models)}")
        for pm in prod_models:
            console.print(
                f"   • v{pm.version} - Accuracy: {pm.metrics.get('test_accuracy', 0.0):.4f}"
            )
    else:
        console.print("[yellow]⚠️  No production models")

    console.print()


if __name__ == "__main__":
    list_all_models()
