#!/usr/bin/env python3
"""
Repository Organization Maintenance Script
xanadOS Search & Destroy v2.8.0

Automatically organizes misplaced files and maintains repository structure.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class RepositoryOrganizer:
    """Organizes repository files according to project structure"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.moved_files = []
        self.created_dirs = []
        
        # Define organization rules
        self.organization_rules = {
            'test_*.py': 'dev/testing/',
            '*_test.py': 'dev/testing/',
            '*_demo.py': 'dev/demos/',
            'demo_*.py': 'dev/demos/',
            '*_report.py': 'dev/reports/',
            'report_*.py': 'dev/reports/',
            'fix_*.py': 'dev/security-tools/',
            'validate_*.py': 'dev/security-tools/',
            'verify_*.py': 'dev/security-tools/',
            'simple_*.py': 'dev/security-tools/',
            '*_analysis.py': 'dev/analysis/',
            'analyze_*.py': 'dev/analysis/',
            '*.md': 'docs/',  # Except README.md, CHANGELOG.md, LICENSE
        }
        
        # Files that should stay in root
        self.root_exceptions = {
            'README.md', 'CHANGELOG.md', 'LICENSE', 'VERSION',
            'Makefile', 'requirements.txt', 'requirements-dev.txt',
            'run.sh', 'mypy.ini', 'pytest.ini', '.gitignore',
            '.gitconfig_project'
        }
    
    def create_directory_if_needed(self, dir_path: str) -> None:
        """Create directory if it doesn't exist"""
        full_path = self.repo_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            self.created_dirs.append(dir_path)
            print(f"📁 Created directory: {dir_path}")
    
    def should_move_file(self, file_path: Path) -> bool:
        """Check if file should be moved"""
        if file_path.name in self.root_exceptions:
            return False
        
        # Don't move files already in proper directories
        if any(part in ['app', 'dev', 'docs', 'config', 'tests', 
                       'scripts', 'packaging', 'tools', 'archive'] 
               for part in file_path.parts[1:]):
            return False
            
        return True
    
    def get_target_directory(self, file_path: Path) -> str | None:
        """Determine target directory for a file"""
        filename = file_path.name
        
        # Check pattern rules
        for pattern, target_dir in self.organization_rules.items():
            if self._matches_pattern(filename, pattern):
                # Special handling for .md files
                if pattern == '*.md' and filename in self.root_exceptions:
                    return None
                return target_dir
        
        # Default categorization
        if filename.endswith('.py'):
            # Try to categorize based on content
            content_category = self._categorize_by_content(file_path)
            if content_category:
                return content_category
            return 'dev/misc/'
        
        return None
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def _categorize_by_content(self, file_path: Path) -> str | None:
        """Categorize Python file by content analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1000 chars
                
                # Look for indicators
                if 'test' in content.lower():
                    return 'dev/testing/'
                elif 'demo' in content.lower():
                    return 'dev/demos/'
                elif any(word in content.lower() for word in ['report', 'summary']):
                    return 'dev/reports/'
                elif any(word in content.lower() for word in ['security', 'hardening', 'fix']):
                    return 'dev/security-tools/'
                elif 'analysis' in content.lower():
                    return 'dev/analysis/'
                    
        except Exception:
            pass
        
        return None
    
    def organize_files(self, dry_run: bool = False) -> None:
        """Organize misplaced files"""
        print("🗂️  Repository Organization")
        print("=" * 40)
        
        # Find files to organize
        for file_path in self.repo_root.iterdir():
            if not file_path.is_file():
                continue
                
            if not self.should_move_file(file_path):
                continue
                
            target_dir = self.get_target_directory(file_path)
            if not target_dir:
                continue
                
            # Create target directory
            if not dry_run:
                self.create_directory_if_needed(target_dir)
            
            # Move file
            target_path = self.repo_root / target_dir / file_path.name
            
            if dry_run:
                print(f"📋 Would move: {file_path.name} → {target_dir}")
            else:
                try:
                    shutil.move(str(file_path), str(target_path))
                    self.moved_files.append((file_path.name, target_dir))
                    print(f"📦 Moved: {file_path.name} → {target_dir}")
                except Exception as e:
                    print(f"❌ Failed to move {file_path.name}: {e}")
    
    def clean_empty_directories(self, dry_run: bool = False) -> None:
        """Remove empty directories"""
        empty_dirs = []
        
        for dir_path in self.repo_root.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                # Don't remove important empty directories
                if dir_path.name in ['.git', '.github', '__pycache__']:
                    continue
                empty_dirs.append(dir_path)
        
        for dir_path in empty_dirs:
            rel_path = dir_path.relative_to(self.repo_root)
            if dry_run:
                print(f"📋 Would remove empty directory: {rel_path}")
            else:
                try:
                    dir_path.rmdir()
                    print(f"🗑️  Removed empty directory: {rel_path}")
                except Exception as e:
                    print(f"❌ Failed to remove {rel_path}: {e}")
    
    def generate_report(self) -> None:
        """Generate organization report"""
        print("\n📊 Organization Report")
        print("=" * 30)
        
        if self.created_dirs:
            print(f"📁 Created {len(self.created_dirs)} directories:")
            for dir_name in self.created_dirs:
                print(f"   - {dir_name}")
        
        if self.moved_files:
            print(f"📦 Moved {len(self.moved_files)} files:")
            for filename, target_dir in self.moved_files:
                print(f"   - {filename} → {target_dir}")
        
        if not self.created_dirs and not self.moved_files:
            print("✅ Repository was already properly organized")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize repository structure")
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually moving files')
    parser.add_argument('--clean-empty', action='store_true',
                       help='Remove empty directories')
    
    args = parser.parse_args()
    
    # Get repository root
    repo_root = Path(__file__).parent.parent
    
    # Initialize organizer
    organizer = RepositoryOrganizer(repo_root)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be moved")
        print("=" * 40)
    
    # Organize files
    organizer.organize_files(dry_run=args.dry_run)
    
    # Clean empty directories if requested
    if args.clean_empty:
        organizer.clean_empty_directories(dry_run=args.dry_run)
    
    # Generate report
    if not args.dry_run:
        organizer.generate_report()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
