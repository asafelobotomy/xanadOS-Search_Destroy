# MCP Examples Index

This page collects local, offline-friendly examples that mimic MCP-style workflows without network calls.

## Available examples

- GitHub Issues Triage (offline demo)
- Path: `examples/mcp/GitHub-issues-triage`
- Run: `npm run mcp:triage`
- Test: `npm run mcp:test`

## Notes

- These examples avoid external APIs to keep the repo secure and runnable anywhere.
- For production integrations, create a separate package with proper auth,

  rate limiting, and secrets handling, following `security.instructions.md`.
