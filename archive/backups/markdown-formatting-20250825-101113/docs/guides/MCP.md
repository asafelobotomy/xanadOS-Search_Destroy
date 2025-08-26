# MCP (Model Context Protocol) integration

This pack supports modern Copilot workflows with MCP so agents and chat can use approved external tools and services.

What MCP is

- MCP is an open standard for connecting LLMs to tools/data.

Copilot supports MCP in VS Code (GA) and other IDEs.

- Organizations can enable/disable MCP via the “MCP servers in Copilot” policy.

It’s disabled by default.

- GitHub provides a hosted GitHub MCP server; you can also run local/remote third‑party MCP servers.

Security notes

- Avoid committing secrets to `.VS Code/mcp.JSON`.

Prefer OAuth sign-in (when supported) or keep tokens local.

- For public repos, push protection applies to GitHub MCP interactions; still, never paste secrets in config.

Quick start in VS Code

- Enable your org MCP policy if you’re on Copilot Business/Enterprise.
- Add a repo-local config: `.VS Code/mcp.JSON` (do not commit secrets).

Examples

1. Remote GitHub MCP server (preferred when available)

  ```JSON
  {
  "servers": {
  "GitHub": {
  "URL": "<HTTPS://API.githubcopilot.com/mcp/",>
  "requestInit": {
  "headers": {
  "Authorization": "Bearer YOUR_PAT_HERE"
  }
  }
  }
  }
  }
  ```

  Note: Prefer OAuth in VS Code when possible; otherwise keep PAT local and never
  commit with tokens.

2. Hugging Face MCP server (example)

  ```JSON
  {
  "servers": {
  "huggingface": {
  "URL": "<HTTPS://<your-hf-mcp-server-domain>/",>
  "requestInit": {
  "headers": {
  "Authorization": "Bearer YOUR_HF_TOKEN"
  }
  }
  }
  }
  }
  ```

  Note: Use the current Hugging Face MCP server URL and required scopes from HF
  documentation. Keep tokens local.

3. Local server example (no secrets committed)

  ```JSON
  {
  "servers": {
  "memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
  }
  }
  }
  ```

Recommended practices

- Centralize policy: allow only approved MCP servers for your org.
- Keep `.VS Code/mcp.JSON` in the repo without tokens; each dev configures secrets locally.
- Start with GitHub + any essential internal/HF MCP servers, then expand as needed.

References

- GitHub Docs: About MCP; Extending Copilot Chat with MCP; MCP GA in VS Code
- Model Context Protocol: spec and official SDKs
- Hugging Face: MCP server docs and course materials
