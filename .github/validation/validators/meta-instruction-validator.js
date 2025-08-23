#!/usr/bin/env node

/**
 * Meta-Instruction Validation Engine
 * Comprehensive validation framework for GitHub Copilot instructions
 */

import { promises as fs } from 'fs';
import { join, extname, dirname } from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

class MetaInstructionValidator {
  constructor(options = {}) {
    this.rootPath = options.rootPath || process.cwd();
    this.configPath = options.configPath || join(this.rootPath, '.github', 'validation', 'configs');
    this.reportsPath = options.reportsPath || join(this.rootPath, '.github', 'validation', 'reports');
    
    this.validationRules = new Map();
    this.validationResults = [];
    this.metrics = {
      totalFiles: 0,
      validatedFiles: 0,
      errors: 0,
      warnings: 0,
      passed: 0,
    };
    
    this.setupValidationRules();
  }

  setupValidationRules() {
    // Structural validation rules
    this.validationRules.set('structure', {
      name: 'Structural Validation',
      rules: [
        { id: 'file-naming', function: this.validateFileNaming.bind(this) },
        { id: 'directory-structure', function: this.validateDirectoryStructure.bind(this) },
        { id: 'template-compliance', function: this.validateTemplateCompliance.bind(this) },
        { id: 'dependency-integrity', function: this.validateDependencyIntegrity.bind(this) },
      ],
    });

    // Content quality validation rules
    this.validationRules.set('content', {
      name: 'Content Quality Validation',
      rules: [
        { id: 'markdown-quality', function: this.validateMarkdownQuality.bind(this) },
        { id: 'instruction-clarity', function: this.validateInstructionClarity.bind(this) },
        { id: 'code-quality', function: this.validateCodeQuality.bind(this) },
        { id: 'documentation-standards', function: this.validateDocumentationStandards.bind(this) },
      ],
    });

    // Integration validation rules
    this.validationRules.set('integration', {
      name: 'Integration Validation',
      rules: [
        { id: 'mcp-compatibility', function: this.validateMCPCompatibility.bind(this) },
        { id: 'chat-mode-integration', function: this.validateChatModeIntegration.bind(this) },
        { id: 'cross-references', function: this.validateCrossReferences.bind(this) },
        { id: 'version-compatibility', function: this.validateVersionCompatibility.bind(this) },
      ],
    });

    // Performance validation rules
    this.validationRules.set('performance', {
      name: 'Performance Validation',
      rules: [
        { id: 'file-size-limits', function: this.validateFileSizeLimits.bind(this) },
        { id: 'complexity-metrics', function: this.validateComplexityMetrics.bind(this) },
        { id: 'resource-efficiency', function: this.validateResourceEfficiency.bind(this) },
      ],
    });
  }

  async validateProject() {
    console.log('🔍 Starting Meta-Instruction Validation...\n');
    
    try {
      // Ensure reports directory exists
      await fs.mkdir(this.reportsPath, { recursive: true });
      
      // Discover all instruction files
      const instructionFiles = await this.discoverInstructionFiles();
      this.metrics.totalFiles = instructionFiles.length;
      
      console.log(`📁 Found ${instructionFiles.length} instruction files to validate\n`);
      
      // Run validation categories
      for (const [category, config] of this.validationRules) {
        console.log(`🔧 Running ${config.name}...`);
        await this.runValidationCategory(category, config, instructionFiles);
      }
      
      // Generate comprehensive report
      await this.generateValidationReport();
      
      // Display summary
      this.displayValidationSummary();
      
      return this.validationResults;
    } catch (error) {
      console.error('❌ Validation failed:', error.message);
      throw error;
    }
  }

  async discoverInstructionFiles() {
    const files = [];
    const directories = [
      '.github/chatmodes',
      '.github/prompts',
      '.github/mcp',
      '.github/validation',
    ];
    
    for (const dir of directories) {
      const fullPath = join(this.rootPath, dir);
      try {
        await this.scanDirectory(fullPath, files);
      } catch (error) {
        // Directory might not exist, skip silently
        continue;
      }
    }
    
    return files.filter(file => 
      file.endsWith('.md') || 
      file.endsWith('.json') || 
      file.endsWith('.js') ||
      file.endsWith('.yaml') ||
      file.endsWith('.yml')
    );
  }

  async scanDirectory(dirPath, files) {
    try {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = join(dirPath, entry.name);
        
        if (entry.isDirectory()) {
          await this.scanDirectory(fullPath, files);
        } else {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Directory doesn't exist or can't be read
      return;
    }
  }

  async runValidationCategory(category, config, files) {
    for (const rule of config.rules) {
      try {
        const results = await rule.function(files);
        this.validationResults.push({
          category,
          rule: rule.id,
          results,
          timestamp: new Date().toISOString(),
        });
        
        // Update metrics
        this.updateMetrics(results);
        
        console.log(`  ✅ ${rule.id}: ${results.passed} passed, ${results.warnings} warnings, ${results.errors} errors`);
      } catch (error) {
        console.log(`  ❌ ${rule.id}: Failed - ${error.message}`);
        this.metrics.errors++;
      }
    }
    console.log();
  }

  updateMetrics(results) {
    this.metrics.validatedFiles += results.filesChecked || 0;
    this.metrics.passed += results.passed || 0;
    this.metrics.warnings += results.warnings || 0;
    this.metrics.errors += results.errors || 0;
  }

  // Structural Validation Methods
  async validateFileNaming(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: files.length, details: [] };
    
    const namingRules = {
      // Chat mode files should follow specific pattern
      chatModes: /^\.github\/chatmodes\/[a-z0-9-]+\.chatmode\.md$/,
      // Prompt files should be in prompts directory
      prompts: /^\.github\/prompts\/[a-z0-9-]+\.prompt\.md$/,
      // MCP servers should follow naming convention
      mcpServers: /^\.github\/mcp\/servers\/[a-z0-9-]+\/index\.js$/,
      // Configuration files should be properly named
      configs: /^\.github\/.*\/[a-z0-9-]+\.(json|yaml|yml)$/,
    };
    
    for (const file of files) {
      const relativePath = file.replace(this.rootPath + '/', '');
      let isValidName = false;
      
      // Check against naming rules
      for (const [type, pattern] of Object.entries(namingRules)) {
        if (pattern.test(relativePath)) {
          isValidName = true;
          break;
        }
      }
      
      // General file naming rules
      const basename = relativePath.split('/').pop();
      const hasValidExtension = /\.(md|json|js|yaml|yml)$/.test(basename);
      const hasValidCharacters = /^[a-z0-9-._]+$/i.test(basename);
      
      if (!hasValidExtension) {
        results.errors++;
        results.details.push({
          file: relativePath,
          type: 'error',
          message: 'File has invalid extension',
        });
      } else if (!hasValidCharacters) {
        results.warnings++;
        results.details.push({
          file: relativePath,
          type: 'warning',
          message: 'File name contains invalid characters (use only a-z, 0-9, -, _, .)',
        });
      } else {
        results.passed++;
      }
    }
    
    return results;
  }

  async validateDirectoryStructure(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const expectedStructure = {
      '.github/chatmodes': [],
      '.github/prompts': [],
      '.github/mcp': ['servers', 'configs'],
      '.github/validation': ['validators', 'configs', 'reports', 'tests', 'tools'],
    };
    
    for (const [basePath, expectedDirs] of Object.entries(expectedStructure)) {
      const fullBasePath = join(this.rootPath, basePath);
      
      try {
        const stats = await fs.stat(fullBasePath);
        if (!stats.isDirectory()) {
          results.errors++;
          results.details.push({
            path: basePath,
            type: 'error',
            message: 'Expected directory does not exist',
          });
          continue;
        }
        
        // Check for expected subdirectories
        for (const expectedDir of expectedDirs) {
          const dirPath = join(fullBasePath, expectedDir);
          try {
            const dirStats = await fs.stat(dirPath);
            if (dirStats.isDirectory()) {
              results.passed++;
            } else {
              results.warnings++;
              results.details.push({
                path: join(basePath, expectedDir),
                type: 'warning',
                message: 'Expected subdirectory is not a directory',
              });
            }
          } catch (error) {
            results.warnings++;
            results.details.push({
              path: join(basePath, expectedDir),
              type: 'warning',
              message: 'Expected subdirectory does not exist',
            });
          }
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          path: basePath,
          type: 'error',
          message: 'Base directory does not exist',
        });
      }
    }
    
    results.filesChecked = Object.values(expectedStructure).flat().length;
    return results;
  }

  async validateTemplateCompliance(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const markdownFiles = files.filter(f => f.endsWith('.md'));
    results.filesChecked = markdownFiles.length;
    
    for (const file of markdownFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check for required sections in instruction files
        if (file.includes('chatmodes') || file.includes('prompts')) {
          const hasTitle = /^#\s+.+$/m.test(content);
          const hasDescription = /##\s+Description/m.test(content) || /##\s+Overview/m.test(content);
          const hasUsage = /##\s+Usage/m.test(content) || /##\s+How to Use/m.test(content);
          
          if (!hasTitle) {
            results.errors++;
            results.details.push({
              file: relativePath,
              type: 'error',
              message: 'Missing main title (# heading)',
            });
          } else if (!hasDescription) {
            results.warnings++;
            results.details.push({
              file: relativePath,
              type: 'warning',
              message: 'Missing description section',
            });
          } else if (!hasUsage) {
            results.warnings++;
            results.details.push({
              file: relativePath,
              type: 'warning',
              message: 'Missing usage section',
            });
          } else {
            results.passed++;
          }
        } else {
          // General markdown files just need a title
          const hasTitle = /^#\s+.+$/m.test(content);
          if (hasTitle) {
            results.passed++;
          } else {
            results.warnings++;
            results.details.push({
              file: relativePath,
              type: 'warning',
              message: 'Missing main title',
            });
          }
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to read file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateDependencyIntegrity(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    // Check package.json files for MCP servers
    const packageFiles = files.filter(f => f.endsWith('package.json'));
    results.filesChecked = packageFiles.length;
    
    for (const file of packageFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const packageData = JSON.parse(content);
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check for required MCP dependencies
        if (file.includes('mcp/servers/')) {
          const hasMCPDep = packageData.dependencies && 
            packageData.dependencies['@modelcontextprotocol/sdk'];
          
          if (!hasMCPDep) {
            results.errors++;
            results.details.push({
              file: relativePath,
              type: 'error',
              message: 'Missing required MCP SDK dependency',
            });
          } else {
            results.passed++;
          }
          
          // Check for proper Node.js version requirement
          if (!packageData.engines || !packageData.engines.node) {
            results.warnings++;
            results.details.push({
              file: relativePath,
              type: 'warning',
              message: 'Missing Node.js engine requirement',
            });
          }
        } else {
          results.passed++;
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to parse package.json: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  // Content Quality Validation Methods
  async validateMarkdownQuality(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const markdownFiles = files.filter(f => f.endsWith('.md'));
    results.filesChecked = markdownFiles.length;
    
    for (const file of markdownFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check for common markdown issues
        const lines = content.split('\n');
        let fileErrors = 0;
        let fileWarnings = 0;
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          const lineNum = i + 1;
          
          // Check for trailing whitespace
          if (line.endsWith(' ') || line.endsWith('\t')) {
            fileWarnings++;
            results.details.push({
              file: relativePath,
              line: lineNum,
              type: 'warning',
              message: 'Line has trailing whitespace',
            });
          }
          
          // Check for very long lines (over 120 characters)
          if (line.length > 120) {
            fileWarnings++;
            results.details.push({
              file: relativePath,
              line: lineNum,
              type: 'warning',
              message: `Line is too long (${line.length} characters)`,
            });
          }
          
          // Check for proper heading spacing
          if (line.match(/^#+/) && i > 0 && lines[i - 1].trim() !== '') {
            fileWarnings++;
            results.details.push({
              file: relativePath,
              line: lineNum,
              type: 'warning',
              message: 'Heading should have blank line before it',
            });
          }
        }
        
        if (fileErrors > 0) {
          results.errors++;
        } else if (fileWarnings > 0) {
          results.warnings++;
        } else {
          results.passed++;
        }
        
        results.warnings += fileWarnings;
        results.errors += fileErrors;
        
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to read file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateInstructionClarity(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const instructionFiles = files.filter(f => 
      (f.includes('chatmodes') || f.includes('prompts')) && f.endsWith('.md')
    );
    results.filesChecked = instructionFiles.length;
    
    for (const file of instructionFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Calculate readability metrics
        const wordCount = content.split(/\s+/).length;
        const sentenceCount = content.split(/[.!?]+/).length;
        const avgWordsPerSentence = wordCount / sentenceCount;
        
        // Check for clarity indicators
        const hasCodeExamples = /```/.test(content);
        const hasStructuredSections = (content.match(/^##/gm) || []).length >= 2;
        const hasActionableSteps = /^\d+\./m.test(content) || /^[-*]\s/m.test(content);
        
        let score = 0;
        const issues = [];
        
        // Scoring criteria
        if (wordCount >= 100) score++;
        else issues.push('Content is too short (less than 100 words)');
        
        if (avgWordsPerSentence <= 20) score++;
        else issues.push('Sentences are too long (average > 20 words)');
        
        if (hasCodeExamples) score++;
        else issues.push('Missing code examples');
        
        if (hasStructuredSections) score++;
        else issues.push('Content lacks proper structure');
        
        if (hasActionableSteps) score++;
        else issues.push('Missing actionable steps or lists');
        
        // Determine result based on score
        if (score >= 4) {
          results.passed++;
        } else if (score >= 2) {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: `Clarity issues: ${issues.join(', ')}`,
          });
        } else {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `Poor clarity (score: ${score}/5): ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateCodeQuality(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const codeFiles = files.filter(f => f.endsWith('.js'));
    results.filesChecked = codeFiles.length;
    
    for (const file of codeFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Basic code quality checks
        const hasShebang = content.startsWith('#!/usr/bin/env node');
        const hasDocstring = /\/\*\*[\s\S]*?\*\//.test(content);
        const hasErrorHandling = /try\s*{[\s\S]*?}\s*catch/.test(content);
        const hasProperExports = /export\s+(default\s+)?class|module\.exports\s*=/.test(content);
        
        let score = 0;
        const issues = [];
        
        if (hasShebang || !file.includes('index.js')) score++;
        else issues.push('Missing shebang line');
        
        if (hasDocstring) score++;
        else issues.push('Missing documentation comments');
        
        if (hasErrorHandling) score++;
        else issues.push('Missing error handling');
        
        if (hasProperExports) score++;
        else issues.push('Missing proper exports');
        
        // Check for console.log (should use console.error for servers)
        if (content.includes('console.log') && file.includes('mcp/servers/')) {
          issues.push('Use console.error instead of console.log for MCP servers');
        }
        
        if (score >= 3 && issues.length <= 1) {
          results.passed++;
        } else if (score >= 2) {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: `Code quality issues: ${issues.join(', ')}`,
          });
        } else {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `Poor code quality: ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateDocumentationStandards(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const docFiles = files.filter(f => f.endsWith('.md'));
    results.filesChecked = docFiles.length;
    
    for (const file of docFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check documentation standards
        const hasProperTitle = /^# [A-Z]/.test(content);
        const hasTableOfContents = /## Table of Contents|## Contents/.test(content) || content.length < 1000;
        const hasProperLinks = !/\[.*\]\(\)/.test(content); // No empty links
        const hasProperCodeBlocks = !content.includes('```\n') || content.includes('```javascript') || content.includes('```bash');
        
        let score = 0;
        const issues = [];
        
        if (hasProperTitle) score++;
        else issues.push('Title should start with capital letter');
        
        if (hasTableOfContents) score++;
        else issues.push('Long documents should have table of contents');
        
        if (hasProperLinks) score++;
        else issues.push('Found empty links');
        
        if (hasProperCodeBlocks) score++;
        else issues.push('Code blocks should specify language');
        
        if (score === 4) {
          results.passed++;
        } else if (score >= 2) {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: `Documentation issues: ${issues.join(', ')}`,
          });
        } else {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `Poor documentation: ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  // Integration Validation Methods
  async validateMCPCompatibility(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const mcpServerFiles = files.filter(f => f.includes('mcp/servers/') && f.endsWith('index.js'));
    results.filesChecked = mcpServerFiles.length;
    
    for (const file of mcpServerFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check for MCP requirements
        const hasStdioImport = content.includes('StdioServerTransport');
        const hasServerImport = content.includes('@modelcontextprotocol/sdk/server');
        const hasProperSetup = content.includes('setupHandlers') || content.includes('setRequestHandler');
        const hasRunMethod = content.includes('async run()') || content.includes('.run()');
        
        let score = 0;
        const issues = [];
        
        if (hasStdioImport) score++;
        else issues.push('Missing StdioServerTransport import');
        
        if (hasServerImport) score++;
        else issues.push('Missing MCP Server SDK import');
        
        if (hasProperSetup) score++;
        else issues.push('Missing request handlers setup');
        
        if (hasRunMethod) score++;
        else issues.push('Missing run method');
        
        if (score === 4) {
          results.passed++;
        } else {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `MCP compatibility issues: ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateChatModeIntegration(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const chatModeFiles = files.filter(f => f.includes('chatmodes') && f.endsWith('.md'));
    results.filesChecked = chatModeFiles.length;
    
    for (const file of chatModeFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check for chat mode requirements
        const hasRoleDefinition = /## Role|## Character|## Persona/.test(content);
        const hasResponseStyle = /## Response Style|## Communication/.test(content);
        const hasExamples = /## Example|## Sample/.test(content);
        const hasConstraints = /## Constraints|## Limitations|## Guidelines/.test(content);
        
        let score = 0;
        const issues = [];
        
        if (hasRoleDefinition) score++;
        else issues.push('Missing role/character definition');
        
        if (hasResponseStyle) score++;
        else issues.push('Missing response style guidelines');
        
        if (hasExamples) score++;
        else issues.push('Missing examples');
        
        if (hasConstraints) score++;
        else issues.push('Missing constraints/guidelines');
        
        if (score >= 3) {
          results.passed++;
        } else if (score >= 2) {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: `Chat mode issues: ${issues.join(', ')}`,
          });
        } else {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `Incomplete chat mode: ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateCrossReferences(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const allFiles = new Set(files.map(f => f.replace(this.rootPath + '/', '')));
    const markdownFiles = files.filter(f => f.endsWith('.md'));
    results.filesChecked = markdownFiles.length;
    
    for (const file of markdownFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Find all relative links
        const relativeLinks = content.match(/\[.*?\]\((?!https?:\/\/)([^)]+)\)/g) || [];
        
        let brokenLinks = 0;
        for (const link of relativeLinks) {
          const urlMatch = link.match(/\[.*?\]\(([^)]+)\)/);
          if (urlMatch) {
            const linkedFile = urlMatch[1];
            // Resolve relative path
            const resolvedPath = join(dirname(relativePath), linkedFile).replace(/\\/g, '/');
            
            if (!allFiles.has(resolvedPath) && !allFiles.has(linkedFile)) {
              brokenLinks++;
              results.details.push({
                file: relativePath,
                type: 'warning',
                message: `Broken link to: ${linkedFile}`,
              });
            }
          }
        }
        
        if (brokenLinks === 0) {
          results.passed++;
        } else {
          results.warnings++;
          results.warnings += brokenLinks - 1; // Subtract 1 since we already counted the file
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze file: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateVersionCompatibility(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const packageFiles = files.filter(f => f.endsWith('package.json'));
    results.filesChecked = packageFiles.length;
    
    for (const file of packageFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const packageData = JSON.parse(content);
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check version compatibility
        const nodeVersion = packageData.engines?.node;
        const mcpVersion = packageData.dependencies?.['@modelcontextprotocol/sdk'];
        
        const issues = [];
        
        if (nodeVersion) {
          if (!nodeVersion.includes('>=18')) {
            issues.push('Node.js version should be >=18.0.0');
          }
        } else if (file.includes('mcp/servers/')) {
          issues.push('Missing Node.js version requirement');
        }
        
        if (mcpVersion && mcpVersion.startsWith('^0.')) {
          issues.push('Using pre-release MCP version');
        }
        
        if (issues.length === 0) {
          results.passed++;
        } else {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: `Version compatibility: ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to parse package.json: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  // Performance Validation Methods
  async validateFileSizeLimits(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: files.length, details: [] };
    
    const limits = {
      '.md': 100 * 1024,    // 100KB for markdown files
      '.js': 200 * 1024,    // 200KB for JavaScript files  
      '.json': 50 * 1024,   // 50KB for JSON files
    };
    
    for (const file of files) {
      try {
        const stats = await fs.stat(file);
        const relativePath = file.replace(this.rootPath + '/', '');
        const ext = extname(file);
        const limit = limits[ext];
        
        if (limit && stats.size > limit) {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `File too large: ${stats.size} bytes (limit: ${limit} bytes)`,
          });
        } else if (limit && stats.size > limit * 0.8) {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: `File approaching size limit: ${stats.size} bytes`,
          });
        } else {
          results.passed++;
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to check file size: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateComplexityMetrics(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const jsFiles = files.filter(f => f.endsWith('.js'));
    results.filesChecked = jsFiles.length;
    
    for (const file of jsFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Simple complexity metrics
        const lines = content.split('\n').length;
        const functions = (content.match(/function\s+\w+|=>\s*{|async\s+\w+/g) || []).length;
        const conditionals = (content.match(/if\s*\(|switch\s*\(|for\s*\(|while\s*\(/g) || []).length;
        const complexity = conditionals + functions;
        
        const issues = [];
        
        if (lines > 1000) {
          issues.push(`File too long: ${lines} lines`);
        }
        
        if (functions > 50) {
          issues.push(`Too many functions: ${functions}`);
        }
        
        if (complexity > 100) {
          issues.push(`High complexity score: ${complexity}`);
        }
        
        if (issues.length === 0) {
          results.passed++;
        } else if (issues.length === 1) {
          results.warnings++;
          results.details.push({
            file: relativePath,
            type: 'warning',
            message: issues[0],
          });
        } else {
          results.errors++;
          results.details.push({
            file: relativePath,
            type: 'error',
            message: `Multiple complexity issues: ${issues.join(', ')}`,
          });
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze complexity: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async validateResourceEfficiency(files) {
    const results = { passed: 0, warnings: 0, errors: 0, filesChecked: 0, details: [] };
    
    const jsFiles = files.filter(f => f.endsWith('.js'));
    results.filesChecked = jsFiles.length;
    
    for (const file of jsFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const relativePath = file.replace(this.rootPath + '/', '');
        
        // Check for resource efficiency patterns
        const hasCaching = /cache|Cache/.test(content);
        const hasRateLimit = /rate.?limit|delay|setTimeout/.test(content);
        const hasErrorHandling = /try.*catch|catch.*error/s.test(content);
        const hasMemoryLeaks = content.includes('setInterval') && !content.includes('clearInterval');
        
        const issues = [];
        let score = 0;
        
        if (file.includes('mcp/servers/')) {
          if (hasCaching) score++;
          else issues.push('MCP server should implement caching');
          
          if (hasRateLimit) score++;
          else issues.push('MCP server should implement rate limiting');
          
          if (hasErrorHandling) score++;
          else issues.push('Missing proper error handling');
          
          if (hasMemoryLeaks) {
            issues.push('Potential memory leak: uncleared intervals');
          } else {
            score++;
          }
          
          if (score >= 3) {
            results.passed++;
          } else {
            results.warnings++;
            results.details.push({
              file: relativePath,
              type: 'warning',
              message: `Resource efficiency issues: ${issues.join(', ')}`,
            });
          }
        } else {
          // For non-MCP files, just check for obvious issues
          if (hasMemoryLeaks) {
            results.warnings++;
            results.details.push({
              file: relativePath,
              type: 'warning',
              message: 'Potential memory leak: uncleared intervals',
            });
          } else {
            results.passed++;
          }
        }
      } catch (error) {
        results.errors++;
        results.details.push({
          file: file.replace(this.rootPath + '/', ''),
          type: 'error',
          message: `Failed to analyze efficiency: ${error.message}`,
        });
      }
    }
    
    return results;
  }

  async generateValidationReport() {
    const timestamp = new Date().toISOString();
    const reportFile = join(this.reportsPath, `validation-report-${timestamp.split('T')[0]}.json`);
    
    const report = {
      timestamp,
      summary: this.metrics,
      categories: this.validationResults,
      recommendations: this.generateRecommendations(),
    };
    
    await fs.writeFile(reportFile, JSON.stringify(report, null, 2));
    
    // Also generate a human-readable report
    const readableReport = this.generateReadableReport(report);
    const readableFile = join(this.reportsPath, `validation-report-${timestamp.split('T')[0]}.md`);
    await fs.writeFile(readableFile, readableReport);
    
    console.log(`📊 Validation report saved to: ${reportFile}`);
    console.log(`📝 Readable report saved to: ${readableFile}`);
  }

  generateRecommendations() {
    const recommendations = [];
    
    // Analyze validation results for patterns
    const allDetails = this.validationResults.flatMap(r => r.results.details || []);
    const errorTypes = {};
    const warningTypes = {};
    
    allDetails.forEach(detail => {
      if (detail.type === 'error') {
        errorTypes[detail.message] = (errorTypes[detail.message] || 0) + 1;
      } else if (detail.type === 'warning') {
        warningTypes[detail.message] = (warningTypes[detail.message] || 0) + 1;
      }
    });
    
    // Generate recommendations based on common issues
    Object.entries(errorTypes)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .forEach(([issue, count]) => {
        recommendations.push({
          priority: 'high',
          category: 'error',
          issue,
          count,
          suggestion: this.getSuggestionForIssue(issue),
        });
      });
    
    Object.entries(warningTypes)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .forEach(([issue, count]) => {
        recommendations.push({
          priority: 'medium',
          category: 'warning',
          issue,
          count,
          suggestion: this.getSuggestionForIssue(issue),
        });
      });
    
    return recommendations;
  }

  getSuggestionForIssue(issue) {
    const suggestions = {
      'Missing main title': 'Add a descriptive # heading at the top of the file',
      'Missing code examples': 'Include practical code examples with ```language blocks',
      'File has invalid extension': 'Use .md for documentation, .js for scripts, .json for configuration',
      'Missing MCP SDK dependency': 'Add "@modelcontextprotocol/sdk": "^1.0.0" to package.json dependencies',
      'Missing error handling': 'Wrap API calls and file operations in try-catch blocks',
      'Line has trailing whitespace': 'Configure your editor to remove trailing whitespace on save',
      'Missing Node.js version requirement': 'Add "engines": {"node": ">=18.0.0"} to package.json',
      'Missing shebang line': 'Add #!/usr/bin/env node at the top of executable scripts',
    };
    
    return suggestions[issue] || 'Review the file and address the reported issue';
  }

  generateReadableReport(report) {
    const { timestamp, summary, categories, recommendations } = report;
    
    let md = `# Validation Report\n\n`;
    md += `**Generated**: ${timestamp}\n\n`;
    
    md += `## Summary\n\n`;
    md += `- **Total Files**: ${summary.totalFiles}\n`;
    md += `- **Validated Files**: ${summary.validatedFiles}\n`;
    md += `- **Passed**: ${summary.passed}\n`;
    md += `- **Warnings**: ${summary.warnings}\n`;
    md += `- **Errors**: ${summary.errors}\n`;
    md += `- **Success Rate**: ${((summary.passed / (summary.passed + summary.warnings + summary.errors)) * 100).toFixed(1)}%\n\n`;
    
    md += `## Validation Categories\n\n`;
    
    categories.forEach(category => {
      const { category: catName, rule, results } = category;
      md += `### ${catName} - ${rule}\n\n`;
      md += `- Passed: ${results.passed}\n`;
      md += `- Warnings: ${results.warnings}\n`;
      md += `- Errors: ${results.errors}\n`;
      
      if (results.details && results.details.length > 0) {
        md += `\n**Issues**:\n\n`;
        results.details.slice(0, 10).forEach(detail => {
          md += `- ${detail.type.toUpperCase()}: ${detail.file} - ${detail.message}\n`;
        });
        
        if (results.details.length > 10) {
          md += `- ... and ${results.details.length - 10} more\n`;
        }
      }
      md += `\n`;
    });
    
    if (recommendations.length > 0) {
      md += `## Recommendations\n\n`;
      
      recommendations.forEach((rec, index) => {
        md += `${index + 1}. **${rec.priority.toUpperCase()}**: ${rec.issue} (${rec.count} occurrences)\n`;
        md += `   - ${rec.suggestion}\n\n`;
      });
    }
    
    return md;
  }

  displayValidationSummary() {
    console.log('📋 Validation Summary:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`📁 Total Files:      ${this.metrics.totalFiles}`);
    console.log(`✅ Passed:           ${this.metrics.passed}`);
    console.log(`⚠️  Warnings:        ${this.metrics.warnings}`);
    console.log(`❌ Errors:           ${this.metrics.errors}`);
    
    const successRate = ((this.metrics.passed / (this.metrics.passed + this.metrics.warnings + this.metrics.errors)) * 100);
    console.log(`📊 Success Rate:     ${successRate.toFixed(1)}%`);
    
    if (this.metrics.errors > 0) {
      console.log('\n🚨 Critical issues found that should be addressed immediately.');
    } else if (this.metrics.warnings > 0) {
      console.log('\n⚠️  Some warnings found that should be reviewed.');
    } else {
      console.log('\n🎉 All validations passed successfully!');
    }
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const validator = new MetaInstructionValidator({
    rootPath: process.cwd(),
  });
  
  validator.validateProject()
    .then(() => {
      process.exit(validator.metrics.errors > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('Validation failed:', error);
      process.exit(1);
    });
}

export { MetaInstructionValidator };
