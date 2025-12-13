#!/bin/bash
# AppImage Basic Automated Testing Script
# This script performs automated checks on the AppImage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APPIMAGE="./releases/appimage/xanadOS-Search-Destroy-3.0.0-x86_64.AppImage"
RESULTS_FILE="test-results-$(date +%Y%m%d-%H%M%S).txt"

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test header
print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}  $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo -n "[$TESTS_TOTAL] $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "[$TESTS_TOTAL] $test_name: PASS" >> "$RESULTS_FILE"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "[$TESTS_TOTAL] $test_name: FAIL" >> "$RESULTS_FILE"
        return 1
    fi
}

# Function to run test with output
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected="$3"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo -n "[$TESTS_TOTAL] $test_name... "

    output=$(eval "$test_command" 2>&1)
    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "[$TESTS_TOTAL] $test_name: PASS" >> "$RESULTS_FILE"
        echo "  Output: $output" >> "$RESULTS_FILE"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo -e "${YELLOW}  Expected: $expected${NC}"
        echo -e "${YELLOW}  Got: $output${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "[$TESTS_TOTAL] $test_name: FAIL" >> "$RESULTS_FILE"
        echo "  Expected: $expected" >> "$RESULTS_FILE"
        echo "  Got: $output" >> "$RESULTS_FILE"
        return 1
    fi
}

# Start testing
print_header "🔍 AppImage Automated Testing Suite"

echo "AppImage: $APPIMAGE"
echo "Results will be saved to: $RESULTS_FILE"
echo ""
echo "Starting tests at $(date)"
echo ""

# Initialize results file
echo "AppImage Automated Test Results" > "$RESULTS_FILE"
echo "Generated: $(date)" >> "$RESULTS_FILE"
echo "AppImage: $APPIMAGE" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

# Phase 1: File Checks
print_header "Phase 1: File Checks"

run_test "File exists" "test -f '$APPIMAGE'"
run_test "File is executable" "test -x '$APPIMAGE'"

# Get file size
SIZE=$(stat -c %s "$APPIMAGE" 2>/dev/null || stat -f %z "$APPIMAGE" 2>/dev/null)
SIZE_MB=$((SIZE / 1024 / 1024))
echo "  File size: ${SIZE_MB}MB"
echo "  File size: ${SIZE_MB}MB" >> "$RESULTS_FILE"

run_test "Size is reasonable (300-400 MB)" "test $SIZE -gt 300000000 && test $SIZE -lt 400000000"

# Phase 2: Command-Line Arguments
print_header "Phase 2: Command-Line Arguments"

run_test_with_output "Version flag works" "'$APPIMAGE' --version" "3.0.0"
run_test_with_output "Help flag works" "'$APPIMAGE' --help" "Advanced malware"
run_test_with_output "Help shows options" "'$APPIMAGE' --help" "skip-policy-check"

# Phase 3: Extraction Test
print_header "Phase 3: Extraction Test"

EXTRACT_DIR="/tmp/appimage-test-extract-$$"
rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"

echo "  Extracting to: $EXTRACT_DIR"
cd "$EXTRACT_DIR"
if "$OLDPWD/$APPIMAGE" --appimage-extract > /dev/null 2>&1; then
    cd "$OLDPWD"

    run_test "AppRun exists after extraction" "test -f '$EXTRACT_DIR/squashfs-root/AppRun'"
    run_test "AppRun is executable" "test -x '$EXTRACT_DIR/squashfs-root/AppRun'"
    run_test "Python binary exists" "test -f '$EXTRACT_DIR/squashfs-root/usr/bin/python3'"
    run_test "Python stdlib exists" "test -d '$EXTRACT_DIR/squashfs-root/usr/lib/python3.13'"
    run_test "App files exist" "test -d '$EXTRACT_DIR/squashfs-root/usr/app'"
    run_test "Desktop file exists" "test -f '$EXTRACT_DIR/squashfs-root/'*.desktop"
    run_test "App icon exists" "test -f '$EXTRACT_DIR/squashfs-root/'*.png"

    # Check PolicyKit policies
    POLICY_COUNT=$(find "$EXTRACT_DIR/squashfs-root/usr/share/polkit-1/actions" -name "*.policy" 2>/dev/null | wc -l)
    echo "  PolicyKit policies found: $POLICY_COUNT"
    echo "  PolicyKit policies: $POLICY_COUNT" >> "$RESULTS_FILE"
    run_test "PolicyKit policies bundled (3 expected)" "test $POLICY_COUNT -eq 3"

    # Check VERSION file
    if [ -f "$EXTRACT_DIR/squashfs-root/usr/app/VERSION" ]; then
        VERSION_CONTENT=$(cat "$EXTRACT_DIR/squashfs-root/usr/app/VERSION")
        echo "  VERSION file content: $VERSION_CONTENT"
        echo "  VERSION file: $VERSION_CONTENT" >> "$RESULTS_FILE"
        run_test "VERSION file contains 3.0.0" "grep -q '3.0.0' '$EXTRACT_DIR/squashfs-root/usr/app/VERSION'"
    fi

    # Cleanup
    rm -rf "$EXTRACT_DIR"
else
    cd "$OLDPWD"
    echo -e "${RED}❌ Extraction failed${NC}"
    echo "Extraction: FAIL" >> "$RESULTS_FILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    rm -rf "$EXTRACT_DIR"
fi

# Phase 4: Environment Check
print_header "Phase 4: System Environment"

# Check for FUSE
if command -v fusermount &> /dev/null || [ -f /usr/bin/fusermount ]; then
    echo -e "${GREEN}✅ FUSE is installed${NC}"
    echo "FUSE: Installed" >> "$RESULTS_FILE"
else
    echo -e "${YELLOW}⚠️  FUSE not found (AppImage will use extraction mode)${NC}"
    echo "FUSE: Not installed" >> "$RESULTS_FILE"
fi

# Check PolicyKit
if command -v pkexec &> /dev/null; then
    echo -e "${GREEN}✅ PolicyKit is installed${NC}"
    echo "PolicyKit: Installed" >> "$RESULTS_FILE"
else
    echo -e "${YELLOW}⚠️  PolicyKit not found${NC}"
    echo "PolicyKit: Not installed" >> "$RESULTS_FILE"
fi

# System information
echo ""
echo "System Information:" >> "$RESULTS_FILE"
echo "  OS: $(uname -s)"
echo "  OS: $(uname -s)" >> "$RESULTS_FILE"
echo "  Kernel: $(uname -r)"
echo "  Kernel: $(uname -r)" >> "$RESULTS_FILE"
echo "  Architecture: $(uname -m)"
echo "  Architecture: $(uname -m)" >> "$RESULTS_FILE"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "  Distribution: $NAME $VERSION"
    echo "  Distribution: $NAME $VERSION" >> "$RESULTS_FILE"
fi

# Desktop environment
if [ -n "$XDG_CURRENT_DESKTOP" ]; then
    echo "  Desktop: $XDG_CURRENT_DESKTOP"
    echo "  Desktop: $XDG_CURRENT_DESKTOP" >> "$RESULTS_FILE"
fi

# Display server
if [ -n "$XDG_SESSION_TYPE" ]; then
    echo "  Display Server: $XDG_SESSION_TYPE"
    echo "  Display Server: $XDG_SESSION_TYPE" >> "$RESULTS_FILE"
fi

# Phase 5: Python Environment Check (in extracted AppImage)
print_header "Phase 5: Python Environment Check"

TEMP_EXTRACT="/tmp/appimage-python-check-$$"
rm -rf "$TEMP_EXTRACT"
mkdir -p "$TEMP_EXTRACT"
cd "$TEMP_EXTRACT"

echo "  Extracting AppImage for Python check..."
if "$OLDPWD/$APPIMAGE" --appimage-extract > /dev/null 2>&1; then
    APPDIR="$TEMP_EXTRACT/squashfs-root"

    # Test Python version
    if [ -f "$APPDIR/usr/bin/python3" ]; then
        PYTHON_VERSION=$("$APPDIR/usr/bin/python3" --version 2>&1 || echo "Failed")
        echo "  Python version: $PYTHON_VERSION"
        echo "  Python version: $PYTHON_VERSION" >> "$OLDPWD/$RESULTS_FILE"

        # Test Python can import basic modules
        if "$APPDIR/usr/bin/python3" -c "import sys; import encodings" 2>/dev/null; then
            echo -e "  ${GREEN}✅ Python can import basic modules${NC}"
            echo "  Python imports: OK" >> "$OLDPWD/$RESULTS_FILE"
        else
            echo -e "  ${RED}❌ Python cannot import basic modules${NC}"
            echo "  Python imports: FAIL" >> "$OLDPWD/$RESULTS_FILE"
        fi

        # Check for key dependencies
        echo ""
        echo "  Checking key dependencies:"
        DEPS_TO_CHECK="PyQt6 fastapi sqlalchemy numpy cryptography"
        for dep in $DEPS_TO_CHECK; do
            if "$APPDIR/usr/bin/python3" -c "import $dep" 2>/dev/null; then
                echo -e "    ${GREEN}✅ $dep${NC}"
                echo "    $dep: Found" >> "$OLDPWD/$RESULTS_FILE"
            else
                echo -e "    ${YELLOW}⚠️  $dep (not found or import error)${NC}"
                echo "    $dep: Not found" >> "$OLDPWD/$RESULTS_FILE"
            fi
        done
    fi

    cd "$OLDPWD"
    rm -rf "$TEMP_EXTRACT"
else
    cd "$OLDPWD"
    echo -e "${RED}❌ Could not extract for Python check${NC}"
    rm -rf "$TEMP_EXTRACT"
fi

# Final Summary
print_header "📊 Test Summary"

echo ""
echo "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

PASS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))
echo "Pass Rate: ${PASS_RATE}%"
echo ""

# Add summary to results file
echo "" >> "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$RESULTS_FILE"
echo "Summary" >> "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$RESULTS_FILE"
echo "Total Tests: $TESTS_TOTAL" >> "$RESULTS_FILE"
echo "Passed: $TESTS_PASSED" >> "$RESULTS_FILE"
echo "Failed: $TESTS_FAILED" >> "$RESULTS_FILE"
echo "Pass Rate: ${PASS_RATE}%" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Test completed at: $(date)" >> "$RESULTS_FILE"

if [ $TESTS_FAILED -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}  ✅ All tests passed! AppImage is ready.${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Status: READY FOR DISTRIBUTION" >> "$RESULTS_FILE"
    exit 0
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}  ⚠️  Some tests failed. Review the results.${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Status: NEEDS ATTENTION" >> "$RESULTS_FILE"
    exit 1
fi
