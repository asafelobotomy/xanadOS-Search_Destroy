#!/usr/bin/env python3
"""
Repository Organization and Maintenance Tool for xanadOS-Search_Destroy

This script organizes the repository structure, moves misplaced files,
and sets up automated organization checks.
"""

import datetime
import shutil
from pathlib import Path


class RepositoryOrganizer:
    """Organizes and maintains repository structure."""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.moves_made = []
        self.issues_found = []

    def organize_repository(self):
        """Main organization function."""
        print("🏗️  Starting Repository Organization")
        print("=" * 50)

        # Step 1: Move misplaced files
        self._move_misplaced_files()

        # Step 2: Clean up duplicate files
        self._remove_duplicates()

        # Step 3: Ensure proper directory structure
        self._ensure_directory_structure()

        # Step 4: Update .gitignore if needed
        self._update_gitignore()

        # Step 5: Create organization maintenance scripts
        self._create_maintenance_scripts()

        # Step 6: Generate organization report
        self._generate_report()

        print("\n✅ Repository organization complete!")

    def _move_misplaced_files(self):
        """Move files that are in the wrong location."""
        print("\n📁 Moving misplaced files...")

        moves = [
            # Move test files from root to appropriate dev directory
            ("test_grace_period.py", "dev/test_grace_period.py"),
            ("verify_cleanup.py", "dev/verify_cleanup.py"),
            # Ensure README files are in the right place
            (
                "REPOSITORY_CLEANUP_SUMMARY.md",
                "docs/project/REPOSITORY_CLEANUP_SUMMARY.md",
            ),
        ]

        for src, dst in moves:
            src_path = self.repo_root / src
            dst_path = self.repo_root / dst

            if src_path.exists():
                # Create destination directory if it doesn't exist
                dst_path.parent.mkdir(parents=True, exist_ok=True)

                # Move the file
                if dst_path.exists():
                    print(f"  ⚠️  Destination exists, backing up: {dst}")
                    backup_path = dst_path.with_suffix(f"{dst_path.suffix}.backup")
                    shutil.move(str(dst_path), str(backup_path))

                shutil.move(str(src_path), str(dst_path))
                self.moves_made.append((src, dst))
                print(f"  ✅ Moved: {src} → {dst}")
            else:
                print(f"  ℹ️  File not found: {src}")

    def _remove_duplicates(self):
        """Remove duplicate files."""
        print("\n🗑️  Checking for duplicates...")

        # Check for duplicate REPOSITORY_CLEANUP_SUMMARY.md files
        potential_duplicates = [
            (
                "docs/REPOSITORY_CLEANUP_SUMMARY.md",
                "docs/project/REPOSITORY_CLEANUP_SUMMARY.md",
            ),
        ]

        for file1, file2 in potential_duplicates:
            path1 = self.repo_root / file1
            path2 = self.repo_root / file2

            if path1.exists() and path2.exists():
                # Compare file contents
                try:
                    if path1.read_text() == path2.read_text():
                        path1.unlink()
                        print(f"  🗑️  Removed duplicate: {file1}")
                    else:
                        print(f"  ⚠️  Files differ, keeping both: {file1}, {file2}")
                except Exception as e:
                    print(f"  ❌ Error comparing files: {e}")

    def _ensure_directory_structure(self):
        """Ensure all necessary directories exist."""
        print("\n📂 Ensuring directory structure...")

        required_dirs = [
            "app/core",
            "app/gui",
            "app/monitoring",
            "app/utils",
            "config",
            "docs/developer",
            "docs/implementation",
            "docs/project",
            "docs/releases",
            "docs/user",
            "dev/debug-scripts",
            "dev/test-scripts",
            "packaging/flatpak",
            "packaging/icons",
            "scripts",
            "tests",
            "archive",
        ]

        for dir_path in required_dirs:
            full_path = self.repo_root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  📁 Created directory: {dir_path}")

        # Ensure __init__.py files exist in Python packages
        python_packages = [
            "app",
            "app/core",
            "app/gui",
            "app/monitoring",
            "app/utils",
            "tests",
        ]

        for package in python_packages:
            init_file = self.repo_root / package / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"  🐍 Created __init__.py: {package}")

    def _update_gitignore(self):
        """Update .gitignore with proper patterns."""
        print("\n🚫 Updating .gitignore...")

        gitignore_path = self.repo_root / ".gitignore"

        required_patterns = [
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "wheels/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            "",
            "# Virtual environments",
            ".venv/",
            "venv/",
            "ENV/",
            "env/",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# Application specific",
            "*.log",
            "temp/",
            "tmp/",
            ".DS_Store",
            "",
            "# Testing",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            "",
            "# Documentation builds",
            "docs/_build/",
            "",
            "# Backup files",
            "*.backup",
            "*.bak",
            "*~",
        ]

        if gitignore_path.exists():
            current_content = gitignore_path.read_text()
        else:
            current_content = ""

        # Add missing patterns
        lines_to_add = []
        for pattern in required_patterns:
            if pattern not in current_content and pattern != "":
                lines_to_add.append(pattern)

        if lines_to_add:
            with gitignore_path.open("a", encoding="utf-8") as f:
                f.write("\n# Added by repository organizer\n")
                for line in lines_to_add:
                    f.write(f"{line}\n")
            print(f"  ✅ Added {len(lines_to_add)} patterns to .gitignore")
        else:
            print("  ℹ️  .gitignore is up to date")

    def _create_maintenance_scripts(self):
        """Create scripts for ongoing organization maintenance."""
        print("\n🔧 Creating maintenance scripts...")

        # Create organization check script
        check_script = self.repo_root / "scripts" / "check-organization.py"
        check_script.parent.mkdir(exist_ok=True)

        check_script_content = '''#!/usr/bin/env python3
"""
Check repository organization and report issues.
"""

import os
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
'''

        check_script.write_text(check_script_content)
        check_script.chmod(0o755)
        print(f"  ✅ Created: {check_script.relative_to(self.repo_root)}")

        # Create pre-commit hook installer
        hook_installer = self.repo_root / "scripts" / "install-hooks.sh"
        hook_installer_content = '''#!/bin/bash
"""
Install git hooks for repository organization.
"""

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Check repository organization before commit

python3 scripts/check-organization.py
if [ $? -ne 0 ]; then
    echo "❌ Please fix organization issues before committing"
    echo "💡 Run: python3 dev/organize_repository.py"
    exit 1
fi
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "✅ Installed git hooks for repository organization"
'''

        hook_installer.write_text(hook_installer_content)
        hook_installer.chmod(0o755)
        print(f"  ✅ Created: {hook_installer.relative_to(self.repo_root)}")

    def _generate_report(self):
        """Generate organization report."""
        print("\n📋 Generating organization report...")

        # Use runtime-specific filename to avoid clobbering curated static doc
        report_path = (
            self.repo_root / "docs" / "project" / "REPOSITORY_ORGANIZATION_RUNTIME.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report_content = f"""# Repository Organization Report

**Generated:** {timestamp}

## Directory Structure

```
xanadOS-Search_Destroy/
├── app/                    # Main application code
│   ├── core/              # Core functionality
│   ├── gui/               # User interface
│   ├── monitoring/        # Real-time monitoring
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── dev/                   # Development tools and tests
├── docs/                  # Documentation
│   ├── developer/         # Developer documentation
│   ├── implementation/    # Implementation details
│   ├── project/          # Project documentation
│   ├── releases/         # Release notes
│   └── user/             # User documentation
├── packaging/             # Packaging files
├── scripts/              # Build and utility scripts
├── tests/                # Unit tests
└── archive/              # Archived files
```

## Organization Rules

### File Placement

### Naming Conventions

## Maintenance

### Automated Checks

### Manual Maintenance

## Recent Changes

"""

        if self.moves_made:
            report_content += "### Files Moved\n\n"
            for src, dst in self.moves_made:
                report_content += f"- `{src}` -> `{dst}`\n"
        else:
            report_content += "No files were moved during this organization.\n"

        if self.issues_found:
            report_content += "\n### Issues Found\n\n"
            for issue in self.issues_found:
                report_content += f"- {issue}\n"
        else:
            report_content += "\nNo organization issues found.\n"

        report_content += """
## Statistics

*This report is automatically generated. Do not edit manually.*
"""

        report_path.write_text(report_content, encoding="utf-8")
        print(f"  ✅ Generated: {report_path.relative_to(self.repo_root)}")


def main():
    """Main function."""
    repo_root = Path(__file__).parent.parent
    organizer = RepositoryOrganizer(str(repo_root))
    organizer.organize_repository()


if __name__ == "__main__":
    main()
