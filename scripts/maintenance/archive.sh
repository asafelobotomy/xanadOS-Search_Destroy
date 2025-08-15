#!/bin/bash

# Archive Helper Script for xanadOS Search & Destroy
# Usage: ./scripts/archive.sh <file_path> <category> [reason]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 <file_path> <category> [reason]"
    echo ""
    echo "Categories:"
    echo "  cleanup-stubs     - Files created as stubs during cleanup"
    echo "  unused-components - Components no longer in active use"
    echo "  old-versions      - Previous versions and backups"
    echo "  experimental      - Experimental/proof-of-concept code"
    echo ""
    echo "Examples:"
    echo "  $0 app/gui/old_dialog.py unused-components \"Replaced by new dialog system\""
    echo "  $0 app/core/legacy_scanner.py old-versions \"Superseded by async scanner\""
    exit 1
}

# Check arguments
if [ $# -lt 2 ]; then
    usage
fi

FILE_PATH="$1"
CATEGORY="$2"
REASON="${3:-Archived on $(date '+%Y-%m-%d')}"

# Validate file exists
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${RED}Error: File '$FILE_PATH' does not exist${NC}"
    exit 1
fi

# Validate category
VALID_CATEGORIES=("cleanup-stubs" "unused-components" "old-versions" "experimental")
category_valid=false
for valid_cat in "${VALID_CATEGORIES[@]}"; do
    if [ "$CATEGORY" = "$valid_cat" ]; then
        category_valid=true
        break
    fi
done

if [ "$category_valid" = false ]; then
    echo -e "${RED}Error: Invalid category '$CATEGORY'${NC}"
    echo "Valid categories: ${VALID_CATEGORIES[*]}"
    exit 1
fi

# Create archive directory if it doesn't exist
ARCHIVE_DIR="archive/$CATEGORY"
mkdir -p "$ARCHIVE_DIR"

# Generate archived filename
FILENAME=$(basename "$FILE_PATH")
FILENAME_NO_EXT="${FILENAME%.*}"
EXTENSION="${FILENAME##*.}"
ARCHIVED_FILENAME="${FILENAME_NO_EXT}_$(date '+%Y%m%d').${EXTENSION}"

# Full archive path
ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVED_FILENAME"

# Check if archive file already exists
if [ -f "$ARCHIVE_PATH" ]; then
    echo -e "${YELLOW}Warning: Archive file '$ARCHIVE_PATH' already exists${NC}"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Archiving cancelled"
        exit 1
    fi
fi

# Create header comment for the archived file
HEADER_COMMENT="# ARCHIVED $(date '+%Y-%m-%d'): $REASON
# Original location: $FILE_PATH
# Archive category: $CATEGORY
# ========================================

"

# Copy file with header
{
    echo "$HEADER_COMMENT"
    cat "$FILE_PATH"
} > "$ARCHIVE_PATH"

echo -e "${GREEN}✓ File archived successfully${NC}"
echo "  Original: $FILE_PATH"
echo "  Archive:  $ARCHIVE_PATH"
echo "  Reason:   $REASON"

# Ask if user wants to remove original
echo ""
read -p "Remove original file? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm "$FILE_PATH"
    echo -e "${GREEN}✓ Original file removed${NC}"
else
    echo -e "${YELLOW}Original file kept${NC}"
fi

# Add to git if in a git repository
if git rev-parse --git-dir > /dev/null 2>&1; then
    git add "$ARCHIVE_PATH"
    if [ ! -f "$FILE_PATH" ]; then
        git add "$FILE_PATH" 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Changes staged for git commit${NC}"
fi

echo ""
echo -e "${GREEN}Archive operation completed successfully!${NC}"
