const fs = require('fs').promises;

class WCAGComplianceChecker {
  constructor() {
    this.violations = [];
    this.warnings = [];
  }

  async checkFile(filePath) {
    const content = await fs.readFile(filePath, 'utf8');

    // Check for alt text on images
    this.checkImageAltText(content, filePath);

    // Check heading hierarchy
    this.checkHeadingHierarchy(content, filePath);

    // Check color contrast indicators
    this.checkColorContrast(content, filePath);

    // Check keyboard navigation hints
    this.checkKeyboardNavigation(content, filePath);

    return {
      violations: this.violations,
      warnings: this.warnings,
      isCompliant: this.violations.length === 0
    };
  }

  checkImageAltText(content, filePath) {
    const imageRegex = /!\[([^\]]*)\]\([^)]+\)/g;
    let match;

    while ((match = imageRegex.exec(content)) !== null) {
      const altText = match[1];
      if (!altText || altText.trim() === '') {
        this.violations.push({
          file: filePath,
          type: 'WCAG 1.1.1',
          message: 'Image missing descriptive alt text',
          line: this.getLineNumber(content, match.index)
        });
      } else if (altText.length < 5) {
        this.warnings.push({
          file: filePath,
          type: 'WCAG 1.1.1',
          message: 'Alt text may be too brief',
          line: this.getLineNumber(content, match.index)
        });
      }
    }
  }

  checkHeadingHierarchy(content, filePath) {
    const headings = content.match(/^#+\s+.+$/gm) || [];
    let previousLevel = 0;

    headings.forEach((heading, index) => {
      const level = heading.match(/^#+/)[0].length;
      if (level > previousLevel + 1) {
        this.violations.push({
          file: filePath,
          type: 'WCAG 1.3.1',
          message: `Heading hierarchy skips levels (H${previousLevel} to H${level})`,
          line: this.getLineNumber(content, content.indexOf(heading))
        });
      }
      previousLevel = level;
    });
  }

  checkColorContrast(content, filePath) {
    // Check for color-only information indicators
    const colorOnlyRegex = /(red|green|blue|yellow|orange|purple)\s+(text|color|background)/gi;
    let match;

    while ((match = colorOnlyRegex.exec(content)) !== null) {
      this.warnings.push({
        file: filePath,
        type: 'WCAG 1.4.1',
        message: 'Avoid using color alone to convey information',
        line: this.getLineNumber(content, match.index)
      });
    }
  }

  checkKeyboardNavigation(content, filePath) {
    // Check for interactive elements without keyboard hints
    const interactiveRegex = /(click here|press|button|link)/gi;
    let match;

    while ((match = interactiveRegex.exec(content)) !== null) {
      if (!content.includes('Tab') && !content.includes('Enter') && !content.includes('Space')) {
        this.warnings.push({
          file: filePath,
          type: 'WCAG 2.1.1',
          message: 'Consider adding keyboard navigation instructions',
          line: this.getLineNumber(content, match.index)
        });
      }
    }
  }

  getLineNumber(content, index) {
    return content.substring(0, index).split('\n').length;
  }
}

module.exports = WCAGComplianceChecker;
