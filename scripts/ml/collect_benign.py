#!/usr/bin/env python3
"""
Collect benign files from system for ML training.

This script collects clean executable files from system directories
(binaries, libraries, applications) to create a benign dataset.

Usage:
    uv run python scripts/ml/collect_benign.py --samples 50000

Safety: Only collects from trusted system directories.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

console = Console()

# System directories with trusted binaries
TRUSTED_DIRECTORIES = [
    "/usr/bin",
    "/usr/sbin",
    "/usr/lib",
    "/usr/lib64",
    "/usr/local/bin",
    "/usr/local/sbin",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
]

# User directories (optional, requires user confirmation)
USER_DIRECTORIES = [
    "~/.local/bin",
    "~/.local/lib",
]

# Output directory
BENIGN_DIR = Path("data/benign")
METADATA_FILE = BENIGN_DIR / "metadata.json"

# File filters
MIN_FILE_SIZE = 1024  # 1 KB minimum
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB maximum
ALLOWED_EXTENSIONS = {
    "",  # No extension (binaries)
    ".so",  # Shared libraries
    ".o",  # Object files
    ".a",  # Static libraries
}


class BenignCollector:
    """Collect benign files from system directories."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = self._load_metadata()
        self.collected_hashes = set()

    def _load_metadata(self) -> dict:
        """Load existing metadata or create new."""
        if METADATA_FILE.exists():
            data = json.loads(METADATA_FILE.read_text())
            return data
        return {"samples": {}, "collection_stats": {}}

    def _save_metadata(self):
        """Save metadata to JSON."""
        METADATA_FILE.write_text(json.dumps(self.metadata, indent=2))

    def is_valid_file(self, file_path: Path) -> bool:
        """Check if file is valid for collection."""
        try:
            # Check if regular file
            if not file_path.is_file():
                return False

            # Check size
            size = file_path.stat().st_size
            if size < MIN_FILE_SIZE or size > MAX_FILE_SIZE:
                return False

            # Check extension
            if file_path.suffix not in ALLOWED_EXTENSIONS:
                return False

            # Check if executable or library (by magic bytes or permissions)
            # ELF magic: \x7fELF
            # PE magic: MZ
            with open(file_path, "rb") as f:
                magic = f.read(4)
                if not (magic[:4] == b"\x7fELF" or magic[:2] == b"MZ"):
                    # Not a binary we're interested in
                    return False

            return True

        except (OSError, PermissionError):
            return False

    def collect_from_directory(
        self, source_dir: Path, max_files: Optional[int] = None
    ) -> int:
        """Collect files from a directory."""
        collected = 0

        try:
            for file_path in source_dir.rglob("*"):
                if max_files and collected >= max_files:
                    break

                if not self.is_valid_file(file_path):
                    continue

                # Calculate hash
                try:
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                except (OSError, PermissionError):
                    continue

                # Skip if already collected
                if file_hash in self.collected_hashes:
                    continue

                # Copy file
                dest_path = self.output_dir / f"{file_path.stem}_{file_hash[:16]}"

                try:
                    shutil.copy2(file_path, dest_path)

                    # Store metadata
                    self.metadata["samples"][file_hash] = {
                        "original_path": str(file_path),
                        "file_name": file_path.name,
                        "file_size": file_path.stat().st_size,
                        "source_directory": str(source_dir),
                    }

                    self.collected_hashes.add(file_hash)
                    collected += 1

                    console.print(
                        f"[green]✅ Collected: {file_path.name[:40]} ({file_hash[:16]})"
                    )

                except (OSError, PermissionError) as e:
                    console.print(f"[yellow]⚠️  Copy failed: {file_path}: {e}")
                    continue

        except (OSError, PermissionError) as e:
            console.print(f"[red]❌ Cannot access directory: {source_dir}: {e}")

        return collected

    def collect_batch(
        self, target_samples: int = 50000, include_user_dirs: bool = False
    ):
        """Collect benign files from system."""
        console.print(f"\n[bold cyan]🛡️  Benign File Collector")
        console.print(f"[cyan]Target: {target_samples:,} benign samples")
        console.print(f"[cyan]Output: {self.output_dir}")
        console.print()

        # Prepare directory list
        directories = [Path(d) for d in TRUSTED_DIRECTORIES]

        if include_user_dirs:
            user_dirs = [Path(d).expanduser() for d in USER_DIRECTORIES]
            directories.extend([d for d in user_dirs if d.exists()])

        console.print(f"[cyan]Scanning {len(directories)} directories...")
        console.print()

        total_collected = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task("[cyan]Collecting files...", total=target_samples)

            for directory in directories:
                if total_collected >= target_samples:
                    break

                if not directory.exists():
                    continue

                console.print(f"[dim]📂 Scanning: {directory}")

                remaining = target_samples - total_collected
                collected = self.collect_from_directory(directory, max_files=remaining)

                total_collected += collected
                progress.update(task, completed=total_collected)

                # Save metadata periodically
                if collected > 0:
                    self._save_metadata()

        console.print()
        console.print(f"[bold green]✅ Collection Complete!")
        console.print(f"[green]Collected: {total_collected:,} benign files")
        console.print(
            f"[cyan]Total size: {sum(p.stat().st_size for p in self.output_dir.glob('*') if p.is_file()) / 1e9:.2f} GB"
        )

        # Update collection stats
        self.metadata["collection_stats"] = {
            "total_collected": total_collected,
            "unique_hashes": len(self.collected_hashes),
            "directories_scanned": len(directories),
            "last_updated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save_metadata()


def main():
    parser = argparse.ArgumentParser(
        description="Collect benign files from system directories"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=50000,
        help="Number of samples to collect (default: 50000)",
    )
    parser.add_argument(
        "--include-user-dirs",
        action="store_true",
        help="Include user directories (~/.local/bin, ~/.local/lib)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BENIGN_DIR,
        help=f"Output directory (default: {BENIGN_DIR})",
    )

    args = parser.parse_args()

    console.print("[bold cyan]ℹ️  This script collects files from system directories")
    console.print("[cyan]• Only trusted system paths are scanned")
    console.print("[cyan]• Files are copied, not moved")
    console.print("[cyan]• Requires read permissions for system directories")
    console.print()

    collector = BenignCollector(output_dir=args.output_dir)
    collector.collect_batch(
        target_samples=args.samples, include_user_dirs=args.include_user_dirs
    )


if __name__ == "__main__":
    main()
