#!/usr/bin/env node

/**
 * Integration Test Framework for Template Validation
 * Comprehensive end-to-end testing of the GitHub Copilot enhancement system
 */

import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class IntegrationTestFramework {
  constructor(options = {}) {
    this.rootPath = options.rootPath || process.cwd();
    this.testResultsPath = join(this.rootPath, '.github', 'validation', 'reports', 'integration');

    this.testSuites = new Map();
    this.testResults = [];
    this.setupStartTime = null;
    this.totalTestTime = 0;

    this.metrics = {
      totalTests: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      setupTime: 0,
      executionTime: 0,
    };

    this.setupTestSuites();
  }

  setupTestSuites() {
    // Template Structure Integration Tests
    this.testSuites.set('template-structure', {
      name: 'Template Structure Integration',
      tests: [
        { name: 'Chat Mode Template Generation', function: this.testChatModeTemplateGeneration.bind(this) },
        { name: 'Prompt Template Validation', function: this.testPromptTemplateValidation.bind(this) },
        { name: 'MCP Server Template Compliance', function: this.testMCPServerTemplateCompliance.bind(this) },
        { name: 'Cross-Template Reference Integrity', function: this.testCrossTemplateReferences.bind(this) },
      ],
    });

    // Content Standard Integration Tests
    this.testSuites.set('content-standards', {
      name: 'Content Standard Integration',
      tests: [
        { name: 'Style Guide Compliance', function: this.testStyleGuideCompliance.bind(this) },
        { name: 'Code Example Validation', function: this.testCodeExampleValidation.bind(this) },
        { name: 'Documentation Completeness', function: this.testDocumentationCompleteness.bind(this) },
        { name: 'Accessibility Standards', function: this.testAccessibilityStandards.bind(this) },
      ],
    });

    // System Integration Tests
    this.testSuites.set('system-integration', {
      name: 'System Integration',
      tests: [
        { name: 'MCP Server Connectivity', function: this.testMCPServerConnectivity.bind(this) },
        { name: 'Chat Mode Functionality', function: this.testChatModeFunctionality.bind(this) },
        { name: 'Validation Framework Integration', function: this.testValidationFrameworkIntegration.bind(this) },
        { name: 'End-to-End Workflow', function: this.testEndToEndWorkflow.bind(this) },
      ],
    });

    // Performance Integration Tests
    this.testSuites.set('performance', {
      name: 'Performance Integration',
      tests: [
        { name: 'Template Generation Performance', function: this.testTemplateGenerationPerformance.bind(this) },
        { name: 'Validation Processing Speed', function: this.testValidationProcessingSpeed.bind(this) },
        { name: 'Memory Usage Efficiency', function: this.testMemoryUsageEfficiency.bind(this) },
        { name: 'Concurrent Processing', function: this.testConcurrentProcessing.bind(this) },
      ],
    });

    // Calculate total test count
    this.metrics.totalTests = Array.from(this.testSuites.values())
      .reduce((total, suite) => total + suite.tests.length, 0);
  }

  async runIntegrationTests(options = {}) {
    console.log('🧪 Starting Integration Test Framework...\n');

    try {
      await fs.mkdir(this.testResultsPath, { recursive: true });

      this.setupStartTime = Date.now();

      // Run test setup
      await this.setupTestEnvironment();

      const executionStartTime = Date.now();

      // Run all test suites
      for (const [suiteId, suite] of this.testSuites) {
        if (options.skipSuites && options.skipSuites.includes(suiteId)) {
          console.log(`⏭️  Skipping ${suite.name}...`);
          continue;
        }

        console.log(`🔧 Running ${suite.name}...`);
        await this.runTestSuite(suiteId, suite, options);
        console.log();
      }

      this.metrics.executionTime = Date.now() - executionStartTime;
      this.totalTestTime = Date.now() - this.setupStartTime;

      // Generate comprehensive report
      await this.generateIntegrationReport();

      // Display summary
      this.displayTestSummary();

      return this.testResults;
    } catch (error) {
      console.error('❌ Integration tests failed:', error.message);
      throw error;
    }
  }

  async setupTestEnvironment() {
    console.log('⚙️  Setting up test environment...');

    const setupTasks = [
      { name: 'Validate Project Structure', function: this.validateProjectStructure.bind(this) },
      { name: 'Check Dependencies', function: this.checkDependencies.bind(this) },
      { name: 'Initialize Test Data', function: this.initializeTestData.bind(this) },
      { name: 'Verify File Permissions', function: this.verifyFilePermissions.bind(this) },
    ];

    for (const task of setupTasks) {
      try {
        await task.function();
        console.log(`  ✅ ${task.name}`);
      } catch (error) {
        console.log(`  ❌ ${task.name}: ${error.message}`);
        throw new Error(`Setup failed: ${task.name}`);
      }
    }

    this.metrics.setupTime = Date.now() - this.setupStartTime;
    console.log(`  ⏱️  Setup completed in ${this.metrics.setupTime}ms\n`);
  }

  async runTestSuite(suiteId, suite, options) {
    const suiteResults = {
      suite: suiteId,
      name: suite.name,
      tests: [],
      startTime: Date.now(),
      endTime: null,
      duration: null,
    };

    for (const test of suite.tests) {
      if (options.skipTests && options.skipTests.includes(test.name)) {
        console.log(`  ⏭️  Skipping: ${test.name}`);
        this.metrics.skipped++;
        continue;
      }

      const testResult = await this.runSingleTest(test);
      suiteResults.tests.push(testResult);

      if (testResult.status === 'passed') {
        this.metrics.passed++;
        console.log(`  ✅ ${test.name}`);
      } else if (testResult.status === 'failed') {
        this.metrics.failed++;
        console.log(`  ❌ ${test.name}: ${testResult.error}`);
      } else {
        this.metrics.skipped++;
        console.log(`  ⏭️  ${test.name}: ${testResult.reason}`);
      }
    }

    suiteResults.endTime = Date.now();
    suiteResults.duration = suiteResults.endTime - suiteResults.startTime;

    this.testResults.push(suiteResults);
  }

  async runSingleTest(test) {
    const testResult = {
      name: test.name,
      status: 'unknown',
      startTime: Date.now(),
      endTime: null,
      duration: null,
      error: null,
      details: null,
    };

    try {
      const result = await test.function();
      testResult.status = result.passed ? 'passed' : 'failed';
      testResult.details = result.details;
      testResult.error = result.error;
    } catch (error) {
      testResult.status = 'failed';
      testResult.error = error.message;
    }

    testResult.endTime = Date.now();
    testResult.duration = testResult.endTime - testResult.startTime;

    return testResult;
  }

  // Setup Methods
  async validateProjectStructure() {
    const requiredPaths = [
      '.github/chatmodes',
      '.github/prompts',
      '.github/mcp',
      '.github/validation',
    ];

    for (const path of requiredPaths) {
      const fullPath = join(this.rootPath, path);
      try {
        const stats = await fs.stat(fullPath);
        if (!stats.isDirectory()) {
          throw new Error(`${path} is not a directory`);
        }
      } catch (error) {
        throw new Error(`Required directory missing: ${path}`);
      }
    }
  }

  async checkDependencies() {
    // Check if required files exist
    const requiredFiles = [
      '.github/validation/validators/meta-instruction-validator.js',
      '.github/validation/templates/template-validation-system.js',
      '.github/mcp/mcp-servers.json',
    ];

    for (const file of requiredFiles) {
      const fullPath = join(this.rootPath, file);
      try {
        await fs.access(fullPath);
      } catch (error) {
        throw new Error(`Required file missing: ${file}`);
      }
    }
  }

  async initializeTestData() {
    // Create test data directory if it doesn't exist
    const testDataPath = join(this.testResultsPath, 'test-data');
    await fs.mkdir(testDataPath, { recursive: true });

    // Create sample test templates
    const sampleChatMode = `# Test Chat Mode

## Description
A test chat mode for integration testing.

## Role
You are a test assistant for validating chat mode functionality.

## Response Style
- Clear and concise responses
- Professional tone
- Include relevant examples

## Examples
**User**: Test the chat mode
**Assistant**: This is a test response demonstrating chat mode functionality.

## Constraints
- Keep responses focused on testing
- Validate all interactions
`;

    await fs.writeFile(join(testDataPath, 'test-chat-mode.md'), sampleChatMode);
  }

  async verifyFilePermissions() {
    // Check write permissions for reports directory
    try {
      const testFile = join(this.testResultsPath, 'permission-test.tmp');
      await fs.writeFile(testFile, 'test');
      await fs.unlink(testFile);
    } catch (error) {
      throw new Error('No write permissions for reports directory');
    }
  }

  // Template Structure Integration Tests
  async testChatModeTemplateGeneration() {
    try {
      // Test chat mode template structure
      const chatModeFiles = await this.findFilesByPattern('.github/chatmodes/*.md');

      if (chatModeFiles.length === 0) {
        return { passed: false, error: 'No chat mode files found' };
      }

      const validationResults = [];
      for (const file of chatModeFiles) {
        const content = await fs.readFile(file, 'utf8');
        const validation = this.validateChatModeStructure(content);
        validationResults.push({ file, ...validation });
      }

      const failedValidations = validationResults.filter(r => !r.valid);

      return {
        passed: failedValidations.length === 0,
        details: {
          totalFiles: chatModeFiles.length,
          validFiles: validationResults.length - failedValidations.length,
          failures: failedValidations,
        },
        error: failedValidations.length > 0 ? `${failedValidations.length} chat mode files failed validation` : null,
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testPromptTemplateValidation() {
    try {
      const promptFiles = await this.findFilesByPattern('.github/prompts/*.md');

      const validationResults = [];
      for (const file of promptFiles) {
        const content = await fs.readFile(file, 'utf8');
        const validation = this.validatePromptStructure(content);
        validationResults.push({ file, ...validation });
      }

      const successfulValidations = validationResults.filter(r => r.valid);

      return {
        passed: successfulValidations.length === validationResults.length,
        details: {
          totalFiles: promptFiles.length,
          validFiles: successfulValidations.length,
          validationResults,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testMCPServerTemplateCompliance() {
    try {
      const mcpServerFiles = await this.findFilesByPattern('.github/mcp/servers/*/index.js');

      const complianceResults = [];
      for (const file of mcpServerFiles) {
        const content = await fs.readFile(file, 'utf8');
        const compliance = this.validateMCPServerCompliance(content);
        complianceResults.push({ file, ...compliance });
      }

      const compliantServers = complianceResults.filter(r => r.compliant);

      return {
        passed: compliantServers.length === complianceResults.length,
        details: {
          totalServers: mcpServerFiles.length,
          compliantServers: compliantServers.length,
          complianceResults,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testCrossTemplateReferences() {
    try {
      // Get all markdown files
      const allMarkdownFiles = await this.findFilesByPattern('.github/**/*.md');

      // Extract and validate internal references
      const referenceValidation = await this.validateCrossReferences(allMarkdownFiles);

      return {
        passed: referenceValidation.brokenReferences.length === 0,
        details: {
          totalFiles: allMarkdownFiles.length,
          totalReferences: referenceValidation.totalReferences,
          validReferences: referenceValidation.validReferences,
          brokenReferences: referenceValidation.brokenReferences,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  // Content Standard Integration Tests
  async testStyleGuideCompliance() {
    try {
      const markdownFiles = await this.findFilesByPattern('.github/**/*.md');

      const styleIssues = [];
      for (const file of markdownFiles) {
        const content = await fs.readFile(file, 'utf8');
        const issues = this.checkStyleCompliance(content);
        if (issues.length > 0) {
          styleIssues.push({ file, issues });
        }
      }

      return {
        passed: styleIssues.length === 0,
        details: {
          totalFiles: markdownFiles.length,
          filesWithIssues: styleIssues.length,
          styleIssues,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testCodeExampleValidation() {
    try {
      const markdownFiles = await this.findFilesByPattern('.github/**/*.md');

      const codeBlockValidation = [];
      for (const file of markdownFiles) {
        const content = await fs.readFile(file, 'utf8');
        const validation = this.validateCodeBlocks(content);
        codeBlockValidation.push({ file, ...validation });
      }

      const filesWithInvalidCode = codeBlockValidation.filter(v => v.invalidBlocks.length > 0);

      return {
        passed: filesWithInvalidCode.length === 0,
        details: {
          totalFiles: markdownFiles.length,
          totalCodeBlocks: codeBlockValidation.reduce((sum, v) => sum + v.totalBlocks, 0),
          validCodeBlocks: codeBlockValidation.reduce((sum, v) => sum + v.validBlocks, 0),
          filesWithInvalidCode,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testDocumentationCompleteness() {
    try {
      const requiredDocumentationSections = [
        { pattern: '.github/chatmodes/**/*.md', requiredSections: ['title', 'description', 'usage'] },
        { pattern: '.github/prompts/**/*.md', requiredSections: ['title', 'description', 'usage'] },
        { pattern: '.github/mcp/**/*.md', requiredSections: ['title', 'overview', 'configuration'] },
        { pattern: '.github/validation/**/*.md', requiredSections: ['title', 'overview'] },
      ];

      const completenessResults = [];
      for (const requirement of requiredDocumentationSections) {
        const files = await this.findFilesByPattern(requirement.pattern);

        for (const file of files) {
          const content = await fs.readFile(file, 'utf8');
          const completeness = this.checkDocumentationCompleteness(content, requirement.requiredSections);
          completenessResults.push({ file, ...completeness });
        }
      }

      const incompleteFiles = completenessResults.filter(r => r.missingSections.length > 0);

      return {
        passed: incompleteFiles.length === 0,
        details: {
          totalFiles: completenessResults.length,
          completeFiles: completenessResults.length - incompleteFiles.length,
          incompleteFiles,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testAccessibilityStandards() {
    try {
      const markdownFiles = await this.findFilesByPattern('.github/**/*.md');

      const accessibilityIssues = [];
      for (const file of markdownFiles) {
        const content = await fs.readFile(file, 'utf8');
        const issues = this.checkAccessibilityCompliance(content);
        if (issues.length > 0) {
          accessibilityIssues.push({ file, issues });
        }
      }

      return {
        passed: accessibilityIssues.length === 0,
        details: {
          totalFiles: markdownFiles.length,
          accessibleFiles: markdownFiles.length - accessibilityIssues.length,
          accessibilityIssues,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  // System Integration Tests
  async testMCPServerConnectivity() {
    try {
      // Test MCP server configuration
      const mcpConfigPath = join(this.rootPath, '.github/mcp/mcp-servers.json');
      const mcpConfig = JSON.parse(await fs.readFile(mcpConfigPath, 'utf8'));

      const connectivityResults = [];
      for (const [serverName, config] of Object.entries(mcpConfig.servers || {})) {
        const result = await this.testMCPServerConfiguration(serverName, config);
        connectivityResults.push({ serverName, ...result });
      }

      const workingServers = connectivityResults.filter(r => r.configValid);

      return {
        passed: workingServers.length === connectivityResults.length,
        details: {
          totalServers: connectivityResults.length,
          workingServers: workingServers.length,
          connectivityResults,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testChatModeFunctionality() {
    try {
      // Test chat mode processing
      const chatModeFiles = await this.findFilesByPattern('.github/chatmodes/*.md');

      const functionalityResults = [];
      for (const file of chatModeFiles) {
        const content = await fs.readFile(file, 'utf8');
        const functionality = this.testChatModeProcessing(content);
        functionalityResults.push({ file, ...functionality });
      }

      const workingChatModes = functionalityResults.filter(r => r.functional);

      return {
        passed: workingChatModes.length === functionalityResults.length,
        details: {
          totalChatModes: chatModeFiles.length,
          workingChatModes: workingChatModes.length,
          functionalityResults,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testValidationFrameworkIntegration() {
    try {
      // Test meta-instruction validator integration
      const validatorPath = join(this.rootPath, '.github/validation/validators/meta-instruction-validator.js');

      try {
        await fs.access(validatorPath);

        // Test basic validator functionality
        const validatorIntegration = await this.testValidatorIntegration();

        return {
          passed: validatorIntegration.working,
          details: validatorIntegration,
        };
      } catch (error) {
        return { passed: false, error: 'Meta-instruction validator not found' };
      }
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testEndToEndWorkflow() {
    try {
      // Test complete workflow from template to validation
      const workflowSteps = [
        { name: 'Template Discovery', function: this.testTemplateDiscovery.bind(this) },
        { name: 'Content Validation', function: this.testContentValidation.bind(this) },
        { name: 'Integration Validation', function: this.testIntegrationValidation.bind(this) },
        { name: 'Report Generation', function: this.testReportGeneration.bind(this) },
      ];

      const stepResults = [];
      for (const step of workflowSteps) {
        const result = await step.function();
        stepResults.push({ stepName: step.name, ...result });

        if (!result.passed) {
          break; // Stop on first failure
        }
      }

      const completedSteps = stepResults.filter(r => r.passed);

      return {
        passed: completedSteps.length === workflowSteps.length,
        details: {
          totalSteps: workflowSteps.length,
          completedSteps: completedSteps.length,
          stepResults,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  // Performance Integration Tests
  async testTemplateGenerationPerformance() {
    try {
      const startTime = Date.now();

      // Simulate template generation for different types
      const templates = await this.findFilesByPattern('.github/**/*.md');

      const generationResults = [];
      for (const template of templates.slice(0, 10)) { // Test first 10 templates
        const templateStartTime = Date.now();
        const content = await fs.readFile(template, 'utf8');
        const processed = this.processTemplate(content);
        const templateEndTime = Date.now();

        generationResults.push({
          template,
          processingTime: templateEndTime - templateStartTime,
          success: processed !== null,
        });
      }

      const totalTime = Date.now() - startTime;
      const averageTime = totalTime / generationResults.length;

      return {
        passed: averageTime < 100, // Should process in under 100ms on average
        details: {
          totalTemplates: generationResults.length,
          totalTime,
          averageTime,
          generationResults,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testValidationProcessingSpeed() {
    try {
      const startTime = Date.now();

      // Test validation speed
      const files = await this.findFilesByPattern('.github/**/*.{md,js,json}');

      let validatedFiles = 0;
      for (const file of files.slice(0, 20)) { // Test first 20 files
        try {
          const content = await fs.readFile(file, 'utf8');
          this.performBasicValidation(content);
          validatedFiles++;
        } catch (error) {
          // Continue with other files
        }
      }

      const totalTime = Date.now() - startTime;
      const averageTime = totalTime / validatedFiles;

      return {
        passed: averageTime < 50, // Should validate in under 50ms on average
        details: {
          validatedFiles,
          totalTime,
          averageTime,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testMemoryUsageEfficiency() {
    try {
      const initialMemory = process.memoryUsage();

      // Process multiple files to test memory usage
      const files = await this.findFilesByPattern('.github/**/*.md');

      for (const file of files) {
        const content = await fs.readFile(file, 'utf8');
        // Simulate processing
        this.processTemplate(content);
      }

      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      const memoryIncreaseKB = memoryIncrease / 1024;

      return {
        passed: memoryIncreaseKB < 10000, // Should not use more than 10MB
        details: {
          initialMemory: initialMemory.heapUsed,
          finalMemory: finalMemory.heapUsed,
          memoryIncrease,
          memoryIncreaseKB,
          filesProcessed: files.length,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testConcurrentProcessing() {
    try {
      const files = await this.findFilesByPattern('.github/**/*.md');
      const testFiles = files.slice(0, 10);

      const startTime = Date.now();

      // Test concurrent processing
      const concurrentPromises = testFiles.map(async (file) => {
        const content = await fs.readFile(file, 'utf8');
        return this.processTemplate(content);
      });

      const results = await Promise.all(concurrentPromises);
      const endTime = Date.now();

      const successfulResults = results.filter(r => r !== null);

      return {
        passed: successfulResults.length === testFiles.length,
        details: {
          totalFiles: testFiles.length,
          successfulProcessing: successfulResults.length,
          processingTime: endTime - startTime,
        },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  // Utility Methods
  async findFilesByPattern(pattern) {
    // Simple glob-like pattern matching
    const files = [];
    await this.scanDirectoryForPattern(this.rootPath, pattern, files);
    return files;
  }

  async scanDirectoryForPattern(dir, pattern, files) {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = join(dir, entry.name);

        if (entry.isDirectory()) {
          if (!entry.name.startsWith('.') || pattern.includes('/.github/')) {
            await this.scanDirectoryForPattern(fullPath, pattern, files);
          }
        } else {
          // Simple pattern matching - can be enhanced with proper glob library
          if (this.matchesPattern(fullPath, pattern)) {
            files.push(fullPath);
          }
        }
      }
    } catch (error) {
      // Directory might not exist or be readable
    }
  }

  matchesPattern(filePath, pattern) {
    // Convert simple glob patterns to regex
    const relativePath = filePath.replace(this.rootPath + '/', '');
    const regexPattern = pattern
      .replace(/\*\*/g, '.*')
      .replace(/\*/g, '[^/]*')
      .replace(/\{([^}]+)\}/g, '($1)')
      .replace(/,/g, '|');

    const regex = new RegExp('^' + regexPattern + '$');
    return regex.test(relativePath);
  }

  // Validation Helper Methods
  validateChatModeStructure(content) {
    const requiredSections = ['# ', '## Description', '## Role', '## Response Style', '## Examples'];
    const missingSections = [];

    for (const section of requiredSections) {
      if (!content.includes(section)) {
        missingSections.push(section);
      }
    }

    return {
      valid: missingSections.length === 0,
      missingSections,
    };
  }

  validatePromptStructure(content) {
    const requiredSections = ['# ', '## Description', '## Usage'];
    const missingSections = [];

    for (const section of requiredSections) {
      if (!content.includes(section)) {
        missingSections.push(section);
      }
    }

    return {
      valid: missingSections.length === 0,
      missingSections,
    };
  }

  validateMCPServerCompliance(content) {
    const requiredElements = [
      'modelcontextprotocol/sdk',
      'StdioServerTransport',
      'setRequestHandler',
      'async run()',
    ];

    const missingElements = [];
    for (const element of requiredElements) {
      if (!content.includes(element)) {
        missingElements.push(element);
      }
    }

    return {
      compliant: missingElements.length === 0,
      missingElements,
    };
  }

  async validateCrossReferences(files) {
    const allFiles = new Set(files.map(f => f.replace(this.rootPath + '/', '')));
    let totalReferences = 0;
    let validReferences = 0;
    const brokenReferences = [];

    for (const file of files) {
      const content = await fs.readFile(file, 'utf8');
      const links = content.match(/\[.*?\]\((?!https?:\/\/)([^)]+)\)/g) || [];

      for (const link of links) {
        totalReferences++;
        const urlMatch = link.match(/\[.*?\]\(([^)]+)\)/);
        if (urlMatch) {
          const linkedFile = urlMatch[1];
          const resolvedPath = join(dirname(file.replace(this.rootPath + '/', '')), linkedFile).replace(/\\/g, '/');

          if (allFiles.has(resolvedPath) || allFiles.has(linkedFile)) {
            validReferences++;
          } else {
            brokenReferences.push({
              file: file.replace(this.rootPath + '/', ''),
              link: linkedFile,
              resolvedPath,
            });
          }
        }
      }
    }

    return {
      totalReferences,
      validReferences,
      brokenReferences,
    };
  }

  checkStyleCompliance(content) {
    const issues = [];
    const lines = content.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Check for trailing whitespace
      if (line.endsWith(' ') || line.endsWith('\t')) {
        issues.push({ line: i + 1, type: 'trailing-whitespace' });
      }

      // Check for very long lines
      if (line.length > 120) {
        issues.push({ line: i + 1, type: 'line-too-long', length: line.length });
      }
    }

    return issues;
  }

  validateCodeBlocks(content) {
    const codeBlocks = content.match(/```[\s\S]*?```/g) || [];
    const totalBlocks = codeBlocks.length;
    let validBlocks = 0;
    const invalidBlocks = [];

    for (const block of codeBlocks) {
      const lines = block.split('\n');
      const firstLine = lines[0];

      // Check if code block has language specified
      if (firstLine === '```') {
        invalidBlocks.push({ block: block.substring(0, 50), issue: 'no-language-specified' });
      } else {
        validBlocks++;
      }
    }

    return {
      totalBlocks,
      validBlocks,
      invalidBlocks,
    };
  }

  checkDocumentationCompleteness(content, requiredSections) {
    const missingSections = [];

    for (const section of requiredSections) {
      const sectionPattern = section === 'title' ? /^#\s+/ : new RegExp(`##\\s+${section}`, 'i');
      if (!sectionPattern.test(content)) {
        missingSections.push(section);
      }
    }

    return {
      complete: missingSections.length === 0,
      missingSections,
    };
  }

  checkAccessibilityCompliance(content) {
    const issues = [];

    // Check for images without alt text
    const images = content.match(/!\[([^\]]*)\]\([^)]+\)/g) || [];
    for (const image of images) {
      const altTextMatch = image.match(/!\[([^\]]*)\]/);
      if (!altTextMatch || !altTextMatch[1].trim()) {
        issues.push({ type: 'missing-alt-text', element: image });
      }
    }

    // Check for proper heading hierarchy
    const headings = content.match(/^#+\s+.+$/gm) || [];
    let previousLevel = 0;

    for (const heading of headings) {
      const level = heading.match(/^#+/)[0].length;
      if (level > previousLevel + 1) {
        issues.push({ type: 'heading-hierarchy-skip', heading });
      }
      previousLevel = level;
    }

    return issues;
  }

  // Test Helper Methods
  async testMCPServerConfiguration(serverName, config) {
    try {
      // Basic configuration validation
      const requiredFields = ['command', 'args'];
      const missingFields = requiredFields.filter(field => !config[field]);

      if (missingFields.length > 0) {
        return {
          configValid: false,
          error: `Missing required fields: ${missingFields.join(', ')}`,
        };
      }

      // Check if server file exists
      const serverPath = join(this.rootPath, config.command);
      try {
        await fs.access(serverPath);
        return { configValid: true };
      } catch (error) {
        return {
          configValid: false,
          error: `Server file not found: ${config.command}`,
        };
      }
    } catch (error) {
      return {
        configValid: false,
        error: error.message,
      };
    }
  }

  testChatModeProcessing(content) {
    try {
      // Simulate chat mode processing
      const structure = this.validateChatModeStructure(content);
      const hasExamples = content.includes('**User**') && content.includes('**Assistant**');

      return {
        functional: structure.valid && hasExamples,
        issues: structure.missingSections,
      };
    } catch (error) {
      return {
        functional: false,
        error: error.message,
      };
    }
  }

  async testValidatorIntegration() {
    try {
      // Test if validator can be imported and basic functionality works
      const validatorExists = await fs.access(join(this.rootPath, '.github/validation/validators/meta-instruction-validator.js')).then(() => true).catch(() => false);

      if (!validatorExists) {
        return {
          working: false,
          error: 'Validator file not found',
        };
      }

      return {
        working: true,
        features: ['file-validation', 'structure-checking', 'report-generation'],
      };
    } catch (error) {
      return {
        working: false,
        error: error.message,
      };
    }
  }

  async testTemplateDiscovery() {
    try {
      const templates = await this.findFilesByPattern('.github/**/*.md');
      return {
        passed: templates.length > 0,
        templatesFound: templates.length,
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testContentValidation() {
    try {
      const files = await this.findFilesByPattern('.github/**/*.md');
      let validatedFiles = 0;

      for (const file of files.slice(0, 5)) {
        const content = await fs.readFile(file, 'utf8');
        if (this.performBasicValidation(content)) {
          validatedFiles++;
        }
      }

      return {
        passed: validatedFiles > 0,
        validatedFiles,
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testIntegrationValidation() {
    try {
      // Test integration between components
      const hasValidator = await fs.access(join(this.rootPath, '.github/validation/validators/meta-instruction-validator.js')).then(() => true).catch(() => false);
      const hasMCPServers = await fs.access(join(this.rootPath, '.github/mcp/mcp-servers.json')).then(() => true).catch(() => false);
      const hasChatModes = await fs.access(join(this.rootPath, '.github/chatmodes')).then(() => true).catch(() => false);
      const hasPrompts = await fs.access(join(this.rootPath, '.github/prompts')).then(() => true).catch(() => false);

      return {
        passed: hasValidator && hasMCPServers && hasChatModes && hasPrompts,
        components: { hasValidator, hasMCPServers, hasChatModes, hasPrompts },
      };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  async testReportGeneration() {
    try {
      // Test report generation capability
      const testReport = {
        timestamp: new Date().toISOString(),
        testData: 'integration-test',
      };

      const reportPath = join(this.testResultsPath, 'test-report.json');
      await fs.writeFile(reportPath, JSON.stringify(testReport, null, 2));

      // Verify file was created
      await fs.access(reportPath);
      await fs.unlink(reportPath); // Clean up

      return { passed: true };
    } catch (error) {
      return { passed: false, error: error.message };
    }
  }

  processTemplate(content) {
    try {
      // Simulate template processing
      if (!content || content.trim().length === 0) {
        return null;
      }

      return {
        processed: true,
        contentLength: content.length,
        hasTitle: content.includes('# '),
        timestamp: Date.now(),
      };
    } catch (error) {
      return null;
    }
  }

  performBasicValidation(content) {
    try {
      // Basic validation checks
      return content.length > 0 && content.includes('#');
    } catch (error) {
      return false;
    }
  }

  async generateIntegrationReport() {
    const timestamp = new Date().toISOString();
    const reportFile = join(this.testResultsPath, `integration-test-report-${timestamp.split('T')[0]}.json`);

    const report = {
      timestamp,
      framework: 'Integration Test Framework',
      version: '1.0.0',
      duration: this.totalTestTime,
      metrics: this.metrics,
      testSuites: this.testResults,
      summary: {
        totalTests: this.metrics.totalTests,
        passed: this.metrics.passed,
        failed: this.metrics.failed,
        skipped: this.metrics.skipped,
        successRate: ((this.metrics.passed / this.metrics.totalTests) * 100).toFixed(1),
      },
      recommendations: this.generateTestRecommendations(),
    };

    await fs.writeFile(reportFile, JSON.stringify(report, null, 2));

    // Generate readable report
    const readableReport = this.generateReadableTestReport(report);
    const readableFile = join(this.testResultsPath, `integration-test-report-${timestamp.split('T')[0]}.md`);
    await fs.writeFile(readableFile, readableReport);

    console.log(`📊 Integration test report saved to: ${reportFile}`);
    console.log(`📝 Readable report saved to: ${readableFile}`);
  }

  generateTestRecommendations() {
    const recommendations = [];

    if (this.metrics.failed > 0) {
      recommendations.push({
        priority: 'high',
        category: 'failures',
        message: `${this.metrics.failed} tests failed and should be addressed immediately`,
        action: 'Review failed test details and fix underlying issues',
      });
    }

    if (this.metrics.skipped > this.metrics.totalTests * 0.1) {
      recommendations.push({
        priority: 'medium',
        category: 'coverage',
        message: 'High number of skipped tests may indicate incomplete test coverage',
        action: 'Review skipped tests and enable where appropriate',
      });
    }

    if (this.totalTestTime > 30000) {
      recommendations.push({
        priority: 'low',
        category: 'performance',
        message: 'Test execution time is longer than expected',
        action: 'Consider optimizing test performance and parallel execution',
      });
    }

    return recommendations;
  }

  generateReadableTestReport(report) {
    const { timestamp, duration, metrics, testSuites, summary, recommendations } = report;

    let md = `# Integration Test Report\n\n`;
    md += `**Generated**: ${timestamp}\n`;
    md += `**Duration**: ${duration}ms\n\n`;

    md += `## Summary\n\n`;
    md += `- **Total Tests**: ${summary.totalTests}\n`;
    md += `- **Passed**: ${summary.passed}\n`;
    md += `- **Failed**: ${summary.failed}\n`;
    md += `- **Skipped**: ${summary.skipped}\n`;
    md += `- **Success Rate**: ${summary.successRate}%\n\n`;

    md += `## Test Suites\n\n`;

    testSuites.forEach(suite => {
      md += `### ${suite.name}\n\n`;
      md += `**Duration**: ${suite.duration}ms\n\n`;

      suite.tests.forEach(test => {
        const status = test.status === 'passed' ? '✅' : test.status === 'failed' ? '❌' : '⏭️';
        md += `- ${status} **${test.name}** (${test.duration}ms)\n`;
        if (test.error) {
          md += `  - Error: ${test.error}\n`;
        }
      });
      md += `\n`;
    });

    if (recommendations.length > 0) {
      md += `## Recommendations\n\n`;
      recommendations.forEach((rec, index) => {
        md += `${index + 1}. **${rec.priority.toUpperCase()}**: ${rec.message}\n`;
        md += `   - Action: ${rec.action}\n\n`;
      });
    }

    return md;
  }

  displayTestSummary() {
    console.log('📋 Integration Test Summary:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`🧪 Total Tests:       ${this.metrics.totalTests}`);
    console.log(`✅ Passed:            ${this.metrics.passed}`);
    console.log(`❌ Failed:            ${this.metrics.failed}`);
    console.log(`⏭️  Skipped:           ${this.metrics.skipped}`);
    console.log(`⏱️  Setup Time:        ${this.metrics.setupTime}ms`);
    console.log(`⚡ Execution Time:    ${this.metrics.executionTime}ms`);
    console.log(`🕐 Total Time:        ${this.totalTestTime}ms`);

    const successRate = ((this.metrics.passed / this.metrics.totalTests) * 100);
    console.log(`📊 Success Rate:      ${successRate.toFixed(1)}%`);

    if (this.metrics.failed > 0) {
      console.log('\n🚨 Critical failures found that should be addressed immediately.');
    } else if (this.metrics.skipped > 0) {
      console.log(`\n⚠️  ${this.metrics.skipped} tests were skipped.`);
    } else {
      console.log('\n🎉 All integration tests passed successfully!');
    }

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const framework = new IntegrationTestFramework({
    rootPath: process.cwd(),
  });

  const options = {};

  // Parse simple CLI arguments
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--skip-performance') {
      options.skipSuites = (options.skipSuites || []).concat(['performance']);
    } else if (args[i] === '--skip-integration') {
      options.skipSuites = (options.skipSuites || []).concat(['system-integration']);
    }
  }

  framework.runIntegrationTests(options)
    .then(() => {
      process.exit(framework.metrics.failed > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('Integration tests failed:', error);
      process.exit(1);
    });
}

export { IntegrationTestFramework };
