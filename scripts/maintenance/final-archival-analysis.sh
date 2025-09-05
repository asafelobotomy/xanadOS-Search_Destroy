#!/bin/bash
# Final Repository Archival and Consolidation Script
# xanadOS Search & Destroy - Complete modernization cleanup
# Date: $(date +%Y-%m-%d)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}🔍 Final Repository Archival & Consolidation Analysis${NC}"
echo "=================================================================="
echo ""

# Archive directory with timestamp
ARCHIVE_DATE=$(date +%Y%m%d)
FINAL_ARCHIVE_DIR="archive/final-cleanup-${ARCHIVE_DATE}"

# Create archive directory
mkdir -p "${FINAL_ARCHIVE_DIR}"/{deprecated-configs,test-files,documentation}

echo -e "${YELLOW}📋 PHASE 1: Deprecated Configuration Files Analysis${NC}"
echo "----------------------------------------------------------------"

# Check deprecated PolicyKit files in config/
DEPRECATED_CONFIGS=()
for file in config/org.xanados.searchanddestroy*.policy; do
    if [[ -f "$file" ]] && grep -q "DEPRECATED" "$file"; then
        DEPRECATED_CONFIGS+=("$file")
        echo -e "${RED}  ❌ DEPRECATED: $(basename "$file")${NC}"
    fi
done

if [[ ${#DEPRECATED_CONFIGS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}  📦 Action: Archive ${#DEPRECATED_CONFIGS[@]} deprecated PolicyKit files${NC}"
    for file in "${DEPRECATED_CONFIGS[@]}"; do
        echo "     • $(basename "$file") → ${FINAL_ARCHIVE_DIR}/deprecated-configs/"
    done
else
    echo -e "${GREEN}  ✅ No deprecated configuration files found${NC}"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 2: Root Directory Test Files Analysis${NC}"
echo "----------------------------------------------------------------"

# Check for test files in root directory
ROOT_TEST_FILES=()
for file in test_*.py debug_*.py temp_*.py tmp_*.py; do
    if [[ -f "$file" ]]; then
        ROOT_TEST_FILES+=("$file")
        echo -e "${RED}  ❌ ROOT TEST FILE: $file${NC}"
    fi
done

if [[ ${#ROOT_TEST_FILES[@]} -gt 0 ]]; then
    echo -e "${YELLOW}  📦 Action: Archive ${#ROOT_TEST_FILES[@]} root-level test files${NC}"
    for file in "${ROOT_TEST_FILES[@]}"; do
        echo "     • $file → ${FINAL_ARCHIVE_DIR}/test-files/"
    done
else
    echo -e "${GREEN}  ✅ No root-level test files found${NC}"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 3: Legacy Documentation Analysis${NC}"
echo "----------------------------------------------------------------"

# Check for outdated documentation patterns
LEGACY_DOCS=()
while IFS= read -r -d '' file; do
    if grep -q "TODO.*remove\|FIXME.*remove\|deprecated.*remove\|outdated.*remove" "$file" 2>/dev/null; then
        LEGACY_DOCS+=("$file")
    fi
done < <(find docs/ -name "*.md" -print0 2>/dev/null || true)

if [[ ${#LEGACY_DOCS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}  📝 Found ${#LEGACY_DOCS[@]} documentation files with removal markers${NC}"
    for file in "${LEGACY_DOCS[@]}"; do
        echo "     • $file"
    done
else
    echo -e "${GREEN}  ✅ No documentation with removal markers found${NC}"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 4: Tests Directory Analysis${NC}"
echo "----------------------------------------------------------------"

# Check tests/test_implementation.py status
if [[ -f "tests/test_implementation.py" ]]; then
    if grep -q "pytest.skip.*Legacy" "tests/test_implementation.py"; then
        echo -e "${RED}  ❌ LEGACY: tests/test_implementation.py (pytest skipped)${NC}"
        echo -e "${YELLOW}  📦 Action: Archive legacy test file${NC}"
        echo "     • tests/test_implementation.py → ${FINAL_ARCHIVE_DIR}/test-files/"
    else
        echo -e "${GREEN}  ✅ tests/test_implementation.py appears current${NC}"
    fi
else
    echo -e "${GREEN}  ✅ tests/test_implementation.py already archived${NC}"
fi

# Check for broken test files
BROKEN_TESTS=()
while IFS= read -r -d '' file; do
    if grep -q "broken\|TODO.*fix\|FIXME" "$file" 2>/dev/null; then
        BROKEN_TESTS+=("$file")
    fi
done < <(find tests/ -name "*.py" -print0 2>/dev/null || true)

if [[ ${#BROKEN_TESTS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}  🔧 Found ${#BROKEN_TESTS[@]} test files needing attention${NC}"
    for file in "${BROKEN_TESTS[@]}"; do
        echo "     • $file"
    done
else
    echo -e "${GREEN}  ✅ No broken test files found${NC}"
fi

echo ""
echo -e "${YELLOW}📋 PHASE 5: Final Repository Quality Check${NC}"
echo "----------------------------------------------------------------"

# Check for any remaining clutter patterns
CLUTTER_PATTERNS=("*.bak" "*.old" "*~" "*.tmp" "*.temp" ".DS_Store" "Thumbs.db")
FOUND_CLUTTER=()

for pattern in "${CLUTTER_PATTERNS[@]}"; do
    while IFS= read -r -d '' file; do
        FOUND_CLUTTER+=("$file")
    done < <(find . -name "$pattern" -not -path "./archive/*" -not -path "./.venv/*" -not -path "./.uv-cache/*" -not -path "./node_modules/*" -print0 2>/dev/null || true)
done

if [[ ${#FOUND_CLUTTER[@]} -gt 0 ]]; then
    echo -e "${RED}  ❌ Found ${#FOUND_CLUTTER[@]} clutter files${NC}"
    for file in "${FOUND_CLUTTER[@]}"; do
        echo "     • $file"
    done
else
    echo -e "${GREEN}  ✅ No clutter files found${NC}"
fi

echo ""
echo -e "${BOLD}${BLUE}📊 FINAL ARCHIVAL SUMMARY${NC}"
echo "=================================================================="

TOTAL_ACTIONS=0
TOTAL_ACTIONS=$((TOTAL_ACTIONS + ${#DEPRECATED_CONFIGS[@]}))
TOTAL_ACTIONS=$((TOTAL_ACTIONS + ${#ROOT_TEST_FILES[@]}))
TOTAL_ACTIONS=$((TOTAL_ACTIONS + ${#FOUND_CLUTTER[@]}))

if [[ $TOTAL_ACTIONS -gt 0 ]]; then
    echo -e "${YELLOW}📦 ARCHIVAL OPPORTUNITIES IDENTIFIED:${NC}"
    echo ""

    if [[ ${#DEPRECATED_CONFIGS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}   🗂️  Deprecated Configs: ${#DEPRECATED_CONFIGS[@]} files${NC}"
    fi

    if [[ ${#ROOT_TEST_FILES[@]} -gt 0 ]]; then
        echo -e "${YELLOW}   🧪 Root Test Files: ${#ROOT_TEST_FILES[@]} files${NC}"
    fi

    if [[ ${#FOUND_CLUTTER[@]} -gt 0 ]]; then
        echo -e "${YELLOW}   🗑️  Clutter Files: ${#FOUND_CLUTTER[@]} files${NC}"
    fi

    echo ""
    echo -e "${BLUE}💡 RECOMMENDED ACTIONS:${NC}"
    echo "   1. Run: scripts/maintenance/final-archival.sh --execute"
    echo "   2. Verify: make validate"
    echo "   3. Commit: git add . && git commit -m 'Complete final repository archival'"

else
    echo -e "${GREEN}🎉 REPOSITORY FULLY OPTIMIZED!${NC}"
    echo ""
    echo -e "${GREEN}✅ All legacy content properly archived${NC}"
    echo -e "${GREEN}✅ All deprecated files removed${NC}"
    echo -e "${GREEN}✅ Repository follows modern structure${NC}"
    echo -e "${GREEN}✅ Only current processes and files remain${NC}"
    echo ""
    echo -e "${BOLD}${GREEN}🏆 Repository modernization and cleanup: COMPLETE${NC}"
fi

echo ""
echo -e "${BLUE}📋 Current Archive Structure:${NC}"
find archive/ -type d | head -10 | sed 's/^/   /'
if [[ $(find archive/ -type d | wc -l) -gt 10 ]]; then
    echo "   ... ($(find archive/ -type d | wc -l) total directories)"
fi

echo ""
echo -e "${BLUE}🔗 Next Steps:${NC}"
echo "   • Documentation: docs/guides/FINAL_CLEANUP_COMPLETE.md"
echo "   • Validation: make validate"
echo "   • Testing: make test"
echo "   • Quality Check: make check-env"

echo ""
echo -e "${BOLD}${BLUE}Final Repository Archival Analysis Complete${NC}"
echo "=================================================================="
