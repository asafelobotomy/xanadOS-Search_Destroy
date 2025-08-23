const fs = require('fs').promises;
const { performance } = require('perf_hooks');

class PerformanceMonitor {
  constructor() {
    this.metrics = {};
    this.thresholds = {
      fileProcessing: 100, // ms per file
      totalValidation: 5000, // ms total
      memoryUsage: 50 * 1024 * 1024 // 50MB
    };
  }

  startTimer(operation) {
    this.metrics[operation] = {
      start: performance.now(),
      memoryStart: process.memoryUsage()
    };
  }

  endTimer(operation) {
    if (!this.metrics[operation]) return null;
    
    const duration = performance.now() - this.metrics[operation].start;
    const memoryEnd = process.memoryUsage();
    const memoryDiff = memoryEnd.heapUsed - this.metrics[operation].memoryStart.heapUsed;
    
    this.metrics[operation] = {
      ...this.metrics[operation],
      duration,
      memoryUsage: memoryDiff,
      end: performance.now()
    };

    return this.metrics[operation];
  }

  getReport() {
    const report = {
      summary: {
        totalOperations: Object.keys(this.metrics).length,
        totalDuration: 0,
        averageDuration: 0,
        peakMemory: 0
      },
      operations: {},
      violations: []
    };

    for (const [operation, data] of Object.entries(this.metrics)) {
      if (data.duration) {
        report.summary.totalDuration += data.duration;
        report.summary.peakMemory = Math.max(report.summary.peakMemory, data.memoryUsage);
        
        report.operations[operation] = {
          duration: Math.round(data.duration * 100) / 100,
          memory: Math.round(data.memoryUsage / 1024 / 1024 * 100) / 100,
          status: this.evaluatePerformance(operation, data)
        };

        // Check thresholds
        if (data.duration > this.thresholds.fileProcessing) {
          report.violations.push({
            operation,
            type: 'SLOW_PROCESSING',
            actual: data.duration,
            threshold: this.thresholds.fileProcessing
          });
        }
      }
    }

    report.summary.averageDuration = report.summary.totalDuration / Object.keys(this.metrics).length;
    return report;
  }

  evaluatePerformance(operation, data) {
    if (data.duration < this.thresholds.fileProcessing * 0.5) return 'EXCELLENT';
    if (data.duration < this.thresholds.fileProcessing) return 'GOOD';
    if (data.duration < this.thresholds.fileProcessing * 2) return 'ACCEPTABLE';
    return 'NEEDS_OPTIMIZATION';
  }
}

module.exports = PerformanceMonitor;
