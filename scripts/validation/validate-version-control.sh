#!/bin/bash

# Version Control Standards Validation Script
# Validates repository compliance with industry-standard version control practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_failure() {
    echo -e "${RED}[✗]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if we're in a git repository
check_git_repo() {
    print_status "Checking git repository..."
    if git rev-parse --git-dir > /dev/null 2>&1; then
        print_success "Repository is a valid git repository"
    else
        print_failure "Not in a git repository"
        exit 1
    fi
}

# Check git configuration
check_git_config() {
    print_status "Checking git configuration..."
    
    # Check commit template
    if git config --get commit.template > /dev/null 2>&1; then
        local template_file=$(git config --get commit.template)
        if [ -f "$template_file" ]; then
            print_success "Commit message template configured: $template_file"
        else
            print_failure "Commit template file not found: $template_file"
        fi
    else
        print_failure "Commit message template not configured"
    fi
    
    # Check pull strategy
    local pull_rebase=$(git config --get pull.rebase 2>/dev/null || echo "not-set")
    if [ "$pull_rebase" = "false" ]; then
        print_success "Pull strategy configured for merge (recommended)"
    else
        print_warning "Pull strategy not configured or set to rebase"
    fi
    
    # Check default branch
    local default_branch=$(git config --get init.defaultBranch 2>/dev/null || echo "not-set")
    if [ "$default_branch" = "main" ]; then
        print_success "Default branch set to 'main'"
    else
        print_warning "Default branch not set to 'main'"
    fi
}

# Check required files
check_required_files() {
    print_status "Checking required version control files..."
    
    local required_files=(
        ".gitignore"
        ".gitmessage"
        "CHANGELOG.md"
        "VERSION"
        ".github/pull_request_template.md"
        ".github/GIT_STRATEGY.md"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "Required file exists: $file"
        else
            print_failure "Required file missing: $file"
        fi
    done
}

# Check GitHub workflows
check_github_workflows() {
    print_status "Checking GitHub Actions workflows..."
    
    local workflow_dir=".github/workflows"
    if [ -d "$workflow_dir" ]; then
        print_success "GitHub workflows directory exists"
        
        # Check for CI workflow
        if [ -f "$workflow_dir/ci.yml" ]; then
            print_success "CI workflow exists"
        else
            print_failure "CI workflow missing"
        fi
        
        # Check for release workflow
        if [ -f "$workflow_dir/release.yml" ]; then
            print_success "Release workflow exists"
        else
            print_failure "Release workflow missing"
        fi
    else
        print_failure "GitHub workflows directory missing"
    fi
}

# Check issue templates
check_issue_templates() {
    print_status "Checking GitHub issue templates..."
    
    local template_dir=".github/ISSUE_TEMPLATE"
    if [ -d "$template_dir" ]; then
        print_success "Issue templates directory exists"
        
        local templates=(
            "bug_report.yml"
            "feature_request.yml"
            "documentation.yml"
        )
        
        for template in "${templates[@]}"; do
            if [ -f "$template_dir/$template" ]; then
                print_success "Issue template exists: $template"
            else
                print_failure "Issue template missing: $template"
            fi
        done
    else
        print_failure "Issue templates directory missing"
    fi
}

# Check branch structure
check_branch_structure() {
    print_status "Checking branch structure..."
    
    # Check if we're on main branch
    local current_branch=$(git branch --show-current)
    if [ "$current_branch" = "main" ]; then
        print_success "Currently on main branch"
    else
        print_warning "Not on main branch (current: $current_branch)"
    fi
    
    # Check for remote origin
    if git remote get-url origin > /dev/null 2>&1; then
        print_success "Remote 'origin' configured"
    else
        print_failure "Remote 'origin' not configured"
    fi
}

# Check commit message format
check_recent_commits() {
    print_status "Checking recent commit message format..."
    
    local conventional_commit_pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,50}'
    
    # Check last 5 commits
    local commit_count=0
    local valid_commits=0
    
    while IFS= read -r commit_msg; do
        commit_count=$((commit_count + 1))
        if [[ $commit_msg =~ $conventional_commit_pattern ]]; then
            valid_commits=$((valid_commits + 1))
        fi
    done < <(git log --format="%s" -5)
    
    if [ $valid_commits -gt 0 ]; then
        print_success "Found $valid_commits/$commit_count recent commits following conventional format"
    else
        print_warning "No recent commits follow conventional commit format"
    fi
}

# Check version control
check_version_control() {
    print_status "Checking version control..."
    
    # Check for tags
    if git tag -l | grep -q "v[0-9]"; then
        local latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
        print_success "Version tags found (latest: $latest_tag)"
    else
        print_failure "No version tags found"
    fi
    
    # Check VERSION file format
    if [ -f "VERSION" ]; then
        if grep -q "VERSION_MAJOR\|VERSION_MINOR\|VERSION_PATCH" VERSION; then
            print_success "VERSION file has semantic versioning format"
        else
            print_failure "VERSION file format is not semantic versioning"
        fi
    fi
}

# Check .gitignore effectiveness
check_gitignore() {
    print_status "Checking .gitignore effectiveness..."
    
    # Check for common patterns
    local patterns=(
        "node_modules/"
        "*.log"
        ".env"
        "dist/"
        "build/"
        ".DS_Store"
    )
    
    local found_patterns=0
    for pattern in "${patterns[@]}"; do
        if grep -q "$pattern" .gitignore 2>/dev/null; then
            found_patterns=$((found_patterns + 1))
        fi
    done
    
    if [ $found_patterns -ge 4 ]; then
        print_success "gitignore contains common patterns ($found_patterns/6)"
    else
        print_warning "gitignore may be missing common patterns ($found_patterns/6)"
    fi
    
    # Check for untracked files that should be ignored
    local untracked_count=$(git ls-files --others --exclude-standard | wc -l)
    if [ $untracked_count -eq 0 ]; then
        print_success "No untracked files (good .gitignore coverage)"
    else
        print_warning "$untracked_count untracked files found"
    fi
}

# Check security
check_security() {
    print_status "Checking security practices..."
    
    # Check for committed secrets (basic check)
    local secret_patterns=(
        "password"
        "secret"
        "api_key"
        "private_key"
        "token"
    )
    
    local issues_found=0
    for pattern in "${secret_patterns[@]}"; do
        if git log --all -p | grep -i "$pattern" | grep -E "^\+" > /dev/null 2>&1; then
            issues_found=$((issues_found + 1))
        fi
    done
    
    if [ $issues_found -eq 0 ]; then
        print_success "No obvious secrets found in commit history"
    else
        print_warning "Potential secrets found in commit history - manual review needed"
    fi
}

# Generate report
generate_report() {
    echo ""
    echo "======================================"
    echo "Version Control Standards Validation Report"
    echo "======================================"
    echo ""
    echo "Total Checks: $TOTAL_CHECKS"
    echo -e "Passed: ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "Failed: ${RED}$CHECKS_FAILED${NC}"
    echo ""
    
    local pass_percentage=$((CHECKS_PASSED * 100 / TOTAL_CHECKS))
    echo "Pass Rate: $pass_percentage%"
    echo ""
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All version control standards met!${NC}"
        echo ""
        echo "Your repository follows industry-standard version control practices."
    elif [ $pass_percentage -ge 80 ]; then
        echo -e "${YELLOW}⚠ Most standards met with minor issues${NC}"
        echo ""
        echo "Consider addressing the failed checks for full compliance."
    else
        echo -e "${RED}✗ Significant version control improvements needed${NC}"
        echo ""
        echo "Please address the failed checks to meet industry standards."
    fi
    
    # Save report
    local report_file="reports/quality/version-control-validation-$(date +%Y-%m-%d).md"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
# Version Control Standards Validation Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Repository:** $(basename "$(git rev-parse --show-toplevel)")

## Summary

- **Total Checks:** $TOTAL_CHECKS
- **Passed:** $CHECKS_PASSED
- **Failed:** $CHECKS_FAILED
- **Pass Rate:** $pass_percentage%

## Status

EOF
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo "✅ **All version control standards met!**" >> "$report_file"
    elif [ $pass_percentage -ge 80 ]; then
        echo "⚠️ **Most standards met with minor issues**" >> "$report_file"
    else
        echo "❌ **Significant version control improvements needed**" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "Repository follows industry-standard version control practices at $pass_percentage% compliance." >> "$report_file"
    
    print_status "Report saved to: $report_file"
}

# Main execution
main() {
    echo "======================================"
    echo "Version Control Standards Validator"
    echo "======================================"
    echo ""
    
    check_git_repo
    check_git_config
    check_required_files
    check_github_workflows
    check_issue_templates
    check_branch_structure
    check_recent_commits
    check_version_control
    check_gitignore
    check_security
    
    generate_report
}

# Run main function
main "$@"
