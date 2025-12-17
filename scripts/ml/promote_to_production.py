#!/usr/bin/env python3
"""
Promote a model from checkpoint to production stage.

This script handles the complete promotion workflow including:
- Loading model metadata
- Validating model performance
- Promoting to production
- Creating deployment documentation
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, UTC

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.model_registry import ModelRegistry, ModelMetadata

console = Console()


def promote_model(
    model_name: str, version: str, min_accuracy: float = 0.90, force: bool = False
):
    """
    Promote a model to production.

    Args:
        model_name: Name of the model (e.g., 'malware_detector_rf')
        version: Version to promote (e.g., '1.1.0')
        min_accuracy: Minimum accuracy threshold for production
        force: Force promotion even if below threshold
    """
    console.print("\n[bold cyan]🚀 Model Promotion Workflow")
    console.print(f"[cyan]Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    registry = ModelRegistry()

    # Load model metadata
    console.print(f"[cyan]📥 Loading model metadata for {model_name} v{version}...")

    try:
        # List all models and find the one matching our version
        all_models = registry.list_models(name=model_name)
        matching_models = [m for m in all_models if m.version == version]

        if not matching_models:
            console.print(
                f"[red]❌ Model {model_name} v{version} not found in registry"
            )
            return False

        metadata = matching_models[0]
    except Exception as e:
        console.print(f"[red]❌ Failed to load model metadata: {e}")
        return False

    console.print(f"[green]✅ Model loaded successfully\n")

    # Display model information
    info_table = Table(
        title="Model Information", show_header=True, header_style="bold cyan"
    )
    info_table.add_column("Property", width=25)
    info_table.add_column("Value", width=50)

    info_table.add_row("Name", metadata.name)
    info_table.add_row("Version", metadata.version)
    info_table.add_row("Architecture", metadata.architecture)
    info_table.add_row("Created", metadata.created_at)
    info_table.add_row("Author", metadata.author)
    info_table.add_row("Description", metadata.description or "N/A")

    console.print(info_table)
    console.print()

    # Display hyperparameters
    if metadata.hyperparameters:
        params_table = Table(
            title="Hyperparameters", show_header=True, header_style="bold cyan"
        )
        params_table.add_column("Parameter", width=25)
        params_table.add_column("Value", width=20)

        for param, value in sorted(metadata.hyperparameters.items()):
            params_table.add_row(param, str(value))

        console.print(params_table)
        console.print()

    # Display metrics
    if metadata.metrics:
        metrics_table = Table(
            title="Performance Metrics", show_header=True, header_style="bold cyan"
        )
        metrics_table.add_column("Metric", width=25)
        metrics_table.add_column("Value", width=20)

        for metric, value in sorted(metadata.metrics.items()):
            if isinstance(value, float):
                metrics_table.add_row(metric, f"{value:.4f}")
            else:
                metrics_table.add_row(metric, str(value))

        console.print(metrics_table)
        console.print()

    # Validate performance
    test_accuracy = metadata.metrics.get("test_accuracy", 0.0)

    console.print(f"[cyan]📊 Validating performance...")
    console.print(f"  • Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    console.print(f"  • Minimum Required: {min_accuracy:.4f} ({min_accuracy*100:.2f}%)")

    if test_accuracy < min_accuracy and not force:
        console.print(
            f"\n[red]❌ Model accuracy ({test_accuracy:.4f}) is below minimum threshold ({min_accuracy:.4f})"
        )
        console.print("[yellow]💡 Use --force to promote anyway\n")
        return False

    if test_accuracy >= min_accuracy:
        console.print(f"[green]✅ Performance meets production standards\n")
    else:
        console.print(
            f"[yellow]⚠️  Performance below threshold, but forcing promotion\n"
        )

    # Check for existing production model
    console.print("[cyan]🔍 Checking for existing production model...")

    try:
        production_models = registry.list_versions(model_name, stage="production")

        if production_models:
            console.print(
                f"[yellow]⚠️  Found {len(production_models)} existing production model(s):"
            )
            for prod_model in production_models:
                prod_version = prod_model.get("version", "unknown")
                prod_accuracy = prod_model.get("metrics", {}).get("test_accuracy", 0.0)
                console.print(f"  • v{prod_version} - Accuracy: {prod_accuracy:.4f}")

            # Compare with existing production
            if production_models:
                best_prod = max(
                    production_models,
                    key=lambda x: x.get("metrics", {}).get("test_accuracy", 0.0),
                )
                best_prod_accuracy = best_prod.get("metrics", {}).get(
                    "test_accuracy", 0.0
                )

                if test_accuracy <= best_prod_accuracy and not force:
                    console.print(
                        f"\n[yellow]⚠️  New model ({test_accuracy:.4f}) is not better than current production ({best_prod_accuracy:.4f})"
                    )
                    console.print("[yellow]💡 Use --force to promote anyway\n")

                    if not force:
                        return False
                elif test_accuracy > best_prod_accuracy:
                    improvement = test_accuracy - best_prod_accuracy
                    console.print(
                        f"[green]✅ New model is better by {improvement:.4f} ({improvement*100:.2f}%)\n"
                    )
        else:
            console.print(
                "[green]✅ No existing production model - this will be the first\n"
            )
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not check existing production models: {e}\n")

    # Confirm promotion
    console.print("[bold yellow]⚠️  PROMOTION CONFIRMATION REQUIRED")
    console.print(
        f"[yellow]This will promote {model_name} v{version} to PRODUCTION stage"
    )
    console.print(
        f"[yellow]Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)\n"
    )

    if not force:
        response = input("Proceed with promotion? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            console.print("\n[yellow]❌ Promotion cancelled by user\n")
            return False
    else:
        console.print("[cyan]🔧 Force mode enabled - skipping confirmation\n")

    # Promote model
    console.print("[bold cyan]🚀 Promoting model to production...")

    try:
        result = registry.promote_to_production(model_name, version)

        if result:
            console.print("[green]✅ Model successfully promoted to production!\n")

            # Create deployment summary
            deployment_summary = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║               ✅ PRODUCTION DEPLOYMENT SUCCESSFUL ✅                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

📦 DEPLOYED MODEL:
   • Name: {metadata.name}
   • Version: v{metadata.version}
   • Architecture: {metadata.architecture}
   • Stage: PRODUCTION

📊 PERFORMANCE:
   • Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)
   • Precision: {metadata.metrics.get('test_precision', 0.0):.4f}
   • Recall: {metadata.metrics.get('test_recall', 0.0):.4f}
   • F1 Score: {metadata.metrics.get('test_f1', 0.0):.4f}
   • AUC: {metadata.metrics.get('test_auc', 0.0):.4f}

🔧 HYPERPARAMETERS:
"""

            if metadata.hyperparameters:
                for param, value in sorted(metadata.hyperparameters.items()):
                    deployment_summary += f"   • {param}: {value}\n"

            deployment_summary += f"""
📝 DEPLOYMENT INFO:
   • Deployed: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}
   • Model Hash: {metadata.model_hash}
   • Training Data Hash: {metadata.training_data_hash}
   • Feature Version: {metadata.feature_version}

🎯 NEXT STEPS:
   1. Test production model with real samples
   2. Monitor performance metrics
   3. Set up automated retraining pipeline
   4. Configure model versioning strategy

═══════════════════════════════════════════════════════════════════════════
"""

            console.print(
                Panel(
                    deployment_summary, border_style="green", title="Deployment Summary"
                )
            )

            # Save deployment summary to file
            deployment_file = Path(
                f"models/deployments/deployment_{model_name}_v{version}.txt"
            )
            deployment_file.parent.mkdir(parents=True, exist_ok=True)
            deployment_file.write_text(deployment_summary)

            console.print(
                f"\n[green]📄 Deployment summary saved to: {deployment_file}\n"
            )

            return True
        else:
            console.print("[red]❌ Promotion failed\n")
            return False

    except Exception as e:
        console.print(f"[red]❌ Promotion failed: {e}\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Promote a model to production stage")
    parser.add_argument(
        "--model",
        type=str,
        default="malware_detector_rf",
        help="Model name (default: malware_detector_rf)",
    )
    parser.add_argument(
        "--version", type=str, required=True, help="Version to promote (e.g., 1.1.0)"
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.90,
        help="Minimum test accuracy for production (default: 0.90)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force promotion without confirmation or validation",
    )

    args = parser.parse_args()

    success = promote_model(
        model_name=args.model,
        version=args.version,
        min_accuracy=args.min_accuracy,
        force=args.force,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
