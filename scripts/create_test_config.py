#!/usr/bin/env python3
"""
Create a test RKHunter configuration with fixable issues for demonstration.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, './app')

def create_test_config_with_issues():
    """Create a test configuration file with some fixable issues"""

    # Get the config path
    config_dir = Path.home() / '.config' / 'search-and-destroy'
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / 'rkhunter.conf'

    # Backup existing config if it exists
    if config_path.exists():
        backup_path = config_path.with_suffix('.conf.backup')
        config_path.rename(backup_path)
        print(f"📁 Backed up existing config to: {backup_path}")

    # Create test config with issues that the interactive dialog can fix
    test_config = """# Test RKHunter Configuration with Fixable Issues
# This file is created for demonstration of the interactive configuration fixes

# Basic settings
LOGFILE=/tmp/rkhunter.log
TMPDIR=/tmp
DBDIR=/var/lib/rkhunter/db
SCRIPTDIR=/usr/share/rkhunter/scripts
MAIL-ON-WARNING=""
MAIL_CMD=mail -s "[rkhunter] Warnings found for ${HOST_NAME}"

# Test Issues - These will be detected and offered for fixing:

# 1. Obsolete setting that should be removed
OBSOLETE_SETTING=value_that_should_be_removed

# 2. Deprecated command that should be updated
DEPRECATED_COMMAND=old_command_name

# 3. Regex pattern that could be improved
ALLOWHIDDENDIR="^/\.old$"

# 4. Another obsolete setting
ANOTHER_OLD_SETTING=remove_this_too

# Valid settings that should remain
ALLOW_SSH_ROOT_USER=no
ALLOW_SSH_PROT_V1=no
ENABLE_TESTS=ALL
DISABLE_TESTS=""

# Package manager settings
PKGMGR=DPKG
PKGMGR_NO_VRFY=""

# Hash function settings
HASH_CMD=SHA256
HASH_FLD_IDX=1

# Update settings
WEB_CMD=""
UPDATE_MIRRORS=1
MIRRORS_MODE=0

# Scan settings
SCANROOTKITMODE=1
UNHIDETCPSQ=0
ALLOWHIDDENFILE=""
ALLOWPROCDELFILE=""
ALLOWPROCLISTEN=""
ALLOWPROMISCIF=""
ALLOWDEVFILE=""

# Mail settings
MAIL_ON_WARNING=""
COPY_LOG_ON_ERROR=0

# Logging settings
USE_SYSLOG=""
APPEND_LOG=0
COLOUR_SET2=""
AUTO_X_DETECT=1
WHITELISTED_IS_WHITE=0
ALLOW_SSH_PROT_V1=0
ALLOW_SYSLOG_REMOTE_LOGGING=0

# End of test configuration
"""

    # Write the test config
    with open(config_path, 'w') as f:
        f.write(test_config)

    print(f"✅ Created test configuration with fixable issues at: {config_path}")
    print("\n📋 Issues added to the configuration:")
    print("  • OBSOLETE_SETTING - Will be detected as obsolete and offered for removal")
    print("  • DEPRECATED_COMMAND - Will be detected as deprecated")
    print("  • Regex patterns that can be improved")
    print("  • Additional obsolete settings")
    print("\n🎯 Now when you click 'Optimize Configuration' in the app,")
    print("   you should see the interactive dialog with these fixable issues!")

    return str(config_path)

def main():
    """Create test configuration"""
    print("🧪 Creating Test RKHunter Configuration with Fixable Issues")
    print("=" * 60)

    try:
        config_path = create_test_config_with_issues()

        print("\n🚀 Test configuration created successfully!")
        print("\n📋 Next steps:")
        print("1. Run the application: make run")
        print("2. Go to Settings tab > RKHunter pane > Optimization tab")
        print("3. Click 'Optimize Configuration' button")
        print("4. You should see the interactive dialog with fixable issues")
        print("5. Select which issues to fix and click 'Apply Selected Fixes'")

        print(f"\n📁 Configuration file: {config_path}")
        print("💡 To restore your original config, look for the .backup file")

    except Exception as e:
        print(f"❌ Error creating test configuration: {e}")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
