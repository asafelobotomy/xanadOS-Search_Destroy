#!/bin/bash
# Repository Structure Verification Script

# Get the script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 xanadOS Search & Destroy - Repository Structure Verification"
echo "=============================================================="
echo "Project root: $PROJECT_ROOT"
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

check_directory() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} Directory exists: $1"
    else
        echo -e "${RED}❌${NC} Missing directory: $1"
        ((ISSUES_FOUND++))
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} File exists: $1"
    else
        echo -e "${RED}❌${NC} Missing file: $1"
        ((ISSUES_FOUND++))
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo -e "${GREEN}✅${NC} Executable: $1"
    else
        echo -e "${YELLOW}⚠️${NC}  Not executable: $1"
        ((ISSUES_FOUND++))
    fi
}

echo -e "\n📁 Core Directories:"
check_directory "app"
check_directory "app/core"
check_directory "app/gui"
check_directory "app/utils"
check_directory "app/monitoring"
check_directory "docs"
check_directory "docs/user"
check_directory "docs/developer"
check_directory "docs/implementation"
check_directory "docs/project"
check_directory "docs/releases"
check_directory "scripts"
check_directory "scripts/build"
check_directory "scripts/setup"
check_directory "scripts/maintenance"
check_directory "scripts/security"
check_directory "scripts/flathub"
check_directory "scripts/utils"
check_directory "tools"
check_directory "packaging"
check_directory "packaging/flatpak"
check_directory "config"
check_directory "tests"

echo -e "\n📄 Essential Files:"
check_file "VERSION"
check_file "LICENSE"
check_file "README.md"
check_file "Makefile"
check_file "requirements.txt"
check_file "run.sh"
check_file "app/main.py"
check_file "app/__init__.py"
check_file "docs/README.md"
check_file "docs/user/User_Manual.md"
check_file "docs/user/Installation.md"
check_file "docs/user/Configuration.md"
check_file "docs/developer/DEVELOPMENT.md"
check_file "docs/developer/API.md"
check_file "docs/developer/CONTRIBUTING.md"

echo -e "\n🔧 Python Package Files:"
check_file "app/core/__init__.py"
check_file "app/gui/__init__.py"
check_file "app/utils/__init__.py"
check_file "app/monitoring/__init__.py"
check_file "tests/__init__.py"

echo -e "\n🚀 Executable Scripts:"
check_executable "run.sh"
check_executable "tools/flatpak-pip-generator"
check_executable "packaging/flatpak/search-and-destroy.sh"

echo -e "\n📦 Build Scripts:"
find scripts/ -name "*.sh" | while read script; do
    check_executable "$script"
done

echo -e "\n🎯 Configuration Files:"
check_file "pytest.ini"
check_file "mypy.ini"
check_file ".gitignore"

echo -e "\n📋 Summary:"
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}🎉 Repository structure is complete! No issues found.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Found $ISSUES_FOUND issues that need attention.${NC}"
    exit 1
fi
