#!/usr/bin/env python3
"""
Version Manager - Single Source of Truth
Reads version from VERSION file and provides utilities for dynamic version injection
"""

import json
import re
import sys
from pathlib import Path

# Get the repository root directory
REPO_ROOT = Path(__file__).parent.parent.parent
VERSION_FILE = REPO_ROOT / "VERSION"


def get_version():
    """Read version from VERSION file"""
    try:
        with open(VERSION_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"ERROR: VERSION file not found at {VERSION_FILE}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read VERSION file: {e}", file=sys.stderr)
        sys.exit(1)

def update_package_json():
    """Update package.json to match VERSION file"""
    package_json_path = REPO_ROOT / "package.json"
    version = get_version()
    
    try:
        with open(package_json_path, 'r') as f:
            data = json.load(f)
        
        data['version'] = version
        
        with open(package_json_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')  # Add trailing newline
        
        print(f"✅ Updated package.json version to {version}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to update package.json: {e}", file=sys.stderr)
        return False

def update_pyproject_toml():
    """Update pyproject.toml to match VERSION file"""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    version = get_version()
    
    try:
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Replace version line
        import re
        pattern = r'^version\s*=\s*"[^"]*"'
        replacement = f'version = "{version}"'
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        with open(pyproject_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated pyproject.toml version to {version}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to update pyproject.toml: {e}", file=sys.stderr)
        return False

def update_config_files():
    """Update configuration TOML files to match VERSION file"""
    config_dir = REPO_ROOT / "config"
    version = get_version()
    updated_files = []
    
    if not config_dir.exists():
        return updated_files
    
    for toml_file in config_dir.glob("*.toml"):
        try:
            with open(toml_file, 'r') as f:
                content = f.read()
            
            # Check if file contains version
            if 'version = ' in content:
                import re
                pattern = r'^version\s*=\s*"[^"]*"'
                replacement = f'version = "{version}"'
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                
                if new_content != content:
                    with open(toml_file, 'w') as f:
                        f.write(new_content)
                    updated_files.append(str(toml_file.relative_to(REPO_ROOT)))
                    print(f"✅ Updated {toml_file.name} version to {version}")
        except Exception as e:
            print(f"ERROR: Failed to update {toml_file}: {e}", file=sys.stderr)
    
    return updated_files

def update_readme():
    """Update README.md version dynamically"""
    readme_path = REPO_ROOT / "README.md"
    version = get_version()
    
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Replace version in the status line
        import re
        pattern = r'(Current Version: )[0-9]+\.[0-9]+\.[0-9]+(_)'
        replacement = f'\\g<1>{version}\\g<2>'
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(readme_path, 'w') as f:
                f.write(new_content)
            print(f"✅ Updated README.md version to {version}")
            return True
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to update README.md: {e}", file=sys.stderr)
        return False

def generate_version_header():
    """Generate version information for inclusion in other files"""
    version = get_version()
    return {
        'version': version,
        'version_short': version,
        'version_major': version.split('.')[0],
        'version_minor': '.'.join(version.split('.')[:2]),
        'version_tuple': tuple(map(int, version.split('.')))
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Version Manager - Single Source of Truth")
    parser.add_argument("--get", action="store_true", help="Get current version")
    parser.add_argument("--sync", action="store_true", help="Sync all files with VERSION file")
    parser.add_argument("--update-package", action="store_true", help="Update package.json only")
    parser.add_argument("--update-pyproject", action="store_true", help="Update pyproject.toml only")
    parser.add_argument("--update-configs", action="store_true", help="Update config files only")
    parser.add_argument("--update-readme", action="store_true", help="Update README.md only")
    parser.add_argument("--version-info", action="store_true", help="Show version information")
    
    args = parser.parse_args()
    
    if args.get:
        print(get_version())
    elif args.sync:
        print("🔄 Synchronizing all files with VERSION file...")
        version = get_version()
        print(f"📋 Current version: {version}")
        
        success = True
        success &= update_package_json()
        success &= update_pyproject_toml()
        success &= update_readme()
        
        updated_configs = update_config_files()
        if updated_configs:
            print(f"✅ Updated config files: {', '.join(updated_configs)}")
        
        if success:
            print(f"🎉 All files synchronized to version {version}")
        else:
            print("❌ Some files failed to update")
            sys.exit(1)
    elif args.update_package:
        update_package_json()
    elif args.update_pyproject:
        update_pyproject_toml()
    elif args.update_configs:
        update_config_files()
    elif args.update_readme:
        update_readme()
    elif args.version_info:
        info = generate_version_header()
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        parser.print_help()
