#!/bin/bash
# Comprehensive Repository Organization Script
# Enterprise-grade organization for GitHub Copilot Enhancement Framework

set -e

echo "🧹 Starting Comprehensive Repository Organization..."

# Create proper directory structure
echo "📁 Creating proper directory structure..."

# Create reports directory for all completion reports
mkdir -p reports/stages
mkdir -p reports/analysis
mkdir -p reports/quality

# Create proper backup directory
mkdir -p archive/backups

# Create proper scripts organization
mkdir -p scripts/stages
mkdir -p scripts/quality
mkdir -p scripts/validation
mkdir -p scripts/utils

# Create proper documentation structure
mkdir -p docs/reports
mkdir -p docs/development
mkdir -p docs/deployment

echo "🗂️ Moving files to proper locations..."

# Move all stage reports to reports/stages/
if [ -f "STAGE_1_COMPLETION_REPORT.md" ]; then
    mv STAGE_1_COMPLETION_REPORT.md reports/stages/
fi

if [ -f "STAGE_4_COMPLETION_REPORT.md" ]; then
    mv STAGE_4_COMPLETION_REPORT.md reports/stages/
fi

if [ -f "STAGE_4_COMPREHENSIVE_REVIEW.md" ]; then
    mv STAGE_4_COMPREHENSIVE_REVIEW.md reports/stages/
fi

if [ -f "PROFESSIONAL_PLAN_90_PERCENT_QUALITY.md" ]; then
    mv PROFESSIONAL_PLAN_90_PERCENT_QUALITY.md reports/
fi

if [ -f "PROFESSIONAL_SUCCESS_REPORT.md" ]; then
    mv PROFESSIONAL_SUCCESS_REPORT.md reports/
fi

# Move analysis reports to reports/analysis/
if [ -f "XANADOS_ENHANCEMENT_ANALYSIS.md" ]; then
    mv XANADOS_ENHANCEMENT_ANALYSIS.md reports/analysis/
fi

if [ -f "COMPREHENSIVE_FIX_REPORT_2025-08-23.md" ]; then
    mv COMPREHENSIVE_FIX_REPORT_2025-08-23.md reports/quality/
fi

if [ -f "BUG_REPORT_2025-08-23.md" ]; then
    mv BUG_REPORT_2025-08-23.md reports/quality/
fi

if [ -f "REPOSITORY_TIDYING_COMPLETE.md" ]; then
    mv REPOSITORY_TIDYING_COMPLETE.md reports/quality/
fi

if [ -f "MISSION_ACCOMPLISHED.md" ]; then
    mv MISSION_ACCOMPLISHED.md reports/
fi

# Move stage scripts to scripts/stages/
if [ -f "stage3a-content-quality-fixer.sh" ]; then
    mv stage3a-content-quality-fixer.sh scripts/stages/
fi

if [ -f "stage3b-integration-enhancement.sh" ]; then
    mv stage3b-integration-enhancement.sh scripts/stages/
fi

if [ -f "stage4-excellence-implementation.sh" ]; then
    mv stage4-excellence-implementation.sh scripts/stages/
fi

# Move quality scripts to scripts/quality/
if [ -f "scripts/markdown-quality-fixer.js" ]; then
    mv scripts/markdown-quality-fixer.js scripts/quality/
fi

if [ -f "scripts/stage2a-markdown-fixer.sh" ]; then
    mv scripts/stage2a-markdown-fixer.sh scripts/stages/
fi

# Move validation scripts to scripts/validation/
if [ -f "scripts/validate-policies.sh" ]; then
    mv scripts/validate-policies.sh scripts/validation/
fi

if [ -f "scripts/verify-structure.sh" ]; then
    mv scripts/verify-structure.sh scripts/validation/
fi

# Move utility scripts to scripts/utils/
if [ -f "scripts/generate-install-links.sh" ]; then
    mv scripts/generate-install-links.sh scripts/utils/
fi

if [ -f "scripts/update-readme.js" ]; then
    mv scripts/update-readme.js scripts/utils/
fi

if [ -f "scripts/stage1-implementation.sh" ]; then
    mv scripts/stage1-implementation.sh scripts/stages/
fi

# Move all backup files to archive/backups/
echo "🗄️ Organizing backup files..."
find . -name "*.backup" -exec mv {} archive/backups/ \;

echo "🧹 Cleaning up empty directories..."
find . -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true

echo "📋 Creating directory README files..."

# Create README for reports directory
cat > reports/README.md << 'EOF'
# Reports Directory

This directory contains all project reports organized by category.

## Structure

- `stages/` - Stage completion reports and reviews
- `analysis/` - Analysis reports and assessments  
- `quality/` - Quality assurance and tidying reports
- `PROFESSIONAL_PLAN_90_PERCENT_QUALITY.md` - Master quality improvement plan
- `PROFESSIONAL_SUCCESS_REPORT.md` - Overall success metrics
- `MISSION_ACCOMPLISHED.md` - Final achievement summary

## Usage

These reports document the development process, quality improvements, and achievements of the GitHub Copilot Enhancement Framework.
EOF

# Create README for scripts directory
cat > scripts/README.md << 'EOF'
# Scripts Directory

Organized automation scripts for the GitHub Copilot Enhancement Framework.

## Structure

- `stages/` - Stage implementation and execution scripts
- `quality/` - Quality assurance and markdown processing scripts
- `validation/` - Template and structure validation scripts
- `utils/` - Utility scripts for general operations

## Usage

All scripts are executable and documented. Run with `--help` for usage information where available.
EOF

# Create README for archive directory
cat > archive/README.md << 'EOF'
# Archive Directory

Contains historical files and backups.

## Structure

- `backups/` - Backup files from various operations
- Other archived content as needed

## Purpose

Maintains project history while keeping the main directory structure clean.
EOF

echo "✅ Repository organization complete!"
echo ""
echo "📊 Organization Summary:"
echo "  ✅ Reports organized into categories"
echo "  ✅ Scripts organized by function"  
echo "  ✅ Backup files archived"
echo "  ✅ Directory structure optimized"
echo "  ✅ README files created for navigation"
echo ""
echo "🎯 New Structure:"
echo "  📁 reports/ - All project reports"
echo "  📁 scripts/ - Organized automation scripts"
echo "  📁 archive/ - Historical files and backups"
echo "  📁 docs/ - Project documentation"
echo "  📁 .github/ - GitHub Copilot framework files"
echo ""
echo "🏆 Repository is now enterprise-ready with optimal organization!"
