#!/bin/bash

# Batch Archive Helper Script for xanadOS Search & Destroy
# Usage: ./scripts/batch_archive.sh <category> <reason> <file1> [file2] [file3] ...

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 <category> <reason> <file1> [file2] [file3] ..."
    echo ""
    echo "Categories:"
    echo "  cleanup-stubs     - Files created as stubs during cleanup"
    echo "  unused-components - Components no longer in active use"
    echo "  old-versions      - Previous versions and backups"
    echo "  experimental      - Experimental/proof-of-concept code"
    echo ""
    echo "Examples:"
    echo "  $0 experimental \"Debug scripts from theme fixes\" debug_*.py"
    echo "  $0 unused-components \"Old UI components\" app/gui/old_*.py"
    exit 1
}

# Check arguments
if [ $# -lt 3 ]; then
    usage
fi

CATEGORY="$1"
REASON="$2"
shift 2
FILES=("$@")

echo -e "${BLUE}🗃️  Batch Archive Operation${NC}"
echo "Category: $CATEGORY"
echo "Reason: $REASON"
echo "Files to archive: ${#FILES[@]}"
echo ""

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

# Count files to process
total_files=0
valid_files=()

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        valid_files+=("$file")
        ((total_files++))
    else
        echo -e "${YELLOW}Warning: File '$file' does not exist, skipping${NC}"
    fi
done

if [ $total_files -eq 0 ]; then
    echo -e "${RED}Error: No valid files to archive${NC}"
    exit 1
fi

echo -e "${GREEN}Found $total_files valid files to archive${NC}"
echo ""

# Ask for confirmation
read -p "Continue with batch archive? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Batch archive cancelled"
    exit 1
fi

echo ""
echo -e "${BLUE}Starting batch archive...${NC}"
echo ""

# Archive each file
success_count=0
failure_count=0

for file in "${valid_files[@]}"; do
    echo -e "${BLUE}📁 Archiving: $file${NC}"
    
    if ./scripts/archive.sh "$file" "$CATEGORY" "$REASON" --yes; then
        ((success_count++))
        echo -e "${GREEN}✓ Successfully archived: $file${NC}"
    else
        ((failure_count++))
        echo -e "${RED}✗ Failed to archive: $file${NC}"
    fi
    echo ""
done

# Summary
echo -e "${BLUE}📊 Batch Archive Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Total files processed: $total_files"
echo -e "${GREEN}Successful archives: $success_count${NC}"
if [ $failure_count -gt 0 ]; then
    echo -e "${RED}Failed archives: $failure_count${NC}"
fi
echo ""

if [ $success_count -eq $total_files ]; then
    echo -e "${GREEN}🎉 All files archived successfully!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some files failed to archive${NC}"
    exit 1
fi
