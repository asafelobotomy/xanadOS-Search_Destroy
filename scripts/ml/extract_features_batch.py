#!/usr/bin/env python3
"""
Batch feature extraction for malware detection dataset.

Processes all files in the organized dataset and caches features as .npz files.
Uses parallel processing for speed.
"""

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np
from joblib import Parallel, delayed
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table

# Import feature extractor (parent directory)
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.feature_extractor import FeatureExtractor, get_feature_names

console = Console()

# Directories
ORGANIZED_DIR = Path("data/organized")
FEATURES_DIR = Path("data/features")


def extract_features_for_file(file_path: Path, output_dir: Path) -> tuple[Path, bool]:
    """
    Extract features for a single file and save to .npz.

    Args:
        file_path: Path to input file
        output_dir: Directory to save features

    Returns:
        Tuple of (file_path, success)
    """
    try:
        # Create extractor in this process (avoid pickling issues)
        extractor = FeatureExtractor()

        # Extract features
        features = extractor.extract(file_path)

        if features is None:
            return (file_path, False)

        # Save as .npz (compressed NumPy format)
        output_path = output_dir / f"{file_path.name}.npz"
        np.savez_compressed(output_path, features=features)

        return (file_path, True)

    except Exception as e:
        console.print(f"[red]❌ Failed: {file_path.name}: {e}")
        return (file_path, False)


def process_split(split_name: str, n_jobs: int = -1) -> dict:
    """
    Process all files in a dataset split.

    Args:
        split_name: Split name ("train", "val", or "test")
        n_jobs: Number of parallel jobs (-1 for all CPUs)

    Returns:
        Statistics dict
    """
    console.print(f"\n[bold cyan]📊 Processing {split_name} split...")

    split_dir = ORGANIZED_DIR / split_name
    features_dir = FEATURES_DIR / split_name

    # Create output directories
    (features_dir / "malware").mkdir(parents=True, exist_ok=True)
    (features_dir / "benign").mkdir(parents=True, exist_ok=True)

    # Collect all files
    malware_files = list((split_dir / "malware").glob("*"))
    benign_files = list((split_dir / "benign").glob("*"))

    all_files = malware_files + benign_files

    if not all_files:
        console.print(f"[yellow]⚠️  No files found in {split_name} split")
        return {"total": 0, "success": 0, "failed": 0}

    console.print(f"[cyan]Total files: {len(all_files)}")
    console.print(f"[cyan]• Malware: {len(malware_files)}")
    console.print(f"[cyan]• Benign: {len(benign_files)}")

    # Initialize extractor
    extractor = FeatureExtractor()

    # Process files sequentially with progress bar
    results = []
    # Initialize extractor
    extractor = FeatureExtractor()

    # Process files sequentially with progress bar
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        task = progress.add_task(
            f"[cyan]Extracting features for {split_name}...", total=len(all_files)
        )

        # Determine output dir for each file and process
        for f in all_files:
            if f.parent.name == "malware":
                output_dir = features_dir / "malware"
            else:
                output_dir = features_dir / "benign"

            # Extract features for this file
            try:
                features = extractor.extract(f)

                if features is not None:
                    output_path = output_dir / f"{f.name}.npz"
                    np.savez_compressed(output_path, features=features)
                    results.append((f, True))
                else:
                    results.append((f, False))
            except Exception as e:
                console.print(f"[red]❌ Failed: {f.name}: {e}")
                results.append((f, False))

            progress.update(task, advance=1)

    # Calculate statistics
    success_count = sum(1 for _, success in results if success)
    failed_count = len(results) - success_count

    stats = {
        "total": len(all_files),
        "malware": len(malware_files),
        "benign": len(benign_files),
        "success": success_count,
        "failed": failed_count,
        "success_rate": (success_count / len(all_files) * 100) if all_files else 0,
    }

    # Display results
    console.print(
        f"[green]✅ Success: {success_count}/{len(all_files)} files ({stats['success_rate']:.1f}%)"
    )
    if failed_count > 0:
        console.print(f"[yellow]⚠️  Failed: {failed_count} files")

    return stats


def save_metadata(stats: dict):
    """Save extraction metadata."""
    metadata_path = FEATURES_DIR / "metadata.json"

    # Add feature information
    stats["feature_extractor"] = {
        "version": "1.0.0",
        "feature_dimension": FeatureExtractor.FEATURE_DIM,
        "feature_names": get_feature_names(),
        "components": {
            "entropy": FeatureExtractor.ENTROPY_DIM,
            "file_size": FeatureExtractor.FILE_SIZE_DIM,
            "byte_histogram": FeatureExtractor.BYTE_HISTOGRAM_DIM,
            "pe_header": FeatureExtractor.PE_HEADER_DIM,
            "elf_header": FeatureExtractor.ELF_HEADER_DIM,
            "section_features": FeatureExtractor.SECTION_FEATURES_DIM,
            "string_features": FeatureExtractor.STRING_FEATURES_DIM,
        },
    }

    metadata_path.write_text(json.dumps(stats, indent=2))
    console.print(f"\n[cyan]📝 Metadata saved: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract features from malware detection dataset"
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test", "all"],
        default="all",
        help="Dataset split to process (default: all)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs (-1 for all CPUs, default: -1)",
    )

    args = parser.parse_args()

    console.print("[bold cyan]🔬 Batch Feature Extraction")
    console.print(f"[cyan]Output directory: {FEATURES_DIR}")
    console.print(f"[cyan]Feature dimension: {FeatureExtractor.FEATURE_DIM}")
    console.print(f"[cyan]Parallel jobs: {args.jobs if args.jobs > 0 else 'all CPUs'}")
    console.print()

    # Create output directory
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    # Process splits
    all_stats = {}

    if args.split == "all":
        splits = ["train", "val", "test"]
    else:
        splits = [args.split]

    for split in splits:
        stats = process_split(split, n_jobs=args.jobs)
        all_stats[split] = stats

    # Display summary table
    console.print("\n[bold cyan]📊 Extraction Summary")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Split")
    table.add_column("Total Files", justify="right")
    table.add_column("Malware", justify="right")
    table.add_column("Benign", justify="right")
    table.add_column("Success", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Success Rate", justify="right")

    for split_name, stats in all_stats.items():
        table.add_row(
            split_name.capitalize(),
            str(stats["total"]),
            str(stats["malware"]),
            str(stats["benign"]),
            str(stats["success"]),
            str(stats["failed"]),
            f"{stats['success_rate']:.1f}%",
        )

    # Calculate totals
    total_files = sum(s["total"] for s in all_stats.values())
    total_success = sum(s["success"] for s in all_stats.values())
    total_failed = sum(s["failed"] for s in all_stats.values())
    total_success_rate = (total_success / total_files * 100) if total_files > 0 else 0

    table.add_row(
        "[bold]TOTAL",
        f"[bold]{total_files}",
        f"[bold]{sum(s['malware'] for s in all_stats.values())}",
        f"[bold]{sum(s['benign'] for s in all_stats.values())}",
        f"[bold]{total_success}",
        f"[bold]{total_failed}",
        f"[bold]{total_success_rate:.1f}%",
    )

    console.print(table)

    # Save metadata
    save_metadata(all_stats)

    console.print(f"\n[bold green]✅ Feature extraction complete!")
    console.print(f"[green]Features saved to: {FEATURES_DIR}")
    console.print(f"[green]Feature dimension: {FeatureExtractor.FEATURE_DIM}")

    # Display feature breakdown
    console.print("\n[bold cyan]📋 Feature Breakdown:")
    extractor = FeatureExtractor()
    console.print(f"  • Entropy: {extractor.ENTROPY_DIM} feature")
    console.print(f"  • File size: {extractor.FILE_SIZE_DIM} feature (log-scaled)")
    console.print(
        f"  • Byte histogram: {extractor.BYTE_HISTOGRAM_DIM} features (normalized)"
    )
    console.print(f"  • PE headers: {extractor.PE_HEADER_DIM} features")
    console.print(f"  • ELF headers: {extractor.ELF_HEADER_DIM} features")
    console.print(f"  • Section analysis: {extractor.SECTION_FEATURES_DIM} features")
    console.print(f"  • String analysis: {extractor.STRING_FEATURES_DIM} features")
    console.print(f"  • [bold]Total: {extractor.FEATURE_DIM} features[/bold]")

    console.print("\n[cyan]💡 Next steps:")
    console.print(
        "  1. Load features: np.load('data/features/train/malware/HASH.npz')['features']"
    )
    console.print("  2. Train model: See Week 3-4 Random Forest baseline")
    console.print(
        "  3. Feature names: from app.ml.feature_extractor import get_feature_names"
    )


if __name__ == "__main__":
    main()
