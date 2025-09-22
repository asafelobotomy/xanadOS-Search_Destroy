#!/bin/bash
# Archive deprecated modules and activate shims for xanadOS Search & Destroy
#
# This script:
# 1. Archives modules that have been consolidated into unified modules
# 2. Replaces archived modules with their corresponding shims
# 3. Maintains backward compatibility through shim redirection

set -e

# Create timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/arch/Documents/xanadOS-Search_Destroy/archive/consolidation-backup/final-consolidation-$TIMESTAMP"
CORE_DIR="/home/arch/Documents/xanadOS-Search_Destroy/app/core"

echo "🚀 Starting final module consolidation cleanup"
echo "📁 Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to archive a module and activate its shim
archive_and_replace() {
    local module_name="$1"
    local module_file="$CORE_DIR/$module_name.py"
    local shim_file="$CORE_DIR/${module_name}_shim.py"

    if [[ -f "$module_file" && -f "$shim_file" ]]; then
        echo "📦 Archiving $module_name.py and activating shim"

        # Backup original module
        cp "$module_file" "$BACKUP_DIR/"

        # Replace original with shim content
        cp "$shim_file" "$module_file"

        # Remove the shim file since it's now the main file
        rm "$shim_file"

        echo "✅ Completed: $module_name"
    elif [[ -f "$module_file" ]]; then
        echo "⚠️  Module $module_name.py exists but no shim found"
    elif [[ -f "$shim_file" ]]; then
        echo "⚠️  Shim ${module_name}_shim.py exists but no original module"
    else
        echo "❌ Neither $module_name.py nor ${module_name}_shim.py found"
    fi
}

echo ""
echo "📋 PHASE 1: Memory Management Modules"
echo "======================================"
archive_and_replace "memory_manager"
archive_and_replace "memory_optimizer"
archive_and_replace "memory_cache"

echo ""
echo "📋 PHASE 2: RKHunter Integration Modules"
echo "======================================="
archive_and_replace "rkhunter_wrapper"
archive_and_replace "rkhunter_optimizer"
archive_and_replace "rkhunter_monitor_enhanced"
archive_and_replace "rkhunter_monitor_non_invasive"
archive_and_replace "rkhunter_analyzer"

echo ""
echo "📋 PHASE 3: Threading/Async Modules"
echo "==================================="
# Note: These might not have shims yet - check if consolidation is complete
modules_to_check=(
    "async_scanner_engine"
    "async_threat_detector"
    "advanced_async_scanner"
    "async_file_watcher"
    "async_scanner"
    "async_integration"
    "async_file_metadata_cache"
    "async_resource_coordinator"
)

for module in "${modules_to_check[@]}"; do
    if [[ -f "$CORE_DIR/$module.py" ]]; then
        echo "🔍 Found $module.py - checking if still needed"
        # For now, just list them - we need to verify these are fully consolidated
    fi
done

echo ""
echo "📋 PHASE 4: Verification"
echo "======================="
echo "📁 Archived modules are in: $BACKUP_DIR"
echo "📁 Active shims are now the primary modules"

echo ""
echo "✅ Final consolidation cleanup complete!"
echo "🧪 Please test the application to ensure all functionality works"
