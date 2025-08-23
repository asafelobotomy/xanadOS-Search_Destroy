#!/usr/bin/env node

/**
 * Advanced Validation Reporting System
 * Comprehensive reporting and analytics for GitHub Copilot enhancement validation
 */

import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class ValidationReportingSystem {
  constructor(options = {}) {
    this.rootPath = options.rootPath || process.cwd();
    this.reportsPath = join(this.rootPath, '.github', 'validation', 'reports');
    
    this.reportTypes = new Map([
      ['comprehensive', { name: 'Comprehensive Analysis', priority: 1 }],
      ['summary', { name: 'Executive Summary', priority: 2 }],
      ['technical', { name: 'Technical Details', priority: 3 }],
      ['performance', { name: 'Performance Analysis', priority: 4 }],
      ['trends', { name: 'Trend Analysis', priority: 5 }],
    ]);
    
    this.metrics = {
      validationResults: [],
      performanceData: [],
      trendAnalysis: [],
      qualityScores: [],
      recommendations: [],
    };
    
    this.templates = {
      report: this.getReportTemplate(),
      dashboard: this.getDashboardTemplate(),
      notification: this.getNotificationTemplate(),
    };
  }

  async generateComprehensiveReport(validationData) {
    console.log('📊 Generating comprehensive validation report...');
    
    try {
      await fs.mkdir(this.reportsPath, { recursive: true });
      
      const timestamp = new Date().toISOString();
      const reportId = `validation-${timestamp.split('T')[0]}-${Date.now()}`;
      
      // Process validation data
      const processedData = await this.processValidationData(validationData);
      
      // Generate different report types
      const reports = await this.generateAllReportTypes(reportId, processedData);
      
      // Create dashboard
      const dashboard = await this.generateDashboard(reportId, processedData);
      
      // Generate trend analysis
      const trendAnalysis = await this.generateTrendAnalysis(processedData);
      
      // Create notification summaries
      const notifications = await this.generateNotifications(processedData);
      
      // Save report metadata
      const metadata = await this.saveReportMetadata(reportId, {
        timestamp,
        reports,
        dashboard,
        trendAnalysis,
        notifications,
        processedData,
      });
      
      console.log(`✅ Comprehensive report generated: ${reportId}`);
      return { reportId, metadata, files: reports };
      
    } catch (error) {
      console.error('❌ Failed to generate comprehensive report:', error);
      throw error;
    }
  }

  async processValidationData(rawData) {
    console.log('🔄 Processing validation data...');
    
    const processed = {
      timestamp: new Date().toISOString(),
      summary: {
        totalFiles: 0,
        validFiles: 0,
        invalidFiles: 0,
        warningFiles: 0,
        errorCount: 0,
        warningCount: 0,
        successRate: 0,
      },
      categories: new Map(),
      qualityMetrics: new Map(),
      performanceMetrics: {
        totalProcessingTime: 0,
        averageFileProcessingTime: 0,
        slowestFiles: [],
        fastestFiles: [],
      },
      trends: {
        qualityTrend: 'stable',
        performanceTrend: 'stable',
        errorTrend: 'stable',
      },
      recommendations: [],
      detailedResults: [],
    };

    // Process each validation result
    if (rawData.validationResults) {
      for (const result of rawData.validationResults) {
        await this.processValidationResult(result, processed);
      }
    }

    // Calculate summary metrics
    processed.summary.successRate = processed.summary.totalFiles > 0 
      ? (processed.summary.validFiles / processed.summary.totalFiles) * 100 
      : 0;

    // Calculate performance metrics
    if (processed.detailedResults.length > 0) {
      processed.performanceMetrics.averageFileProcessingTime = 
        processed.performanceMetrics.totalProcessingTime / processed.detailedResults.length;
      
      // Sort by processing time
      const sortedByTime = [...processed.detailedResults].sort((a, b) => b.processingTime - a.processingTime);
      processed.performanceMetrics.slowestFiles = sortedByTime.slice(0, 5);
      processed.performanceMetrics.fastestFiles = sortedByTime.slice(-5).reverse();
    }

    // Generate recommendations
    processed.recommendations = await this.generateRecommendations(processed);

    console.log(`✅ Processed ${processed.summary.totalFiles} files`);
    return processed;
  }

  async processValidationResult(result, processed) {
    processed.summary.totalFiles++;
    
    // Categorize result
    if (result.status === 'valid' || result.status === 'passed') {
      processed.summary.validFiles++;
    } else if (result.status === 'invalid' || result.status === 'failed') {
      processed.summary.invalidFiles++;
    } else if (result.status === 'warning') {
      processed.summary.warningFiles++;
    }
    
    // Count errors and warnings
    if (result.errors) {
      processed.summary.errorCount += Array.isArray(result.errors) ? result.errors.length : 1;
    }
    if (result.warnings) {
      processed.summary.warningCount += Array.isArray(result.warnings) ? result.warnings.length : 1;
    }
    
    // Categorize by file type or validation type
    const category = result.category || this.determineCategory(result.file || result.path);
    if (!processed.categories.has(category)) {
      processed.categories.set(category, {
        total: 0,
        valid: 0,
        invalid: 0,
        warnings: 0,
        errors: [],
      });
    }
    
    const categoryData = processed.categories.get(category);
    categoryData.total++;
    
    if (result.status === 'valid' || result.status === 'passed') {
      categoryData.valid++;
    } else {
      categoryData.invalid++;
    }
    
    if (result.warnings) {
      categoryData.warnings += Array.isArray(result.warnings) ? result.warnings.length : 1;
    }
    
    if (result.errors) {
      categoryData.errors.push(...(Array.isArray(result.errors) ? result.errors : [result.errors]));
    }
    
    // Track quality metrics
    if (result.qualityScore !== undefined) {
      if (!processed.qualityMetrics.has(category)) {
        processed.qualityMetrics.set(category, {
          scores: [],
          average: 0,
          min: Infinity,
          max: -Infinity,
        });
      }
      
      const qualityData = processed.qualityMetrics.get(category);
      qualityData.scores.push(result.qualityScore);
      qualityData.min = Math.min(qualityData.min, result.qualityScore);
      qualityData.max = Math.max(qualityData.max, result.qualityScore);
      qualityData.average = qualityData.scores.reduce((sum, score) => sum + score, 0) / qualityData.scores.length;
    }
    
    // Track performance
    if (result.processingTime !== undefined) {
      processed.performanceMetrics.totalProcessingTime += result.processingTime;
    }
    
    // Store detailed result
    processed.detailedResults.push({
      file: result.file || result.path,
      category,
      status: result.status,
      qualityScore: result.qualityScore,
      processingTime: result.processingTime || 0,
      errors: result.errors || [],
      warnings: result.warnings || [],
      details: result.details || {},
    });
  }

  determineCategory(filePath) {
    if (!filePath) return 'unknown';
    
    if (filePath.includes('/chatmodes/')) return 'chatmodes';
    if (filePath.includes('/prompts/')) return 'prompts';
    if (filePath.includes('/mcp/')) return 'mcp-servers';
    if (filePath.includes('/validation/')) return 'validation';
    if (filePath.endsWith('.md')) return 'documentation';
    if (filePath.endsWith('.js') || filePath.endsWith('.ts')) return 'code';
    if (filePath.endsWith('.json')) return 'configuration';
    
    return 'other';
  }

  async generateRecommendations(processedData) {
    const recommendations = [];
    
    // Quality-based recommendations
    if (processedData.summary.successRate < 80) {
      recommendations.push({
        priority: 'high',
        category: 'quality',
        title: 'Low Success Rate Detected',
        description: `Success rate is ${processedData.summary.successRate.toFixed(1)}%, which is below the 80% threshold.`,
        action: 'Review failed validations and address common issues',
        impact: 'high',
      });
    }
    
    // Performance-based recommendations
    if (processedData.performanceMetrics.averageFileProcessingTime > 1000) {
      recommendations.push({
        priority: 'medium',
        category: 'performance',
        title: 'Slow Processing Detected',
        description: `Average processing time is ${processedData.performanceMetrics.averageFileProcessingTime.toFixed(0)}ms per file.`,
        action: 'Optimize validation algorithms and consider parallel processing',
        impact: 'medium',
      });
    }
    
    // Category-specific recommendations
    for (const [category, data] of processedData.categories) {
      const successRate = (data.valid / data.total) * 100;
      
      if (successRate < 70 && data.total > 3) {
        recommendations.push({
          priority: 'medium',
          category: 'category-specific',
          title: `${category} Category Needs Attention`,
          description: `${category} has a ${successRate.toFixed(1)}% success rate with ${data.errors.length} errors.`,
          action: `Focus on improving ${category} validation rules and documentation`,
          impact: 'medium',
        });
      }
    }
    
    // Error pattern recommendations
    if (processedData.summary.errorCount > processedData.summary.totalFiles * 0.5) {
      recommendations.push({
        priority: 'high',
        category: 'errors',
        title: 'High Error Rate',
        description: `${processedData.summary.errorCount} errors across ${processedData.summary.totalFiles} files.`,
        action: 'Identify and fix common error patterns',
        impact: 'high',
      });
    }
    
    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  async generateAllReportTypes(reportId, processedData) {
    console.log('📝 Generating report types...');
    
    const reports = {};
    
    // Comprehensive report
    reports.comprehensive = await this.generateComprehensiveReportFile(reportId, processedData);
    
    // Executive summary
    reports.summary = await this.generateExecutiveSummary(reportId, processedData);
    
    // Technical details
    reports.technical = await this.generateTechnicalReport(reportId, processedData);
    
    // Performance analysis
    reports.performance = await this.generatePerformanceReport(reportId, processedData);
    
    // Trends analysis (if historical data exists)
    reports.trends = await this.generateTrendsReport(reportId, processedData);
    
    console.log('✅ All report types generated');
    return reports;
  }

  async generateComprehensiveReportFile(reportId, data) {
    const filePath = join(this.reportsPath, `${reportId}-comprehensive.md`);
    
    let content = `# Comprehensive Validation Report\n\n`;
    content += `**Report ID**: ${reportId}\n`;
    content += `**Generated**: ${data.timestamp}\n`;
    content += `**Total Files Analyzed**: ${data.summary.totalFiles}\n\n`;
    
    // Executive Summary
    content += `## Executive Summary\n\n`;
    content += `- **Success Rate**: ${data.summary.successRate.toFixed(1)}%\n`;
    content += `- **Valid Files**: ${data.summary.validFiles}\n`;
    content += `- **Invalid Files**: ${data.summary.invalidFiles}\n`;
    content += `- **Files with Warnings**: ${data.summary.warningFiles}\n`;
    content += `- **Total Errors**: ${data.summary.errorCount}\n`;
    content += `- **Total Warnings**: ${data.summary.warningCount}\n\n`;
    
    // Quality Assessment
    const qualityLevel = data.summary.successRate >= 90 ? 'Excellent' :
                        data.summary.successRate >= 80 ? 'Good' :
                        data.summary.successRate >= 70 ? 'Fair' : 'Needs Improvement';
    
    content += `### Overall Quality Assessment: ${qualityLevel}\n\n`;
    
    // Category Analysis
    content += `## Category Analysis\n\n`;
    for (const [category, categoryData] of data.categories) {
      const categorySuccessRate = (categoryData.valid / categoryData.total) * 100;
      content += `### ${category.charAt(0).toUpperCase() + category.slice(1)}\n\n`;
      content += `- **Files**: ${categoryData.total}\n`;
      content += `- **Success Rate**: ${categorySuccessRate.toFixed(1)}%\n`;
      content += `- **Errors**: ${categoryData.errors.length}\n`;
      content += `- **Warnings**: ${categoryData.warnings}\n\n`;
      
      if (categoryData.errors.length > 0) {
        content += `**Common Errors:**\n`;
        const errorCounts = {};
        categoryData.errors.forEach(error => {
          const errorMsg = typeof error === 'string' ? error : error.message || 'Unknown error';
          errorCounts[errorMsg] = (errorCounts[errorMsg] || 0) + 1;
        });
        
        Object.entries(errorCounts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .forEach(([error, count]) => {
            content += `- ${error} (${count} occurrences)\n`;
          });
        content += `\n`;
      }
    }
    
    // Quality Metrics
    if (data.qualityMetrics.size > 0) {
      content += `## Quality Metrics\n\n`;
      for (const [category, metrics] of data.qualityMetrics) {
        content += `### ${category}\n\n`;
        content += `- **Average Score**: ${metrics.average.toFixed(2)}\n`;
        content += `- **Min Score**: ${metrics.min.toFixed(2)}\n`;
        content += `- **Max Score**: ${metrics.max.toFixed(2)}\n`;
        content += `- **Score Distribution**: ${metrics.scores.length} files scored\n\n`;
      }
    }
    
    // Performance Analysis
    content += `## Performance Analysis\n\n`;
    content += `- **Total Processing Time**: ${data.performanceMetrics.totalProcessingTime}ms\n`;
    content += `- **Average Time per File**: ${data.performanceMetrics.averageFileProcessingTime.toFixed(0)}ms\n\n`;
    
    if (data.performanceMetrics.slowestFiles.length > 0) {
      content += `### Slowest Files\n\n`;
      data.performanceMetrics.slowestFiles.forEach((file, index) => {
        content += `${index + 1}. **${file.file}** - ${file.processingTime}ms\n`;
      });
      content += `\n`;
    }
    
    // Recommendations
    if (data.recommendations.length > 0) {
      content += `## Recommendations\n\n`;
      data.recommendations.forEach((rec, index) => {
        const priorityEmoji = rec.priority === 'high' ? '🔴' : rec.priority === 'medium' ? '🟡' : '🟢';
        content += `### ${index + 1}. ${priorityEmoji} ${rec.title}\n\n`;
        content += `**Priority**: ${rec.priority.toUpperCase()}\n`;
        content += `**Category**: ${rec.category}\n`;
        content += `**Impact**: ${rec.impact}\n\n`;
        content += `**Description**: ${rec.description}\n\n`;
        content += `**Recommended Action**: ${rec.action}\n\n`;
      });
    }
    
    // Detailed Results
    content += `## Detailed Results\n\n`;
    const groupedResults = {};
    data.detailedResults.forEach(result => {
      if (!groupedResults[result.category]) {
        groupedResults[result.category] = [];
      }
      groupedResults[result.category].push(result);
    });
    
    for (const [category, results] of Object.entries(groupedResults)) {
      content += `### ${category}\n\n`;
      results.forEach(result => {
        const statusEmoji = result.status === 'valid' || result.status === 'passed' ? '✅' : 
                           result.status === 'warning' ? '⚠️' : '❌';
        content += `- ${statusEmoji} **${result.file}**`;
        if (result.qualityScore !== undefined) {
          content += ` (Quality: ${result.qualityScore.toFixed(2)})`;
        }
        if (result.processingTime > 0) {
          content += ` (${result.processingTime}ms)`;
        }
        content += `\n`;
        
        if (result.errors.length > 0) {
          result.errors.forEach(error => {
            content += `  - ❌ ${typeof error === 'string' ? error : error.message}\n`;
          });
        }
        
        if (result.warnings.length > 0) {
          result.warnings.forEach(warning => {
            content += `  - ⚠️ ${typeof warning === 'string' ? warning : warning.message}\n`;
          });
        }
      });
      content += `\n`;
    }
    
    await fs.writeFile(filePath, content);
    return filePath;
  }

  async generateExecutiveSummary(reportId, data) {
    const filePath = join(this.reportsPath, `${reportId}-summary.md`);
    
    let content = `# Executive Summary - Validation Report\n\n`;
    content += `**Report Date**: ${new Date(data.timestamp).toLocaleDateString()}\n`;
    content += `**Files Analyzed**: ${data.summary.totalFiles}\n\n`;
    
    // Key Metrics
    content += `## Key Metrics\n\n`;
    content += `| Metric | Value | Status |\n`;
    content += `|--------|-------|--------|\n`;
    content += `| Success Rate | ${data.summary.successRate.toFixed(1)}% | ${data.summary.successRate >= 80 ? '✅ Good' : '⚠️ Needs Attention'} |\n`;
    content += `| Valid Files | ${data.summary.validFiles} | - |\n`;
    content += `| Invalid Files | ${data.summary.invalidFiles} | ${data.summary.invalidFiles === 0 ? '✅ None' : '⚠️ Review Required'} |\n`;
    content += `| Total Errors | ${data.summary.errorCount} | ${data.summary.errorCount === 0 ? '✅ None' : '⚠️ Action Required'} |\n\n`;
    
    // Top Priority Actions
    const highPriorityRecs = data.recommendations.filter(r => r.priority === 'high');
    if (highPriorityRecs.length > 0) {
      content += `## 🔴 High Priority Actions Required\n\n`;
      highPriorityRecs.forEach((rec, index) => {
        content += `${index + 1}. **${rec.title}**\n`;
        content += `   - ${rec.action}\n\n`;
      });
    } else {
      content += `## ✅ No High Priority Issues\n\n`;
    }
    
    // Category Performance
    content += `## Category Performance\n\n`;
    const sortedCategories = Array.from(data.categories.entries())
      .sort((a, b) => (b[1].valid / b[1].total) - (a[1].valid / a[1].total));
    
    sortedCategories.forEach(([category, categoryData]) => {
      const successRate = (categoryData.valid / categoryData.total) * 100;
      const status = successRate >= 80 ? '✅' : successRate >= 60 ? '⚠️' : '❌';
      content += `- ${status} **${category}**: ${successRate.toFixed(1)}% (${categoryData.valid}/${categoryData.total})\n`;
    });
    
    content += `\n## Next Steps\n\n`;
    if (data.recommendations.length > 0) {
      content += `1. Address ${highPriorityRecs.length} high priority recommendations\n`;
      content += `2. Review detailed report for specific actions\n`;
      content += `3. Implement quality improvements\n`;
      content += `4. Schedule follow-up validation\n`;
    } else {
      content += `1. Maintain current quality standards\n`;
      content += `2. Continue regular validation monitoring\n`;
      content += `3. Consider advanced quality enhancements\n`;
    }
    
    await fs.writeFile(filePath, content);
    return filePath;
  }

  async generateTechnicalReport(reportId, data) {
    const filePath = join(this.reportsPath, `${reportId}-technical.json`);
    
    const technicalData = {
      reportId,
      timestamp: data.timestamp,
      metadata: {
        generator: 'ValidationReportingSystem',
        version: '1.0.0',
        environment: process.env.NODE_ENV || 'development',
      },
      summary: data.summary,
      categories: Object.fromEntries(data.categories),
      qualityMetrics: Object.fromEntries(data.qualityMetrics),
      performanceMetrics: data.performanceMetrics,
      detailedResults: data.detailedResults,
      recommendations: data.recommendations,
      rawData: data,
    };
    
    await fs.writeFile(filePath, JSON.stringify(technicalData, null, 2));
    return filePath;
  }

  async generatePerformanceReport(reportId, data) {
    const filePath = join(this.reportsPath, `${reportId}-performance.md`);
    
    let content = `# Performance Analysis Report\n\n`;
    content += `**Report ID**: ${reportId}\n`;
    content += `**Analysis Date**: ${new Date(data.timestamp).toLocaleDateString()}\n\n`;
    
    // Performance Summary
    content += `## Performance Summary\n\n`;
    content += `- **Total Processing Time**: ${data.performanceMetrics.totalProcessingTime}ms\n`;
    content += `- **Average Time per File**: ${data.performanceMetrics.averageFileProcessingTime.toFixed(2)}ms\n`;
    content += `- **Files Processed**: ${data.summary.totalFiles}\n`;
    content += `- **Processing Rate**: ${(data.summary.totalFiles / (data.performanceMetrics.totalProcessingTime / 1000)).toFixed(2)} files/second\n\n`;
    
    // Performance Categories
    const performanceRating = data.performanceMetrics.averageFileProcessingTime < 100 ? 'Excellent' :
                             data.performanceMetrics.averageFileProcessingTime < 500 ? 'Good' :
                             data.performanceMetrics.averageFileProcessingTime < 1000 ? 'Fair' : 'Needs Improvement';
    
    content += `### Performance Rating: ${performanceRating}\n\n`;
    
    // Slowest Files
    if (data.performanceMetrics.slowestFiles.length > 0) {
      content += `## Slowest Processing Files\n\n`;
      content += `| File | Processing Time | Category | Status |\n`;
      content += `|------|----------------|----------|--------|\n`;
      data.performanceMetrics.slowestFiles.forEach(file => {
        content += `| ${file.file} | ${file.processingTime}ms | ${file.category} | ${file.status} |\n`;
      });
      content += `\n`;
    }
    
    // Fastest Files
    if (data.performanceMetrics.fastestFiles.length > 0) {
      content += `## Fastest Processing Files\n\n`;
      content += `| File | Processing Time | Category | Status |\n`;
      content += `|------|----------------|----------|--------|\n`;
      data.performanceMetrics.fastestFiles.forEach(file => {
        content += `| ${file.file} | ${file.processingTime}ms | ${file.category} | ${file.status} |\n`;
      });
      content += `\n`;
    }
    
    // Performance by Category
    content += `## Performance by Category\n\n`;
    const categoryPerformance = new Map();
    data.detailedResults.forEach(result => {
      if (!categoryPerformance.has(result.category)) {
        categoryPerformance.set(result.category, {
          totalTime: 0,
          fileCount: 0,
          averageTime: 0,
        });
      }
      const catPerf = categoryPerformance.get(result.category);
      catPerf.totalTime += result.processingTime;
      catPerf.fileCount++;
      catPerf.averageTime = catPerf.totalTime / catPerf.fileCount;
    });
    
    const sortedCategoryPerf = Array.from(categoryPerformance.entries())
      .sort((a, b) => b[1].averageTime - a[1].averageTime);
    
    content += `| Category | Files | Average Time | Total Time |\n`;
    content += `|----------|-------|--------------|------------|\n`;
    sortedCategoryPerf.forEach(([category, perf]) => {
      content += `| ${category} | ${perf.fileCount} | ${perf.averageTime.toFixed(2)}ms | ${perf.totalTime}ms |\n`;
    });
    
    // Performance Recommendations
    content += `\n## Performance Recommendations\n\n`;
    const perfRecommendations = data.recommendations.filter(r => r.category === 'performance');
    if (perfRecommendations.length > 0) {
      perfRecommendations.forEach((rec, index) => {
        content += `${index + 1}. **${rec.title}**\n`;
        content += `   - ${rec.action}\n\n`;
      });
    } else {
      content += `✅ No specific performance recommendations at this time.\n\n`;
    }
    
    await fs.writeFile(filePath, content);
    return filePath;
  }

  async generateTrendsReport(reportId, data) {
    const filePath = join(this.reportsPath, `${reportId}-trends.md`);
    
    let content = `# Trends Analysis Report\n\n`;
    content += `**Report ID**: ${reportId}\n`;
    content += `**Analysis Date**: ${new Date(data.timestamp).toLocaleDateString()}\n\n`;
    
    // Note about historical data
    content += `## Historical Trend Analysis\n\n`;
    content += `*This report shows trends based on available historical validation data.*\n\n`;
    
    try {
      // Try to load historical data
      const historicalData = await this.loadHistoricalData();
      
      if (historicalData.length > 1) {
        content += await this.generateTrendAnalysis(historicalData, data);
      } else {
        content += `### Insufficient Historical Data\n\n`;
        content += `This is the first report or insufficient historical data is available for trend analysis.\n`;
        content += `Trend analysis will be available after multiple validation runs.\n\n`;
        
        content += `### Current Baseline Metrics\n\n`;
        content += `- **Success Rate**: ${data.summary.successRate.toFixed(1)}%\n`;
        content += `- **Average Processing Time**: ${data.performanceMetrics.averageFileProcessingTime.toFixed(2)}ms\n`;
        content += `- **Error Rate**: ${((data.summary.errorCount / data.summary.totalFiles) * 100).toFixed(1)}%\n`;
      }
    } catch (error) {
      content += `### Trend Analysis Unavailable\n\n`;
      content += `Unable to perform trend analysis: ${error.message}\n\n`;
    }
    
    await fs.writeFile(filePath, content);
    return filePath;
  }

  async generateDashboard(reportId, data) {
    const filePath = join(this.reportsPath, `${reportId}-dashboard.html`);
    
    const htmlContent = this.templates.dashboard
      .replace(/{{REPORT_ID}}/g, reportId)
      .replace(/{{TIMESTAMP}}/g, data.timestamp)
      .replace(/{{SUCCESS_RATE}}/g, data.summary.successRate.toFixed(1))
      .replace(/{{TOTAL_FILES}}/g, data.summary.totalFiles)
      .replace(/{{VALID_FILES}}/g, data.summary.validFiles)
      .replace(/{{INVALID_FILES}}/g, data.summary.invalidFiles)
      .replace(/{{ERROR_COUNT}}/g, data.summary.errorCount)
      .replace(/{{WARNING_COUNT}}/g, data.summary.warningCount)
      .replace(/{{PROCESSING_TIME}}/g, data.performanceMetrics.totalProcessingTime)
      .replace(/{{CATEGORIES_DATA}}/g, JSON.stringify(Array.from(data.categories.entries())))
      .replace(/{{RECOMMENDATIONS_DATA}}/g, JSON.stringify(data.recommendations));
    
    await fs.writeFile(filePath, htmlContent);
    return filePath;
  }

  async generateNotifications(data) {
    const notifications = [];
    
    // Critical notifications
    if (data.summary.successRate < 60) {
      notifications.push({
        type: 'critical',
        title: 'Critical Quality Issues Detected',
        message: `Success rate is ${data.summary.successRate.toFixed(1)}%, immediate action required.`,
        actions: ['Review failed validations', 'Fix critical errors', 'Update validation rules'],
      });
    }
    
    // Warning notifications
    if (data.summary.errorCount > data.summary.totalFiles * 0.3) {
      notifications.push({
        type: 'warning',
        title: 'High Error Rate',
        message: `${data.summary.errorCount} errors detected across ${data.summary.totalFiles} files.`,
        actions: ['Identify error patterns', 'Update documentation', 'Improve validation'],
      });
    }
    
    // Performance notifications
    if (data.performanceMetrics.averageFileProcessingTime > 1000) {
      notifications.push({
        type: 'info',
        title: 'Performance Degradation',
        message: `Average processing time is ${data.performanceMetrics.averageFileProcessingTime.toFixed(0)}ms.`,
        actions: ['Optimize validation algorithms', 'Consider parallel processing'],
      });
    }
    
    // Success notifications
    if (data.summary.successRate >= 95) {
      notifications.push({
        type: 'success',
        title: 'Excellent Validation Results',
        message: `${data.summary.successRate.toFixed(1)}% success rate achieved.`,
        actions: ['Maintain quality standards', 'Consider advanced features'],
      });
    }
    
    // Save notifications
    const notificationsFile = join(this.reportsPath, 'notifications.json');
    await fs.writeFile(notificationsFile, JSON.stringify(notifications, null, 2));
    
    return notifications;
  }

  async saveReportMetadata(reportId, reportData) {
    const metadataFile = join(this.reportsPath, `${reportId}-metadata.json`);
    
    const metadata = {
      reportId,
      timestamp: reportData.timestamp,
      generator: 'ValidationReportingSystem',
      version: '1.0.0',
      files: reportData.reports,
      dashboard: reportData.dashboard,
      summary: {
        totalFiles: reportData.processedData.summary.totalFiles,
        successRate: reportData.processedData.summary.successRate,
        criticalIssues: reportData.processedData.recommendations.filter(r => r.priority === 'high').length,
      },
      processingTime: Date.now() - new Date(reportData.timestamp).getTime(),
    };
    
    await fs.writeFile(metadataFile, JSON.stringify(metadata, null, 2));
    return metadata;
  }

  async loadHistoricalData() {
    try {
      const files = await fs.readdir(this.reportsPath);
      const metadataFiles = files.filter(f => f.endsWith('-metadata.json'));
      
      const historicalData = [];
      for (const file of metadataFiles) {
        try {
          const content = await fs.readFile(join(this.reportsPath, file), 'utf8');
          const metadata = JSON.parse(content);
          historicalData.push(metadata);
        } catch (error) {
          // Skip invalid metadata files
        }
      }
      
      return historicalData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    } catch (error) {
      return [];
    }
  }

  async generateTrendAnalysis(historicalData, currentData) {
    let content = `### Quality Trends\n\n`;
    
    if (historicalData.length >= 2) {
      const latest = historicalData[historicalData.length - 1];
      const previous = historicalData[historicalData.length - 2];
      
      const successRateTrend = currentData.summary.successRate - previous.summary.successRate;
      const trendDirection = successRateTrend > 1 ? '📈 Improving' : 
                           successRateTrend < -1 ? '📉 Declining' : '➡️ Stable';
      
      content += `- **Success Rate Trend**: ${trendDirection} (${successRateTrend > 0 ? '+' : ''}${successRateTrend.toFixed(1)}%)\n`;
      content += `- **Current Success Rate**: ${currentData.summary.successRate.toFixed(1)}%\n`;
      content += `- **Previous Success Rate**: ${previous.summary.successRate.toFixed(1)}%\n\n`;
      
      // Generate chart data for the last 10 reports
      const recentData = historicalData.slice(-10);
      content += `### Recent Success Rate History\n\n`;
      content += `| Date | Success Rate | Change |\n`;
      content += `|------|--------------|--------|\n`;
      
      for (let i = 0; i < recentData.length; i++) {
        const report = recentData[i];
        const change = i > 0 ? report.summary.successRate - recentData[i-1].summary.successRate : 0;
        const changeText = i === 0 ? '-' : `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
        content += `| ${new Date(report.timestamp).toLocaleDateString()} | ${report.summary.successRate.toFixed(1)}% | ${changeText} |\n`;
      }
    }
    
    return content;
  }

  getReportTemplate() {
    return `# Validation Report

**Generated**: {{TIMESTAMP}}
**Report ID**: {{REPORT_ID}}

## Summary
- Success Rate: {{SUCCESS_RATE}}%
- Total Files: {{TOTAL_FILES}}
- Valid Files: {{VALID_FILES}}
- Invalid Files: {{INVALID_FILES}}

## Details
{{DETAILED_CONTENT}}

## Recommendations
{{RECOMMENDATIONS}}
`;
  }

  getDashboardTemplate() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validation Dashboard - {{REPORT_ID}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2d3748; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #2d3748; }
        .metric-label { color: #718096; margin-top: 5px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .recommendations { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .rec-high { border-left: 4px solid #e53e3e; }
        .rec-medium { border-left: 4px solid #d69e2e; }
        .rec-low { border-left: 4px solid #38a169; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Validation Dashboard</h1>
            <p>Report: {{REPORT_ID}} | Generated: {{TIMESTAMP}}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{{SUCCESS_RATE}}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{TOTAL_FILES}}</div>
                <div class="metric-label">Total Files</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{VALID_FILES}}</div>
                <div class="metric-label">Valid Files</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ERROR_COUNT}}</div>
                <div class="metric-label">Errors</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Category Analysis</h3>
            <div id="categoryChart"></div>
        </div>
        
        <div class="recommendations">
            <h3>Recommendations</h3>
            <div id="recommendationsList"></div>
        </div>
    </div>
    
    <script>
        // Simple visualization
        const categories = {{CATEGORIES_DATA}};
        const recommendations = {{RECOMMENDATIONS_DATA}};
        
        // Render category chart
        const chartDiv = document.getElementById('categoryChart');
        categories.forEach(([name, data]) => {
            const successRate = (data.valid / data.total * 100).toFixed(1);
            chartDiv.innerHTML += \`
                <div style="margin: 10px 0; padding: 10px; border: 1px solid #e2e8f0; border-radius: 4px;">
                    <strong>\${name}</strong>: \${successRate}% (\${data.valid}/\${data.total})
                    <div style="background: #e2e8f0; height: 10px; border-radius: 5px; margin-top: 5px;">
                        <div style="background: #48bb78; height: 100%; width: \${successRate}%; border-radius: 5px;"></div>
                    </div>
                </div>
            \`;
        });
        
        // Render recommendations
        const recDiv = document.getElementById('recommendationsList');
        recommendations.forEach(rec => {
            const priorityClass = \`rec-\${rec.priority}\`;
            recDiv.innerHTML += \`
                <div class="\${priorityClass}" style="margin: 10px 0; padding: 15px; border-radius: 4px;">
                    <h4>\${rec.title}</h4>
                    <p><strong>Priority:</strong> \${rec.priority.toUpperCase()}</p>
                    <p>\${rec.description}</p>
                    <p><strong>Action:</strong> \${rec.action}</p>
                </div>
            \`;
        });
    </script>
</body>
</html>`;
  }

  getNotificationTemplate() {
    return `# Validation Notification

**Type**: {{TYPE}}
**Title**: {{TITLE}}
**Time**: {{TIMESTAMP}}

## Message
{{MESSAGE}}

## Recommended Actions
{{ACTIONS}}

---
Generated by Validation Reporting System
`;
  }

  async generateQuickReport(data) {
    console.log('⚡ Generating quick validation report...');
    
    const timestamp = new Date().toISOString();
    const quickReportPath = join(this.reportsPath, `quick-report-${timestamp.split('T')[0]}.md`);
    
    let content = `# Quick Validation Report\n\n`;
    content += `**Generated**: ${timestamp}\n\n`;
    
    if (data.summary) {
      content += `## Summary\n\n`;
      content += `- **Files**: ${data.summary.totalFiles || 0}\n`;
      content += `- **Success Rate**: ${(data.summary.successRate || 0).toFixed(1)}%\n`;
      content += `- **Errors**: ${data.summary.errorCount || 0}\n`;
      content += `- **Warnings**: ${data.summary.warningCount || 0}\n\n`;
    }
    
    if (data.recommendations && data.recommendations.length > 0) {
      const criticalRecs = data.recommendations.filter(r => r.priority === 'high');
      if (criticalRecs.length > 0) {
        content += `## 🔴 Critical Issues\n\n`;
        criticalRecs.forEach(rec => {
          content += `- **${rec.title}**: ${rec.action}\n`;
        });
        content += `\n`;
      }
    }
    
    content += `## Status\n\n`;
    const overallStatus = (data.summary?.successRate || 0) >= 80 ? '✅ Good' : '⚠️ Needs Attention';
    content += `Overall: ${overallStatus}\n`;
    
    await fs.mkdir(this.reportsPath, { recursive: true });
    await fs.writeFile(quickReportPath, content);
    
    console.log(`✅ Quick report saved: ${quickReportPath}`);
    return quickReportPath;
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const reportingSystem = new ValidationReportingSystem({
    rootPath: process.cwd(),
  });
  
  // Example usage - in real usage, this would receive actual validation data
  const sampleData = {
    validationResults: [
      { file: 'test1.md', status: 'valid', category: 'documentation', qualityScore: 8.5, processingTime: 150 },
      { file: 'test2.md', status: 'failed', category: 'chatmodes', errors: ['Missing description'], processingTime: 200 },
    ],
  };
  
  if (process.argv.includes('--quick')) {
    reportingSystem.generateQuickReport({ summary: { totalFiles: 2, successRate: 50, errorCount: 1, warningCount: 0 } });
  } else {
    reportingSystem.generateComprehensiveReport(sampleData);
  }
}

export { ValidationReportingSystem };
