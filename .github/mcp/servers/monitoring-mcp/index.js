#!/usr/bin/env node

/**
 * Monitoring MCP Server
 * Provides system health monitoring and alert management capabilities
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { promises as fs } from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

class MonitoringMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'monitoring-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
          notifications: {},
        },
      }
    );
    
    this.cache = new Map();
    this.cacheTimeout = 30 * 1000; // 30 seconds for system metrics
    this.alertsFile = process.env.ALERTS_FILE || '/tmp/monitoring-alerts.json';
    this.metricsEndpoints = this.parseMetricsEndpoints();
    
    this.setupHandlers();
  }

  parseMetricsEndpoints() {
    const endpoints = process.env.METRICS_ENDPOINTS || '';
    if (!endpoints) return [];
    
    return endpoints.split(',').map(endpoint => {
      const [name, url] = endpoint.split('=');
      return { name: name.trim(), url: url.trim() };
    });
  }

  setupHandlers() {
    // List available monitoring resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      try {
        const resources = [
          {
            uri: 'monitor://system/health',
            mimeType: 'application/json',
            name: 'System Health',
            description: 'Overall system health metrics including CPU, memory, and disk usage',
          },
          {
            uri: 'monitor://system/processes',
            mimeType: 'application/json',
            name: 'System Processes',
            description: 'Running processes and resource consumption',
          },
          {
            uri: 'monitor://system/network',
            mimeType: 'application/json',
            name: 'Network Status',
            description: 'Network interfaces and connectivity status',
          },
          {
            uri: 'monitor://alerts/active',
            mimeType: 'application/json',
            name: 'Active Alerts',
            description: 'Currently active monitoring alerts',
          },
          {
            uri: 'monitor://alerts/history',
            mimeType: 'application/json',
            name: 'Alert History',
            description: 'Historical alert data and trends',
          },
        ];
        
        // Add endpoint-specific resources
        this.metricsEndpoints.forEach(endpoint => {
          resources.push({
            uri: `monitor://endpoint/${endpoint.name}`,
            mimeType: 'application/json',
            name: `${endpoint.name} Metrics`,
            description: `Metrics from ${endpoint.url}`,
          });
        });
        
        return { resources };
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to list monitoring resources: ${error.message}`
        );
      }
    });

    // Read monitoring data
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      
      try {
        const match = uri.match(/^monitor:\/\/(.+?)\/(.+)$/);
        if (!match) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid monitoring URI: ${uri}`
          );
        }
        
        const [, category, type] = match;
        let content = {};
        
        switch (category) {
          case 'system':
            switch (type) {
              case 'health':
                content = await this.getSystemHealth();
                break;
              case 'processes':
                content = await this.getSystemProcesses();
                break;
              case 'network':
                content = await this.getNetworkStatus();
                break;
              default:
                throw new McpError(
                  ErrorCode.InvalidRequest,
                  `Unknown system monitoring type: ${type}`
                );
            }
            break;
          case 'alerts':
            switch (type) {
              case 'active':
                content = await this.getActiveAlerts();
                break;
              case 'history':
                content = await this.getAlertHistory();
                break;
              default:
                throw new McpError(
                  ErrorCode.InvalidRequest,
                  `Unknown alert type: ${type}`
                );
            }
            break;
          case 'endpoint':
            content = await this.getEndpointMetrics(type);
            break;
          default:
            throw new McpError(
              ErrorCode.InvalidRequest,
              `Unknown monitoring category: ${category}`
            );
        }
        
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(content, null, 2),
            },
          ],
        };
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to read monitoring data: ${error.message}`
        );
      }
    });

    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'check_service_health',
            description: 'Check the health of a specific service or endpoint',
            inputSchema: {
              type: 'object',
              properties: {
                service: {
                  type: 'string',
                  description: 'Service name or URL to check',
                },
                timeout: {
                  type: 'number',
                  description: 'Timeout in seconds',
                  default: 10,
                  minimum: 1,
                  maximum: 60,
                },
              },
              required: ['service'],
            },
          },
          {
            name: 'create_alert',
            description: 'Create a new monitoring alert',
            inputSchema: {
              type: 'object',
              properties: {
                name: {
                  type: 'string',
                  description: 'Alert name',
                },
                description: {
                  type: 'string',
                  description: 'Alert description',
                },
                severity: {
                  type: 'string',
                  enum: ['low', 'medium', 'high', 'critical'],
                  description: 'Alert severity level',
                },
                condition: {
                  type: 'string',
                  description: 'Alert condition/trigger',
                },
                tags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Alert tags for categorization',
                },
              },
              required: ['name', 'description', 'severity'],
            },
          },
          {
            name: 'resolve_alert',
            description: 'Resolve an existing alert',
            inputSchema: {
              type: 'object',
              properties: {
                alert_id: {
                  type: 'string',
                  description: 'Alert ID to resolve',
                },
                resolution_note: {
                  type: 'string',
                  description: 'Note about how the alert was resolved',
                },
              },
              required: ['alert_id'],
            },
          },
          {
            name: 'get_metrics',
            description: 'Get specific metrics with custom parameters',
            inputSchema: {
              type: 'object',
              properties: {
                metric_type: {
                  type: 'string',
                  enum: ['cpu', 'memory', 'disk', 'network', 'custom'],
                  description: 'Type of metrics to retrieve',
                },
                time_range: {
                  type: 'string',
                  enum: ['1m', '5m', '15m', '1h', '6h', '24h'],
                  description: 'Time range for metrics',
                  default: '5m',
                },
                aggregation: {
                  type: 'string',
                  enum: ['avg', 'min', 'max', 'sum'],
                  description: 'Aggregation method',
                  default: 'avg',
                },
              },
              required: ['metric_type'],
            },
          },
          {
            name: 'run_health_check',
            description: 'Run a comprehensive health check',
            inputSchema: {
              type: 'object',
              properties: {
                include_external: {
                  type: 'boolean',
                  description: 'Include external service checks',
                  default: false,
                },
                detailed: {
                  type: 'boolean',
                  description: 'Include detailed diagnostic information',
                  default: false,
                },
              },
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        switch (name) {
          case 'check_service_health':
            return await this.checkServiceHealth(args);
          case 'create_alert':
            return await this.createAlert(args);
          case 'resolve_alert':
            return await this.resolveAlert(args);
          case 'get_metrics':
            return await this.getMetrics(args);
          case 'run_health_check':
            return await this.runHealthCheck(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async getSystemHealth() {
    const cacheKey = 'system:health';
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const [cpuInfo, memInfo, diskInfo, loadAvg] = await Promise.all([
        this.getCPUUsage(),
        this.getMemoryUsage(),
        this.getDiskUsage(),
        this.getLoadAverage(),
      ]);
      
      const health = {
        status: this.calculateOverallHealth(cpuInfo, memInfo, diskInfo, loadAvg),
        timestamp: new Date().toISOString(),
        uptime: await this.getUptime(),
        cpu: cpuInfo,
        memory: memInfo,
        disk: diskInfo,
        load_average: loadAvg,
        alerts: await this.getSystemAlerts(cpuInfo, memInfo, diskInfo),
      };
      
      this.setCachedData(cacheKey, health);
      return health;
    } catch (error) {
      throw new Error(`Failed to get system health: ${error.message}`);
    }
  }

  async getCPUUsage() {
    try {
      // Get CPU usage using top command
      const { stdout } = await execAsync("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1");
      const usage = parseFloat(stdout.trim());
      
      // Get CPU info
      const { stdout: cpuInfo } = await execAsync("cat /proc/cpuinfo | grep 'processor' | wc -l");
      const cores = parseInt(cpuInfo.trim());
      
      return {
        usage_percent: isNaN(usage) ? 0 : usage,
        cores: cores,
        status: usage > 80 ? 'critical' : usage > 60 ? 'warning' : 'normal',
      };
    } catch (error) {
      return {
        usage_percent: 0,
        cores: 1,
        status: 'unknown',
        error: error.message,
      };
    }
  }

  async getMemoryUsage() {
    try {
      const { stdout } = await execAsync("free -m | grep '^Mem:'");
      const parts = stdout.trim().split(/\s+/);
      const total = parseInt(parts[1]);
      const used = parseInt(parts[2]);
      const free = parseInt(parts[3]);
      const available = parseInt(parts[6]) || free;
      
      const usage_percent = (used / total) * 100;
      
      return {
        total_mb: total,
        used_mb: used,
        free_mb: free,
        available_mb: available,
        usage_percent: Math.round(usage_percent * 100) / 100,
        status: usage_percent > 90 ? 'critical' : usage_percent > 75 ? 'warning' : 'normal',
      };
    } catch (error) {
      return {
        total_mb: 0,
        used_mb: 0,
        free_mb: 0,
        usage_percent: 0,
        status: 'unknown',
        error: error.message,
      };
    }
  }

  async getDiskUsage() {
    try {
      const { stdout } = await execAsync("df -h / | tail -1");
      const parts = stdout.trim().split(/\s+/);
      const total = parts[1];
      const used = parts[2];
      const available = parts[3];
      const usage_percent = parseInt(parts[4].replace('%', ''));
      
      return {
        total: total,
        used: used,
        available: available,
        usage_percent: usage_percent,
        status: usage_percent > 90 ? 'critical' : usage_percent > 80 ? 'warning' : 'normal',
      };
    } catch (error) {
      return {
        total: '0G',
        used: '0G',
        available: '0G',
        usage_percent: 0,
        status: 'unknown',
        error: error.message,
      };
    }
  }

  async getLoadAverage() {
    try {
      const { stdout } = await execAsync("cat /proc/loadavg");
      const loads = stdout.trim().split(' ').slice(0, 3).map(parseFloat);
      
      return {
        '1min': loads[0],
        '5min': loads[1],
        '15min': loads[2],
        status: loads[0] > 2 ? 'critical' : loads[0] > 1 ? 'warning' : 'normal',
      };
    } catch (error) {
      return {
        '1min': 0,
        '5min': 0,
        '15min': 0,
        status: 'unknown',
        error: error.message,
      };
    }
  }

  async getUptime() {
    try {
      const { stdout } = await execAsync("uptime -p");
      return stdout.trim();
    } catch (error) {
      return 'unknown';
    }
  }

  async getSystemProcesses() {
    const cacheKey = 'system:processes';
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { stdout } = await execAsync("ps aux --sort=-%cpu | head -20");
      const lines = stdout.trim().split('\n');
      const headers = lines[0].trim().split(/\s+/);
      
      const processes = lines.slice(1).map(line => {
        const parts = line.trim().split(/\s+/);
        return {
          pid: parts[1],
          user: parts[0],
          cpu_percent: parseFloat(parts[2]),
          memory_percent: parseFloat(parts[3]),
          command: parts.slice(10).join(' '),
        };
      });
      
      const processInfo = {
        timestamp: new Date().toISOString(),
        top_processes_by_cpu: processes,
        summary: {
          total_processes: await this.getTotalProcessCount(),
          high_cpu_count: processes.filter(p => p.cpu_percent > 10).length,
          high_memory_count: processes.filter(p => p.memory_percent > 5).length,
        },
      };
      
      this.setCachedData(cacheKey, processInfo);
      return processInfo;
    } catch (error) {
      throw new Error(`Failed to get system processes: ${error.message}`);
    }
  }

  async getTotalProcessCount() {
    try {
      const { stdout } = await execAsync("ps aux | wc -l");
      return parseInt(stdout.trim()) - 1; // Subtract header line
    } catch (error) {
      return 0;
    }
  }

  async getNetworkStatus() {
    const cacheKey = 'system:network';
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const [interfaces, connections] = await Promise.all([
        this.getNetworkInterfaces(),
        this.getNetworkConnections(),
      ]);
      
      const networkStatus = {
        timestamp: new Date().toISOString(),
        interfaces: interfaces,
        active_connections: connections,
        connectivity: await this.checkConnectivity(),
      };
      
      this.setCachedData(cacheKey, networkStatus);
      return networkStatus;
    } catch (error) {
      throw new Error(`Failed to get network status: ${error.message}`);
    }
  }

  async getNetworkInterfaces() {
    try {
      const { stdout } = await execAsync("ip addr show");
      const interfaces = [];
      const interfaceBlocks = stdout.split(/^\d+:/m).filter(block => block.trim());
      
      for (const block of interfaceBlocks) {
        const lines = block.split('\n');
        const firstLine = lines[0];
        const name = firstLine.split(':')[0].trim();
        
        if (name && name !== 'lo') { // Skip loopback
          const isUp = firstLine.includes('UP');
          const ipMatch = block.match(/inet (\d+\.\d+\.\d+\.\d+)/);
          
          interfaces.push({
            name: name,
            status: isUp ? 'up' : 'down',
            ip_address: ipMatch ? ipMatch[1] : null,
          });
        }
      }
      
      return interfaces;
    } catch (error) {
      return [];
    }
  }

  async getNetworkConnections() {
    try {
      const { stdout } = await execAsync("ss -tuln | grep LISTEN | wc -l");
      return {
        listening_ports: parseInt(stdout.trim()),
      };
    } catch (error) {
      return { listening_ports: 0 };
    }
  }

  async checkConnectivity() {
    try {
      const { stdout } = await execAsync("ping -c 1 -W 2 8.8.8.8 2>/dev/null && echo 'success' || echo 'failed'");
      return {
        internet: stdout.trim() === 'success',
        dns: await this.checkDNS(),
      };
    } catch (error) {
      return { internet: false, dns: false };
    }
  }

  async checkDNS() {
    try {
      const { stdout } = await execAsync("nslookup google.com 2>/dev/null | grep 'Address:' | wc -l");
      return parseInt(stdout.trim()) > 1; // More than just the server address
    } catch (error) {
      return false;
    }
  }

  async getActiveAlerts() {
    try {
      const alertsData = await this.loadAlerts();
      const activeAlerts = alertsData.alerts.filter(alert => alert.status === 'active');
      
      return {
        total_active: activeAlerts.length,
        alerts: activeAlerts,
        summary_by_severity: this.summarizeAlertsBySeverity(activeAlerts),
      };
    } catch (error) {
      return {
        total_active: 0,
        alerts: [],
        summary_by_severity: {},
        error: error.message,
      };
    }
  }

  async getAlertHistory() {
    try {
      const alertsData = await this.loadAlerts();
      const last24h = new Date(Date.now() - 24 * 60 * 60 * 1000);
      
      const recentAlerts = alertsData.alerts.filter(alert => 
        new Date(alert.created_at) > last24h
      );
      
      return {
        total_last_24h: recentAlerts.length,
        alerts: recentAlerts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
        trends: this.calculateAlertTrends(alertsData.alerts),
      };
    } catch (error) {
      return {
        total_last_24h: 0,
        alerts: [],
        trends: {},
        error: error.message,
      };
    }
  }

  async getEndpointMetrics(endpointName) {
    const endpoint = this.metricsEndpoints.find(e => e.name === endpointName);
    if (!endpoint) {
      throw new Error(`Endpoint ${endpointName} not found`);
    }
    
    const cacheKey = `endpoint:${endpointName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const response = await fetch(endpoint.url, {
        timeout: 10000,
        headers: {
          'User-Agent': 'monitoring-mcp/1.0.0',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      const metrics = {
        endpoint: endpointName,
        url: endpoint.url,
        status: 'healthy',
        response_time_ms: response.headers.get('x-response-time') || 'unknown',
        timestamp: new Date().toISOString(),
        data: data,
      };
      
      this.setCachedData(cacheKey, metrics);
      return metrics;
    } catch (error) {
      const errorMetrics = {
        endpoint: endpointName,
        url: endpoint.url,
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString(),
      };
      
      this.setCachedData(cacheKey, errorMetrics);
      return errorMetrics;
    }
  }

  async checkServiceHealth(args) {
    const { service, timeout = 10 } = args;
    
    try {
      let result;
      
      if (service.startsWith('http://') || service.startsWith('https://')) {
        // HTTP endpoint check
        const startTime = Date.now();
        const response = await fetch(service, {
          timeout: timeout * 1000,
          method: 'GET',
        });
        const endTime = Date.now();
        
        result = {
          service,
          type: 'http',
          status: response.ok ? 'healthy' : 'unhealthy',
          response_code: response.status,
          response_time_ms: endTime - startTime,
          checked_at: new Date().toISOString(),
        };
      } else {
        // System service check
        try {
          const { stdout } = await execAsync(`systemctl is-active ${service}`);
          result = {
            service,
            type: 'systemd',
            status: stdout.trim() === 'active' ? 'healthy' : 'unhealthy',
            service_status: stdout.trim(),
            checked_at: new Date().toISOString(),
          };
        } catch (error) {
          result = {
            service,
            type: 'systemd',
            status: 'unhealthy',
            error: error.message,
            checked_at: new Date().toISOString(),
          };
        }
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Service health check failed: ${error.message}`);
    }
  }

  async createAlert(args) {
    const { name, description, severity, condition, tags = [] } = args;
    
    try {
      const alertsData = await this.loadAlerts();
      
      const newAlert = {
        id: this.generateAlertId(),
        name,
        description,
        severity,
        condition,
        tags,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      alertsData.alerts.push(newAlert);
      await this.saveAlerts(alertsData);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              alert: newAlert,
              message: 'Alert created successfully',
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to create alert: ${error.message}`);
    }
  }

  async resolveAlert(args) {
    const { alert_id, resolution_note } = args;
    
    try {
      const alertsData = await this.loadAlerts();
      const alertIndex = alertsData.alerts.findIndex(alert => alert.id === alert_id);
      
      if (alertIndex === -1) {
        throw new Error(`Alert with ID ${alert_id} not found`);
      }
      
      alertsData.alerts[alertIndex] = {
        ...alertsData.alerts[alertIndex],
        status: 'resolved',
        resolved_at: new Date().toISOString(),
        resolution_note,
        updated_at: new Date().toISOString(),
      };
      
      await this.saveAlerts(alertsData);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              alert: alertsData.alerts[alertIndex],
              message: 'Alert resolved successfully',
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to resolve alert: ${error.message}`);
    }
  }

  async getMetrics(args) {
    const { metric_type, time_range = '5m', aggregation = 'avg' } = args;
    
    try {
      let metrics;
      
      switch (metric_type) {
        case 'cpu':
          metrics = await this.getCPUUsage();
          break;
        case 'memory':
          metrics = await this.getMemoryUsage();
          break;
        case 'disk':
          metrics = await this.getDiskUsage();
          break;
        case 'network':
          metrics = await this.getNetworkStatus();
          break;
        case 'custom':
          metrics = await this.getCustomMetrics();
          break;
        default:
          throw new Error(`Unknown metric type: ${metric_type}`);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              metric_type,
              time_range,
              aggregation,
              timestamp: new Date().toISOString(),
              data: metrics,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get metrics: ${error.message}`);
    }
  }

  async runHealthCheck(args) {
    const { include_external = false, detailed = false } = args;
    
    try {
      const healthCheck = {
        timestamp: new Date().toISOString(),
        overall_status: 'unknown',
        checks: {},
      };
      
      // System checks
      const [systemHealth, processes, network] = await Promise.all([
        this.getSystemHealth(),
        detailed ? this.getSystemProcesses() : null,
        this.getNetworkStatus(),
      ]);
      
      healthCheck.checks.system = {
        status: systemHealth.status,
        cpu: systemHealth.cpu.status,
        memory: systemHealth.memory.status,
        disk: systemHealth.disk.status,
      };
      
      healthCheck.checks.network = {
        status: network.connectivity.internet ? 'healthy' : 'unhealthy',
        interfaces: network.interfaces.length,
        connectivity: network.connectivity,
      };
      
      if (detailed) {
        healthCheck.checks.processes = {
          total: processes.summary.total_processes,
          high_cpu: processes.summary.high_cpu_count,
          high_memory: processes.summary.high_memory_count,
        };
      }
      
      // External checks
      if (include_external) {
        const externalChecks = await Promise.all(
          this.metricsEndpoints.map(async (endpoint) => {
            try {
              const metrics = await this.getEndpointMetrics(endpoint.name);
              return {
                name: endpoint.name,
                status: metrics.status,
                url: endpoint.url,
              };
            } catch (error) {
              return {
                name: endpoint.name,
                status: 'unhealthy',
                error: error.message,
              };
            }
          })
        );
        
        healthCheck.checks.external = externalChecks;
      }
      
      // Calculate overall status
      const allStatuses = Object.values(healthCheck.checks).flat().map(check => 
        typeof check === 'object' && check.status ? check.status : check
      );
      
      if (allStatuses.some(status => status === 'critical' || status === 'unhealthy')) {
        healthCheck.overall_status = 'unhealthy';
      } else if (allStatuses.some(status => status === 'warning')) {
        healthCheck.overall_status = 'warning';
      } else {
        healthCheck.overall_status = 'healthy';
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(healthCheck, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  calculateOverallHealth(cpu, memory, disk, loadAvg) {
    const statuses = [cpu.status, memory.status, disk.status, loadAvg.status];
    
    if (statuses.includes('critical')) return 'critical';
    if (statuses.includes('warning')) return 'warning';
    return 'normal';
  }

  async getSystemAlerts(cpu, memory, disk) {
    const alerts = [];
    
    if (cpu.status === 'critical') {
      alerts.push({
        type: 'cpu',
        severity: 'high',
        message: `High CPU usage: ${cpu.usage_percent}%`,
      });
    }
    
    if (memory.status === 'critical') {
      alerts.push({
        type: 'memory',
        severity: 'high',
        message: `High memory usage: ${memory.usage_percent}%`,
      });
    }
    
    if (disk.status === 'critical') {
      alerts.push({
        type: 'disk',
        severity: 'high',
        message: `High disk usage: ${disk.usage_percent}%`,
      });
    }
    
    return alerts;
  }

  async getCustomMetrics() {
    // Placeholder for custom metrics integration
    return {
      message: 'Custom metrics not configured',
      endpoints: this.metricsEndpoints.length,
    };
  }

  async loadAlerts() {
    try {
      const data = await fs.readFile(this.alertsFile, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      // Return empty structure if file doesn't exist
      return {
        alerts: [],
        last_updated: new Date().toISOString(),
      };
    }
  }

  async saveAlerts(alertsData) {
    alertsData.last_updated = new Date().toISOString();
    await fs.writeFile(this.alertsFile, JSON.stringify(alertsData, null, 2));
  }

  generateAlertId() {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  summarizeAlertsBySeverity(alerts) {
    const summary = { low: 0, medium: 0, high: 0, critical: 0 };
    alerts.forEach(alert => {
      if (summary.hasOwnProperty(alert.severity)) {
        summary[alert.severity]++;
      }
    });
    return summary;
  }

  calculateAlertTrends(alerts) {
    const now = Date.now();
    const last24h = alerts.filter(alert => 
      now - new Date(alert.created_at).getTime() < 24 * 60 * 60 * 1000
    );
    const last7d = alerts.filter(alert => 
      now - new Date(alert.created_at).getTime() < 7 * 24 * 60 * 60 * 1000
    );
    
    return {
      last_24h: last24h.length,
      last_7d: last7d.length,
      resolved_24h: last24h.filter(alert => alert.status === 'resolved').length,
      resolved_7d: last7d.filter(alert => alert.status === 'resolved').length,
    };
  }

  getCachedData(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  setCachedData(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Monitoring MCP server running on stdio');
  }
}

const server = new MonitoringMCPServer();
server.run().catch(console.error);
