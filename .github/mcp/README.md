# MCP Server Configuration

This directory contains Model Context Protocol (MCP) server configurations and integrations that enhance the GitHub Copilot instruction system with real-time capabilities.

## Overview

MCP servers provide dynamic context and external integrations to supplement the static instruction files. They enable:

- **Real-time Documentation Access** - Live documentation retrieval from external sources
- **API Integration** - Dynamic data from external services and APIs
- **Development Tool Integration** - Real-time status from CI/CD, monitoring, etc.
- **Knowledge Base Access** - Dynamic content from wikis, databases, and knowledge systems

## MCP Server Types

### 1. Documentation Servers

- **confluence-mcp** - Real-time Confluence documentation access
- **notion-mcp** - Dynamic Notion page content retrieval
- **github-docs-mcp** - Live GitHub repository documentation
- **api-docs-mcp** - OpenAPI/Swagger specification access

### 2. Development Tool Servers

- **github-status-mcp** - Real-time GitHub Actions, PR, and issue status
- **jira-mcp** - Live JIRA ticket and project information
- **slack-mcp** - Team communication context and status updates
- **monitoring-mcp** - Real-time application and infrastructure metrics

### 3. Knowledge Base Servers

- **stackoverflow-mcp** - Dynamic Stack Overflow answer retrieval
- **internal-kb-mcp** - Company knowledge base integration
- **code-search-mcp** - Live code search across repositories
- **dependency-mcp** - Real-time dependency and security information

## Configuration Files

### Core Configuration

- `mcp-servers.json` - Main MCP server configuration
- `server-registry.json` - Available server definitions
- `auth-config.json` - Authentication configurations
- `rate-limits.json` - Rate limiting and throttling settings

### Server Implementations

- `servers/` - Individual MCP server implementations
- `middleware/` - Shared middleware and utilities
- `integrations/` - Third-party service integrations
- `security/` - Security and authentication modules

## Usage Integration

MCP servers automatically provide context to GitHub Copilot through:

1. **Automatic Context Injection** - Relevant information based on current work
2. **On-Demand Queries** - Explicit requests for specific information
3. **Workspace Awareness** - Context based on current files and projects
4. **Team Collaboration** - Shared context from team tools and communications

## Setup and Deployment

See individual server directories for specific setup instructions. All servers follow the MCP specification for consistent integration with GitHub Copilot.
