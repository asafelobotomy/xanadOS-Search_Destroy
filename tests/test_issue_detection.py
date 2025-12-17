#!/usr/bin/env python3
import pytest
pytest.skip("Legacy test file - rkhunter_optimizer module deprecated", allow_module_level=True)

import sys
sys.path.insert(0, './app')

from pathlib import Path
# from core.rkhunter_optimizer import RKHunterOptimizer

config_path = str(Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf')
print(f"Testing config: {config_path}")

optimizer = RKHunterOptimizer(config_path=config_path)
issues = optimizer.detect_fixable_issues()
print(f"Issues found: {len(issues)}")

for fix_id, issue in issues.items():
    print(f"  - {fix_id}: {issue['description']}")
    print(f"    Detail: {issue['detail']}")
    print()
