#!/usr/bin/env python3
"""
Test Random Forest detector on sample files.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rich.console import Console
from rich.table import Table

from app.ml.random_forest_detector import RandomForestDetector

console = Console()


def main():
    """Test ML detector on sample files."""
    console.print("\n[bold cyan]🤖 Testing Random Forest ML Detector\n")

    # Initialize detector
    console.print("[cyan]Loading model...")
    try:
        detector = RandomForestDetector(model_version="1.0.0")
        console.print("[green]✅ Model loaded successfully\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to load model: {e}")
        return 1

    # Get test files
    test_malware_dir = Path("data/organized/test/malware")
    test_benign_dir = Path("data/organized/test/benign")

    malware_files = list(test_malware_dir.glob("*"))[:5]  # Test 5 malware samples
    benign_files = list(test_benign_dir.glob("*"))[:5]  # Test 5 benign samples

    if not malware_files or not benign_files:
        console.print("[yellow]⚠️  Test files not found")
        return 1

    console.print(f"[cyan]Testing on {len(malware_files)} malware + {len(benign_files)} benign samples\n")

    # Results table
    results_table = Table(show_header=True, header_style="bold cyan")
    results_table.add_column("File", width=40)
    results_table.add_column("Type", width=10)
    results_table.add_column("Prediction", width=12)
    results_table.add_column("Confidence", justify="right", width=12)
    results_table.add_column("Time (ms)", justify="right", width=10)

    correct = 0
    total = 0

    # Test malware files
    for file_path in malware_files:
        result = detector.scan_file(file_path)
        total += 1

        if result.is_malware:
            correct += 1
            prediction = "[green]MALWARE ✓"
        else:
            prediction = "[red]BENIGN ✗"

        results_table.add_row(
            file_path.name[:38],
            "[red]Malware",
            prediction,
            f"{result.confidence:.2%}",
            f"{result.prediction_time * 1000:.1f}",
        )

    # Test benign files
    for file_path in benign_files:
        result = detector.scan_file(file_path)
        total += 1

        if not result.is_malware:
            correct += 1
            prediction = "[green]BENIGN ✓"
        else:
            prediction = "[red]MALWARE ✗"

        results_table.add_row(
            file_path.name[:38],
            "[green]Benign",
            prediction,
            f"{result.confidence:.2%}",
            f"{result.prediction_time * 1000:.1f}",
        )

    console.print(results_table)
    console.print()

    # Statistics
    stats = detector.get_statistics()
    accuracy = correct / total if total > 0 else 0.0

    console.print(f"[bold]Accuracy: {accuracy:.1%} ({correct}/{total} correct)")
    console.print(f"Avg scan time: {stats['avg_scan_time'] * 1000:.2f} ms")
    console.print(f"Malware detected: {stats['malware_detected']}/{total}")
    console.print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
