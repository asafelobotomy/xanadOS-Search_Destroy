#!/usr/bin/env python3
"""
Comprehensive linting fixes for xanadOS Search & Destroy project.
This script addresses all markdown, Python, and shell script linting issues.
"""

import re
import subprocess
from pathlib import Path


def fix_markdown_files():
    """Fix common markdown linting issues."""
    print("🔧 Fixing markdown files...")
    
    readme_path = Path("README.md")
    if readme_path.exists():
        content = readme_path.read_text()
        
        # Fix line length issues by adding line breaks where appropriate
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if len(line) > 80 and not line.startswith('|') and not line.startswith('#'):
                # Try to break long lines at logical points
                if ' - ' in line and len(line) > 80:
                    # Split at bullet points
                    parts = line.split(' - ')
                    if len(parts) > 1:
                        fixed_lines.append(parts[0])
                        for part in parts[1:]:
                            fixed_lines.append(f"  - {part}")
                        continue
                
                # For URLs and badges, keep as is (they can't be broken)
                if 'http' in line or 'img.shields.io' in line:
                    fixed_lines.append(line)
                    continue
                    
            fixed_lines.append(line)
        
        # Write back the fixed content
        readme_path.write_text('\n'.join(fixed_lines))
        print("  ✅ Fixed README.md")


def run_flake8_fixes():
    """Run automated flake8 fixes where possible."""
    print("🔧 Running automated Python fixes...")
    
    try:
        # Install autopep8 for automatic fixes
        subprocess.run(["pip", "install", "autopep8"], check=True, capture_output=True)
        
        # Run autopep8 to fix most flake8 issues
        subprocess.run([
            "python", "-m", "autopep8", 
            "--in-place", 
            "--aggressive", 
            "--aggressive",
            "--recursive", 
            "app/"
        ], check=True)
        
        print("  ✅ Applied autopep8 fixes")
        
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️ autopep8 failed: {e}")


def fix_shell_scripts():
    """Fix common shell script issues."""
    print("🔧 Fixing shell scripts...")
    
    shell_scripts = [
        "run.sh",
        "scripts/setup-security.sh",
        "scripts/prepare-build.sh",
        "scripts/verify-build.sh",
        "scripts/activate.sh",
        "packaging/flatpak/search-and-destroy.sh"
    ]
    
    for script_path in shell_scripts:
        script = Path(script_path)
        if not script.exists():
            continue
            
        content = script.read_text()
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix read without -r
            if 'read ' in line and '-r' not in line and 'echo' not in line:
                line = line.replace('read ', 'read -r ')
            
            # Fix variable declarations
            if re.match(r'^.*="\$\(.*\)".*', line):
                # Already properly quoted
                pass
            
            fixed_lines.append(line)
        
        script.write_text('\n'.join(fixed_lines))
        print(f"  ✅ Fixed {script_path}")


def main():
    """Main function to run all fixes."""
    print("🚀 Starting comprehensive linting fixes...\n")
    
    # Ensure we're in the project root
    if not Path("app").exists():
        print("❌ Please run this script from the project root directory")
        return 1
    
    # Fix markdown files
    fix_markdown_files()
    print()
    
    # Fix Python issues with autopep8
    run_flake8_fixes()
    print()
    
    # Fix shell scripts
    fix_shell_scripts()
    print()
    
    print("🎉 Linting fixes completed!")
    print("\nNext steps:")
    print("1. Review the changes manually")
    print("2. Run the linters again to verify fixes")
    print("3. Commit the improvements")
    
    return 0


if __name__ == "__main__":
    exit(main())
