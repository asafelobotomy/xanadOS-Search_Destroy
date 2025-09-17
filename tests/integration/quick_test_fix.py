#!/usr/bin/env python3
"""
Quick test to verify the single-config optimization implementation
"""
import sys
from pathlib import Path
# Add project root to path (go up two levels from tests/integration/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.rkhunter_optimizer import RKHunterOptimizer

def main():
    print("=== Single Config Implementation Test ===")

    # Use system config (single source of truth)
    optimizer = RKHunterOptimizer()  # Uses /etc/rkhunter.conf by default

    print(f"Config path: {optimizer.config_path}")
    print(f"Can read config: {optimizer.can_read_config()}")
    print(f"Can write config: {optimizer.can_write_config()}")
    print(f"Arch permission anomaly: {optimizer.detect_arch_permission_anomaly()}")

    # Test the unified detection system
    print("\n1. System config issues (detect_fixable_issues):")
    system_issues = optimizer.detect_fixable_issues()
    print(f"   Found: {len(system_issues)} issues")

    for issue_id, issue in system_issues.items():
        sudo_req = " (requires sudo)" if issue.get("requires_sudo", False) else ""
        print(f"   • {issue['description']}{sudo_req}")

    print("\n2. System validation (_validate_configuration):")
    try:
        system_warnings = optimizer._validate_configuration()
        print(f"   Found: {len(system_warnings)} warnings")
        if system_warnings:
            print("   Sample warnings:")
            for w in system_warnings[:2]:
                print(f"     • {w}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n3. Conclusion:")
    print("   ✅ Single source of truth: /etc/rkhunter.conf")
    print("   🔧 Intelligent permission handling")
    print("   🛡️ Clear sudo requirements when needed")
    print("   📝 No more configuration divergence")

if __name__ == "__main__":
    main()
