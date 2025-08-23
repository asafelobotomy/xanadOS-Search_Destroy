#!/usr/bin/env node

/**
 * GitHub Status MCP Server
 * Provides real-time access to GitHub Actions, PR status, and repository information
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
import { Octokit } from '@octokit/rest';

class GitHubStatusMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'github-status-mcp',
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
    
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });
    
    this.orgName = process.env.GITHUB_ORG || '';
    this.cache = new Map();
    this.cacheTimeout = 2 * 60 * 1000; // 2 minutes for status data
    
    this.setupHandlers();
  }

  setupHandlers() {
    // List available status resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      try {
        const repositories = await this.getRepositories();
        const resources = [];
        
        for (const repo of repositories.slice(0, 20)) { // Limit to avoid rate limits
          resources.push({
            uri: `github://status/${repo.name}/actions`,
            mimeType: 'application/json',
            name: `${repo.name} Actions Status`,
            description: `GitHub Actions workflow status for ${repo.name}`,
          });
          
          resources.push({
            uri: `github://status/${repo.name}/pulls`,
            mimeType: 'application/json',
            name: `${repo.name} Pull Requests`,
            description: `Open pull requests for ${repo.name}`,
          });
          
          resources.push({
            uri: `github://status/${repo.name}/issues`,
            mimeType: 'application/json',
            name: `${repo.name} Issues`,
            description: `Open issues for ${repo.name}`,
          });
        }
        
        // Add organization-wide resources
        resources.push({
          uri: `github://status/org/overview`,
          mimeType: 'application/json',
          name: 'Organization Overview',
          description: 'Overall status across all repositories',
        });
        
        return { resources };
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to list status resources: ${error.message}`
        );
      }
    });

    // Read status data
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      
      try {
        const match = uri.match(/^github:\/\/status\/(.+?)\/(.+)$/) || 
                     uri.match(/^github:\/\/status\/(org)\/(overview)$/);
        
        if (!match) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid GitHub status URI: ${uri}`
          );
        }
        
        const [, repoOrOrg, statusType] = match;
        let content = {};
        
        if (repoOrOrg === 'org' && statusType === 'overview') {
          content = await this.getOrganizationOverview();
        } else {
          switch (statusType) {
            case 'actions':
              content = await this.getActionsStatus(repoOrOrg);
              break;
            case 'pulls':
              content = await this.getPullRequests(repoOrOrg);
              break;
            case 'issues':
              content = await this.getIssues(repoOrOrg);
              break;
            default:
              throw new McpError(
                ErrorCode.InvalidRequest,
                `Unknown status type: ${statusType}`
              );
          }
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
          `Failed to read status data: ${error.message}`
        );
      }
    });

    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'get_workflow_runs',
            description: 'Get recent workflow runs for a repository',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name',
                },
                status: {
                  type: 'string',
                  enum: ['completed', 'in_progress', 'queued', 'all'],
                  description: 'Filter by workflow status',
                  default: 'all',
                },
                limit: {
                  type: 'number',
                  description: 'Number of runs to return',
                  default: 10,
                  minimum: 1,
                  maximum: 100,
                },
              },
              required: ['repository'],
            },
          },
          {
            name: 'get_pr_status',
            description: 'Get detailed status of a specific pull request',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name',
                },
                pr_number: {
                  type: 'number',
                  description: 'Pull request number',
                },
              },
              required: ['repository', 'pr_number'],
            },
          },
          {
            name: 'get_deployment_status',
            description: 'Get deployment status for a repository',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name',
                },
                environment: {
                  type: 'string',
                  description: 'Environment name (e.g., production, staging)',
                },
              },
              required: ['repository'],
            },
          },
          {
            name: 'get_security_alerts',
            description: 'Get security alerts for a repository',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name',
                },
                state: {
                  type: 'string',
                  enum: ['open', 'fixed', 'dismissed', 'all'],
                  description: 'Filter by alert state',
                  default: 'open',
                },
              },
              required: ['repository'],
            },
          },
          {
            name: 'trigger_workflow',
            description: 'Trigger a workflow dispatch event',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name',
                },
                workflow_id: {
                  type: 'string',
                  description: 'Workflow ID or filename',
                },
                ref: {
                  type: 'string',
                  description: 'Git reference (branch, tag, or SHA)',
                  default: 'main',
                },
                inputs: {
                  type: 'object',
                  description: 'Workflow inputs',
                  additionalProperties: {
                    type: 'string',
                  },
                },
              },
              required: ['repository', 'workflow_id'],
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
          case 'get_workflow_runs':
            return await this.getWorkflowRuns(args);
          case 'get_pr_status':
            return await this.getPRStatus(args);
          case 'get_deployment_status':
            return await this.getDeploymentStatus(args);
          case 'get_security_alerts':
            return await this.getSecurityAlerts(args);
          case 'trigger_workflow':
            return await this.triggerWorkflow(args);
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

  async getRepositories() {
    const cacheKey = 'repositories';
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { data } = await this.octokit.rest.repos.listForOrg({
        org: this.orgName,
        type: 'all',
        sort: 'updated',
        per_page: 100,
      });
      
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      throw new Error(`Failed to fetch repositories: ${error.message}`);
    }
  }

  async getActionsStatus(repoName) {
    const cacheKey = `actions:${repoName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { data: runs } = await this.octokit.rest.actions.listWorkflowRunsForRepo({
        owner: this.orgName,
        repo: repoName,
        per_page: 20,
      });
      
      const summary = {
        repository: repoName,
        total_runs: runs.total_count,
        recent_runs: runs.workflow_runs.map(run => ({
          id: run.id,
          name: run.name,
          status: run.status,
          conclusion: run.conclusion,
          created_at: run.created_at,
          updated_at: run.updated_at,
          head_branch: run.head_branch,
          head_sha: run.head_sha.substring(0, 7),
          actor: run.actor.login,
          event: run.event,
          html_url: run.html_url,
        })),
        status_summary: this.summarizeWorkflowStatus(runs.workflow_runs),
      };
      
      this.setCachedData(cacheKey, summary);
      return summary;
    } catch (error) {
      throw new Error(`Failed to fetch actions status: ${error.message}`);
    }
  }

  async getPullRequests(repoName) {
    const cacheKey = `pulls:${repoName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { data: pulls } = await this.octokit.rest.pulls.list({
        owner: this.orgName,
        repo: repoName,
        state: 'open',
        sort: 'updated',
        direction: 'desc',
        per_page: 20,
      });
      
      const pullRequestsWithStatus = await Promise.all(
        pulls.map(async (pr) => {
          try {
            // Get PR status checks
            const { data: status } = await this.octokit.rest.repos.getCombinedStatusForRef({
              owner: this.orgName,
              repo: repoName,
              ref: pr.head.sha,
            });
            
            // Get PR reviews
            const { data: reviews } = await this.octokit.rest.pulls.listReviews({
              owner: this.orgName,
              repo: repoName,
              pull_number: pr.number,
            });
            
            return {
              number: pr.number,
              title: pr.title,
              state: pr.state,
              created_at: pr.created_at,
              updated_at: pr.updated_at,
              user: pr.user.login,
              head_branch: pr.head.ref,
              base_branch: pr.base.ref,
              draft: pr.draft,
              mergeable: pr.mergeable,
              mergeable_state: pr.mergeable_state,
              html_url: pr.html_url,
              status_checks: {
                state: status.state,
                total_count: status.total_count,
                statuses: status.statuses.map(s => ({
                  context: s.context,
                  state: s.state,
                  description: s.description,
                })),
              },
              reviews: {
                total: reviews.length,
                approved: reviews.filter(r => r.state === 'APPROVED').length,
                changes_requested: reviews.filter(r => r.state === 'CHANGES_REQUESTED').length,
              },
            };
          } catch (error) {
            // Return basic info if detailed status fails
            return {
              number: pr.number,
              title: pr.title,
              state: pr.state,
              created_at: pr.created_at,
              updated_at: pr.updated_at,
              user: pr.user.login,
              head_branch: pr.head.ref,
              base_branch: pr.base.ref,
              draft: pr.draft,
              html_url: pr.html_url,
              status_checks: { state: 'unknown' },
              reviews: { total: 0 },
            };
          }
        })
      );
      
      const summary = {
        repository: repoName,
        total_open: pulls.length,
        pull_requests: pullRequestsWithStatus,
        summary: {
          draft: pullRequestsWithStatus.filter(pr => pr.draft).length,
          ready_for_review: pullRequestsWithStatus.filter(pr => !pr.draft).length,
          approved: pullRequestsWithStatus.filter(pr => pr.reviews.approved > 0).length,
          needs_changes: pullRequestsWithStatus.filter(pr => pr.reviews.changes_requested > 0).length,
          checks_passing: pullRequestsWithStatus.filter(pr => pr.status_checks.state === 'success').length,
          checks_failing: pullRequestsWithStatus.filter(pr => pr.status_checks.state === 'failure').length,
        },
      };
      
      this.setCachedData(cacheKey, summary);
      return summary;
    } catch (error) {
      throw new Error(`Failed to fetch pull requests: ${error.message}`);
    }
  }

  async getIssues(repoName) {
    const cacheKey = `issues:${repoName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { data: issues } = await this.octokit.rest.issues.listForRepo({
        owner: this.orgName,
        repo: repoName,
        state: 'open',
        sort: 'updated',
        direction: 'desc',
        per_page: 20,
      });
      
      // Filter out pull requests (they show up in issues API)
      const actualIssues = issues.filter(issue => !issue.pull_request);
      
      const summary = {
        repository: repoName,
        total_open: actualIssues.length,
        issues: actualIssues.map(issue => ({
          number: issue.number,
          title: issue.title,
          state: issue.state,
          created_at: issue.created_at,
          updated_at: issue.updated_at,
          user: issue.user.login,
          assignees: issue.assignees.map(a => a.login),
          labels: issue.labels.map(l => l.name),
          milestone: issue.milestone?.title,
          html_url: issue.html_url,
        })),
        summary: {
          unassigned: actualIssues.filter(issue => issue.assignees.length === 0).length,
          with_milestone: actualIssues.filter(issue => issue.milestone).length,
          labeled: actualIssues.filter(issue => issue.labels.length > 0).length,
        },
      };
      
      this.setCachedData(cacheKey, summary);
      return summary;
    } catch (error) {
      throw new Error(`Failed to fetch issues: ${error.message}`);
    }
  }

  async getOrganizationOverview() {
    const cacheKey = 'org:overview';
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const repositories = await this.getRepositories();
      
      // Get a sample of recent activity
      const recentActivity = [];
      for (const repo of repositories.slice(0, 10)) {
        try {
          const { data: runs } = await this.octokit.rest.actions.listWorkflowRunsForRepo({
            owner: this.orgName,
            repo: repo.name,
            per_page: 5,
          });
          
          recentActivity.push(...runs.workflow_runs.map(run => ({
            repository: repo.name,
            type: 'workflow_run',
            name: run.name,
            status: run.status,
            conclusion: run.conclusion,
            created_at: run.created_at,
            actor: run.actor.login,
            html_url: run.html_url,
          })));
        } catch (error) {
          // Skip repositories we can't access
          continue;
        }
      }
      
      // Sort by most recent
      recentActivity.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      const overview = {
        organization: this.orgName,
        total_repositories: repositories.length,
        recent_activity: recentActivity.slice(0, 20),
        repository_summary: {
          public: repositories.filter(r => !r.private).length,
          private: repositories.filter(r => r.private).length,
          archived: repositories.filter(r => r.archived).length,
          languages: this.getLanguageDistribution(repositories),
        },
        generated_at: new Date().toISOString(),
      };
      
      this.setCachedData(cacheKey, overview);
      return overview;
    } catch (error) {
      throw new Error(`Failed to fetch organization overview: ${error.message}`);
    }
  }

  async getWorkflowRuns(args) {
    const { repository, status = 'all', limit = 10 } = args;
    
    try {
      const params = {
        owner: this.orgName,
        repo: repository,
        per_page: Math.min(limit, 100),
      };
      
      if (status !== 'all') {
        params.status = status;
      }
      
      const { data } = await this.octokit.rest.actions.listWorkflowRunsForRepo(params);
      
      const runs = data.workflow_runs.map(run => ({
        id: run.id,
        name: run.name,
        status: run.status,
        conclusion: run.conclusion,
        created_at: run.created_at,
        updated_at: run.updated_at,
        head_branch: run.head_branch,
        head_sha: run.head_sha.substring(0, 7),
        actor: run.actor.login,
        event: run.event,
        html_url: run.html_url,
        workflow_id: run.workflow_id,
        run_number: run.run_number,
      }));
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ repository, runs, total_count: data.total_count }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get workflow runs: ${error.message}`);
    }
  }

  async getPRStatus(args) {
    const { repository, pr_number } = args;
    
    try {
      const { data: pr } = await this.octokit.rest.pulls.get({
        owner: this.orgName,
        repo: repository,
        pull_number: pr_number,
      });
      
      // Get detailed status information
      const [statusResponse, reviewsResponse, checksResponse] = await Promise.all([
        this.octokit.rest.repos.getCombinedStatusForRef({
          owner: this.orgName,
          repo: repository,
          ref: pr.head.sha,
        }),
        this.octokit.rest.pulls.listReviews({
          owner: this.orgName,
          repo: repository,
          pull_number: pr_number,
        }),
        this.octokit.rest.checks.listForRef({
          owner: this.orgName,
          repo: repository,
          ref: pr.head.sha,
        }).catch(() => ({ data: { check_runs: [] } })), // Fallback if checks not available
      ]);
      
      const prStatus = {
        number: pr.number,
        title: pr.title,
        state: pr.state,
        merged: pr.merged,
        mergeable: pr.mergeable,
        mergeable_state: pr.mergeable_state,
        draft: pr.draft,
        user: pr.user.login,
        created_at: pr.created_at,
        updated_at: pr.updated_at,
        head_branch: pr.head.ref,
        base_branch: pr.base.ref,
        html_url: pr.html_url,
        status_checks: {
          state: statusResponse.data.state,
          total_count: statusResponse.data.total_count,
          statuses: statusResponse.data.statuses,
        },
        check_runs: checksResponse.data.check_runs.map(check => ({
          name: check.name,
          status: check.status,
          conclusion: check.conclusion,
          started_at: check.started_at,
          completed_at: check.completed_at,
          html_url: check.html_url,
        })),
        reviews: reviewsResponse.data.map(review => ({
          id: review.id,
          user: review.user.login,
          state: review.state,
          submitted_at: review.submitted_at,
          body: review.body,
        })),
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(prStatus, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get PR status: ${error.message}`);
    }
  }

  async getDeploymentStatus(args) {
    const { repository, environment } = args;
    
    try {
      const params = {
        owner: this.orgName,
        repo: repository,
        per_page: 10,
      };
      
      if (environment) {
        params.environment = environment;
      }
      
      const { data: deployments } = await this.octokit.rest.repos.listDeployments(params);
      
      const deploymentsWithStatus = await Promise.all(
        deployments.map(async (deployment) => {
          try {
            const { data: statuses } = await this.octokit.rest.repos.listDeploymentStatuses({
              owner: this.orgName,
              repo: repository,
              deployment_id: deployment.id,
            });
            
            return {
              id: deployment.id,
              sha: deployment.sha.substring(0, 7),
              ref: deployment.ref,
              environment: deployment.environment,
              created_at: deployment.created_at,
              updated_at: deployment.updated_at,
              creator: deployment.creator.login,
              status: statuses[0]?.state || 'unknown',
              description: statuses[0]?.description,
              statuses: statuses.map(s => ({
                state: s.state,
                created_at: s.created_at,
                description: s.description,
              })),
            };
          } catch (error) {
            return {
              id: deployment.id,
              sha: deployment.sha.substring(0, 7),
              ref: deployment.ref,
              environment: deployment.environment,
              created_at: deployment.created_at,
              status: 'unknown',
            };
          }
        })
      );
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ repository, deployments: deploymentsWithStatus }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get deployment status: ${error.message}`);
    }
  }

  async getSecurityAlerts(args) {
    const { repository, state = 'open' } = args;
    
    try {
      const { data: alerts } = await this.octokit.rest.secretScanning.listAlertsForRepo({
        owner: this.orgName,
        repo: repository,
        state,
      });
      
      const securityAlerts = alerts.map(alert => ({
        number: alert.number,
        state: alert.state,
        secret_type: alert.secret_type,
        secret_type_display_name: alert.secret_type_display_name,
        created_at: alert.created_at,
        updated_at: alert.updated_at,
        html_url: alert.html_url,
        locations: alert.locations?.map(loc => ({
          type: loc.type,
          path: loc.details?.path,
          start_line: loc.details?.start_line,
          end_line: loc.details?.end_line,
        })),
      }));
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ repository, alerts: securityAlerts }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get security alerts: ${error.message}`);
    }
  }

  async triggerWorkflow(args) {
    const { repository, workflow_id, ref = 'main', inputs = {} } = args;
    
    try {
      const { data } = await this.octokit.rest.actions.createWorkflowDispatch({
        owner: this.orgName,
        repo: repository,
        workflow_id,
        ref,
        inputs,
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              message: `Workflow ${workflow_id} triggered successfully`,
              repository,
              ref,
              inputs,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to trigger workflow: ${error.message}`);
    }
  }

  summarizeWorkflowStatus(runs) {
    const summary = {
      total: runs.length,
      success: 0,
      failure: 0,
      in_progress: 0,
      cancelled: 0,
      skipped: 0,
    };
    
    runs.forEach(run => {
      if (run.status === 'completed') {
        if (run.conclusion === 'success') {
          summary.success++;
        } else if (run.conclusion === 'failure') {
          summary.failure++;
        } else if (run.conclusion === 'cancelled') {
          summary.cancelled++;
        } else if (run.conclusion === 'skipped') {
          summary.skipped++;
        }
      } else {
        summary.in_progress++;
      }
    });
    
    return summary;
  }

  getLanguageDistribution(repositories) {
    const languages = {};
    repositories.forEach(repo => {
      if (repo.language) {
        languages[repo.language] = (languages[repo.language] || 0) + 1;
      }
    });
    
    return Object.entries(languages)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .reduce((obj, [lang, count]) => {
        obj[lang] = count;
        return obj;
      }, {});
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
    console.error('GitHub Status MCP server running on stdio');
  }
}

const server = new GitHubStatusMCPServer();
server.run().catch(console.error);
