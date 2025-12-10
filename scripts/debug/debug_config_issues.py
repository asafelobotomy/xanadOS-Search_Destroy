#!/usr/bin/env python3
"""
Debug script to check what detect_fixable_issues finds vs what RKHunter reports
"""

import sys
import os
from pathlib import Path

# Add project root to path (go up two levels from scripts/debug/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def check_config_issues():
    try:
        from app.core.unified_rkhunter_integration import RKHunterOptimizer

        config_path = str(Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf')
        print(f"🔍 Checking config: {config_path}")
        print(f"📂 File exists: {os.path.exists(config_path)}")

        if not os.path.exists(config_path):
            print("❌ Config file not found")
            return

        # Check what's in the file
        with open(config_path, 'r') as f:
            lines = f.readlines()

        print(f"📄 Config file has {len(lines)} lines")

        # Look for problematic patterns
        for i, line in enumerate(lines[:20], 1):  # Check first 20 lines
            if 'WEB_CMD_TIMEOUT' in line:
                print(f"🔧 Found WEB_CMD_TIMEOUT at line {i}: {line.strip()}")
            if 'egrep' in line and not line.strip().startswith('#'):
                print(f"📅 Found egrep at line {i}: {line.strip()}")
            if ('\\+' in line or '\\-' in line) and not line.strip().startswith('#'):
                print(f"🔍 Found backslash escape at line {i}: {line.strip()}")

        # Test our detection method
        optimizer = RKHunterOptimizer(config_path=config_path)
        issues = optimizer.detect_fixable_issues()

        print(f"\n📊 detect_fixable_issues() found: {len(issues)} issues")
        for fix_id, issue in issues.items():
            print(f"  • {fix_id}: {issue['description']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_config_issues()
