#!/usr/bin/env python3
"""
Comprehensive Repository Maintenance and Cleanup - 2025
========================================================

Performs full repository maintenance following the file organization policy
and modern best practices. This script:

1. Moves misplaced files to correct locations per policy
2. Archives temporary/debug files
3. Cleans up root directory violations
4. Updates documentation indexes
5. Validates final structure
"""

import shutil
from datetime import datetime
from pathlib import Path


class RepositoryMaintenance:
    """Comprehensive repository maintenance and cleanup."""

    def __init__(self):
        self.repo_root = Path.cwd()
        self.archive_dir = self.repo_root / "archive"
        self.docs_dir = self.repo_root / "docs"
        self.tests_dir = self.repo_root / "tests"
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.changes_made = []

    def log_change(self, action: str, source: str, target: str = ""):
        """Log changes for reporting."""
        change = f"{action}: {source}"
        if target:
            change += f" → {target}"
        self.changes_made.append(change)
        print(f"  ✅ {change}")

    def move_file_safely(self, source: Path, target: Path):
        """Move file with backup and directory creation."""
        if not source.exists():
            return False

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        # Handle existing target
        if target.exists():
            backup = target.with_suffix(f".backup_{self.timestamp}")
            shutil.move(str(target), str(backup))
            self.log_change("BACKUP", str(target), str(backup))

        # Move file
        shutil.move(str(source), str(target))
        self.log_change("MOVED", str(source), str(target))
        return True

    def archive_file(self, source: Path, reason: str):
        """Archive a file with documentation."""
        if not source.exists():
            return False

        # Determine archive subdirectory
        if source.name.startswith("test_"):
            archive_subdir = self.archive_dir / "temp-testing"
        elif "debug" in source.name:
            archive_subdir = self.archive_dir / "development"
        elif source.suffix == ".md":
            archive_subdir = self.archive_dir / "temp-docs"
        else:
            archive_subdir = self.archive_dir / "superseded"

        archive_subdir.mkdir(parents=True, exist_ok=True)
        target = archive_subdir / source.name

        # Move file
        shutil.move(str(source), str(target))
        self.log_change("ARCHIVED", str(source), str(target))

        # Update archive index
        self.update_archive_index(target, reason)
        return True

    def update_archive_index(self, archived_file: Path, reason: str):
        """Update the archive index with new entry."""
        index_file = self.archive_dir / "ARCHIVE_INDEX.md"

        # Add entry to archive index
        entry = f"- `{archived_file.relative_to(self.repo_root)}` — Archived {datetime.now().strftime('%Y-%m-%d')} ({reason})\n"

        try:
            with open(index_file, 'a') as f:
                f.write(entry)
        except Exception as e:
            print(f"  ⚠️  Could not update archive index: {e}")

    def cleanup_test_files(self):
        """Clean up test files from root directory."""
        print("\n📋 Phase 1: Cleaning up test files from root directory")

        test_files = list(self.repo_root.glob("test_*.py"))
        if not test_files:
            print("  ✅ No test files found in root directory")
            return

        print(f"  📋 Found {len(test_files)} test files to clean up")

        for test_file in test_files:
            # Determine if this is a temporary test or permanent test
            if any(keyword in test_file.name for keyword in ["fix", "config", "cron", "integration", "optimization"]):
                # These are temporary testing files from recent work
                self.archive_file(test_file, "temporary test file from recent development work")
            else:
                # Move to tests directory
                target = self.tests_dir / test_file.name
                self.move_file_safely(test_file, target)

    def cleanup_documentation_files(self):
        """Clean up documentation files from root directory."""
        print("\n📋 Phase 2: Organizing documentation files")

        # Check for documentation files in root
        doc_files = [
            ("CRON_INTEGRATION_SUMMARY.md", "implementation-reports"),
            ("RKHUNTER_FIX_SUMMARY.md", "implementation-reports"),
        ]

        for filename, subdir in doc_files:
            source = self.repo_root / filename
            if source.exists():
                target = self.docs_dir / subdir / filename.lower().replace("_", "-")
                self.move_file_safely(source, target)

    def cleanup_cache_and_temp_files(self):
        """Clean up cache and temporary files."""
        print("\n📋 Phase 3: Cleaning cache and temporary files")

        # Clean Python cache
        pycache_dirs = list(self.repo_root.rglob("__pycache__"))
        for cache_dir in pycache_dirs:
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)
                self.log_change("REMOVED", str(cache_dir))

        # Clean .pyc files
        pyc_files = list(self.repo_root.rglob("*.pyc"))
        for pyc_file in pyc_files:
            pyc_file.unlink()
            self.log_change("REMOVED", str(pyc_file))

        # Clean other temporary files
        temp_patterns = ["*.tmp", "*.bak", "*.swp", "*~"]
        for pattern in temp_patterns:
            for temp_file in self.repo_root.rglob(pattern):
                temp_file.unlink()
                self.log_change("REMOVED", str(temp_file))

    def cleanup_logs_directory(self):
        """Archive old logs and clean up logs directory."""
        print("\n📋 Phase 4: Cleaning up logs directory")

        logs_dir = self.repo_root / "logs"
        if not logs_dir.exists():
            print("  ✅ No logs directory found")
            return

        # Archive entire logs directory if it has content
        log_files = list(logs_dir.iterdir())
        if log_files:
            archive_logs_dir = self.archive_dir / "performance-monitoring" / f"logs_{self.timestamp}"
            archive_logs_dir.mkdir(parents=True, exist_ok=True)

            for log_file in log_files:
                if log_file.is_file():
                    shutil.move(str(log_file), str(archive_logs_dir / log_file.name))
                    self.log_change("ARCHIVED", str(log_file), str(archive_logs_dir / log_file.name))

            # Remove empty logs directory
            try:
                logs_dir.rmdir()
                self.log_change("REMOVED", str(logs_dir))
            except OSError:
                pass  # Directory not empty

    def cleanup_node_modules(self):
        """Clean up Node.js dependencies that may be outdated."""
        print("\n📋 Phase 5: Checking Node.js dependencies")

        node_modules = self.repo_root / "node_modules"
        self.repo_root / "package-lock.json"

        if node_modules.exists():
            print(f"  📋 Node modules directory size: {self.get_dir_size(node_modules):.1f}MB")
            print("  💡 Consider running 'npm ci' to refresh dependencies")
        else:
            print("  ✅ No node_modules directory found")

    def get_dir_size(self, path: Path) -> float:
        """Get directory size in MB."""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except (OSError, PermissionError):
            pass
        return total / (1024 * 1024)

    def validate_structure(self):
        """Validate final repository structure."""
        print("\n📋 Phase 6: Validating repository structure")

        # Count files in root directory
        root_files = [f for f in self.repo_root.iterdir() if f.is_file()]
        print(f"  📋 Files in root directory: {len(root_files)}")

        # Check for policy violations
        allowed_files = {
            "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE", "VERSION",
            "package.json", "package-lock.json", "pyproject.toml", "uv.lock", "uv.toml",
            "Makefile", "Dockerfile", "docker-compose.yml", ".gitignore", ".gitattributes",
            ".editorconfig", ".prettierrc.json", ".prettierignore", ".markdownlint.json",
            ".markdownlintignore", ".nvmrc", ".pre-commit-config.yaml", ".cspellignore"
        }

        violations = []
        for file in root_files:
            if file.name not in allowed_files:
                violations.append(file.name)

        if violations:
            print(f"  ⚠️  Policy violations found: {violations}")
        else:
            print("  ✅ Root directory complies with file organization policy")

    def generate_maintenance_report(self):
        """Generate maintenance report."""
        print("\n📊 Generating maintenance report...")

        report_content = f"""# Repository Maintenance Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
Performed comprehensive repository maintenance and cleanup.

## Changes Made ({len(self.changes_made)} total)

"""

        for change in self.changes_made:
            report_content += f"- {change}\n"

        report_content += f"""
## Statistics
- **Timestamp**: {self.timestamp}
- **Changes**: {len(self.changes_made)}
- **Categories**: Test files, documentation, cache cleanup, logs archival

## Validation
Repository structure validated for compliance with file organization policy.
"""

        report_file = self.docs_dir / "implementation-reports" / f"maintenance-report-{self.timestamp}.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            f.write(report_content)

        print(f"  ✅ Maintenance report saved: {report_file}")

    def run_maintenance(self):
        """Run complete maintenance process."""
        print("🧹 Starting Comprehensive Repository Maintenance")
        print("=" * 60)
        print(f"Repository: {self.repo_root}")
        print(f"Timestamp: {self.timestamp}")

        try:
            self.cleanup_test_files()
            self.cleanup_documentation_files()
            self.cleanup_cache_and_temp_files()
            self.cleanup_logs_directory()
            self.cleanup_node_modules()
            self.validate_structure()
            self.generate_maintenance_report()

            print("\n🎉 Repository maintenance completed successfully!")
            print(f"📊 Total changes made: {len(self.changes_made)}")

        except Exception as e:
            print(f"\n❌ Maintenance failed: {e}")
            raise


if __name__ == "__main__":
    maintenance = RepositoryMaintenance()
    maintenance.run_maintenance()
