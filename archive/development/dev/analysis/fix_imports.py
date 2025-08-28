#!/usr/bin/env python3
"""
Script to fix relative imports in FileScanner to handle different module loading scenarios.
"""
import re


def fix_file_scanner_imports():
    """Fix relative imports in file_scanner.py"""
    file_path = "app/core/file_scanner.py"

    with open(file_path, "r") as f:
        content = f.read()

    # Pattern to find remaining ..utils imports
    pattern = r"(\s+)from \.\.utils\.([a-zA-Z_]+) import (.+)"

    def replace_import(match):
        indent = match.group(1)
        module = match.group(2)
        imports = match.group(3)

        return """{indent}try:
{indent}    from ..utils.{module} import {imports}
{indent}except ImportError:
{indent}    try:
{indent}        from utils.{module} import {imports}
{indent}    except ImportError:
{indent}        from app.utils.{module} import {imports}"""

    # Replace all ..utils imports with try/except fallbacks
    new_content = re.sub(pattern, replace_import, content)

    # Write back the file
    with open(file_path, "w") as f:
        f.write(new_content)

    print("✅ Fixed FileScanner imports")


if __name__ == "__main__":
    fix_file_scanner_imports()
