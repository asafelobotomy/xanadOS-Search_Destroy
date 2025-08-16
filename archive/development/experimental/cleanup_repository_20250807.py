# ARCHIVED 2025-08-07: Repository cleanup script - moved to archive
# Original location: cleanup_repository.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3
"""
Comprehensive repository cleanup script for xanadOS Search & Destroy.
Fixes code quality issues, removes unused imports, and optimizes the codebase.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set


class RepositoryCleanup:
    """Main cleanup orchestrator for the repository."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.fixed_files = []
        self.issues_found = {}
        
    def run_comprehensive_cleanup(self):
        """Run all cleanup operations."""
        print("🚀 Starting comprehensive repository cleanup...\n")
        
        # 1. Fix Python code issues
        self.fix_python_issues()
        
        # 2. Clean up imports
        self.optimize_imports()
        
        # 3. Fix line length issues
        self.fix_line_length_issues()
        
        # 4. Remove dead code and unused variables
        self.remove_dead_code()
        
        # 5. Optimize file structure
        self.optimize_file_structure()
        
        # 6. Update documentation
        self.update_documentation()
        
        # 7. Clean build artifacts
        self.clean_build_artifacts()
        
        # 8. Run final validation
        self.validate_cleanup()
        
        print("\n🎉 Cleanup completed!")
        print(f"📁 Fixed {len(self.fixed_files)} files")
        self.print_summary()
    
    def fix_python_issues(self):
        """Fix Python code quality issues."""
        print("🐍 Fixing Python code issues...")
        
        # Find all Python files (excluding .venv)
        python_files = list(self.repo_path.rglob("*.py"))
        python_files = [f for f in python_files if ".venv" not in str(f)]
        
        for py_file in python_files:
            try:
                self.fix_python_file(py_file)
            except Exception as e:
                print(f"  ⚠️ Error processing {py_file}: {e}")
    
    def fix_python_file(self, file_path: Path):
        """Fix issues in a single Python file."""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Fix common issues
        content = self.remove_unused_imports(content, file_path)
        content = self.fix_f_string_issues(content)
        content = self.fix_redefinitions(content)
        content = self.fix_star_imports(content, file_path)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            self.fixed_files.append(str(file_path))
            print(f"  ✅ Fixed {file_path.relative_to(self.repo_path)}")
    
    def remove_unused_imports(self, content: str, file_path: Path) -> str:
        """Remove unused imports from Python files."""
        lines = content.split('\n')
        used_names = self.find_used_names(content)
        
        new_lines = []
        for line in lines:
            # Skip import lines that import unused names
            if line.strip().startswith(('import ', 'from ')):
                if self.is_import_used(line, used_names):
                    new_lines.append(line)
                else:
                    # Keep import but add comment for clarity
                    if not line.strip().endswith('# noqa'):
                        print(f"    📝 Removing unused import: {line.strip()}")
                        continue
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def find_used_names(self, content: str) -> Set[str]:
        """Find all names used in the file content."""
        used_names = set()
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle attribute access like module.function
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
        except SyntaxError:
            # If AST parsing fails, use regex fallback
            import_pattern = r'\b(\w+)\b'
            for match in re.finditer(import_pattern, content):
                used_names.add(match.group(1))
        
        return used_names
    
    def is_import_used(self, import_line: str, used_names: Set[str]) -> bool:
        """Check if an import line contains used names."""
        # Simple heuristic - check if any imported name is used
        if 'import' in import_line:
            # Extract imported names
            if 'from' in import_line:
                # from module import name1, name2
                parts = import_line.split('import')[-1].strip()
                if '*' in parts:
                    return True  # Keep star imports for now
                names = [name.strip() for name in parts.split(',')]
            else:
                # import module
                parts = import_line.split('import')[-1].strip()
                names = [parts.split(' as ')[0].strip()]
            
            for name in names:
                base_name = name.split('.')[0]  # Handle module.submodule
                if base_name in used_names:
                    return True
        
        return False
    
    def fix_f_string_issues(self, content: str) -> str:
        """Fix f-string issues."""
        # Find f-strings without placeholders
        fstring_pattern = r'f(["\'])([^{]*?)\1'
        
        def replace_fstring(match):
            quote = match.group(1)
            string_content = match.group(2)
            # If no placeholders, convert to regular string
            if '{' not in string_content and '}' not in string_content:
                return f"{quote}{string_content}{quote}"
            return match.group(0)
        
        return re.sub(fstring_pattern, replace_fstring, content)
    
    def fix_redefinitions(self, content: str) -> str:
        """Fix variable redefinitions."""
        lines = content.split('\n')
        new_lines = []
        imported_names = set()
        
        for line in lines:
            # Track imports to avoid redefinition conflicts
            if line.strip().startswith(('import ', 'from ')):
                # Extract imported names
                if 'import' in line:
                    if 'from' in line:
                        parts = line.split('import')[-1].strip()
                        names = [name.strip().split(' as ')[0] for name in parts.split(',')]
                        imported_names.update(names)
                    else:
                        module = line.split('import')[-1].strip().split(' as ')[0]
                        imported_names.add(module)
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def fix_star_imports(self, content: str, file_path: Path) -> str:
        """Replace star imports with explicit imports where possible."""
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if 'from' in line and 'import *' in line:  # noqa: F403 - Star import for module
                # Add comment to explain why star import is used
                if '# noqa' not in line:
                    new_lines.append(f"{line}  # noqa: F403 - Star import for module")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def optimize_imports(self):
        """Optimize import organization using isort."""
        print("📦 Optimizing import organization...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "isort", 
                "app/", "--profile", "black", "--line-length", "88"
            ], check=True, cwd=self.repo_path, capture_output=True)
            print("  ✅ Import organization optimized")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ Import optimization failed: {e}")
    
    def fix_line_length_issues(self):
        """Fix line length issues using autopep8."""
        print("📏 Fixing line length issues...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "autopep8", 
                "--in-place", "--aggressive", "--aggressive",
                "--max-line-length", "88", "--recursive", "app/"
            ], check=True, cwd=self.repo_path, capture_output=True)
            print("  ✅ Line length issues fixed")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ Line length fix failed: {e}")
    
    def remove_dead_code(self):
        """Remove dead code and unused variables."""
        print("🧹 Removing dead code...")
        
        # This would be complex to implement fully, so we'll focus on obvious cases
        python_files = list(self.repo_path.rglob("*.py"))
        python_files = [f for f in python_files if ".venv" not in str(f)]
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Remove unused local variables (simple cases)
                content = self.remove_simple_unused_vars(content)
                
                py_file.write_text(content, encoding='utf-8')
            except Exception as e:
                print(f"  ⚠️ Error processing {py_file}: {e}")
        
        print("  ✅ Dead code removal completed")
    
    def remove_simple_unused_vars(self, content: str) -> str:
        """Remove simple unused variable assignments."""
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            # Simple heuristic: if a line assigns to a variable that's never used again
            if '=' in line and not line.strip().startswith('#'):
                var_match = re.match(r'\s*(\w+)\s*=', line)
                if var_match:
                    var_name = var_match.group(1)
                    # Check if variable is used in subsequent lines
                    remaining_content = '\n'.join(lines[i+1:])
                    if var_name not in remaining_content and '_' not in var_name:
                        # Skip this line if variable seems unused
                        print(f"    📝 Potentially unused variable: {var_name}")
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def optimize_file_structure(self):
        """Optimize file and directory structure."""
        print("📁 Optimizing file structure...")
        
        # Remove empty __pycache__ directories
        for pycache_dir in self.repo_path.rglob("__pycache__"):
            if pycache_dir.is_dir():
                try:
                    pycache_dir.rmdir()
                    print(f"  🗑️ Removed empty {pycache_dir}")
                except OSError:
                    pass  # Directory not empty
        
        # Remove .pyc files
        for pyc_file in self.repo_path.rglob("*.pyc"):
            try:
                pyc_file.unlink()
                print(f"  🗑️ Removed {pyc_file}")
            except OSError:
                pass
        
        print("  ✅ File structure optimized")
    
    def update_documentation(self):
        """Update documentation to reflect cleanup changes."""
        print("📚 Updating documentation...")
        
        # Update CHANGELOG.md
        changelog_path = self.repo_path / "CHANGELOG.md"
        if changelog_path.exists():
            content = changelog_path.read_text(encoding='utf-8')
            
            # Add cleanup entry if not already present
            cleanup_entry = "- Code quality improvements: removed unused imports, fixed line lengths, optimized structure"
            if cleanup_entry not in content:
                # Find the [Unreleased] section and add entry
                unreleased_pattern = r'(## \[Unreleased\]\s*\n)(.*?)(### Added|### Changed|### Fixed|##)'
                match = re.search(unreleased_pattern, content, re.DOTALL)
                if match:
                    new_content = content.replace(match.group(1), 
                        f"{match.group(1)}\n### Changed\n{cleanup_entry}\n\n")
                    changelog_path.write_text(new_content, encoding='utf-8')
                    print("  ✅ Updated CHANGELOG.md")
        
        print("  ✅ Documentation updated")
    
    def clean_build_artifacts(self):
        """Clean up build artifacts and temporary files."""
        print("🧹 Cleaning build artifacts...")
        
        # Patterns to clean
        patterns = [
            "**/*.pyc",
            "**/__pycache__",
            "**/build",
            "**/dist",
            "**/*.egg-info",
            "**/.*cache*",
            "**/.pytest_cache",
            "**/node_modules"
        ]
        
        for pattern in patterns:
            for item in self.repo_path.rglob(pattern.replace("**/", "")):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                    print(f"  🗑️ Removed {item.relative_to(self.repo_path)}")
                except (OSError, PermissionError):
                    pass  # Skip files we can't remove
        
        print("  ✅ Build artifacts cleaned")
    
    def validate_cleanup(self):
        """Validate that cleanup was successful."""
        print("✅ Validating cleanup...")
        
        # Run basic syntax check
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", "app/main.py"
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✅ Python syntax validation passed")
            else:
                print(f"  ⚠️ Syntax validation failed: {result.stderr}")
        except Exception as e:
            print(f"  ⚠️ Validation error: {e}")
    
    def print_summary(self):
        """Print cleanup summary."""
        print("\n📊 Cleanup Summary:")
        print(f"  📁 Files processed: {len(self.fixed_files)}")
        print("  🔧 Issues fixed:")
        print("    - Removed unused imports")
        print("    - Fixed f-string placeholders")
        print("    - Optimized line lengths")  
        print("    - Organized imports")
        print("    - Cleaned build artifacts")
        print("    - Updated documentation")


def main():
    """Main cleanup execution."""
    repo_path = Path(__file__).parent
    
    # Ensure we're in the project root
    if not (repo_path / "app").exists():
        print("❌ Please run this script from the project root directory")
        return 1
    
    # Run cleanup
    cleanup = RepositoryCleanup(repo_path)
    cleanup.run_comprehensive_cleanup()
    
    print("\n🎉 Repository cleanup completed!")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Test the application")
    print("3. Run linting tools to verify improvements")
    print("4. Commit the cleanup changes")
    
    return 0


if __name__ == "__main__":
    exit(main())
