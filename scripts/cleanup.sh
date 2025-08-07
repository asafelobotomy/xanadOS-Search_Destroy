#!/bin/bash
# Repository cleanup script for xanadOS Search & Destroy

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Starting repository cleanup...${NC}"

# Function to safely remove files/directories
safe_remove() {
    if [ -e "$1" ]; then
        echo -e "${YELLOW}  Removing: $1${NC}"
        rm -rf "$1"
    fi
}

# Function to count and report removed items
count_and_remove() {
    local pattern="$1"
    local description="$2"
    local count=$(find . -name "$pattern" -not -path "./.venv/*" | wc -l)
    
    if [ "$count" -gt 0 ]; then
        echo -e "${YELLOW}  Removing $count $description files...${NC}"
        find . -name "$pattern" -not -path "./.venv/*" -delete 2>/dev/null || true
    else
        echo -e "${GREEN}  ✅ No $description files found${NC}"
    fi
}

# 1. Remove Python cache files
echo -e "${BLUE}📁 Cleaning Python cache files...${NC}"
count_and_remove "*.pyc" "Python bytecode"
count_and_remove "*.pyo" "Python optimized bytecode"

# Remove __pycache__ directories
pycache_count=$(find . -name "__pycache__" -not -path "./.venv/*" -type d | wc -l)
if [ "$pycache_count" -gt 0 ]; then
    echo -e "${YELLOW}  Removing $pycache_count __pycache__ directories...${NC}"
    find . -name "__pycache__" -not -path "./.venv/*" -type d -exec rm -rf {} + 2>/dev/null || true
else
    echo -e "${GREEN}  ✅ No __pycache__ directories found${NC}"
fi

# 2. Remove temporary files
echo -e "${BLUE}🗑️  Cleaning temporary files...${NC}"
count_and_remove "*.tmp" "temporary"
count_and_remove "*.temp" "temp"
count_and_remove "*.bak" "backup"
count_and_remove "*.backup" "backup"
count_and_remove "*.orig" "original"
count_and_remove "*.rej" "rejected patch"
count_and_remove "*~" "backup"

# 3. Remove editor temporary files
echo -e "${BLUE}✏️  Cleaning editor temporary files...${NC}"
count_and_remove ".#*" "Emacs lock"
count_and_remove "#*#" "Emacs auto-save"
count_and_remove "*.swp" "Vim swap"
count_and_remove "*.swo" "Vim swap"

# 4. Remove log files (but keep log directories)
echo -e "${BLUE}📋 Cleaning log files...${NC}"
count_and_remove "*.log" "log"

# 5. Remove OS-specific files
echo -e "${BLUE}💻 Cleaning OS-specific files...${NC}"
count_and_remove ".DS_Store" "macOS metadata"
count_and_remove "Thumbs.db" "Windows thumbnail"
count_and_remove "desktop.ini" "Windows desktop"

# 6. Clean up empty directories (except important ones)
echo -e "${BLUE}📂 Removing empty directories...${NC}"
find . -type d -empty -not -path "./.git/*" -not -path "./.venv/*" -not -path "./data/*" -delete 2>/dev/null || true

# 7. Check for large files (>10MB)
echo -e "${BLUE}📏 Checking for large files...${NC}"
large_files=$(find . -type f -size +10M -not -path "./.venv/*" -not -path "./.git/*" 2>/dev/null | head -5)
if [ -n "$large_files" ]; then
    echo -e "${YELLOW}  ⚠️  Large files found (>10MB):${NC}"
    echo "$large_files" | while read file; do
        size=$(du -h "$file" | cut -f1)
        echo -e "${YELLOW}    $file ($size)${NC}"
    done
    echo -e "${YELLOW}    Consider using Git LFS for large files${NC}"
else
    echo -e "${GREEN}  ✅ No large files found${NC}"
fi

# 8. Update Git status
echo -e "${BLUE}📊 Git repository status:${NC}"
echo -e "${GREEN}  Current branch: $(git branch --show-current)${NC}"
echo -e "${GREEN}  Untracked files: $(git status --porcelain | grep '^??' | wc -l)${NC}"
echo -e "${GREEN}  Modified files: $(git status --porcelain | grep '^ M' | wc -l)${NC}"

# 9. Optimization suggestions
echo -e "${BLUE}💡 Optimization suggestions:${NC}"
echo -e "${GREEN}  • Run 'git gc' to optimize Git repository${NC}"
echo -e "${GREEN}  • Consider 'git prune' to remove unreachable objects${NC}"
echo -e "${GREEN}  • Use 'git clean -fd' for aggressive cleanup (be careful!)${NC}"

echo -e "${GREEN}✅ Repository cleanup completed!${NC}"

# Optional: Git garbage collection
read -p "Run Git garbage collection? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🗂️  Running Git garbage collection...${NC}"
    git gc --aggressive --prune=now
    echo -e "${GREEN}✅ Git garbage collection completed!${NC}"
fi
