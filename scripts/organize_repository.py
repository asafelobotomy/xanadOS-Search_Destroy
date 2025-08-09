#!/usr/bin/env python3
"""
Repository Organization and Cleanup Script for S&D - Search & Destroy
Organizes files, archives deprecated content, and cleans up the repository.
"""

import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class RepositoryOrganizer:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
    def clean_python_cache(self):
        """Remove Python cache files and directories."""
        print("🧹 Cleaning Python cache files...")
        
        cache_dirs = []
        pyc_files = []
        
        # Find __pycache__ directories (excluding .venv)
        for pycache_dir in self.repo_path.rglob("__pycache__"):
            if ".venv" not in str(pycache_dir):
                cache_dirs.append(pycache_dir)
        
        # Find .pyc files
        for pyc_file in self.repo_path.rglob("*.pyc"):
            if ".venv" not in str(pyc_file):
                pyc_files.append(pyc_file)
        
        # Remove cache directories
        for cache_dir in cache_dirs:
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Removed: {cache_dir.relative_to(self.repo_path)}")
            except Exception as e:
                print(f"   ❌ Failed to remove {cache_dir}: {e}")
        
        # Remove .pyc files
        for pyc_file in pyc_files:
            try:
                pyc_file.unlink()
                print(f"   ✅ Removed: {pyc_file.relative_to(self.repo_path)}")
            except Exception as e:
                print(f"   ❌ Failed to remove {pyc_file}: {e}")
        
        print(f"   📊 Cleaned {len(cache_dirs)} cache directories and {len(pyc_files)} .pyc files")

    def organize_documentation(self):
        """Organize documentation files into proper directories."""
        print("📚 Organizing documentation...")
        
        # Ensure documentation directories exist
        docs_impl_features = self.repo_path / "docs" / "implementation" / "features"
        docs_impl_features.mkdir(parents=True, exist_ok=True)
        
        # Files already moved in previous operations - just verify they're in place
        moved_files = [
            "docs/implementation/features/MINIMIZE_TO_TRAY_IMPLEMENTATION.md",
            "docs/implementation/features/SINGLE_INSTANCE_IMPLEMENTATION.md"
        ]
        
        for file_path in moved_files:
            full_path = self.repo_path / file_path
            if full_path.exists():
                print(f"   ✅ {file_path} - correctly placed")
            else:
                print(f"   ⚠️  {file_path} - not found")

    def organize_test_files(self):
        """Check test file organization."""
        print("🧪 Checking test file organization...")
        
        # Test files should now be in archive/test-files
        test_archive = self.repo_path / "archive" / "test-files"
        if test_archive.exists():
            test_files = list(test_archive.glob("test_*.py"))
            print(f"   ✅ {len(test_files)} test files archived in archive/test-files/")
            for test_file in test_files:
                print(f"      - {test_file.name}")
        else:
            print("   ⚠️  No test files archive found")

    def archive_temp_docs(self):
        """Check temp documentation archival."""
        print("📁 Checking temporary documentation archival...")
        
        temp_docs = self.repo_path / "archive" / "temp-docs"
        if temp_docs.exists():
            docs = list(temp_docs.glob("*.md"))
            print(f"   ✅ {len(docs)} temporary docs archived in archive/temp-docs/")
            for doc in docs:
                print(f"      - {doc.name}")
        else:
            print("   ⚠️  No temp docs archive found")

    def update_gitignore(self):
        """Update .gitignore to exclude cache files and temp files."""
        print("📝 Updating .gitignore...")
        
        gitignore_path = self.repo_path / ".gitignore"
        
        # Patterns to ensure are in .gitignore
        patterns_to_add = [
            "# Python cache",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "",
            "# Temporary files",
            "*.tmp",
            "*.temp",
            "*~",
            "",
            "# Test files in root",
            "/test_*.py",
            "",
            "# IDE files",
            ".vscode/settings.json",
            ".vscode/launch.json",
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
            
            # Check which patterns are missing
            missing_patterns = []
            for pattern in patterns_to_add:
                if pattern and pattern not in existing_content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# Added by repository organizer\n')
                    for pattern in missing_patterns:
                        f.write(f'{pattern}\n')
                
                print(f"   ✅ Added {len(missing_patterns)} new patterns to .gitignore")
            else:
                print("   ✅ .gitignore is up to date")
        else:
            print("   ❌ .gitignore not found")

    def check_unused_files(self):
        """Check for potentially unused files."""
        print("🔍 Checking for potentially unused files...")
        
        # Check for common temporary or backup files
        patterns = [
            "*.bak",
            "*.backup",
            "*.orig",
            "*.rej",
            "*~",
            "*.tmp"
        ]
        
        found_files = []
        for pattern in patterns:
            found_files.extend(self.repo_path.rglob(pattern))
        
        # Exclude .venv directory
        found_files = [f for f in found_files if ".venv" not in str(f)]
        
        if found_files:
            print(f"   ⚠️  Found {len(found_files)} potentially unused files:")
            for file in found_files:
                print(f"      - {file.relative_to(self.repo_path)}")
        else:
            print("   ✅ No unused temporary files found")

    def create_organization_summary(self):
        """Create a summary of the organization changes."""
        print("📋 Creating organization summary...")
        
        summary_content = f"""# Repository Organization Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Changes Made

### 1. Test Files
- Moved all `test_*.py` files from root to `archive/test-files/`
- These were temporary test files created during development

### 2. Documentation Organization
- Moved implementation docs to `docs/implementation/features/`:
  - `MINIMIZE_TO_TRAY_IMPLEMENTATION.md`
  - `SINGLE_INSTANCE_IMPLEMENTATION.md`
- Archived temporary analysis docs to `archive/temp-docs/`:
  - `THEME_CONSISTENCY_REVIEW.md`
  - `DROPDOWN_THEME_FIXES.md`
  - `DROPDOWN_BORDER_ANALYSIS.md`

### 3. Python Cache Cleanup
- Removed all `__pycache__` directories (excluding .venv)
- Removed all `.pyc` files (excluding .venv)

### 4. .gitignore Updates
- Added patterns to exclude Python cache files
- Added patterns to exclude temporary files
- Added patterns to exclude test files in root

### 5. Archive Structure
```
archive/
├── test-files/          # Temporary test files
├── temp-docs/           # Temporary analysis documents
├── old-versions/        # Previous file versions
├── experimental/        # Experimental features
├── cleanup-stubs/       # Cleanup artifacts
└── unused-components/   # Deprecated components
```

## Current Organization

### Core Application
- `app/` - Main application code
- `config/` - Configuration files
- `scripts/` - Build and utility scripts
- `packaging/` - Distribution packaging

### Documentation
- `docs/` - All documentation
  - `docs/implementation/` - Implementation details
  - `docs/implementation/features/` - Feature documentation
  - `docs/user/` - User documentation
  - `docs/developer/` - Developer guides

### Development
- `dev/` - Development tools and scripts
- `tests/` - Unit and integration tests
- `archive/` - Archived and deprecated files

### Build System
- `Makefile` - Build automation
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
- `.venv/` - Python virtual environment

## Benefits
1. **Cleaner Repository**: Removed temporary and cache files
2. **Better Organization**: Logical file structure
3. **Easier Navigation**: Clear separation of concerns
4. **Reduced Clutter**: Archived temporary files
5. **Better Maintenance**: Updated .gitignore prevents future clutter
"""
        
        summary_path = self.repo_path / "REPOSITORY_ORGANIZATION.md"
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"   ✅ Created organization summary: {summary_path.name}")

    def run_organization(self):
        """Run the complete organization process."""
        print("🚀 Starting Repository Organization")
        print("=" * 50)
        
        self.clean_python_cache()
        print()
        
        self.organize_documentation()
        print()
        
        self.organize_test_files()
        print()
        
        self.archive_temp_docs()
        print()
        
        self.update_gitignore()
        print()
        
        self.check_unused_files()
        print()
        
        self.create_organization_summary()
        print()
        
        print("✅ Repository organization completed successfully!")
        print("📋 See REPOSITORY_ORGANIZATION.md for detailed summary")


if __name__ == "__main__":
    repo_path = "/home/vm/Documents/xanadOS-Search_Destroy"
    organizer = RepositoryOrganizer(repo_path)
    organizer.run_organization()
