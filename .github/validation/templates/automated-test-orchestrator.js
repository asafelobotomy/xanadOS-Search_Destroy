#!/usr/bin/env node

/**
 * Automated Test Orchestrator
 * Comprehensive orchestration of GitHub Copilot enhancement validation system
 */

import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class AutomatedTestOrchestrator {
  constructor(options = {}) {
    this.rootPath = options.rootPath || process.cwd();
    this.configPath = join(this.rootPath, '.github', 'validation', 'orchestrator-config.json');
    this.reportsPath = join(this.rootPath, '.github', 'validation', 'reports', 'orchestration');
    
    this.testPhases = new Map([
      ['setup', { name: 'Environment Setup', priority: 1, critical: true }],
      ['validation', { name: 'Core Validation', priority: 2, critical: true }],
      ['integration', { name: 'Integration Testing', priority: 3, critical: false }],
      ['performance', { name: 'Performance Testing', priority: 4, critical: false }],
      ['reporting', { name: 'Report Generation', priority: 5, critical: true }],
      ['cleanup', { name: 'Cleanup & Archive', priority: 6, critical: false }],
    ]);
    
    this.orchestrationState = {
      sessionId: this.generateSessionId(),
      startTime: null,
      endTime: null,
      currentPhase: null,
      completedPhases: [],
      failedPhases: [],
      skippedPhases: [],
      results: new Map(),
      metrics: {
        totalDuration: 0,
        setupTime: 0,
        validationTime: 0,
        integrationTime: 0,
        performanceTime: 0,
        reportingTime: 0,
        cleanupTime: 0,
      },
    };
    
    this.configuration = {
      enabledPhases: ['setup', 'validation', 'integration', 'reporting'],
      parallelExecution: false,
      timeoutMinutes: 30,
      retryAttempts: 2,
      reportFormats: ['comprehensive', 'summary', 'technical'],
      notificationLevel: 'critical', // 'all', 'critical', 'none'
      archiveResults: true,
      cleanupOnSuccess: false,
    };
  }

  async initialize() {
    console.log('🚀 Initializing Automated Test Orchestrator...');
    
    try {
      await fs.mkdir(this.reportsPath, { recursive: true });
      
      // Load configuration if exists
      if (await this.fileExists(this.configPath)) {
        await this.loadConfiguration();
      }
      
      // Validate environment
      await this.validateEnvironment();
      
      console.log(`✅ Orchestrator initialized with session ID: ${this.orchestrationState.sessionId}`);
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize orchestrator:', error.message);
      throw error;
    }
  }

  async executeOrchestration(options = {}) {
    console.log('🎭 Starting automated test orchestration...\n');
    
    try {
      this.orchestrationState.startTime = Date.now();
      
      // Override configuration with options
      this.applyOptions(options);
      
      // Execute phases in order
      for (const [phaseId, phaseInfo] of this.testPhases) {
        if (!this.configuration.enabledPhases.includes(phaseId)) {
          console.log(`⏭️  Skipping phase: ${phaseInfo.name}`);
          this.orchestrationState.skippedPhases.push(phaseId);
          continue;
        }
        
        await this.executePhase(phaseId, phaseInfo);
      }
      
      this.orchestrationState.endTime = Date.now();
      this.orchestrationState.metrics.totalDuration = this.orchestrationState.endTime - this.orchestrationState.startTime;
      
      // Generate final orchestration report
      await this.generateOrchestrationReport();
      
      // Send notifications if configured
      await this.sendNotifications();
      
      // Archive results if configured
      if (this.configuration.archiveResults) {
        await this.archiveResults();
      }
      
      this.displayOrchestrationSummary();
      
      return {
        sessionId: this.orchestrationState.sessionId,
        success: this.orchestrationState.failedPhases.length === 0,
        completedPhases: this.orchestrationState.completedPhases,
        failedPhases: this.orchestrationState.failedPhases,
        metrics: this.orchestrationState.metrics,
      };
      
    } catch (error) {
      console.error('❌ Orchestration failed:', error.message);
      await this.handleOrchestrationFailure(error);
      throw error;
    }
  }

  async executePhase(phaseId, phaseInfo) {
    console.log(`🔄 Executing phase: ${phaseInfo.name}`);
    this.orchestrationState.currentPhase = phaseId;
    
    const phaseStartTime = Date.now();
    let retryCount = 0;
    let lastError = null;
    
    while (retryCount <= this.configuration.retryAttempts) {
      try {
        const result = await this.executePhaseImplementation(phaseId, phaseInfo);
        
        const phaseDuration = Date.now() - phaseStartTime;
        this.orchestrationState.metrics[`${phaseId}Time`] = phaseDuration;
        
        this.orchestrationState.results.set(phaseId, {
          ...result,
          duration: phaseDuration,
          retryCount,
          success: true,
        });
        
        this.orchestrationState.completedPhases.push(phaseId);
        console.log(`✅ Phase completed: ${phaseInfo.name} (${phaseDuration}ms)`);
        return result;
        
      } catch (error) {
        lastError = error;
        retryCount++;
        
        if (retryCount <= this.configuration.retryAttempts) {
          console.log(`⚠️  Phase failed, retrying (${retryCount}/${this.configuration.retryAttempts}): ${error.message}`);
          await this.delay(1000 * retryCount); // Exponential backoff
        }
      }
    }
    
    // All retries failed
    console.log(`❌ Phase failed: ${phaseInfo.name} - ${lastError.message}`);
    
    const phaseDuration = Date.now() - phaseStartTime;
    this.orchestrationState.results.set(phaseId, {
      error: lastError.message,
      duration: phaseDuration,
      retryCount,
      success: false,
    });
    
    this.orchestrationState.failedPhases.push(phaseId);
    
    // Check if this is a critical phase
    if (phaseInfo.critical) {
      throw new Error(`Critical phase failed: ${phaseInfo.name}`);
    }
  }

  async executePhaseImplementation(phaseId, phaseInfo) {
    switch (phaseId) {
      case 'setup':
        return await this.executeSetupPhase();
      case 'validation':
        return await this.executeValidationPhase();
      case 'integration':
        return await this.executeIntegrationPhase();
      case 'performance':
        return await this.executePerformancePhase();
      case 'reporting':
        return await this.executeReportingPhase();
      case 'cleanup':
        return await this.executeCleanupPhase();
      default:
        throw new Error(`Unknown phase: ${phaseId}`);
    }
  }

  async executeSetupPhase() {
    const setupTasks = [
      { name: 'Validate Project Structure', function: this.validateProjectStructure.bind(this) },
      { name: 'Check Dependencies', function: this.checkDependencies.bind(this) },
      { name: 'Initialize Working Directories', function: this.initializeWorkingDirectories.bind(this) },
      { name: 'Load Configuration Files', function: this.loadConfigurationFiles.bind(this) },
      { name: 'Verify System Resources', function: this.verifySystemResources.bind(this) },
    ];
    
    const results = [];
    for (const task of setupTasks) {
      try {
        const result = await task.function();
        results.push({ task: task.name, success: true, result });
        console.log(`  ✅ ${task.name}`);
      } catch (error) {
        results.push({ task: task.name, success: false, error: error.message });
        console.log(`  ❌ ${task.name}: ${error.message}`);
        throw error;
      }
    }
    
    return { taskResults: results, setupComplete: true };
  }

  async executeValidationPhase() {
    console.log('  🔍 Running core validation...');
    
    const validationResults = [];
    
    // Run meta-instruction validation
    try {
      const metaValidatorPath = join(this.rootPath, '.github', 'validation', 'validators', 'meta-instruction-validator.js');
      if (await this.fileExists(metaValidatorPath)) {
        console.log('    🧪 Meta-instruction validation...');
        const metaResult = await this.runValidator(metaValidatorPath, ['--format', 'json']);
        validationResults.push({ type: 'meta-instruction', ...metaResult });
      }
    } catch (error) {
      console.log(`    ⚠️  Meta-instruction validation failed: ${error.message}`);
    }
    
    // Run template validation
    try {
      const templateValidatorPath = join(this.rootPath, '.github', 'validation', 'templates', 'template-validation-system.js');
      if (await this.fileExists(templateValidatorPath)) {
        console.log('    📝 Template validation...');
        const templateResult = await this.runValidator(templateValidatorPath, ['--json']);
        validationResults.push({ type: 'template', ...templateResult });
      }
    } catch (error) {
      console.log(`    ⚠️  Template validation failed: ${error.message}`);
    }
    
    // Aggregate results
    const aggregatedResults = this.aggregateValidationResults(validationResults);
    
    if (aggregatedResults.successRate < 60) {
      throw new Error(`Validation failed: ${aggregatedResults.successRate.toFixed(1)}% success rate`);
    }
    
    return {
      validationResults,
      aggregatedResults,
      validationComplete: true,
    };
  }

  async executeIntegrationPhase() {
    console.log('  🔗 Running integration tests...');
    
    try {
      const integrationFrameworkPath = join(this.rootPath, '.github', 'validation', 'templates', 'integration-test-framework.js');
      
      if (await this.fileExists(integrationFrameworkPath)) {
        console.log('    🧪 Running integration test framework...');
        
        // Import and run integration tests
        const { IntegrationTestFramework } = await import(integrationFrameworkPath);
        const framework = new IntegrationTestFramework({ rootPath: this.rootPath });
        
        const integrationResults = await framework.runIntegrationTests({
          skipSuites: this.configuration.enabledPhases.includes('performance') ? [] : ['performance']
        });
        
        return {
          integrationResults,
          integrationComplete: true,
        };
      } else {
        console.log('    ⚠️  Integration test framework not found, skipping...');
        return { integrationSkipped: true };
      }
    } catch (error) {
      console.log(`    ❌ Integration tests failed: ${error.message}`);
      throw error;
    }
  }

  async executePerformancePhase() {
    console.log('  ⚡ Running performance tests...');
    
    const performanceMetrics = {
      startTime: Date.now(),
      memoryUsage: process.memoryUsage(),
      fileProcessingTimes: [],
      totalFiles: 0,
      averageProcessingTime: 0,
    };
    
    try {
      // Test file processing performance
      const testFiles = await this.findTestFiles();
      performanceMetrics.totalFiles = testFiles.length;
      
      for (const file of testFiles.slice(0, 20)) { // Test first 20 files
        const fileStartTime = Date.now();
        try {
          await fs.readFile(file, 'utf8');
          // Simulate processing
          await this.delay(Math.random() * 50);
        } catch (error) {
          // Skip problematic files
        }
        const processingTime = Date.now() - fileStartTime;
        performanceMetrics.fileProcessingTimes.push({
          file: file.replace(this.rootPath, ''),
          processingTime,
        });
      }
      
      performanceMetrics.averageProcessingTime = 
        performanceMetrics.fileProcessingTimes.reduce((sum, item) => sum + item.processingTime, 0) / 
        performanceMetrics.fileProcessingTimes.length;
      
      performanceMetrics.endTime = Date.now();
      performanceMetrics.totalDuration = performanceMetrics.endTime - performanceMetrics.startTime;
      performanceMetrics.finalMemoryUsage = process.memoryUsage();
      
      // Performance validation
      if (performanceMetrics.averageProcessingTime > 1000) {
        console.log(`    ⚠️  Performance warning: Average processing time ${performanceMetrics.averageProcessingTime.toFixed(0)}ms`);
      }
      
      return {
        performanceMetrics,
        performanceComplete: true,
      };
    } catch (error) {
      console.log(`    ❌ Performance tests failed: ${error.message}`);
      throw error;
    }
  }

  async executeReportingPhase() {
    console.log('  📊 Generating reports...');
    
    try {
      const reportingSystemPath = join(this.rootPath, '.github', 'validation', 'templates', 'validation-reporting-system.js');
      
      if (await this.fileExists(reportingSystemPath)) {
        console.log('    📝 Running validation reporting system...');
        
        // Import and run reporting system
        const { ValidationReportingSystem } = await import(reportingSystemPath);
        const reportingSystem = new ValidationReportingSystem({ rootPath: this.rootPath });
        
        // Aggregate all results for reporting
        const aggregatedData = this.aggregateAllResults();
        
        const reportResult = await reportingSystem.generateComprehensiveReport(aggregatedData);
        
        return {
          reportResult,
          reportingComplete: true,
        };
      } else {
        console.log('    ⚠️  Reporting system not found, generating basic report...');
        const basicReport = await this.generateBasicReport();
        return {
          basicReport,
          reportingComplete: true,
        };
      }
    } catch (error) {
      console.log(`    ❌ Reporting failed: ${error.message}`);
      throw error;
    }
  }

  async executeCleanupPhase() {
    console.log('  🧹 Running cleanup...');
    
    const cleanupTasks = [
      { name: 'Archive Test Results', function: this.archiveTestResults.bind(this) },
      { name: 'Clean Temporary Files', function: this.cleanTemporaryFiles.bind(this) },
      { name: 'Update Metrics Database', function: this.updateMetricsDatabase.bind(this) },
      { name: 'Send Final Notifications', function: this.sendFinalNotifications.bind(this) },
    ];
    
    const results = [];
    for (const task of cleanupTasks) {
      try {
        const result = await task.function();
        results.push({ task: task.name, success: true, result });
        console.log(`    ✅ ${task.name}`);
      } catch (error) {
        results.push({ task: task.name, success: false, error: error.message });
        console.log(`    ⚠️  ${task.name}: ${error.message}`);
        // Continue with other cleanup tasks
      }
    }
    
    return { cleanupResults: results, cleanupComplete: true };
  }

  // Helper Methods
  async validateProjectStructure() {
    const requiredDirectories = [
      '.github/chatmodes',
      '.github/prompts',
      '.github/validation',
      '.github/mcp',
    ];
    
    for (const dir of requiredDirectories) {
      const fullPath = join(this.rootPath, dir);
      const exists = await this.fileExists(fullPath);
      if (!exists) {
        throw new Error(`Required directory missing: ${dir}`);
      }
    }
    
    return { structureValid: true };
  }

  async checkDependencies() {
    const requiredFiles = [
      '.github/validation/validators/meta-instruction-validator.js',
      '.github/validation/templates/template-validation-system.js',
    ];
    
    const missingFiles = [];
    for (const file of requiredFiles) {
      const fullPath = join(this.rootPath, file);
      const exists = await this.fileExists(fullPath);
      if (!exists) {
        missingFiles.push(file);
      }
    }
    
    if (missingFiles.length > 0) {
      throw new Error(`Missing required files: ${missingFiles.join(', ')}`);
    }
    
    return { dependenciesValid: true };
  }

  async initializeWorkingDirectories() {
    const workingDirs = [
      this.reportsPath,
      join(this.reportsPath, 'temp'),
      join(this.reportsPath, 'archive'),
    ];
    
    for (const dir of workingDirs) {
      await fs.mkdir(dir, { recursive: true });
    }
    
    return { directoriesInitialized: true };
  }

  async loadConfigurationFiles() {
    const configFiles = [
      join(this.rootPath, '.github', 'validation', 'configs', 'validation-rules.json'),
      join(this.rootPath, '.github', 'validation', 'configs', 'quality-standards.json'),
    ];
    
    const loadedConfigs = {};
    for (const configFile of configFiles) {
      if (await this.fileExists(configFile)) {
        try {
          const content = await fs.readFile(configFile, 'utf8');
          const config = JSON.parse(content);
          loadedConfigs[configFile] = config;
        } catch (error) {
          console.log(`    ⚠️  Failed to load config: ${configFile}`);
        }
      }
    }
    
    return { configsLoaded: Object.keys(loadedConfigs).length };
  }

  async verifySystemResources() {
    const memoryUsage = process.memoryUsage();
    const memoryMB = memoryUsage.heapUsed / 1024 / 1024;
    
    if (memoryMB > 512) {
      console.log(`    ⚠️  High memory usage: ${memoryMB.toFixed(1)}MB`);
    }
    
    return { 
      memoryUsage: memoryMB,
      resourcesOk: memoryMB < 1024 
    };
  }

  async runValidator(validatorPath, args = []) {
    try {
      const command = `node "${validatorPath}" ${args.join(' ')}`;
      const { stdout, stderr } = await execAsync(command, { 
        cwd: this.rootPath,
        timeout: 30000 
      });
      
      let result;
      try {
        result = JSON.parse(stdout);
      } catch (error) {
        result = { output: stdout, stderr };
      }
      
      return { success: true, result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  aggregateValidationResults(validationResults) {
    let totalFiles = 0;
    let validFiles = 0;
    let totalErrors = 0;
    let totalWarnings = 0;
    
    for (const result of validationResults) {
      if (result.result && result.result.summary) {
        totalFiles += result.result.summary.totalFiles || 0;
        validFiles += result.result.summary.validFiles || 0;
        totalErrors += result.result.summary.errorCount || 0;
        totalWarnings += result.result.summary.warningCount || 0;
      }
    }
    
    const successRate = totalFiles > 0 ? (validFiles / totalFiles) * 100 : 0;
    
    return {
      totalFiles,
      validFiles,
      totalErrors,
      totalWarnings,
      successRate,
      validationTypes: validationResults.length,
    };
  }

  aggregateAllResults() {
    const aggregated = {
      sessionId: this.orchestrationState.sessionId,
      timestamp: new Date().toISOString(),
      validationResults: [],
      summary: {
        totalFiles: 0,
        validFiles: 0,
        errorCount: 0,
        warningCount: 0,
        successRate: 0,
      },
    };
    
    // Extract validation results
    const validationResult = this.orchestrationState.results.get('validation');
    if (validationResult && validationResult.validationResults) {
      aggregated.validationResults = validationResult.validationResults;
      if (validationResult.aggregatedResults) {
        aggregated.summary = {
          totalFiles: validationResult.aggregatedResults.totalFiles,
          validFiles: validationResult.aggregatedResults.validFiles,
          errorCount: validationResult.aggregatedResults.totalErrors,
          warningCount: validationResult.aggregatedResults.totalWarnings,
          successRate: validationResult.aggregatedResults.successRate,
        };
      }
    }
    
    return aggregated;
  }

  async findTestFiles() {
    const files = [];
    await this.scanDirectory(join(this.rootPath, '.github'), files);
    return files.filter(f => f.endsWith('.md') || f.endsWith('.js') || f.endsWith('.json'));
  }

  async scanDirectory(dir, files) {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = join(dir, entry.name);
        
        if (entry.isDirectory() && !entry.name.startsWith('.')) {
          await this.scanDirectory(fullPath, files);
        } else if (entry.isFile()) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Directory might not be readable
    }
  }

  async generateBasicReport() {
    const reportPath = join(this.reportsPath, `basic-report-${this.orchestrationState.sessionId}.md`);
    
    let content = `# Basic Orchestration Report\n\n`;
    content += `**Session ID**: ${this.orchestrationState.sessionId}\n`;
    content += `**Date**: ${new Date().toISOString()}\n\n`;
    
    content += `## Phase Summary\n\n`;
    content += `- **Completed**: ${this.orchestrationState.completedPhases.length}\n`;
    content += `- **Failed**: ${this.orchestrationState.failedPhases.length}\n`;
    content += `- **Skipped**: ${this.orchestrationState.skippedPhases.length}\n\n`;
    
    if (this.orchestrationState.failedPhases.length > 0) {
      content += `## Failed Phases\n\n`;
      this.orchestrationState.failedPhases.forEach(phase => {
        const result = this.orchestrationState.results.get(phase);
        content += `- **${phase}**: ${result?.error || 'Unknown error'}\n`;
      });
      content += `\n`;
    }
    
    content += `## Metrics\n\n`;
    content += `- **Total Duration**: ${this.orchestrationState.metrics.totalDuration}ms\n`;
    content += `- **Setup Time**: ${this.orchestrationState.metrics.setupTime}ms\n`;
    content += `- **Validation Time**: ${this.orchestrationState.metrics.validationTime}ms\n`;
    
    await fs.writeFile(reportPath, content);
    return reportPath;
  }

  // Cleanup and utility methods
  async archiveTestResults() {
    const archivePath = join(this.reportsPath, 'archive', `session-${this.orchestrationState.sessionId}`);
    await fs.mkdir(archivePath, { recursive: true });
    
    // Archive session data
    const sessionData = {
      sessionId: this.orchestrationState.sessionId,
      timestamp: new Date().toISOString(),
      state: this.orchestrationState,
      configuration: this.configuration,
    };
    
    await fs.writeFile(join(archivePath, 'session.json'), JSON.stringify(sessionData, null, 2));
    return { archived: true, path: archivePath };
  }

  async cleanTemporaryFiles() {
    const tempPath = join(this.reportsPath, 'temp');
    try {
      await fs.rmdir(tempPath, { recursive: true });
      await fs.mkdir(tempPath, { recursive: true });
      return { cleaned: true };
    } catch (error) {
      return { cleaned: false, error: error.message };
    }
  }

  async updateMetricsDatabase() {
    const metricsFile = join(this.reportsPath, 'metrics-history.json');
    
    let history = [];
    if (await this.fileExists(metricsFile)) {
      try {
        const content = await fs.readFile(metricsFile, 'utf8');
        history = JSON.parse(content);
      } catch (error) {
        // Start fresh if file is corrupted
      }
    }
    
    history.push({
      sessionId: this.orchestrationState.sessionId,
      timestamp: new Date().toISOString(),
      metrics: this.orchestrationState.metrics,
      success: this.orchestrationState.failedPhases.length === 0,
    });
    
    // Keep only last 100 entries
    if (history.length > 100) {
      history = history.slice(-100);
    }
    
    await fs.writeFile(metricsFile, JSON.stringify(history, null, 2));
    return { updated: true, entries: history.length };
  }

  async sendFinalNotifications() {
    if (this.configuration.notificationLevel === 'none') {
      return { sent: false, reason: 'notifications disabled' };
    }
    
    const notifications = [];
    
    if (this.orchestrationState.failedPhases.length > 0) {
      notifications.push({
        type: 'failure',
        message: `Orchestration failed: ${this.orchestrationState.failedPhases.length} phases failed`,
        phases: this.orchestrationState.failedPhases,
      });
    } else {
      notifications.push({
        type: 'success',
        message: `Orchestration completed successfully in ${this.orchestrationState.metrics.totalDuration}ms`,
        phases: this.orchestrationState.completedPhases,
      });
    }
    
    // In a real implementation, these would be sent via email, Slack, etc.
    console.log(`📨 Notifications: ${notifications.length} generated`);
    
    return { sent: true, count: notifications.length };
  }

  async generateOrchestrationReport() {
    const reportPath = join(this.reportsPath, `orchestration-${this.orchestrationState.sessionId}.json`);
    
    const report = {
      sessionId: this.orchestrationState.sessionId,
      timestamp: new Date().toISOString(),
      duration: this.orchestrationState.metrics.totalDuration,
      success: this.orchestrationState.failedPhases.length === 0,
      summary: {
        completedPhases: this.orchestrationState.completedPhases.length,
        failedPhases: this.orchestrationState.failedPhases.length,
        skippedPhases: this.orchestrationState.skippedPhases.length,
      },
      phaseResults: Object.fromEntries(this.orchestrationState.results),
      metrics: this.orchestrationState.metrics,
      configuration: this.configuration,
    };
    
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    return reportPath;
  }

  displayOrchestrationSummary() {
    console.log('\n🎭 Orchestration Summary:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`🆔 Session ID:         ${this.orchestrationState.sessionId}`);
    console.log(`⏱️  Total Duration:     ${this.orchestrationState.metrics.totalDuration}ms`);
    console.log(`✅ Completed Phases:   ${this.orchestrationState.completedPhases.length}`);
    console.log(`❌ Failed Phases:      ${this.orchestrationState.failedPhases.length}`);
    console.log(`⏭️  Skipped Phases:     ${this.orchestrationState.skippedPhases.length}`);
    
    if (this.orchestrationState.completedPhases.length > 0) {
      console.log('\n✅ Completed:');
      this.orchestrationState.completedPhases.forEach(phase => {
        const result = this.orchestrationState.results.get(phase);
        console.log(`   - ${this.testPhases.get(phase).name} (${result?.duration || 0}ms)`);
      });
    }
    
    if (this.orchestrationState.failedPhases.length > 0) {
      console.log('\n❌ Failed:');
      this.orchestrationState.failedPhases.forEach(phase => {
        const result = this.orchestrationState.results.get(phase);
        console.log(`   - ${this.testPhases.get(phase).name}: ${result?.error || 'Unknown error'}`);
      });
    }
    
    const overallStatus = this.orchestrationState.failedPhases.length === 0 ? 
      '🎉 SUCCESS' : '🚨 FAILURE';
    console.log(`\n🏁 Overall Status: ${overallStatus}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }

  // Configuration and utility methods
  async loadConfiguration() {
    try {
      const content = await fs.readFile(this.configPath, 'utf8');
      const config = JSON.parse(content);
      this.configuration = { ...this.configuration, ...config };
    } catch (error) {
      console.log('⚠️  Could not load configuration, using defaults');
    }
  }

  applyOptions(options) {
    if (options.phases) {
      this.configuration.enabledPhases = options.phases;
    }
    if (options.timeout) {
      this.configuration.timeoutMinutes = options.timeout;
    }
    if (options.skipIntegration) {
      this.configuration.enabledPhases = this.configuration.enabledPhases.filter(p => p !== 'integration');
    }
    if (options.skipPerformance) {
      this.configuration.enabledPhases = this.configuration.enabledPhases.filter(p => p !== 'performance');
    }
  }

  async validateEnvironment() {
    // Check Node.js version
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
    
    if (majorVersion < 16) {
      throw new Error(`Node.js version ${nodeVersion} is not supported. Requires Node.js 16+`);
    }
    
    // Check available memory
    const memoryUsage = process.memoryUsage();
    const totalMemoryMB = memoryUsage.heapTotal / 1024 / 1024;
    
    if (totalMemoryMB < 100) {
      console.log('⚠️  Low memory available, performance may be affected');
    }
    
    return { valid: true, nodeVersion, memoryMB: totalMemoryMB };
  }

  async sendNotifications() {
    if (this.configuration.notificationLevel === 'none') {
      return;
    }
    
    const shouldNotify = this.configuration.notificationLevel === 'all' || 
                        (this.configuration.notificationLevel === 'critical' && this.orchestrationState.failedPhases.length > 0);
    
    if (shouldNotify) {
      console.log('📨 Sending notifications...');
      // In a real implementation, this would send actual notifications
    }
  }

  async archiveResults() {
    console.log('📦 Archiving results...');
    await this.archiveTestResults();
  }

  async handleOrchestrationFailure(error) {
    console.log('🚨 Handling orchestration failure...');
    
    const failureReport = {
      sessionId: this.orchestrationState.sessionId,
      timestamp: new Date().toISOString(),
      error: error.message,
      failedPhases: this.orchestrationState.failedPhases,
      completedPhases: this.orchestrationState.completedPhases,
      state: this.orchestrationState,
    };
    
    const failureReportPath = join(this.reportsPath, `failure-${this.orchestrationState.sessionId}.json`);
    await fs.writeFile(failureReportPath, JSON.stringify(failureReport, null, 2));
    
    console.log(`💾 Failure report saved: ${failureReportPath}`);
  }

  generateSessionId() {
    return `orch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const orchestrator = new AutomatedTestOrchestrator({
    rootPath: process.cwd(),
  });
  
  const options = {};
  
  // Parse CLI arguments
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--skip-integration':
        options.skipIntegration = true;
        break;
      case '--skip-performance':
        options.skipPerformance = true;
        break;
      case '--timeout':
        options.timeout = parseInt(args[++i]) || 30;
        break;
      case '--phases':
        options.phases = args[++i].split(',');
        break;
    }
  }
  
  orchestrator.initialize()
    .then(() => orchestrator.executeOrchestration(options))
    .then(result => {
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('Orchestration failed:', error);
      process.exit(1);
    });
}

export { AutomatedTestOrchestrator };
