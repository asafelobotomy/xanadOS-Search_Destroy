#!/usr/bin/env python3
"""
Compatibility Fix Script for Phase 1-3 Integration

This script addresses all compatibility issues identified during the Phase 1-3 review:
1. Pydantic v2 compatibility (validator -> field_validator)
2. SQLAlchemy session execution fixes
3. Type annotation improvements
4. Import and dependency corrections
"""

import re
import sys
from pathlib import Path

def fix_pydantic_validators(file_path: Path):
    """Fix Pydantic v1 to v2 validator syntax."""
    content = file_path.read_text()

    # Fix remaining validator decorators
    validator_patterns = [
        (r'@validator\(([^)]+)\)\s*\n\s*def (\w+)\(cls, v\):',
         r'@field_validator(\1)\n    @classmethod\n    def \2(cls, v: Any):'),

        # Fix Field regex parameter
        (r'Field\([^)]*regex="([^"]*)"([^)]*)\)',
         r'Field(\2, pattern="\1")'),

        # Fix Field parameter order
        (r'Field\(([^,]*), pattern="([^"]*)"([^)]*)\)',
         r'Field(\1\3, pattern="\2")'),
    ]

    for pattern, replacement in validator_patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content

def fix_type_annotations(content: str) -> str:
    """Add missing type annotations."""
    # Add Any import if not present
    if 'from typing import' in content and 'Any' not in content:
        content = re.sub(
            r'from typing import ([^,\n]+)',
            r'from typing import \1, Any',
            content
        )

    # Fix function signatures for validators
    patterns = [
        (r'def validate_(\w+)\(cls, v\):', r'def validate_\1(cls, v: Any) -> Any:'),
        (r'def (\w+)\(self([^)]*)\):\s*"""[^"]*"""', r'def \1(self\2) -> None:\n        """'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content

def fix_sqlalchemy_session(content: str) -> str:
    """Fix SQLAlchemy session execution issues."""
    patterns = [
        # Fix session.execute for pragma statements
        (r'self\.db_session\.execute\("PRAGMA ([^"]+)"\)',
         r'self.db_session.execute(text("PRAGMA \1"))'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # Add text import if using PRAGMA statements
    if 'PRAGMA' in content and 'from sqlalchemy import' in content:
        content = re.sub(
            r'from sqlalchemy import ([^,\n]+)',
            r'from sqlalchemy import \1, text',
            content
        )

    return content

def fix_redis_typing(content: str) -> str:
    """Fix Redis typing issues."""
    patterns = [
        # Fix Redis None assignment
        (r'self\.redis_client = None',
         r'self.redis_client: Optional[redis.Redis] = None'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content

def apply_comprehensive_fixes(file_path: Path) -> bool:
    """Apply all compatibility fixes to a file."""
    try:
        print(f"🔧 Fixing {file_path}")

        # Read original content
        original_content = file_path.read_text()

        # Apply fixes
        content = fix_pydantic_validators(file_path)
        content = fix_type_annotations(content)
        content = fix_sqlalchemy_session(content)
        content = fix_redis_typing(content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            print(f"  ✅ Fixed {file_path}")
            return True
        else:
            print(f"  ℹ️  No changes needed for {file_path}")
            return False

    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main fix execution."""
    project_root = Path(__file__).parent.parent.parent

    # Files to fix
    files_to_fix = [
        project_root / "app" / "api" / "security_api.py",
        project_root / "app" / "api" / "client_sdk.py",
        project_root / "app" / "core" / "exceptions.py",
    ]

    print("🚀 Starting comprehensive compatibility fixes for Phase 1-3 integration")
    print("-" * 80)

    fixed_count = 0
    for file_path in files_to_fix:
        if file_path.exists():
            if apply_comprehensive_fixes(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    print("-" * 80)
    print(f"🎯 Fixed {fixed_count} files")
    print("✅ Compatibility fixes complete!")

if __name__ == "__main__":
    main()
