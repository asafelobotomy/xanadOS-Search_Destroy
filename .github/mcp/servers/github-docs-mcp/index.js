#!/usr/bin/env node

/**
 * GitHub Documentation MCP Server
 * Provides real-time access to GitHub repository documentation, READMEs, and wiki content
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
import { marked } from 'marked';

class GitHubDocsMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'github-docs-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      }
    );
    
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });
    
    this.orgName = process.env.GITHUB_ORG || '';
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    
    this.setupHandlers();
  }

  setupHandlers() {
    // List available documentation resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      try {
        const repositories = await this.getRepositories();
        const resources = [];
        
        for (const repo of repositories) {
          // Add README resource
          resources.push({
            uri: `github://docs/${repo.name}/readme`,
            mimeType: 'text/markdown',
            name: `${repo.name} README`,
            description: `README documentation for ${repo.name}`,
          });
          
          // Add Wiki resource if wiki is enabled
          if (repo.has_wiki) {
            resources.push({
              uri: `github://docs/${repo.name}/wiki`,
              mimeType: 'text/markdown',
              name: `${repo.name} Wiki`,
              description: `Wiki documentation for ${repo.name}`,
            });
          }
          
          // Add docs directory if it exists
          try {
            await this.octokit.rest.repos.getContent({
              owner: this.orgName,
              repo: repo.name,
              path: 'docs',
            });
            
            resources.push({
              uri: `github://docs/${repo.name}/docs`,
              mimeType: 'text/markdown',
              name: `${repo.name} Documentation`,
              description: `Documentation directory for ${repo.name}`,
            });
          } catch (error) {
            // docs directory doesn't exist, skip
          }
        }
        
        return { resources };
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to list documentation resources: ${error.message}`
        );
      }
    });

    // Read documentation content
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      
      try {
        const match = uri.match(/^github:\/\/docs\/(.+?)\/(.+)$/);
        if (!match) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid GitHub docs URI: ${uri}`
          );
        }
        
        const [, repoName, docType] = match;
        let content = '';
        
        switch (docType) {
          case 'readme':
            content = await this.getReadmeContent(repoName);
            break;
          case 'wiki':
            content = await this.getWikiContent(repoName);
            break;
          case 'docs':
            content = await this.getDocsContent(repoName);
            break;
          default:
            throw new McpError(
              ErrorCode.InvalidRequest,
              `Unknown documentation type: ${docType}`
            );
        }
        
        return {
          contents: [
            {
              uri,
              mimeType: 'text/markdown',
              text: content,
            },
          ],
        };
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to read documentation: ${error.message}`
        );
      }
    });

    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_documentation',
            description: 'Search across all GitHub documentation for specific content',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for documentation content',
                },
                repository: {
                  type: 'string',
                  description: 'Optional: Limit search to specific repository',
                },
                type: {
                  type: 'string',
                  enum: ['readme', 'wiki', 'docs', 'all'],
                  description: 'Type of documentation to search',
                  default: 'all',
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'get_repository_info',
            description: 'Get detailed information about a repository including documentation structure',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name to get information for',
                },
              },
              required: ['repository'],
            },
          },
          {
            name: 'get_file_content',
            description: 'Get content of a specific file from a repository',
            inputSchema: {
              type: 'object',
              properties: {
                repository: {
                  type: 'string',
                  description: 'Repository name',
                },
                path: {
                  type: 'string',
                  description: 'File path within the repository',
                },
                branch: {
                  type: 'string',
                  description: 'Branch to read from (default: main)',
                  default: 'main',
                },
              },
              required: ['repository', 'path'],
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
          case 'search_documentation':
            return await this.searchDocumentation(args);
          case 'get_repository_info':
            return await this.getRepositoryInfo(args);
          case 'get_file_content':
            return await this.getFileContent(args);
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

  async getReadmeContent(repoName) {
    const cacheKey = `readme:${repoName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { data } = await this.octokit.rest.repos.getReadme({
        owner: this.orgName,
        repo: repoName,
      });
      
      const content = Buffer.from(data.content, 'base64').toString('utf-8');
      this.setCachedData(cacheKey, content);
      return content;
    } catch (error) {
      if (error.status === 404) {
        return `# ${repoName}\n\nNo README file found for this repository.`;
      }
      throw new Error(`Failed to fetch README: ${error.message}`);
    }
  }

  async getWikiContent(repoName) {
    const cacheKey = `wiki:${repoName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      // Get wiki pages using GitHub API
      const { data: pages } = await this.octokit.request(
        'GET /repos/{owner}/{repo}/wiki',
        {
          owner: this.orgName,
          repo: repoName,
        }
      );
      
      let wikiContent = `# ${repoName} Wiki\n\n`;
      
      for (const page of pages) {
        const { data: pageContent } = await this.octokit.request(
          'GET /repos/{owner}/{repo}/wiki/{page_name}',
          {
            owner: this.orgName,
            repo: repoName,
            page_name: page.title,
          }
        );
        
        wikiContent += `## ${page.title}\n\n${pageContent.content}\n\n`;
      }
      
      this.setCachedData(cacheKey, wikiContent);
      return wikiContent;
    } catch (error) {
      if (error.status === 404) {
        return `# ${repoName} Wiki\n\nNo wiki content found for this repository.`;
      }
      throw new Error(`Failed to fetch wiki content: ${error.message}`);
    }
  }

  async getDocsContent(repoName) {
    const cacheKey = `docs:${repoName}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    try {
      const { data: contents } = await this.octokit.rest.repos.getContent({
        owner: this.orgName,
        repo: repoName,
        path: 'docs',
      });
      
      let docsContent = `# ${repoName} Documentation\n\n`;
      
      for (const item of contents) {
        if (item.type === 'file' && item.name.endsWith('.md')) {
          const { data: fileContent } = await this.octokit.rest.repos.getContent({
            owner: this.orgName,
            repo: repoName,
            path: item.path,
          });
          
          const content = Buffer.from(fileContent.content, 'base64').toString('utf-8');
          docsContent += `## ${item.name}\n\n${content}\n\n`;
        }
      }
      
      this.setCachedData(cacheKey, docsContent);
      return docsContent;
    } catch (error) {
      if (error.status === 404) {
        return `# ${repoName} Documentation\n\nNo documentation directory found for this repository.`;
      }
      throw new Error(`Failed to fetch documentation: ${error.message}`);
    }
  }

  async searchDocumentation(args) {
    const { query, repository, type = 'all' } = args;
    
    try {
      let repositories = [];
      
      if (repository) {
        repositories = [{ name: repository }];
      } else {
        repositories = await this.getRepositories();
      }
      
      const results = [];
      
      for (const repo of repositories) {
        const searchResults = await this.searchInRepository(repo.name, query, type);
        results.push(...searchResults);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Search failed: ${error.message}`);
    }
  }

  async searchInRepository(repoName, query, type) {
    const results = [];
    const searchQuery = query.toLowerCase();
    
    try {
      if (type === 'readme' || type === 'all') {
        const readme = await this.getReadmeContent(repoName);
        if (readme.toLowerCase().includes(searchQuery)) {
          results.push({
            repository: repoName,
            type: 'readme',
            title: `${repoName} README`,
            excerpt: this.extractExcerpt(readme, query),
            uri: `github://docs/${repoName}/readme`,
          });
        }
      }
      
      if (type === 'wiki' || type === 'all') {
        const wiki = await this.getWikiContent(repoName);
        if (wiki.toLowerCase().includes(searchQuery)) {
          results.push({
            repository: repoName,
            type: 'wiki',
            title: `${repoName} Wiki`,
            excerpt: this.extractExcerpt(wiki, query),
            uri: `github://docs/${repoName}/wiki`,
          });
        }
      }
      
      if (type === 'docs' || type === 'all') {
        const docs = await this.getDocsContent(repoName);
        if (docs.toLowerCase().includes(searchQuery)) {
          results.push({
            repository: repoName,
            type: 'docs',
            title: `${repoName} Documentation`,
            excerpt: this.extractExcerpt(docs, query),
            uri: `github://docs/${repoName}/docs`,
          });
        }
      }
    } catch (error) {
      // Skip repositories that can't be accessed
      console.warn(`Could not search in repository ${repoName}: ${error.message}`);
    }
    
    return results;
  }

  extractExcerpt(content, query, contextLength = 200) {
    const index = content.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return '';
    
    const start = Math.max(0, index - contextLength / 2);
    const end = Math.min(content.length, index + query.length + contextLength / 2);
    
    let excerpt = content.substring(start, end);
    
    if (start > 0) excerpt = '...' + excerpt;
    if (end < content.length) excerpt = excerpt + '...';
    
    return excerpt;
  }

  async getRepositoryInfo(args) {
    const { repository } = args;
    
    try {
      const { data: repo } = await this.octokit.rest.repos.get({
        owner: this.orgName,
        repo: repository,
      });
      
      // Check for documentation structure
      const docStructure = await this.analyzeDocumentationStructure(repository);
      
      const info = {
        name: repo.name,
        description: repo.description,
        language: repo.language,
        topics: repo.topics,
        has_wiki: repo.has_wiki,
        has_pages: repo.has_pages,
        documentation_structure: docStructure,
        clone_url: repo.clone_url,
        html_url: repo.html_url,
        updated_at: repo.updated_at,
        created_at: repo.created_at,
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(info, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get repository info: ${error.message}`);
    }
  }

  async analyzeDocumentationStructure(repoName) {
    const structure = {
      has_readme: false,
      has_docs_directory: false,
      has_wiki: false,
      documentation_files: [],
    };
    
    try {
      // Check for README
      await this.octokit.rest.repos.getReadme({
        owner: this.orgName,
        repo: repoName,
      });
      structure.has_readme = true;
    } catch (error) {
      // README doesn't exist
    }
    
    try {
      // Check for docs directory
      const { data: contents } = await this.octokit.rest.repos.getContent({
        owner: this.orgName,
        repo: repoName,
        path: 'docs',
      });
      structure.has_docs_directory = true;
      structure.documentation_files = contents
        .filter(item => item.type === 'file' && item.name.endsWith('.md'))
        .map(item => item.name);
    } catch (error) {
      // docs directory doesn't exist
    }
    
    try {
      // Check for wiki
      await this.octokit.request('GET /repos/{owner}/{repo}/wiki', {
        owner: this.orgName,
        repo: repoName,
      });
      structure.has_wiki = true;
    } catch (error) {
      // Wiki doesn't exist
    }
    
    return structure;
  }

  async getFileContent(args) {
    const { repository, path, branch = 'main' } = args;
    
    try {
      const { data } = await this.octokit.rest.repos.getContent({
        owner: this.orgName,
        repo: repository,
        path,
        ref: branch,
      });
      
      if (data.type !== 'file') {
        throw new Error(`Path ${path} is not a file`);
      }
      
      const content = Buffer.from(data.content, 'base64').toString('utf-8');
      
      return {
        content: [
          {
            type: 'text',
            text: content,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get file content: ${error.message}`);
    }
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
    console.error('GitHub Docs MCP server running on stdio');
  }
}

const server = new GitHubDocsMCPServer();
server.run().catch(console.error);
