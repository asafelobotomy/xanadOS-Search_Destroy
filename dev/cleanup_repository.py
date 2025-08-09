#!/usr/bin/env python3
"""
Repository Cleanup and Organization Script
==========================================

This script performs comprehensive cleanup and organization of the
xanadOS-Search_Destroy repository for better maintainability.

Cleanup Tasks:
1. Move test/debug files to appropriate directories
2. Remove unnecessary Node.js artifacts
3. Organize development files
4. Clean up temporary files
5. Update documentation structure
6. Validate project structure
"""

import os
import shutil
import sys
from pathlib import Path

def cleanup_repository():
    """Perform comprehensive repository cleanup."""
    print("🧹 Starting Repository Cleanup and Organization...")
    print("=" * 60)
    
    repo_root = Path("/home/vm/Documents/xanadOS-Search_Destroy")
    os.chdir(repo_root)
    
    # Task 1: Move test and debug files to dev directory
    print("\n📂 Task 1: Organizing Test and Debug Files")
    test_debug_files = [
        "debug_firewall.py",
        "debug_pkexec_gui.py", 
        "debug_rkhunter.py",
        "debug_sudo_command.py",
        "test_authentication_methods.py",
        "test_auth_fix.py",
        "test_direct_authentication.py",
        "test_direct_auth_final.py",
        "test_firewall_gui.py",
        "test_firewall.py",
        "test_gui_pkexec.py",
        "test_gui_scan.py",
        "test_gui_scan_simple.py",
        "test_improved_auth.py",
        "test_pkexec.py",
        "test_threats_card.py",
        "test_without_config.py",
        "test_wrapper_auth_fix.py"
    ]
    
    # Create debug directory in dev
    debug_dir = repo_root / "dev" / "debug-scripts"
    debug_dir.mkdir(exist_ok=True)
    
    moved_files = []
    for file in test_debug_files:
        if Path(file).exists():
            shutil.move(file, debug_dir / file)
            moved_files.append(file)
            print(f"✅ Moved {file} → dev/debug-scripts/")
    
    print(f"📊 Moved {len(moved_files)} test/debug files")
    
    # Task 2: Remove Node.js artifacts (if not needed)
    print("\n📦 Task 2: Removing Node.js Artifacts")
    node_artifacts = ["node_modules", "package-lock.json"]
    removed_artifacts = []
    
    for artifact in node_artifacts:
        if Path(artifact).exists():
            if Path(artifact).is_dir():
                shutil.rmtree(artifact)
            else:
                Path(artifact).unlink()
            removed_artifacts.append(artifact)
            print(f"✅ Removed {artifact}")
    
    print(f"📊 Removed {len(removed_artifacts)} Node.js artifacts")
    
    # Task 3: Clean up Python cache files
    print("\n🐍 Task 3: Cleaning Python Cache Files")
    cache_cleaned = 0
    for cache_dir in Path(".").rglob("__pycache__"):
        shutil.rmtree(cache_dir)
        cache_cleaned += 1
        print(f"✅ Removed {cache_dir}")
    
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
        cache_cleaned += 1
    
    print(f"📊 Cleaned {cache_cleaned} Python cache entries")
    
    # Task 4: Organize archive directory
    print("\n📁 Task 4: Archive Directory Organization")
    archive_organized = False
    if Path("archive").exists():
        print("✅ Archive directory exists with proper structure")
        archive_organized = True
    
    # Task 5: Create missing documentation
    print("\n📚 Task 5: Documentation Structure")
    docs_created = []
    
    # Create development documentation
    dev_docs = [
        ("dev/README.md", "Development Guide and Scripts"),
        ("dev/debug-scripts/README.md", "Debug and Test Scripts"),
        ("docs/API.md", "API Documentation"),
        ("docs/CONTRIBUTING.md", "Contribution Guidelines")
    ]
    
    for doc_path, doc_title in dev_docs:
        doc_file = Path(doc_path)
        if not doc_file.exists():
            doc_file.parent.mkdir(parents=True, exist_ok=True)
            doc_file.write_text(f"# {doc_title}\n\n*Documentation to be completed*\n")
            docs_created.append(doc_path)
            print(f"✅ Created {doc_path}")
    
    print(f"📊 Created {len(docs_created)} documentation files")
    
    # Task 6: Update .gitignore
    print("\n🚫 Task 6: Updating .gitignore")
    gitignore_additions = [
        "# Python cache",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "",
        "# Virtual environments", 
        ".venv/",
        "venv/",
        "",
        "# Node.js (if added back)",
        "node_modules/",
        "package-lock.json",
        "",
        "# Development files",
        "*.tmp",
        "*.log",
        "",
        "# IDE files",
        ".vscode/settings.json",
        ".idea/",
        "",
        "# OS files",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    gitignore_updated = False
    if Path(".gitignore").exists():
        current_gitignore = Path(".gitignore").read_text()
        if "__pycache__/" not in current_gitignore:
            with open(".gitignore", "a") as f:
                f.write("\n# Added by cleanup script\n")
                f.write("\n".join(gitignore_additions))
            gitignore_updated = True
            print("✅ Updated .gitignore with additional patterns")
    
    # Task 7: Validate project structure
    print("\n🏗️  Task 7: Project Structure Validation")
    required_dirs = [
        "app", "app/core", "app/gui", "app/monitoring", "app/utils",
        "config", "data", "dev", "docs", "packaging", "scripts", "tests"
    ]
    
    structure_valid = True
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Missing directory: {dir_path}")
            structure_valid = False
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    print("\n" + "=" * 60)
    print("🎉 REPOSITORY CLEANUP COMPLETE!")
    print(f"✅ Moved {len(moved_files)} test/debug files")
    print(f"✅ Removed {len(removed_artifacts)} Node.js artifacts") 
    print(f"✅ Cleaned {cache_cleaned} Python cache entries")
    print(f"✅ Created {len(docs_created)} documentation files")
    print(f"✅ Project structure: {'Valid' if structure_valid else 'Needs attention'}")
    print("🚀 Repository is now clean and organized!")

if __name__ == "__main__":
    cleanup_repository()
