#!/usr/bin/env python3
"""
Version Management Summary and Validation Script
Check all files for version consistency and provide a comprehensive summary.
"""

import os
import re
import sys


def find_version_patterns():
    """Find all version patterns in the codebase."""
    version_patterns = []

    # Patterns to search for
    patterns = [
        r'["\']?[Vv]ersion["\']?\s*[:=]?\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)["\']?',
        r'["\']([0-9]+\.[0-9]+\.[0-9]+)["\']',
        r"v([0-9]+\.[0-9]+\.[0-9]+)",
        r"Version\s+([0-9]+\.[0-9]+\.[0-9]+)",
    ]

    # Directories to search
    search_dirs = [
        "app/",
        "packaging/",
        "docs/",
        "scripts/",
    ]

    # Files to search in root
    root_files = [
        "VERSION",
        "CHANGELOG.md",
        "README.md",
        "package.json",
    ]

    for directory in search_dirs:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(
                        (".py", ".md", ".json", ".xml", ".txt", ".yaml", ".yml")
                    ):
                        file_path = os.path.join(root, file)
                        try:
                            with open(
                                file_path, encoding="utf-8", errors="ignore"
                            ) as f:
                                content = f.read()
                                for i, line in enumerate(content.split("\n"), 1):
                                    for pattern in patterns:
                                        matches = re.finditer(
                                            pattern, line, re.IGNORECASE
                                        )
                                        for match in matches:
                                            version_patterns.append(
                                                {
                                                    "file": file_path,
                                                    "line": i,
                                                    "version": (
                                                        match.group(1)
                                                        if match.groups()
                                                        else match.group(0)
                                                    ),
                                                    "context": line.strip(),
                                                    "pattern": pattern,
                                                }
                                            )
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")

    # Check root files
    for file in root_files:
        if os.path.exists(file):
            try:
                with open(file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for i, line in enumerate(content.split("\n"), 1):
                        for pattern in patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                version_patterns.append(
                                    {
                                        "file": file,
                                        "line": i,
                                        "version": (
                                            match.group(1)
                                            if match.groups()
                                            else match.group(0)
                                        ),
                                        "context": line.strip(),
                                        "pattern": pattern,
                                    }
                                )
            except Exception as e:
                print(f"Error reading {file}: {e}")

    return version_patterns


def get_current_version():
    """Get the current version from VERSION file."""
    try:
        with open("VERSION") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Unknown"


def main():
    """Main function to analyze version consistency."""
    print("🔍 Version Management Analysis")
    print("=" * 50)

    current_version = get_current_version()
    print(f"📋 Current VERSION file: {current_version}")

    # Test centralized version system
    try:
        sys.path.insert(0, ".")
        from app import __version__

        print(f"📋 Centralized version system: {__version__}")

        if current_version == __version__:
            print("✅ Version file and centralized system match")
        else:
            print("❌ Version file and centralized system MISMATCH")
    except Exception as e:
        print(f"❌ Error importing centralized version: {e}")

    print("\n🔍 Scanning for version patterns...")
    patterns = find_version_patterns()

    # Group by version
    version_groups = {}
    for pattern in patterns:
        version = pattern["version"]
        if version not in version_groups:
            version_groups[version] = []
        version_groups[version].append(pattern)

    print(
        f"\n📊 Found {len(patterns)} version references in {len(version_groups)} different versions:"
    )

    for version, occurrences in sorted(version_groups.items()):
        status = "✅" if version == current_version else "⚠️"
        print(f"\n{status} Version {version} ({len(occurrences)} occurrences):")

        for occ in occurrences:
            print(f"    📄 {occ['file']}:{occ['line']}")
            print(f"       {occ['context'][:80]}...")

    # Summary
    print("\n📋 Summary:")
    print(f"   Current version: {current_version}")
    print(f"   Total version references: {len(patterns)}")
    print(f"   Different versions found: {len(version_groups)}")

    outdated_count = sum(
        len(occs) for ver, occs in version_groups.items() if ver != current_version
    )
    if outdated_count > 0:
        print(f"   ⚠️  Outdated references: {outdated_count}")
        print("\n🔧 Files that may need updating:")
        for version, occurrences in version_groups.items():
            if version != current_version:
                files = set(occ["file"] for occ in occurrences)
                for file in files:
                    print(f"      📄 {file} (contains version {version})")
    else:
        print("   ✅ All versions are up to date!")


if __name__ == "__main__":
    main()
