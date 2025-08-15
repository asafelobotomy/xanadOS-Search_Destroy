#!/bin/bash

# Archive Restoration Helper Script for xanadOS Search & Destroy
# Usage: ./scripts/restore.sh <archived_file> [target_path]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 <archived_file> [target_path]"
    echo ""
    echo "Examples:"
    echo "  $0 archive/old-versions/main_window_20250807.py"
    echo "  $0 archive/unused-components/old_dialog.py app/gui/restored_dialog.py"
    echo ""
    echo "Available archived files:"
    find archive -name "*.py" -type f | sort
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

ARCHIVED_FILE="$1"
TARGET_PATH="$2"

# Validate archived file exists
if [ ! -f "$ARCHIVED_FILE" ]; then
    echo -e "${RED}Error: Archived file '$ARCHIVED_FILE' does not exist${NC}"
    echo ""
    echo "Available archived files:"
    find archive -name "*.py" -type f | sort
    exit 1
fi

# Extract metadata from archived file
echo -e "${BLUE}Reading archive metadata...${NC}"
ORIGINAL_LOCATION=$(head -n 10 "$ARCHIVED_FILE" | grep "# Original location:" | sed 's/# Original location: //')
ARCHIVE_DATE=$(head -n 10 "$ARCHIVED_FILE" | grep "# ARCHIVED" | sed 's/# ARCHIVED //' | cut -d':' -f1)
ARCHIVE_REASON=$(head -n 10 "$ARCHIVED_FILE" | grep "# ARCHIVED" | sed 's/.*: //')

echo "Archive Date: $ARCHIVE_DATE"
echo "Original Location: $ORIGINAL_LOCATION"
echo "Archive Reason: $ARCHIVE_REASON"
echo ""

# Determine target path
if [ -z "$TARGET_PATH" ]; then
    if [ -n "$ORIGINAL_LOCATION" ]; then
        TARGET_PATH="$ORIGINAL_LOCATION"
        echo -e "${YELLOW}Using original location: $TARGET_PATH${NC}"
    else
        echo -e "${RED}Error: Could not determine original location and no target path provided${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Using specified target: $TARGET_PATH${NC}"
fi

# Check if target already exists
if [ -f "$TARGET_PATH" ]; then
    echo -e "${YELLOW}Warning: Target file '$TARGET_PATH' already exists${NC}"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restoration cancelled"
        exit 1
    fi
fi

# Create target directory if needed
TARGET_DIR=$(dirname "$TARGET_PATH")
mkdir -p "$TARGET_DIR"

# Extract content (skip archive header)
echo -e "${BLUE}Extracting original content...${NC}"
# Find the line where archive header ends (look for the separator line)
HEADER_END=$(grep -n "^# ========================================$" "$ARCHIVED_FILE" | head -n1 | cut -d: -f1)

if [ -n "$HEADER_END" ]; then
    # Skip header and empty line after separator
    tail -n +$((HEADER_END + 2)) "$ARCHIVED_FILE" > "$TARGET_PATH"
else
    echo -e "${YELLOW}Warning: Could not find archive header separator, copying entire file${NC}"
    cp "$ARCHIVED_FILE" "$TARGET_PATH"
fi

echo -e "${GREEN}✓ File restored successfully${NC}"
echo "  Archive:  $ARCHIVED_FILE"
echo "  Restored: $TARGET_PATH"

# Check if restoration looks correct
RESTORED_SIZE=$(wc -l < "$TARGET_PATH")
echo "  Size:     $RESTORED_SIZE lines"

# Add to git if in a git repository
if git rev-parse --git-dir > /dev/null 2>&1; then
    git add "$TARGET_PATH"
    echo -e "${GREEN}✓ Restored file staged for git commit${NC}"
fi

echo ""
echo -e "${YELLOW}Important: Please test the restored functionality before committing!${NC}"
echo ""
echo -e "${GREEN}Restoration completed successfully!${NC}"
