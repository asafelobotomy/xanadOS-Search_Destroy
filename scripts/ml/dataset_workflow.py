#!/usr/bin/env python3
"""
Complete dataset acquisition workflow for Day 2-3.

This script orchestrates the full dataset collection process:
1. Download malware samples from MalwareBazaar
2. Collect benign files from system
3. Organize into train/val/test splits
4. Verify dataset integrity

Usage:
    # Full workflow (100K samples - production)
    uv run python scripts/ml/dataset_workflow.py --full

    # Quick test (1K samples - testing)
    uv run python scripts/ml/dataset_workflow.py --quick

    # Custom sample count
    uv run python scripts/ml/dataset_workflow.py --malware 10000 --benign 10000
"""

import argparse
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()


class DatasetWorkflow:
    """Orchestrate dataset acquisition workflow."""

    def __init__(self, malware_samples: int, benign_samples: int):
        self.malware_samples = malware_samples
        self.benign_samples = benign_samples
        self.scripts_dir = Path("scripts/ml")

    def run_script(self, script_name: str, *args) -> bool:
        """Run a Python script and return success status."""
        # SECURITY: Whitelist validation to prevent command injection (CWE-78 mitigation)
        allowed_scripts = [
            "download_malwarebazaar.py",
            "collect_benign.py",
            "organize_dataset.py",
        ]

        if script_name not in allowed_scripts:
            console.print(f"[red]❌ Script '{script_name}' not in whitelist")
            return False

        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            console.print(f"[red]❌ Script not found: {script_path}")
            return False

        # Build command with explicit shell=False and validated arguments
        cmd = ["uv", "run", "python", str(script_path)] + [str(arg) for arg in args]

        console.print(f"\n[bold cyan]▶️  Running: {' '.join(cmd)}")
        console.print()

        try:
            result = subprocess.run(
                cmd, check=True, shell=False
            )  # Explicit shell=False
            return result.returncode == 0

        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Script failed with exit code {e.returncode}")
            return False

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Interrupted by user")
            return False

    def step1_download_malware(self) -> bool:
        """Step 1: Download malware samples."""
        console.print(
            Panel.fit(
                "[bold cyan]Step 1: Download Malware Samples\n"
                f"Target: {self.malware_samples:,} samples from MalwareBazaar",
                title="🦠 Malware Acquisition",
                border_style="cyan",
            )
        )

        return self.run_script(
            "download_malwarebazaar.py", "--samples", str(self.malware_samples)
        )

    def step2_collect_benign(self) -> bool:
        """Step 2: Collect benign files."""
        console.print(
            Panel.fit(
                "[bold green]Step 2: Collect Benign Files\n"
                f"Target: {self.benign_samples:,} files from system directories",
                title="🛡️  Benign Collection",
                border_style="green",
            )
        )

        return self.run_script(
            "collect_benign.py", "--samples", str(self.benign_samples)
        )

    def step3_organize_dataset(self) -> bool:
        """Step 3: Organize into train/val/test."""
        console.print(
            Panel.fit(
                "[bold yellow]Step 3: Organize Dataset\n"
                "Split: 70% train / 15% val / 15% test",
                title="📊 Dataset Organization",
                border_style="yellow",
            )
        )

        return self.run_script("organize_dataset.py")

    def run_workflow(self):
        """Execute complete workflow."""
        console.print(
            Panel.fit(
                "[bold magenta]Phase 3 Day 2-3: Dataset Acquisition Workflow\n\n"
                f"• Malware samples: {self.malware_samples:,}\n"
                f"• Benign samples: {self.benign_samples:,}\n"
                f"• Total dataset: {self.malware_samples + self.benign_samples:,}\n"
                f"• Estimated time: {self._estimate_time()} hours\n"
                f"• Estimated size: {self._estimate_size():.1f} GB",
                title="🚀 Dataset Workflow",
                border_style="magenta",
            )
        )

        # Step 1: Download malware
        if not self.step1_download_malware():
            console.print("[red]❌ Workflow failed at Step 1")
            sys.exit(1)

        # Step 2: Collect benign
        if not self.step2_collect_benign():
            console.print("[red]❌ Workflow failed at Step 2")
            sys.exit(1)

        # Step 3: Organize dataset
        if not self.step3_organize_dataset():
            console.print("[red]❌ Workflow failed at Step 3")
            sys.exit(1)

        # Success summary
        console.print(
            Panel.fit(
                "[bold green]✅ Dataset Acquisition Complete!\n\n"
                "Next steps:\n"
                "• Day 4-5: Implement feature extraction pipeline\n"
                "• Run: uv run python scripts/ml/extract_features_batch.py\n\n"
                "Dataset location:\n"
                "• data/organized/train/ (70% of data)\n"
                "• data/organized/val/ (15% of data)\n"
                "• data/organized/test/ (15% of data)",
                title="🎉 Success",
                border_style="green",
            )
        )

    def _estimate_time(self) -> float:
        """Estimate total time in hours."""
        # Rough estimates:
        # - MalwareBazaar: 1s per sample (API rate limit)
        # - Benign collection: ~100 files/second
        # - Organization: ~1000 files/second

        malware_time = (self.malware_samples * 1.0) / 3600  # seconds to hours
        benign_time = (self.benign_samples / 100) / 3600
        org_time = ((self.malware_samples + self.benign_samples) / 1000) / 3600

        return malware_time + benign_time + org_time

    def _estimate_size(self) -> float:
        """Estimate total size in GB."""
        # Rough estimates:
        # - Malware: ~1 MB average
        # - Benign: ~500 KB average

        malware_gb = (self.malware_samples * 1.0) / 1024  # MB to GB
        benign_gb = (self.benign_samples * 0.5) / 1024

        return malware_gb + benign_gb


def main():
    parser = argparse.ArgumentParser(
        description="Complete dataset acquisition workflow"
    )

    # Preset modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Full production dataset (50K malware + 50K benign = 100K total)",
    )
    mode_group.add_argument(
        "--quick",
        action="store_true",
        help="Quick test dataset (500 malware + 500 benign = 1K total)",
    )
    mode_group.add_argument(
        "--small",
        action="store_true",
        help="Small dataset for prototyping (5K malware + 5K benign = 10K total)",
    )

    # Custom counts
    parser.add_argument(
        "--malware", type=int, help="Number of malware samples to download"
    )
    parser.add_argument(
        "--benign", type=int, help="Number of benign samples to collect"
    )

    args = parser.parse_args()

    # Determine sample counts
    if args.full:
        malware_samples = 50000
        benign_samples = 50000
    elif args.quick:
        malware_samples = 500
        benign_samples = 500
    elif args.small:
        malware_samples = 5000
        benign_samples = 5000
    elif args.malware and args.benign:
        malware_samples = args.malware
        benign_samples = args.benign
    else:
        # Default to small dataset
        console.print("[yellow]No mode specified, using --small (10K samples)")
        console.print(
            "[yellow]Use --full for production (100K) or --quick for testing (1K)"
        )
        malware_samples = 5000
        benign_samples = 5000

    workflow = DatasetWorkflow(malware_samples, benign_samples)
    workflow.run_workflow()


if __name__ == "__main__":
    main()
