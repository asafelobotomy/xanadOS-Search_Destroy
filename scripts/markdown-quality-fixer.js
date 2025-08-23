#!/usr/bin/env node

/**
 * Stage 2A: Automated Markdown Quality Fixer
 * Professional implementation for achieving 90%+ quality score
 *
 * Fixes all major markdown quality issues:
 * - MD009: Trailing spaces
 * - MD013: Line length violations
 * - MD022: Missing blank lines around headings
 * - MD032: Missing blank lines around lists
 * - MD031: Missing blank lines around code blocks
 * - MD040: Missing language specification in code blocks
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

class MarkdownQualityFixer {
    constructor() {
        this.fixesApplied = {
            trailingSpaces: 0,
            lineLength: 0,
            headingSpacing: 0,
            listSpacing: 0,
            codeBlockSpacing: 0,
            codeBlockLanguage: 0
        };
    }

    /**
     * Fix all markdown files in the repository
     */
    async fixAllMarkdownFiles() {
        console.log('🔧 Starting Stage 2A: Automated Markdown Quality Fixes');

        // Find all markdown files
        const markdownFiles = glob.sync('**/*.md', {
            ignore: ['node_modules/**', '.git/**', '*.min.md']
        });

        console.log(`📋 Found ${markdownFiles.length} markdown files to process`);

        for (const filePath of markdownFiles) {
            console.log(`🔄 Processing: ${filePath}`);
            await this.fixMarkdownFile(filePath);
        }

        this.reportResults();
    }

    /**
     * Fix a single markdown file
     */
    async fixMarkdownFile(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            let fixedContent = content;

            // Apply fixes in order
            fixedContent = this.fixTrailingSpaces(fixedContent);
            fixedContent = this.fixLineLength(fixedContent);
            fixedContent = this.fixHeadingSpacing(fixedContent);
            fixedContent = this.fixListSpacing(fixedContent);
            fixedContent = this.fixCodeBlockSpacing(fixedContent);
            fixedContent = this.fixCodeBlockLanguage(fixedContent);

            // Only write if content changed
            if (fixedContent !== content) {
                fs.writeFileSync(filePath, fixedContent, 'utf8');
                console.log(`   ✅ Fixed: ${filePath}`);
            } else {
                console.log(`   ℹ️ No changes needed: ${filePath}`);
            }
        } catch (error) {
            console.error(`   ❌ Error processing ${filePath}:`, error.message);
        }
    }

    /**
     * MD009: Fix trailing spaces
     */
    fixTrailingSpaces(content) {
        const lines = content.split('\\n');
        const fixedLines = lines.map(line => {
            if (line.endsWith(' ') && !line.endsWith('  ')) {
                this.fixesApplied.trailingSpaces++;
                return line.trimEnd();
            }
            return line;
        });
        return fixedLines.join('\\n');
    }

    /**
     * MD013: Fix line length violations (max 100 characters)
     */
    fixLineLength(content) {
        const lines = content.split('\\n');
        const fixedLines = [];

        for (const line of lines) {
            if (line.length > 100 && !line.startsWith('http') && !line.includes('```')) {
                // Intelligent word wrapping
                const wrapped = this.wrapLine(line, 100);
                fixedLines.push(...wrapped);
                this.fixesApplied.lineLength++;
            } else {
                fixedLines.push(line);
            }
        }

        return fixedLines.join('\\n');
    }

    /**
     * Intelligent line wrapping that preserves markdown structure
     */
    wrapLine(line, maxLength) {
        // Preserve markdown list structure
        const listMatch = line.match(/^(\\s*[-*+]\\s+|\\s*\\d+\\.\\s+)/);
        const prefix = listMatch ? listMatch[1] : '';
        const content = listMatch ? line.substring(prefix.length) : line;

        if (content.length <= maxLength - prefix.length) {
            return [line];
        }

        const words = content.split(' ');
        const wrappedLines = [];
        let currentLine = prefix;

        for (const word of words) {
            if ((currentLine + word).length <= maxLength) {
                currentLine += (currentLine === prefix ? '' : ' ') + word;
            } else {
                if (currentLine.trim() !== prefix.trim()) {
                    wrappedLines.push(currentLine);
                }
                currentLine = prefix + word;
            }
        }

        if (currentLine.trim() !== prefix.trim()) {
            wrappedLines.push(currentLine);
        }

        return wrappedLines;
    }

    /**
     * MD022: Fix missing blank lines around headings
     */
    fixHeadingSpacing(content) {
        const lines = content.split('\\n');
        const fixedLines = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const isHeading = line.match(/^#{1,6}\\s+/);

            if (isHeading) {
                // Add blank line before heading (if not at start and previous line isn't blank)
                if (i > 0 && lines[i - 1].trim() !== '' && !fixedLines[fixedLines.length - 1]?.trim() === '') {
                    fixedLines.push('');
                    this.fixesApplied.headingSpacing++;
                }

                fixedLines.push(line);

                // Add blank line after heading (if next line exists and isn't blank)
                if (i < lines.length - 1 && lines[i + 1].trim() !== '') {
                    fixedLines.push('');
                    this.fixesApplied.headingSpacing++;
                }
            } else {
                fixedLines.push(line);
            }
        }

        return fixedLines.join('\\n');
    }

    /**
     * MD032: Fix missing blank lines around lists
     */
    fixListSpacing(content) {
        const lines = content.split('\\n');
        const fixedLines = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const isListItem = line.match(/^\\s*[-*+]\\s+|^\\s*\\d+\\.\\s+/);
            const prevLine = i > 0 ? lines[i - 1] : '';
            const nextLine = i < lines.length - 1 ? lines[i + 1] : '';

            if (isListItem) {
                const prevIsListItem = prevLine.match(/^\\s*[-*+]\\s+|^\\s*\\d+\\.\\s+/);

                // Add blank line before first list item
                if (!prevIsListItem && prevLine.trim() !== '' && fixedLines[fixedLines.length - 1]?.trim() !== '') {
                    fixedLines.push('');
                    this.fixesApplied.listSpacing++;
                }

                fixedLines.push(line);

                const nextIsListItem = nextLine.match(/^\\s*[-*+]\\s+|^\\s*\\d+\\.\\s+/);

                // Add blank line after last list item
                if (!nextIsListItem && nextLine.trim() !== '') {
                    fixedLines.push('');
                    this.fixesApplied.listSpacing++;
                }
            } else {
                fixedLines.push(line);
            }
        }

        return fixedLines.join('\\n');
    }

    /**
     * MD031: Fix missing blank lines around code blocks
     */
    fixCodeBlockSpacing(content) {
        const lines = content.split('\\n');
        const fixedLines = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const isCodeFence = line.match(/^```/);

            if (isCodeFence) {
                const prevLine = i > 0 ? lines[i - 1] : '';

                // Add blank line before opening fence
                if (line.startsWith('```') && !line.includes('```', 3) && prevLine.trim() !== '') {
                    fixedLines.push('');
                    this.fixesApplied.codeBlockSpacing++;
                }

                fixedLines.push(line);

                // Add blank line after closing fence
                if (line === '```' && i < lines.length - 1 && lines[i + 1].trim() !== '') {
                    fixedLines.push('');
                    this.fixesApplied.codeBlockSpacing++;
                }
            } else {
                fixedLines.push(line);
            }
        }

        return fixedLines.join('\\n');
    }

    /**
     * MD040: Fix missing language specification in code blocks
     */
    fixCodeBlockLanguage(content) {
        const lines = content.split('\\n');
        const fixedLines = [];

        for (const line of lines) {
            if (line === '```') {
                // Default to markdown for unspecified code blocks
                fixedLines.push('```markdown');
                this.fixesApplied.codeBlockLanguage++;
            } else {
                fixedLines.push(line);
            }
        }

        return fixedLines.join('\\n');
    }

    /**
     * Report results of all fixes applied
     */
    reportResults() {
        console.log('\\n📊 Stage 2A Completion Report:');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        const totalFixes = Object.values(this.fixesApplied).reduce((a, b) => a + b, 0);

        console.log(`✅ Total fixes applied: ${totalFixes}`);
        console.log(`   • Trailing spaces: ${this.fixesApplied.trailingSpaces}`);
        console.log(`   • Line length: ${this.fixesApplied.lineLength}`);
        console.log(`   • Heading spacing: ${this.fixesApplied.headingSpacing}`);
        console.log(`   • List spacing: ${this.fixesApplied.listSpacing}`);
        console.log(`   • Code block spacing: ${this.fixesApplied.codeBlockSpacing}`);
        console.log(`   • Code block language: ${this.fixesApplied.codeBlockLanguage}`);

        console.log('\\n🎯 Expected Impact: +15-20% quality score improvement');
        console.log('📋 Next: Run validation to measure actual improvement');
    }
}

// Execute if run directly
if (require.main === module) {
    const fixer = new MarkdownQualityFixer();
    fixer.fixAllMarkdownFiles().catch(console.error);
}

module.exports = MarkdownQualityFixer;
