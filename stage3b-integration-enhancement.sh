#!/bin/bash

# Stage 3B: Advanced Integration Test Enhancement
# Implements comprehensive content quality optimization based on validation system analysis

echo "🔧 Stage 3B: Advanced Integration Test Enhancement"
echo "Implementing GitHub Copilot 2025 content quality standards"
echo ""

# Create comprehensive content fixer that addresses exact validation criteria
cat << 'EOF' > .github/validation/content-quality-optimizer.js
const fs = require('fs').promises;
const path = require('path');

class ContentQualityOptimizer {
  constructor() {
    this.fixes = [];
  }

  async optimizeFile(filePath) {
    console.log(`🔧 Optimizing: ${filePath}`);
    let content = await fs.readFile(filePath, 'utf8');
    const originalContent = content;

    // Fix heading hierarchy - ensure no level skips
    content = this.fixHeadingHierarchy(content);

    // Fix code blocks missing language specification
    content = this.fixCodeBlockLanguages(content);

    // Fix list formatting (blank lines before lists)
    content = this.fixListFormatting(content);

    // Fix table formatting
    content = this.fixTableFormatting(content);

    // Write back if changed
    if (content !== originalContent) {
      await fs.writeFile(filePath, content, 'utf8');
      console.log(`  ✅ Fixed: ${filePath}`);
      return true;
    }

    return false;
  }

  fixHeadingHierarchy(content) {
    const lines = content.split('\n');
    const result = [];
    let lastHeadingLevel = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const headingMatch = line.match(/^(#+)\s+(.+)$/);

      if (headingMatch) {
        const currentLevel = headingMatch[1].length;
        const headingText = headingMatch[2];

        // Fix skipped levels
        if (currentLevel > lastHeadingLevel + 1) {
          const correctedLevel = lastHeadingLevel + 1;
          const correctedHeading = '#'.repeat(correctedLevel) + ' ' + headingText;
          result.push(correctedHeading);
          lastHeadingLevel = correctedLevel;
          this.fixes.push(`Fixed heading level skip: "${line}" -> "${correctedHeading}"`);
        } else {
          result.push(line);
          lastHeadingLevel = currentLevel;
        }
      } else {
        result.push(line);
      }
    }

    return result.join('\n');
  }

  fixCodeBlockLanguages(content) {
    // Fix code blocks that start with ``` but have no language
    return content.replace(/^```\s*$/gm, '```markdown');
  }

  fixListFormatting(content) {
    const lines = content.split('\n');
    const result = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const prevLine = i > 0 ? lines[i - 1] : '';

      // If this line starts a list and previous line is not blank
      if (line.match(/^[-*+]\s+/) || line.match(/^\d+\.\s+/)) {
        if (prevLine.trim() !== '' && !prevLine.match(/^[-*+]\s+/) && !prevLine.match(/^\d+\.\s+/)) {
          result.push(''); // Add blank line before list
          this.fixes.push(`Added blank line before list at: "${line}"`);
        }
      }

      result.push(line);
    }

    return result.join('\n');
  }

  fixTableFormatting(content) {
    const lines = content.split('\n');
    const result = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Check if this line looks like a table header
      if (line.includes('|') && line.split('|').length >= 3) {
        const nextLine = i + 1 < lines.length ? lines[i + 1] : '';

        // If next line is not a table separator, add one
        if (!nextLine.match(/^\|?[-:]+\|[-:|\s]+$/)) {
          result.push(line);

          // Generate separator based on number of columns
          const columns = line.split('|').length - 2;
          const separator = '|' + '---|'.repeat(columns);
          result.push(separator);
          this.fixes.push(`Added table separator after: "${line}"`);
        } else {
          result.push(line);
        }
      } else {
        result.push(line);
      }
    }

    return result.join('\n');
  }
}

// Main execution
async function main() {
  const optimizer = new ContentQualityOptimizer();

  const filesToFix = [
    '.github/chatmodes/documentation.chatmode.md',
    '.github/chatmodes/security.chatmode.md',
    '.github/prompts/database-optimization.prompt.md',
    '.github/prompts/deployment-strategy.prompt.md',
    '.github/validation/IMPLEMENTATION_SUMMARY.md'
  ];

  console.log('🚀 Starting advanced content optimization...\n');

  for (const file of filesToFix) {
    try {
      const fixed = await optimizer.optimizeFile(file);
      if (fixed) {
        console.log(`  📝 Applied fixes to ${file}`);
      } else {
        console.log(`  ✅ No issues found in ${file}`);
      }
    } catch (error) {
      console.error(`  ❌ Error processing ${file}: ${error.message}`);
    }
  }

  console.log(`\n🎯 Optimization complete!`);
  console.log(`📊 Total fixes applied: ${optimizer.fixes.length}`);

  if (optimizer.fixes.length > 0) {
    console.log('\n📋 Summary of fixes:');
    optimizer.fixes.forEach(fix => console.log(`  - ${fix}`));
  }
}

main().catch(console.error);
EOF

# Run the content quality optimizer
echo "🎯 Running Advanced Content Quality Optimizer..."
node .github/validation/content-quality-optimizer.js

echo ""
echo "✅ Stage 3B Integration Test Enhancement Complete"
echo ""
echo "Next: Validate quality improvements..."
