#!/usr/bin/env node

/**
 * Template Validation System
 * Comprehensive validation for instruction templates, content standards, and integration testing
 */

import { promises as fs } from 'fs';
import { join, extname, dirname, basename } from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

class TemplateValidationSystem {
  constructor(options = {}) {
    this.rootPath = options.rootPath || process.cwd();
    this.templatesPath = join(this.rootPath, '.github', 'chatmodes');
    this.promptsPath = join(this.rootPath, '.github', 'prompts');
    this.validationPath = join(this.rootPath, '.github', 'validation');
    this.reportsPath = join(this.validationPath, 'reports', 'templates');

    this.templateSchemas = new Map();
    this.validationResults = [];
    this.integrationTests = [];
    this.performanceMetrics = {};

    this.metrics = {
      templatesValidated: 0,
      schemasValidated: 0,
      integrationTestsPassed: 0,
      complianceChecksPassed: 0,
      errors: 0,
      warnings: 0,
    };

    this.setupTemplateSchemas();
  }

  setupTemplateSchemas() {
    // Define expected template structures
    this.templateSchemas.set('chat-mode', {
      requiredSections: [
        'title',
        'description',
        'role',
        'responseStyle',
        'examples'
      ],
      optionalSections: [
        'constraints',
        'context',
        'limitations',
        'usage',
        'variables'
      ],
      structure: {
        title: { pattern: /^# .+/m, required: true },
        description: { pattern: /## Description/m, required: true },
        role: { pattern: /## Role/m, required: true },
        responseStyle: { pattern: /## Response Style/m, required: true },
        examples: { pattern: /## Examples/m, required: true },
        constraints: { pattern: /## (?:Constraints|Limitations|Guidelines)/m, required: false }
      }
    });

    this.templateSchemas.set('prompt', {
      requiredSections: [
        'title'
      ],
      optionalSections: [
        'description',
        'usage',
        'parameters',
        'examples',
        'output',
        'methodology',
        'approach',
        'guidelines'
      ],
      structure: {
        title: { pattern: /^# .+/m, required: true },
        description: { pattern: /## (?:Description|Overview|Purpose)/m, required: false },
        usage: { pattern: /## (?:Usage|How to Use)/m, required: false },
        parameters: { pattern: /## (?:Parameters|Arguments|Variables)/m, required: false },
        examples: { pattern: /## (?:Examples?|Sample)/m, required: false },
        output: { pattern: /## (?:Output|Result|Response)/m, required: false },
        methodology: { pattern: /## (?:Methodology|Approach)/m, required: false },
        guidelines: { pattern: /## (?:Guidelines|Rules|Principles)/m, required: false }
      }
    });

    this.templateSchemas.set('mcp-server', {
      requiredSections: [
        'title'
      ],
      optionalSections: [
        'description',
        'overview',
        'installation',
        'configuration',
        'usage',
        'api',
        'examples',
        'troubleshooting',
        'development',
        'testing'
      ],
      structure: {
        title: { pattern: /^# .+/m, required: true },
        description: { pattern: /## (?:Description|Overview)/m, required: false },
        installation: { pattern: /## (?:Installation|Setup)/m, required: false },
        configuration: { pattern: /## (?:Configuration|Config)/m, required: false },
        usage: { pattern: /## (?:Usage|Getting Started)/m, required: false },
        api: { pattern: /## (?:API|Interface|Methods)/m, required: false }
      }
    });

    this.templateSchemas.set('documentation', {
      requiredSections: [
        'title'
      ],
      optionalSections: [
        'overview',
        'content',
        'tableOfContents',
        'prerequisites',
        'examples',
        'references',
        'summary'
      ],
      structure: {
        title: { pattern: /^# .+/m, required: true },
        overview: { pattern: /## (?:Overview|Introduction|Summary)/m, required: false },
        content: { pattern: /## .+/m, required: false, multiple: true }
      }
    });

    // Add JSON file type schemas
    this.templateSchemas.set('config-file', {
      requiredSections: [],
      optionalSections: [],
      structure: {
        validJson: { required: true }
      }
    });

    this.templateSchemas.set('package-file', {
      requiredSections: [],
      optionalSections: [],
      structure: {
        validJson: { required: true }
      }
    });

    this.templateSchemas.set('json-file', {
      requiredSections: [],
      optionalSections: [],
      structure: {
        validJson: { required: true }
      }
    });
  }

  async validateTemplateSystem() {
    console.log('🔧 Starting Template Validation System...\n');

    try {
      // Ensure reports directory exists
      await fs.mkdir(this.reportsPath, { recursive: true });

      // Run validation phases
      await this.validateTemplateStructures();
      await this.validateContentStandards();
      await this.runIntegrationTests();
      await this.performQualityAssurance();

      // Generate comprehensive report
      await this.generateValidationReport();

      // Display summary
      this.displayValidationSummary();

      return {
        success: this.metrics.errors === 0,
        metrics: this.metrics,
        results: this.validationResults
      };

    } catch (error) {
      console.error('❌ Template validation failed:', error.message);
      throw error;
    }
  }

  async validateTemplateStructures() {
    console.log('📋 Validating Template Structures...');

    try {
      // Discover template files
      const templateFiles = await this.discoverTemplateFiles();
      console.log(`  Found ${templateFiles.length} template files`);

      for (const templateFile of templateFiles) {
        await this.validateTemplateStructure(templateFile);
      }

      console.log(`  ✅ Template structure validation complete\n`);
    } catch (error) {
      console.log(`  ❌ Template structure validation failed: ${error.message}\n`);
      this.metrics.errors++;
    }
  }

  async discoverTemplateFiles() {
    const files = [];
    const searchPaths = [
      join(this.rootPath, '.github', 'chatmodes'),
      join(this.rootPath, '.github', 'prompts'),
      join(this.rootPath, '.github', 'mcp'),
      join(this.rootPath, '.github', 'validation')
    ];

    for (const searchPath of searchPaths) {
      try {
        await this.scanForTemplates(searchPath, files);
      } catch (error) {
        // Directory might not exist, continue
      }
    }

    return files.filter(file => file.endsWith('.md') || file.endsWith('.json'));
  }

  async scanForTemplates(dirPath, files) {
    try {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = join(dirPath, entry.name);

        if (entry.isDirectory()) {
          await this.scanForTemplates(fullPath, files);
        } else if (entry.isFile()) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Directory doesn't exist or can't be read
      return;
    }
  }

  async validateTemplateStructure(templateFile) {
    try {
      const content = await fs.readFile(templateFile, 'utf8');
      const relativePath = templateFile.replace(this.rootPath + '/', '');

      // Determine template type
      const templateType = this.determineTemplateType(templateFile, content);
      const schema = this.templateSchemas.get(templateType);

      if (!schema) {
        this.validationResults.push({
          type: 'template-structure',
          file: relativePath,
          status: 'warning',
          message: `Unknown template type: ${templateType}`
        });
        this.metrics.warnings++;
        return;
      }

      // Validate structure against schema
      const structureValidation = this.validateAgainstSchema(content, schema);

      if (structureValidation.isValid) {
        this.validationResults.push({
          type: 'template-structure',
          file: relativePath,
          status: 'passed',
          templateType,
          message: 'Template structure is valid'
        });
        this.metrics.templatesValidated++;
      } else {
        this.validationResults.push({
          type: 'template-structure',
          file: relativePath,
          status: 'error',
          templateType,
          message: `Structure validation failed: ${structureValidation.errors.join(', ')}`,
          errors: structureValidation.errors
        });
        this.metrics.errors++;
      }

    } catch (error) {
      this.validationResults.push({
        type: 'template-structure',
        file: templateFile.replace(this.rootPath + '/', ''),
        status: 'error',
        message: `Failed to validate template: ${error.message}`
      });
      this.metrics.errors++;
    }
  }

  determineTemplateType(filePath, content) {
    const fileName = basename(filePath).toLowerCase();
    const dirName = basename(dirname(filePath)).toLowerCase();

    // Handle JSON files first
    if (fileName.endsWith('.json')) {
      // Configuration files
      if (fileName.includes('config') || fileName.includes('validation') || fileName.includes('quality')) {
        return 'config-file';
      }
      // Package.json files
      if (fileName === 'package.json') {
        return 'package-file';
      }
      // Default JSON file type
      return 'json-file';
    }

    // Determine type based on file extension and location
    if (fileName.endsWith('.chatmode.md') || dirName === 'chatmodes') {
      return 'chat-mode';
    }

    if (fileName.endsWith('.prompt.md') || dirName === 'prompts') {
      return 'prompt';
    }

    if (filePath.includes('mcp') && content.includes('MCP')) {
      return 'mcp-server';
    }

    // Analyze content for patterns
    if (content.includes('## Role') || content.includes('## Character')) {
      return 'chat-mode';
    }

    if (content.includes('## Parameters') || content.includes('## Arguments')) {
      return 'prompt';
    }

    if (content.includes('## Installation') || content.includes('## API')) {
      return 'mcp-server';
    }

    return 'documentation';
  }

  validateAgainstSchema(content, schema) {
    const result = {
      isValid: true,
      errors: [],
      warnings: [],
      coverage: 0
    };

    // Handle JSON file validation
    if (schema.structure && schema.structure.validJson) {
      try {
        JSON.parse(content);
        result.isValid = true;
        result.coverage = 1.0;
        return result;
      } catch (error) {
        result.isValid = false;
        result.errors.push(`Invalid JSON syntax: ${error.message}`);
        return result;
      }
    }

    let sectionsFound = 0;
    const totalRequired = schema.requiredSections.length;

    // Check required sections using schema patterns
    for (const sectionName of schema.requiredSections) {
      const sectionDef = schema.structure[sectionName];
      if (sectionDef && sectionDef.pattern) {
        const matches = sectionDef.pattern.test(content);
        if (matches) {
          sectionsFound++;
        } else {
          result.isValid = false;
          result.errors.push(`Missing required section: ${sectionName}`);
        }
      }
    }

    // Count sections for warnings
    const lines = content.split('\n');
    let headingCount = 0;

    for (const line of lines) {
      if (line.startsWith('## ')) {
        headingCount++;
      }
    }

    if (headingCount < 2 && totalRequired > 0) {
      result.warnings.push('Template should have at least 2 sections');
    }

    result.coverage = totalRequired > 0 ? sectionsFound / totalRequired : 1.0;

    return result;
  }

  async validateContentStandards() {
    console.log('📝 Validating Content Standards...');

    try {
      const markdownFiles = await this.getMarkdownFiles();

      for (const file of markdownFiles) {
        await this.validateContentStandard(file);
      }

      console.log(`  ✅ Content standards validation complete\n`);
    } catch (error) {
      console.log(`  ❌ Content standards validation failed: ${error.message}\n`);
      this.metrics.errors++;
    }
  }

  async getMarkdownFiles() {
    const files = await this.discoverTemplateFiles();
    return files.filter(file => file.endsWith('.md'));
  }

  async validateContentStandard(file) {
    try {
      const content = await fs.readFile(file, 'utf8');
      const relativePath = file.replace(this.rootPath + '/', '');

      const standards = {
        accessibility: this.validateAccessibility(content),
        formatting: this.validateFormatting(content),
        style: this.validateStyleGuide(content),
        internationalization: this.validateI18n(content)
      };

      const overallScore = Object.values(standards).reduce((sum, std) => sum + std.score, 0) / 4;
      const issues = Object.values(standards).flatMap(std => std.issues);

      if (overallScore >= 0.8) {
        this.validationResults.push({
          type: 'content-standards',
          file: relativePath,
          status: 'passed',
          score: overallScore,
          message: 'Content meets quality standards'
        });
        this.metrics.complianceChecksPassed++;
      } else if (overallScore >= 0.6) {
        this.validationResults.push({
          type: 'content-standards',
          file: relativePath,
          status: 'warning',
          score: overallScore,
          message: `Content quality issues: ${issues.slice(0, 3).join(', ')}`,
          issues: issues
        });
        this.metrics.warnings++;
      } else {
        this.validationResults.push({
          type: 'content-standards',
          file: relativePath,
          status: 'error',
          score: overallScore,
          message: `Poor content quality: ${issues.slice(0, 5).join(', ')}`,
          issues: issues
        });
        this.metrics.errors++;
      }

    } catch (error) {
      this.validationResults.push({
        type: 'content-standards',
        file: file.replace(this.rootPath + '/', ''),
        status: 'error',
        message: `Failed to validate content: ${error.message}`
      });
      this.metrics.errors++;
    }
  }

  validateAccessibility(content) {
    const issues = [];
    let score = 1.0;

    // Check for proper heading hierarchy
    const headings = content.match(/^#+\s+.+$/gm) || [];
    let previousLevel = 0;

    for (const heading of headings) {
      const level = heading.match(/^#+/)[0].length;
      if (level > previousLevel + 1) {
        issues.push('Heading hierarchy skips levels');
        score -= 0.2;
        break;
      }
      previousLevel = level;
    }

    // Check for alt text on images
    const images = content.match(/!\[.*?\]\(.+?\)/g) || [];
    for (const image of images) {
      const altText = image.match(/!\[(.*?)\]/)[1];
      if (!altText || altText.trim() === '') {
        issues.push('Image missing alt text');
        score -= 0.1;
      }
    }

    // Check for descriptive link text
    const links = content.match(/\[.*?\]\(.+?\)/g) || [];
    for (const link of links) {
      const linkText = link.match(/\[(.*?)\]/)[1];
      if (linkText.toLowerCase().includes('click here') || linkText.toLowerCase().includes('read more')) {
        issues.push('Non-descriptive link text');
        score -= 0.1;
      }
    }

    return { score: Math.max(0, score), issues };
  }

  validateFormatting(content) {
    const issues = [];
    let score = 1.0;

    // Check for consistent code block formatting
    const codeBlocks = content.match(/```[\s\S]*?```/g) || [];
    for (const block of codeBlocks) {
      if (!block.match(/```\w+/)) {
        issues.push('Code block missing language specification');
        score -= 0.1;
      }
    }

    // Check for proper list formatting
    const lines = content.split('\n');
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      if (line.match(/^[-*+]\s/) || line.match(/^\d+\.\s/)) {
        if (!inList && i > 0 && lines[i - 1].trim() !== '') {
          issues.push('List not preceded by blank line');
          score -= 0.05;
        }
        inList = true;
      } else if (inList && line.trim() === '') {
        inList = false;
      } else if (inList && !line.match(/^\s/) && line.trim() !== '') {
        if (i < lines.length - 1 && lines[i + 1].trim() !== '') {
          issues.push('List not followed by blank line');
          score -= 0.05;
        }
        inList = false;
      }
    }

    // Check for proper table formatting (ignore fenced code blocks)
    const textNoCode = content.replace(/```[\s\S]*?```/g, '');
    const tables = textNoCode.match(/\|.*\|/g) || [];
    if (tables.length > 0) {
      const tableBlocks = textNoCode.split('\n\n').filter(block => block.includes('|'));
      for (const table of tableBlocks) {
        const tableLines = table.split('\n').filter(line => line.includes('|'));
        if (tableLines.length < 3) {
          issues.push('Incomplete table formatting');
          score -= 0.1;
        }
      }
    }

    return { score: Math.max(0, score), issues };
  }

  validateStyleGuide(content) {
    const issues = [];
    let score = 1.0;

  // Check sentence length (ignore fenced code blocks)
  const textNoCode = content.replace(/```[\s\S]*?```/g, '');
  const sentences = textNoCode.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const longSentences = sentences.filter(s => s.split(/\s+/).length > 25);

    if (longSentences.length > 0) {
      issues.push(`${longSentences.length} sentences are too long`);
      score -= 0.1 * (longSentences.length / sentences.length);
    }

    // Check for passive voice (simple heuristic)
    const passiveIndicators = /\b(is|are|was|were|been|being)\s+\w+ed\b/gi;
    const passiveMatches = content.match(passiveIndicators) || [];
    const passiveRatio = passiveMatches.length / sentences.length;

    if (passiveRatio > 0.3) {
      issues.push('Excessive use of passive voice');
      score -= 0.2;
    }

    // Check for consistent terminology
    const words = content.toLowerCase().split(/\W+/);
    const terminology = {
      'github copilot': words.filter(w => w === 'copilot').length,
      'mcp': words.filter(w => w === 'mcp').length,
      'api': words.filter(w => w === 'api').length
    };

    // Basic consistency check
    if (terminology['github copilot'] > 0 && words.includes('copilot') && !content.includes('GitHub Copilot')) {
      issues.push('Inconsistent terminology for GitHub Copilot');
      score -= 0.1;
    }

    return { score: Math.max(0, score), issues };
  }

  validateI18n(content) {
    const issues = [];
    let score = 1.0;

    // Check for hardcoded dates (basic check)
    const datePatterns = [
      /\d{1,2}\/\d{1,2}\/\d{4}/g,  // MM/DD/YYYY
      /\d{1,2}-\d{1,2}-\d{4}/g,    // MM-DD-YYYY
      /\w+\s+\d{1,2},?\s+\d{4}/g   // Month DD, YYYY
    ];

    for (const pattern of datePatterns) {
      if (pattern.test(content)) {
        issues.push('Hardcoded date format may not be internationally compatible');
        score -= 0.1;
        break;
      }
    }

  // Check for currency symbols (ignore fenced code blocks)
  const textNoCode = content.replace(/```[\s\S]*?```/g, '');
  if (/[$£€¥]/.test(textNoCode)) {
      issues.push('Hardcoded currency symbols');
      score -= 0.1;
    }

  // Check for units without international alternatives (ignore fenced code blocks)
  const imperialUnits = /\b\d+\s*(feet|ft|inches|in|pounds|lbs|fahrenheit|°f)\b/gi;
  if (imperialUnits.test(textNoCode)) {
      issues.push('Imperial units without metric alternatives');
      score -= 0.1;
    }

    return { score: Math.max(0, score), issues };
  }

  async runIntegrationTests() {
    console.log('🔗 Running Integration Tests...');

    try {
      await this.testMCPServerIntegration();
      await this.testChatModeIntegration();
      await this.testTemplateGeneration();
      await this.testEndToEndWorkflow();

      console.log(`  ✅ Integration tests complete\n`);
    } catch (error) {
      console.log(`  ❌ Integration tests failed: ${error.message}\n`);
      this.metrics.errors++;
    }
  }

  async testMCPServerIntegration() {
    const mcpServers = await this.findMCPServers();

    for (const server of mcpServers) {
      await this.testMCPServer(server);
    }
  }

  async findMCPServers() {
    const servers = [];
    const mcpPath = join(this.rootPath, '.github', 'mcp', 'servers');

    try {
      const serverDirs = await fs.readdir(mcpPath, { withFileTypes: true });

      for (const dir of serverDirs) {
        if (dir.isDirectory()) {
          const serverPath = join(mcpPath, dir.name);
          const indexFile = join(serverPath, 'index.js');

          try {
            await fs.access(indexFile);
            servers.push({
              name: dir.name,
              path: serverPath,
              indexFile: indexFile
            });
          } catch (error) {
            // No index.js file
          }
        }
      }
    } catch (error) {
      // MCP servers directory doesn't exist
    }

    return servers;
  }

  async testMCPServer(server) {
    try {
      const content = await fs.readFile(server.indexFile, 'utf8');

      // Test basic MCP requirements
      const tests = {
        hasStdioTransport: content.includes('StdioServerTransport'),
        hasServerImport: content.includes('@modelcontextprotocol/sdk/server'),
        hasRequestHandlers: content.includes('setRequestHandler'),
        hasRunMethod: /async\s+run\s*\(\s*\)/.test(content) || content.includes('.run()'),
        hasErrorHandling: /try\s*{[\s\S]*?}\s*catch/.test(content)
      };

      const passedTests = Object.values(tests).filter(Boolean).length;
      const totalTests = Object.keys(tests).length;

      if (passedTests === totalTests) {
        this.integrationTests.push({
          type: 'mcp-server',
          name: server.name,
          status: 'passed',
          message: 'MCP server integration tests passed'
        });
        this.metrics.integrationTestsPassed++;
      } else {
        const failedTests = Object.entries(tests)
          .filter(([, passed]) => !passed)
          .map(([test]) => test);

        this.integrationTests.push({
          type: 'mcp-server',
          name: server.name,
          status: 'failed',
          message: `MCP server tests failed: ${failedTests.join(', ')}`,
          failedTests
        });
        this.metrics.errors++;
      }

    } catch (error) {
      this.integrationTests.push({
        type: 'mcp-server',
        name: server.name,
        status: 'error',
        message: `Failed to test MCP server: ${error.message}`
      });
      this.metrics.errors++;
    }
  }

  async testChatModeIntegration() {
    const chatModes = await this.findChatModes();

    for (const chatMode of chatModes) {
      await this.testChatMode(chatMode);
    }
  }

  async findChatModes() {
    const chatModes = [];
    const chatModesPath = join(this.rootPath, '.github', 'chatmodes');

    try {
      const files = await fs.readdir(chatModesPath);

      for (const file of files) {
        if (file.endsWith('.md')) {
          chatModes.push({
            name: file.replace('.md', ''),
            path: join(chatModesPath, file)
          });
        }
      }
    } catch (error) {
      // Chat modes directory doesn't exist
    }

    return chatModes;
  }

  async testChatMode(chatMode) {
    try {
      const content = await fs.readFile(chatMode.path, 'utf8');

      // Test chat mode requirements
      const tests = {
        hasRole: /## (?:Role|Character|Persona)/.test(content),
        hasResponseStyle: /## (?:Response Style|Communication)/.test(content),
        hasExamples: /## (?:Examples?|Sample)/.test(content),
        hasConstraints: /## (?:Constraints|Limitations|Guidelines)/.test(content),
        hasPersonaConsistency: this.testPersonaConsistency(content)
      };

      const passedTests = Object.values(tests).filter(Boolean).length;
      const totalTests = Object.keys(tests).length;

      if (passedTests >= totalTests - 1) { // Allow one failure
        this.integrationTests.push({
          type: 'chat-mode',
          name: chatMode.name,
          status: 'passed',
          message: 'Chat mode integration tests passed'
        });
        this.metrics.integrationTestsPassed++;
      } else {
        const failedTests = Object.entries(tests)
          .filter(([, passed]) => !passed)
          .map(([test]) => test);

        this.integrationTests.push({
          type: 'chat-mode',
          name: chatMode.name,
          status: 'failed',
          message: `Chat mode tests failed: ${failedTests.join(', ')}`,
          failedTests
        });
        this.metrics.warnings++;
      }

    } catch (error) {
      this.integrationTests.push({
        type: 'chat-mode',
        name: chatMode.name,
        status: 'error',
        message: `Failed to test chat mode: ${error.message}`
      });
      this.metrics.errors++;
    }
  }

  testPersonaConsistency(content) {
    // Simple consistency check - look for consistent tone and style
    const sections = content.split(/^## /m);

    if (sections.length < 3) return false;

    // Check for consistent voice (first person, second person, etc.)
    const firstPersonWords = ['I', 'me', 'my', 'mine'];
    const secondPersonWords = ['you', 'your', 'yours'];

    let firstPersonCount = 0;
    let secondPersonCount = 0;

    sections.forEach(section => {
      const words = section.toLowerCase().split(/\W+/);
      firstPersonCount += firstPersonWords.filter(word => words.includes(word)).length;
      secondPersonCount += secondPersonWords.filter(word => words.includes(word)).length;
    });

    // Should be consistently one style or the other
    return Math.abs(firstPersonCount - secondPersonCount) > Math.min(firstPersonCount, secondPersonCount);
  }

  async testTemplateGeneration() {
    // Test that templates can be properly instantiated
    const templateFiles = await this.getMarkdownFiles();

    for (const templateFile of templateFiles) {
      if (templateFile.includes('template')) {
        await this.testTemplateInstantiation(templateFile);
      }
    }
  }

  async testTemplateInstantiation(templateFile) {
    try {
      const content = await fs.readFile(templateFile, 'utf8');
      const relativePath = templateFile.replace(this.rootPath + '/', '');

      // Look for template variables (basic pattern)
      const variables = content.match(/\{\{[^}]+\}\}/g) || [];
      const placeholders = content.match(/\[.*?\]/g) || [];

      // Test variable replacement
      let testContent = content;
      variables.forEach((variable, index) => {
        testContent = testContent.replace(variable, `test_value_${index}`);
      });

      placeholders.forEach((placeholder, index) => {
        if (placeholder.includes('TODO') || placeholder.includes('REPLACE')) {
          testContent = testContent.replace(placeholder, `test_placeholder_${index}`);
        }
      });

      // Check if instantiated template is valid
      const hasValidStructure = /^# .+/.test(testContent) && /## .+/.test(testContent);

      if (hasValidStructure) {
        this.integrationTests.push({
          type: 'template-generation',
          file: relativePath,
          status: 'passed',
          message: 'Template instantiation test passed'
        });
        this.metrics.integrationTestsPassed++;
      } else {
        this.integrationTests.push({
          type: 'template-generation',
          file: relativePath,
          status: 'failed',
          message: 'Template instantiation produces invalid structure'
        });
        this.metrics.warnings++;
      }

    } catch (error) {
      this.integrationTests.push({
        type: 'template-generation',
        file: templateFile.replace(this.rootPath + '/', ''),
        status: 'error',
        message: `Template instantiation test failed: ${error.message}`
      });
      this.metrics.errors++;
    }
  }

  async testEndToEndWorkflow() {
    // Test complete workflow from template to instruction
    try {
      const workflowTests = [
        this.testChatModeWorkflow(),
        this.testPromptWorkflow(),
        this.testMCPWorkflow()
      ];

      const results = await Promise.allSettled(workflowTests);

      results.forEach((result, index) => {
        const workflowType = ['chat-mode', 'prompt', 'mcp'][index];

        if (result.status === 'fulfilled' && result.value) {
          this.integrationTests.push({
            type: 'end-to-end',
            workflow: workflowType,
            status: 'passed',
            message: `${workflowType} workflow test passed`
          });
          this.metrics.integrationTestsPassed++;
        } else {
          this.integrationTests.push({
            type: 'end-to-end',
            workflow: workflowType,
            status: 'failed',
            message: `${workflowType} workflow test failed`
          });
          this.metrics.warnings++;
        }
      });

    } catch (error) {
      this.integrationTests.push({
        type: 'end-to-end',
        status: 'error',
        message: `End-to-end workflow tests failed: ${error.message}`
      });
      this.metrics.errors++;
    }
  }

  async testChatModeWorkflow() {
    // Test that chat modes can be discovered and used
    const chatModes = await this.findChatModes();
    return chatModes.length > 0;
  }

  async testPromptWorkflow() {
    // Test that prompts can be discovered and used
    const prompts = await this.findPrompts();
    return prompts.length > 0;
  }

  async findPrompts() {
    const prompts = [];
    const promptsPath = join(this.rootPath, '.github', 'prompts');

    try {
      const files = await fs.readdir(promptsPath);

      for (const file of files) {
        if (file.endsWith('.md')) {
          prompts.push({
            name: file.replace('.md', ''),
            path: join(promptsPath, file)
          });
        }
      }
    } catch (error) {
      // Prompts directory doesn't exist
    }

    return prompts;
  }

  async testMCPWorkflow() {
    // Test that MCP servers can be discovered and configured
    const mcpServers = await this.findMCPServers();
    const mcpConfig = await this.findMCPConfig();

    return mcpServers.length > 0 && mcpConfig;
  }

  async findMCPConfig() {
    const configPath = join(this.rootPath, '.github', 'mcp', 'mcp-servers.json');

    try {
      await fs.access(configPath);
      return true;
    } catch (error) {
      return false;
    }
  }

  async performQualityAssurance() {
    console.log('✅ Performing Quality Assurance...');

    try {
      await this.runPerformanceTests();
      await this.generateQualityMetrics();
      await this.validateCompliance();

      console.log(`  ✅ Quality assurance complete\n`);
    } catch (error) {
      console.log(`  ❌ Quality assurance failed: ${error.message}\n`);
      this.metrics.errors++;
    }
  }

  async runPerformanceTests() {
    const startTime = Date.now();

    // Test template processing performance
    const templateFiles = await this.getMarkdownFiles();
    const processingTimes = [];

    for (const file of templateFiles) {
      const fileStart = Date.now();
      try {
        await fs.readFile(file, 'utf8');
        processingTimes.push(Date.now() - fileStart);
      } catch (error) {
        // File processing failed
      }
    }

    const totalTime = Date.now() - startTime;
    const avgProcessingTime = processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length;

    this.performanceMetrics = {
      totalValidationTime: totalTime,
      averageFileProcessingTime: avgProcessingTime,
      filesProcessed: processingTimes.length,
      throughput: processingTimes.length / (totalTime / 1000)
    };
  }

  async generateQualityMetrics() {
    const totalValidations = this.validationResults.length + this.integrationTests.length;
    const passedValidations = this.validationResults.filter(r => r.status === 'passed').length +
                             this.integrationTests.filter(t => t.status === 'passed').length;

    this.qualityMetrics = {
      overallScore: totalValidations > 0 ? passedValidations / totalValidations : 0,
      validationCoverage: this.metrics.templatesValidated / Math.max(1, this.metrics.templatesValidated + this.metrics.errors),
      complianceRate: this.metrics.complianceChecksPassed / Math.max(1, this.metrics.complianceChecksPassed + this.metrics.warnings),
      integrationSuccess: this.metrics.integrationTestsPassed / Math.max(1, this.metrics.integrationTestsPassed + this.metrics.errors)
    };
  }

  async validateCompliance() {
    // Check overall system compliance
    const complianceChecks = {
      templateStructureCompliance: this.validationResults.filter(r =>
        r.type === 'template-structure' && r.status === 'passed'
      ).length > 0,

      contentStandardsCompliance: this.validationResults.filter(r =>
        r.type === 'content-standards' && r.status === 'passed'
      ).length > 0,

      integrationTestsCompliance: this.integrationTests.filter(t =>
        t.status === 'passed'
      ).length > 0,

      performanceCompliance: this.performanceMetrics.averageFileProcessingTime < 100 // ms
    };

    const complianceScore = Object.values(complianceChecks).filter(Boolean).length /
                           Object.keys(complianceChecks).length;

    this.complianceStatus = {
      score: complianceScore,
      checks: complianceChecks,
      isCompliant: complianceScore >= 0.75
    };
  }

  async generateValidationReport() {
    const timestamp = new Date().toISOString();
    const reportFile = join(this.reportsPath, `template-validation-${timestamp.split('T')[0]}.json`);

    const report = {
      timestamp,
      summary: this.metrics,
      qualityMetrics: this.qualityMetrics,
      performanceMetrics: this.performanceMetrics,
      complianceStatus: this.complianceStatus,
      validationResults: this.validationResults,
      integrationTests: this.integrationTests,
      recommendations: this.generateRecommendations()
    };

    await fs.writeFile(reportFile, JSON.stringify(report, null, 2));

    // Generate human-readable report
    const readableReport = this.generateReadableReport(report);
    const readableFile = join(this.reportsPath, `template-validation-${timestamp.split('T')[0]}.md`);
    await fs.writeFile(readableFile, readableReport);

    console.log(`📊 Template validation report saved to: ${reportFile}`);
    console.log(`📝 Readable report saved to: ${readableFile}`);
  }

  generateRecommendations() {
    const recommendations = [];

    // Analyze validation results for patterns
    const structureErrors = this.validationResults.filter(r =>
      r.type === 'template-structure' && r.status === 'error'
    );

    const contentIssues = this.validationResults.filter(r =>
      r.type === 'content-standards' && r.status !== 'passed'
    );

    const integrationFailures = this.integrationTests.filter(t =>
      t.status === 'failed' || t.status === 'error'
    );

    // Generate recommendations based on common issues
    if (structureErrors.length > 0) {
      recommendations.push({
        priority: 'high',
        category: 'structure',
        issue: 'Template structure validation failures',
        count: structureErrors.length,
        suggestion: 'Review template schemas and ensure all required sections are present'
      });
    }

    if (contentIssues.length > 0) {
      recommendations.push({
        priority: 'medium',
        category: 'content',
        issue: 'Content quality issues',
        count: contentIssues.length,
        suggestion: 'Improve content clarity, formatting, and accessibility'
      });
    }

    if (integrationFailures.length > 0) {
      recommendations.push({
        priority: 'high',
        category: 'integration',
        issue: 'Integration test failures',
        count: integrationFailures.length,
        suggestion: 'Fix integration issues with MCP servers and chat modes'
      });
    }

    // Performance recommendations
    if (this.performanceMetrics.averageFileProcessingTime > 100) {
      recommendations.push({
        priority: 'low',
        category: 'performance',
        issue: 'Slow template processing',
        suggestion: 'Optimize template validation for better performance'
      });
    }

    return recommendations;
  }

  generateReadableReport(report) {
    const { timestamp, summary, qualityMetrics, performanceMetrics, complianceStatus } = report;

    let md = `# Template Validation Report\n\n`;
    md += `**Generated**: ${timestamp}\n\n`;

    md += `## Executive Summary\n\n`;
    md += `- **Overall Quality Score**: ${(qualityMetrics.overallScore * 100).toFixed(1)}%\n`;
    md += `- **Compliance Status**: ${complianceStatus.isCompliant ? '✅ Compliant' : '❌ Non-compliant'}\n`;
    md += `- **Templates Validated**: ${summary.templatesValidated}\n`;
    md += `- **Integration Tests Passed**: ${summary.integrationTestsPassed}\n`;
    md += `- **Total Errors**: ${summary.errors}\n`;
    md += `- **Total Warnings**: ${summary.warnings}\n\n`;

    md += `## Quality Metrics\n\n`;
    md += `- **Validation Coverage**: ${(qualityMetrics.validationCoverage * 100).toFixed(1)}%\n`;
    md += `- **Compliance Rate**: ${(qualityMetrics.complianceRate * 100).toFixed(1)}%\n`;
    md += `- **Integration Success**: ${(qualityMetrics.integrationSuccess * 100).toFixed(1)}%\n\n`;

    md += `## Performance Metrics\n\n`;
    md += `- **Total Validation Time**: ${performanceMetrics.totalValidationTime}ms\n`;
    md += `- **Average Processing Time**: ${performanceMetrics.averageFileProcessingTime.toFixed(2)}ms\n`;
    md += `- **Files Processed**: ${performanceMetrics.filesProcessed}\n`;
    md += `- **Throughput**: ${performanceMetrics.throughput.toFixed(2)} files/second\n\n`;

    if (report.recommendations && report.recommendations.length > 0) {
      md += `## Recommendations\n\n`;

      report.recommendations.forEach((rec, index) => {
        md += `${index + 1}. **${rec.priority.toUpperCase()}**: ${rec.issue}\n`;
        md += `   - ${rec.suggestion}\n`;
        if (rec.count) {
          md += `   - Affects ${rec.count} items\n`;
        }
        md += `\n`;
      });
    }

    return md;
  }

  displayValidationSummary() {
    console.log('📋 Template Validation Summary:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`📋 Templates Validated:    ${this.metrics.templatesValidated}`);
    console.log(`🔧 Schemas Validated:      ${this.metrics.schemasValidated}`);
    console.log(`🔗 Integration Tests:      ${this.metrics.integrationTestsPassed} passed`);
    console.log(`✅ Compliance Checks:      ${this.metrics.complianceChecksPassed} passed`);
    console.log(`⚠️  Warnings:              ${this.metrics.warnings}`);
    console.log(`❌ Errors:                 ${this.metrics.errors}`);

    if (this.qualityMetrics) {
      console.log(`📊 Overall Quality Score:  ${(this.qualityMetrics.overallScore * 100).toFixed(1)}%`);
    }

    if (this.complianceStatus) {
      console.log(`🏆 Compliance Status:      ${this.complianceStatus.isCompliant ? '✅ Compliant' : '❌ Non-compliant'}`);
    }

    if (this.metrics.errors > 0) {
      console.log('\n🚨 Critical issues found that must be addressed.');
    } else if (this.metrics.warnings > 0) {
      console.log('\n⚠️  Some warnings found that should be reviewed.');
    } else {
      console.log('\n🎉 All template validations passed successfully!');
    }

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const validator = new TemplateValidationSystem({
    rootPath: process.cwd(),
  });

  validator.validateTemplateSystem()
    .then((result) => {
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('Template validation failed:', error);
      process.exit(1);
    });
}

export { TemplateValidationSystem };
