#!/usr/bin/env python3
"""
Repository Organization Script
==============================
Comprehensive cleanup and organization of the xanadOS-Search_Destroy repository.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


class RepositoryOrganizer:
    """Organizes and cleans up the repository structure."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.changes_made = []
        
    def log_change(self, message: str):
        """Log a change that was made."""
        self.changes_made.append(message)
        print(f"✅ {message}")
    
    def clean_python_cache(self):
        """Remove all __pycache__ directories and .pyc files."""
        print("🧹 Cleaning Python cache files...")
        
        # Remove __pycache__ directories
        cache_dirs = list(self.repo_path.rglob("__pycache__"))
        app_cache_dirs = [d for d in cache_dirs if not str(d).startswith(str(self.repo_path / ".venv"))]
        
        for cache_dir in app_cache_dirs:
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                
        # Remove .pyc files
        pyc_files = list(self.repo_path.rglob("*.pyc"))
        app_pyc_files = [f for f in pyc_files if not str(f).startswith(str(self.repo_path / ".venv"))]
        
        for pyc_file in app_pyc_files:
            if pyc_file.exists():
                pyc_file.unlink()
                
        self.log_change(f"Removed {len(app_cache_dirs)} __pycache__ directories and {len(app_pyc_files)} .pyc files")
    
    def update_gitignore(self):
        """Update .gitignore to ensure proper exclusions."""
        print("📝 Updating .gitignore...")
        
        gitignore_path = self.repo_path / ".gitignore"
        
        # Essential patterns that should be in .gitignore
        essential_patterns = [
            "# Python cache and compiled files",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            "",
            "# Virtual environments", 
            ".venv/",
            "venv/",
            "ENV/",
            "env/",
            "",
            "# IDE and editor files",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# OS generated files",
            ".DS_Store",
            ".DS_Store?",
            "._*",
            ".Spotlight-V100",
            ".Trashes",
            "ehthumbs.db",
            "Thumbs.db",
            "",
            "# Application specific",
            "*.log",
            "*.tmp",
            "config.json",
            "activity_logs.json",
            "scan_reports/",
            "quarantine/",
            "temp/",
            "",
            "# Build and distribution",
            "build/",
            "dist/",
            "*.egg-info/",
            "",
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                current_content = f.read()
        else:
            current_content = ""
            
        # Add missing patterns
        missing_patterns = []
        for pattern in essential_patterns:
            if pattern.strip() and pattern not in current_content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            with open(gitignore_path, 'a') as f:
                f.write('\n# Added by repository organizer\n')
                for pattern in missing_patterns:
                    f.write(f'{pattern}\n')
            
            self.log_change(f"Added {len(missing_patterns)} missing patterns to .gitignore")
        else:
            print("✅ .gitignore is already comprehensive")
    
    def organize_documentation(self):
        """Organize documentation files."""
        print("📚 Organizing documentation...")
        
        docs_path = self.repo_path / "docs"
        
        # Ensure proper documentation structure
        required_docs = [
            "user/",
            "developer/", 
            "project/",
            "implementation/",
            "releases/"
        ]
        
        created_dirs = []
        for doc_dir in required_docs:
            dir_path = docs_path / doc_dir
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(doc_dir)
        
        if created_dirs:
            self.log_change(f"Created documentation directories: {', '.join(created_dirs)}")
    
    def clean_development_files(self):
        """Clean up development and experimental files."""
        print("🔧 Cleaning development files...")
        
        dev_path = self.repo_path / "dev"
        archive_path = self.repo_path / "archive"
        
        # Move obviously outdated files to archive
        outdated_patterns = [
            "*.bak",
            "*.backup", 
            "*.old",
            "*.tmp",
            "*.temp",
        ]
        
        moved_files = []
        for pattern in outdated_patterns:
            for file_path in self.repo_path.rglob(pattern):
                if not str(file_path).startswith(str(archive_path)) and not str(file_path).startswith(str(self.repo_path / ".venv")):
                    # Move to archive
                    archive_dest = archive_path / "auto-archived" / file_path.name
                    archive_dest.parent.mkdir(parents=True, exist_ok=True)
                    if not archive_dest.exists():
                        shutil.move(str(file_path), str(archive_dest))
                        moved_files.append(file_path.name)
        
        if moved_files:
            self.log_change(f"Moved {len(moved_files)} outdated files to archive")
    
    def organize_app_structure(self):
        """Ensure proper app module structure."""
        print("🏗️ Organizing app structure...")
        
        app_path = self.repo_path / "app"
        
        # Ensure all modules have proper __init__.py files
        module_dirs = [
            app_path / "core",
            app_path / "gui", 
            app_path / "utils",
            app_path / "monitoring",
        ]
        
        created_inits = []
        for module_dir in module_dirs:
            if module_dir.exists():
                init_file = module_dir / "__init__.py"
                if not init_file.exists():
                    init_file.write_text('"""Module initialization."""\n')
                    created_inits.append(module_dir.name)
        
        if created_inits:
            self.log_change(f"Created __init__.py files for: {', '.join(created_inits)}")
    
    def update_version_consistency(self):
        """Ensure version consistency across files."""
        print("🔢 Checking version consistency...")
        
        version_file = self.repo_path / "VERSION"
        if version_file.exists():
            version = version_file.read_text().strip()
            
            # Check app/__init__.py
            app_init = self.repo_path / "app" / "__init__.py"
            if app_init.exists():
                content = app_init.read_text()
                if "__version__" not in content:
                    content += f'\n__version__ = "{version}"\n'
                    app_init.write_text(content)
                    self.log_change("Added version to app/__init__.py")
    
    def create_organization_summary(self):
        """Create a summary of organization changes."""
        print("📋 Creating organization summary...")
        
        summary_path = self.repo_path / "ORGANIZATION_SUMMARY.md"
        
        summary_content = f"""# Repository Organization Summary

This file documents the organization changes made to the xanadOS-Search_Destroy repository.

## Changes Made

"""
        
        for i, change in enumerate(self.changes_made, 1):
            summary_content += f"{i}. {change}\n"
        
        summary_content += f"""

## Repository Structure

```
xanadOS-Search_Destroy/
├── app/                    # Main application code
│   ├── core/              # Core functionality modules
│   ├── gui/               # User interface components
│   ├── monitoring/        # System monitoring modules
│   └── utils/             # Utility functions
├── archive/               # Archived and deprecated files
├── config/                # Configuration files
├── dev/                   # Development tools and scripts
├── docs/                  # Documentation
│   ├── user/              # User documentation
│   ├── developer/         # Developer documentation
│   ├── project/           # Project documentation
│   ├── implementation/    # Implementation details
│   └── releases/          # Release notes
├── packaging/             # Package distribution files
├── scripts/               # Build and utility scripts
└── tests/                 # Test files
```

## Maintenance Notes

- Python cache files (__pycache__) are automatically cleaned
- .gitignore has been updated with comprehensive patterns
- All modules have proper __init__.py files
- Development files are properly organized

## Next Steps

1. Review the organized structure
2. Update any hardcoded paths in configuration
3. Run tests to ensure functionality is preserved
4. Update CI/CD scripts if necessary

Generated on: {subprocess.check_output(['date'], text=True).strip()}
"""
        
        summary_path.write_text(summary_content)
        self.log_change("Created ORGANIZATION_SUMMARY.md")
    
    def run_organization(self):
        """Run the complete organization process."""
        print("🚀 Starting repository organization...")
        print(f"📁 Repository: {self.repo_path}")
        print()
        
        try:
            # Run organization steps
            self.clean_python_cache()
            self.update_gitignore()
            self.organize_documentation()
            self.clean_development_files()
            self.organize_app_structure()
            self.update_version_consistency()
            self.create_organization_summary()
            
            print()
            print("🎉 Repository organization complete!")
            print(f"📊 Total changes made: {len(self.changes_made)}")
            print()
            print("📋 Summary of changes:")
            for change in self.changes_made:
                print(f"  • {change}")
            
            print()
            print("💡 Recommendations:")
            print("  • Review ORGANIZATION_SUMMARY.md for details")
            print("  • Run tests to ensure functionality is preserved")
            print("  • Commit the organized repository structure")
            print("  • Update documentation if needed")
            
        except Exception as e:
            print(f"❌ Error during organization: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    repo_path = os.getcwd()
    
    if not os.path.exists(os.path.join(repo_path, "app", "main.py")):
        print("❌ This doesn't appear to be the xanadOS-Search_Destroy repository")
        print("Please run this script from the repository root directory")
        sys.exit(1)
    
    organizer = RepositoryOrganizer(repo_path)
    organizer.run_organization()


if __name__ == "__main__":
    main()
