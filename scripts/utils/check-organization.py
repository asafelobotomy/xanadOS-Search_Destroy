#!/usr/bin/env python3
"""
Check repository organization and report issues.
"""

import sys
from pathlib import Path


def check_organization():
    """Check if repository is properly organized."""
    issues = []
    repo_root = Path(__file__).parent.parent

    # Check for files in wrong locations
    misplaced_files = [
        (repo_root / "*.py", "Python files should be in app/, dev/, or scripts/"),
        (repo_root / "test_*.py", "Test files should be in dev/ or tests/"),
        (repo_root / "*.md", "Documentation should be in docs/ (except main README)"),
    ]

    for pattern, message in misplaced_files:
        for file in repo_root.glob(pattern.name):
            if file.name not in ["README.md", "CHANGELOG.md", "LICENSE"]:
                issues.append(f"Misplaced file: {file.name} - {message}")

    # Check for missing __init__.py files
    python_dirs = ["app", "app/core", "app/gui", "app/monitoring", "app/utils", "tests"]
    for dir_name in python_dirs:
        init_file = repo_root / dir_name / "__init__.py"
        if not init_file.exists() and (repo_root / dir_name).exists():
            issues.append(f"Missing __init__.py in {dir_name}")

    if issues:
        print("❌ Organization issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Repository is properly organized")
        return True


if __name__ == "__main__":
    sys.exit(0 if check_organization() else 1)
