const WCAGChecker = require('./wcag-compliance-checker');
const PerformanceMonitor = require('./performance-monitor');

class EnterpriseValidator {
  constructor() {
    this.wcagChecker = new WCAGChecker();
    this.perfMonitor = new PerformanceMonitor();
    this.enterpriseRules = {
      maxFileSize: 50 * 1024, // 50KB
      requiredSections: ['Title', 'Description', 'Usage'],
      securityKeywords: ['password', 'token', 'secret', 'key', 'auth'],
      performanceTargets: {
        loadTime: 100, // ms
        memoryUsage: 10 * 1024 * 1024 // 10MB
      }
    };
  }

  async validateEnterpriseStandards(filePath) {
    this.perfMonitor.startTimer(`enterprise-${filePath}`);
    
    const results = {
      wcagCompliance: await this.wcagChecker.checkFile(filePath),
      securityReview: await this.checkSecurityStandards(filePath),
      performanceCheck: await this.checkPerformanceStandards(filePath),
      enterpriseCompliance: await this.checkEnterpriseCompliance(filePath)
    };

    this.perfMonitor.endTimer(`enterprise-${filePath}`);
    
    return {
      ...results,
      overallScore: this.calculateEnterpriseScore(results),
      recommendations: this.generateRecommendations(results)
    };
  }

  async checkSecurityStandards(filePath) {
    const content = await require('fs').promises.readFile(filePath, 'utf8');
    const violations = [];
    
    // Check for exposed secrets
    this.enterpriseRules.securityKeywords.forEach(keyword => {
      const regex = new RegExp(`${keyword}\\s*[=:]\\s*['"\\`]([^'"\\`\\s]+)`, 'gi');
      if (regex.test(content)) {
        violations.push({
          type: 'POTENTIAL_SECRET_EXPOSURE',
          keyword,
          message: `Potential hardcoded ${keyword} detected`
        });
      }
    });

    return { violations, isSecure: violations.length === 0 };
  }

  async checkPerformanceStandards(filePath) {
    const stats = await require('fs').promises.stat(filePath);
    const issues = [];
    
    if (stats.size > this.enterpriseRules.maxFileSize) {
      issues.push({
        type: 'FILE_SIZE_VIOLATION',
        actual: stats.size,
        limit: this.enterpriseRules.maxFileSize
      });
    }

    return { issues, meetsStandards: issues.length === 0 };
  }

  async checkEnterpriseCompliance(filePath) {
    const content = await require('fs').promises.readFile(filePath, 'utf8');
    const compliance = {
      hasRequiredSections: true,
      hasVersionInfo: content.includes('version') || content.includes('Version'),
      hasOwnerInfo: content.includes('owner') || content.includes('Author'),
      hasLastUpdated: content.includes('updated') || content.includes('Date'),
      hasComplianceStatement: content.includes('compliance') || content.includes('standard')
    };

    const score = Object.values(compliance).filter(Boolean).length / Object.keys(compliance).length;
    
    return { ...compliance, score };
  }

  calculateEnterpriseScore(results) {
    const weights = {
      wcagCompliance: 0.25,
      securityReview: 0.35,
      performanceCheck: 0.20,
      enterpriseCompliance: 0.20
    };

    let totalScore = 0;
    totalScore += (results.wcagCompliance.isCompliant ? 1 : 0) * weights.wcagCompliance;
    totalScore += (results.securityReview.isSecure ? 1 : 0) * weights.securityReview;
    totalScore += (results.performanceCheck.meetsStandards ? 1 : 0) * weights.performanceCheck;
    totalScore += results.enterpriseCompliance.score * weights.enterpriseCompliance;

    return Math.round(totalScore * 100);
  }

  generateRecommendations(results) {
    const recommendations = [];
    
    if (!results.wcagCompliance.isCompliant) {
      recommendations.push('Improve accessibility compliance (WCAG 2.1)');
    }
    
    if (!results.securityReview.isSecure) {
      recommendations.push('Address security vulnerabilities');
    }
    
    if (!results.performanceCheck.meetsStandards) {
      recommendations.push('Optimize file size and performance');
    }
    
    if (results.enterpriseCompliance.score < 0.8) {
      recommendations.push('Add required enterprise metadata');
    }

    return recommendations;
  }
}

module.exports = EnterpriseValidator;
