#!/bin/bash
# GitHub Copilot Enhancement Framework - Policy Validation Script
# This script validates all mandatory policies are properly implemented

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 GitHub Copilot Enhancement Framework - Policy Validation${NC}"
echo "============================================================="

# Counters
total_checks=0
passed_checks=0
failed_checks=0

# Helper function to check file existence
check_file() {
    local file="$1"
    local description="$2"
    total_checks=$((total_checks + 1))

    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $description${NC}"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo -e "${RED}❌ $description${NC}"
        failed_checks=$((failed_checks + 1))
        return 1
    fi
}

# Helper function to check directory existence
check_directory() {
    local dir="$1"
    local description="$2"
    total_checks=$((total_checks + 1))

    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✅ $description${NC}"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo -e "${RED}❌ $description${NC}"
        failed_checks=$((failed_checks + 1))
        return 1
    fi
}

echo -e "\n${YELLOW}📋 MANDATORY POLICIES VALIDATION${NC}"
echo "================================="

# Check Archive Policy
echo -e "\n${BLUE}🗄️  Archive Management Policy${NC}"
check_file ".github/instructions/archive-policy.instructions.md" "Archive policy instructions"
check_directory "archive" "Archive directory structure"
check_directory "archive/deprecated" "Deprecated content directory"
check_directory "archive/legacy-versions" "Legacy versions directory"
check_directory "archive/superseded" "Superseded content directory"
check_file "archive/README.md" "Archive documentation"

# Check Documentation Policy
echo -e "\n${BLUE}📚 Documentation Organization Policy${NC}"
check_file ".github/instructions/docs-policy.instructions.md" "Documentation policy instructions"
check_directory "docs" "Documentation directory structure"
check_directory "docs/guides" "Documentation guides directory"
# Note: analysis and implementation-reports archived to archive/superseded/
check_file "docs/README.md" "Documentation overview"

# Check Code Quality Policy
echo -e "\n${BLUE}⚡ Code Quality Standards Policy${NC}"
check_file ".github/instructions/code-quality.instructions.md" "Code quality policy instructions"

# Check File Organization Policy
echo -e "\n${BLUE}📁 File Organization Policy${NC}"
check_file ".github/instructions/file-organization.instructions.md" "File organization policy instructions"

# Check Additional Policies
echo -e "\n${BLUE}🔒 Additional Mandatory Policies${NC}"
check_file ".github/instructions/security.instructions.md" "Security guidelines"
check_file ".github/instructions/testing.instructions.md" "Testing standards"
check_file ".github/instructions/debugging.instructions.md" "Debugging and error resolution guidelines"

# Check GitHub Copilot Enhancement Framework
echo -e "\n${BLUE}🤖 GitHub Copilot Enhancement Framework${NC}"
check_directory ".github/chatmodes" "Chat modes directory"
check_directory ".github/prompts" "Prompts directory"
check_file "README.md" "Main project documentation"

# Count chat modes and prompts
if [[ -d ".github/chatmodes" ]]; then
    chatmode_count=$(find .github/chatmodes -name "*.chatmode.md" | wc -l)
    echo -e "${GREEN}📝 Found $chatmode_count chat modes${NC}"
fi

if [[ -d ".github/prompts" ]]; then
    prompt_count=$(find .github/prompts -name "*.prompt.md" | wc -l)
    echo -e "${GREEN}🎯 Found $prompt_count prompts${NC}"
fi

# Check VS Code integration
echo -e "\n${BLUE}💻 VS Code Integration${NC}"
check_file ".vscode/settings.json" "VS Code workspace settings"
check_file ".vscode/extensions.json" "VS Code recommended extensions"

# Optional but recommended files
echo -e "\n${YELLOW}🔧 RECOMMENDED CONFIGURATIONS${NC}"
echo "============================="

recommended_checks=0
recommended_passed=0

check_recommended() {
    local file="$1"
    local description="$2"
    recommended_checks=$((recommended_checks + 1))

    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $description${NC}"
        recommended_passed=$((recommended_passed + 1))
    else
        echo -e "${YELLOW}⚠️  $description (recommended)${NC}"
    fi
}

check_recommended ".editorconfig" "EditorConfig file"
check_recommended ".prettierrc" "Prettier configuration"
check_recommended ".markdownlint.json" "Markdown linting configuration"
check_recommended ".gitignore" "Git ignore file"
check_recommended "package.json" "Node.js package configuration"

# Summary
echo -e "\n${BLUE}📊 VALIDATION SUMMARY${NC}"
echo "==================="
echo -e "Total Policy Checks: $total_checks"
echo -e "${GREEN}Passed: $passed_checks${NC}"
echo -e "${RED}Failed: $failed_checks${NC}"

if [[ $recommended_checks -gt 0 ]]; then
    echo -e "\nRecommended Configurations: $recommended_checks"
    echo -e "${GREEN}Present: $recommended_passed${NC}"
    echo -e "${YELLOW}Missing: $((recommended_checks - recommended_passed))${NC}"
fi

# Policy compliance percentage
compliance_percentage=$(( (passed_checks * 100) / total_checks ))
echo -e "\n${BLUE}Policy Compliance: ${compliance_percentage}%${NC}"

# Final result
echo -e "\n${BLUE}🎯 FINAL RESULT${NC}"
echo "==============="

if [[ $failed_checks -eq 0 ]]; then
    echo -e "${GREEN}🎉 ALL MANDATORY POLICIES ARE PROPERLY IMPLEMENTED!${NC}"
    echo -e "${GREEN}✅ Repository is fully compliant with GitHub Copilot Enhancement Framework${NC}"
    exit 0
else
    echo -e "${RED}❌ $failed_checks mandatory policy requirement(s) are missing${NC}"
    echo -e "${YELLOW}⚠️  Please address the failed checks above before deployment${NC}"
    exit 1
fi
