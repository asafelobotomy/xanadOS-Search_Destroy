#!/usr/bin/env python3
"""
Organize malware and benign samples into train/val/test splits.

This script takes raw malware and benign samples and organizes them into
a structured dataset with train/validation/test splits (70/15/15).

Usage:
    uv run python scripts/ml/organize_dataset.py

Output:
    data/organized/
    ├── train/
    │   ├── malware/
    │   └── benign/
    ├── val/
    │   ├── malware/
    │   └── benign/
    ├── test/
    │   ├── malware/
    │   └── benign/
    └── metadata.json
"""

import argparse
import json
import random
import shutil
from pathlib import Path
from typing import List

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table

console = Console()

# Directories
MALWARE_DIR = Path("data/malware")
BENIGN_DIR = Path("data/benign")
ORGANIZED_DIR = Path("data/organized")

# Split ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


class DatasetOrganizer:
    """Organize dataset into train/val/test splits."""

    def __init__(
        self,
        malware_dir: Path,
        benign_dir: Path,
        output_dir: Path,
        train_ratio: float = TRAIN_RATIO,
        val_ratio: float = VAL_RATIO,
        test_ratio: float = TEST_RATIO,
        seed: int = 42,
    ):
        self.malware_dir = malware_dir
        self.benign_dir = benign_dir
        self.output_dir = output_dir
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

        # Set random seed for reproducibility
        random.seed(seed)

    def create_directory_structure(self):
        """Create train/val/test directory structure."""
        for split in ["train", "val", "test"]:
            (self.output_dir / split / "malware").mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / "benign").mkdir(parents=True, exist_ok=True)

    def collect_files(self, directory: Path) -> List[Path]:
        """Collect all files from directory."""
        if not directory.exists():
            console.print(f"[yellow]⚠️  Directory not found: {directory}")
            return []

        files = [
            f for f in directory.iterdir() if f.is_file() and f.name != "metadata.json"
        ]
        return files

    def split_files(self, files: List[Path]) -> dict:
        """Split files into train/val/test."""
        # Shuffle files
        shuffled = files.copy()
        random.shuffle(shuffled)

        total = len(shuffled)
        train_end = int(total * self.train_ratio)
        val_end = train_end + int(total * self.val_ratio)

        splits = {
            "train": shuffled[:train_end],
            "val": shuffled[train_end:val_end],
            "test": shuffled[val_end:],
        }

        return splits

    def copy_files(self, files: List[Path], dest_dir: Path, label: str):
        """Copy files to destination directory."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task(
                f"[cyan]Copying {label} files...", total=len(files)
            )

            for file_path in files:
                dest_path = dest_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                progress.update(task, advance=1)

    def organize(self):
        """Organize dataset into train/val/test splits."""
        console.print("\n[bold cyan]📊 Dataset Organizer")
        console.print(f"[cyan]Malware: {self.malware_dir}")
        console.print(f"[cyan]Benign: {self.benign_dir}")
        console.print(f"[cyan]Output: {self.output_dir}")
        console.print(
            f"[cyan]Split: {self.train_ratio:.0%} train / {self.val_ratio:.0%} val / {self.test_ratio:.0%} test"
        )
        console.print()

        # Create directory structure
        console.print("[cyan]Creating directory structure...")
        self.create_directory_structure()

        # Collect files
        console.print("[cyan]Collecting files...")
        malware_files = self.collect_files(self.malware_dir)
        benign_files = self.collect_files(self.benign_dir)

        console.print(f"[green]Found {len(malware_files):,} malware samples")
        console.print(f"[green]Found {len(benign_files):,} benign samples")
        console.print()

        if len(malware_files) == 0 or len(benign_files) == 0:
            console.print("[red]❌ Insufficient samples found!")
            console.print(
                "[yellow]Run download_malwarebazaar.py and collect_benign.py first"
            )
            return

        # Split files
        console.print("[cyan]Splitting dataset...")
        malware_splits = self.split_files(malware_files)
        benign_splits = self.split_files(benign_files)

        # Copy files to splits
        stats = {}

        for split_name in ["train", "val", "test"]:
            console.print(f"\n[bold cyan]Organizing {split_name} split...")

            # Copy malware
            malware_dest = self.output_dir / split_name / "malware"
            self.copy_files(
                malware_splits[split_name], malware_dest, f"{split_name}/malware"
            )

            # Copy benign
            benign_dest = self.output_dir / split_name / "benign"
            self.copy_files(
                benign_splits[split_name], benign_dest, f"{split_name}/benign"
            )

            # Store stats
            stats[split_name] = {
                "malware": len(malware_splits[split_name]),
                "benign": len(benign_splits[split_name]),
                "total": len(malware_splits[split_name])
                + len(benign_splits[split_name]),
            }

        # Create metadata
        metadata = {
            "total_samples": len(malware_files) + len(benign_files),
            "malware_samples": len(malware_files),
            "benign_samples": len(benign_files),
            "seed": self.seed,
            "splits": stats,
            "ratios": {
                "train": self.train_ratio,
                "val": self.val_ratio,
                "test": self.test_ratio,
            },
        }

        metadata_file = self.output_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Display summary table
        console.print("\n[bold green]✅ Dataset Organized!")

        table = Table(title="Dataset Statistics")
        table.add_column("Split", style="cyan", justify="center")
        table.add_column("Malware", style="red", justify="right")
        table.add_column("Benign", style="green", justify="right")
        table.add_column("Total", style="bold", justify="right")
        table.add_column("Percentage", style="dim", justify="right")

        total_samples = metadata["total_samples"]

        for split_name, split_stats in stats.items():
            percentage = (split_stats["total"] / total_samples) * 100
            table.add_row(
                split_name.capitalize(),
                f"{split_stats['malware']:,}",
                f"{split_stats['benign']:,}",
                f"{split_stats['total']:,}",
                f"{percentage:.1f}%",
            )

        # Add total row
        table.add_row(
            "TOTAL",
            f"{metadata['malware_samples']:,}",
            f"{metadata['benign_samples']:,}",
            f"{metadata['total_samples']:,}",
            "100.0%",
            style="bold",
        )

        console.print(table)
        console.print()
        console.print(f"[cyan]Metadata saved to: {metadata_file}")
        console.print(
            f"[cyan]Total size: {sum(p.stat().st_size for p in self.output_dir.rglob('*') if p.is_file()) / 1e9:.2f} GB"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Organize dataset into train/val/test splits"
    )
    parser.add_argument(
        "--malware-dir",
        type=Path,
        default=MALWARE_DIR,
        help=f"Malware directory (default: {MALWARE_DIR})",
    )
    parser.add_argument(
        "--benign-dir",
        type=Path,
        default=BENIGN_DIR,
        help=f"Benign directory (default: {BENIGN_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ORGANIZED_DIR,
        help=f"Output directory (default: {ORGANIZED_DIR})",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=TRAIN_RATIO,
        help=f"Training set ratio (default: {TRAIN_RATIO})",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=VAL_RATIO,
        help=f"Validation set ratio (default: {VAL_RATIO})",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=TEST_RATIO,
        help=f"Test set ratio (default: {TEST_RATIO})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    # Validate ratios
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        console.print(f"[red]❌ Ratios must sum to 1.0 (current: {total_ratio})")
        return

    organizer = DatasetOrganizer(
        malware_dir=args.malware_dir,
        benign_dir=args.benign_dir,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    organizer.organize()


if __name__ == "__main__":
    main()
