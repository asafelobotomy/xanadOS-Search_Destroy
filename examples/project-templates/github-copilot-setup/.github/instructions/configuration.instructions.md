---
applyTo: "**/*.{example,template,sample}"
priority: 80
category: "configuration"
---

# Configuration & Template Management Instructions

## Template File Handling

- When encountering `.example`, `.template`, or `.sample` files, automatically suggest creating the actual config file
- Replace placeholder values with specific environment variable references using `${VAR_NAME}` syntax
- Never commit actual secrets, tokens, or credentials - always use environment variables or HashiCorp Vault
- Maintain the `.example` file as documentation while creating the actual config file in `.gitignore`

## Placeholder Replacement Strategy

- `YOUR_*_HERE` patterns: Replace with environment variable references like `${GITHUB_PAT}` or `process.env.GITHUB_PAT`
- `<your-*>` patterns: Replace with uppercase env vars: `<your-api-key>` → `${API_KEY}`
- Domain placeholders: Use specific patterns: `example.com` → `${API_DOMAIN:-api.example.com}`
- Token placeholders: Use secure patterns: `your-token` → `${API_TOKEN}` with validation

## MCP Configuration Automation

- For `.vscode/mcp.json.example`, create `.vscode/mcp.json` with environment variable references
- Add `.vscode/mcp.json` to `.gitignore` if not already present
- Create `.env.example` with all required variables and placeholder descriptions
- Implement dotenv loading using `python-dotenv`, `dotenv` (Node.js), or language-specific loaders

## Security-First Configuration

- Always validate that sensitive values are externalized to environment variables
- Suggest using tools like `dotenv`, `vault`, or cloud secret managers for production
- Implement configuration validation to ensure required environment variables are set
- Add runtime checks for missing configuration values with helpful error messages

## Development Workflow Integration

- Create setup scripts that copy `.example` files and prompt for required values
- Generate README sections explaining configuration requirements and setup steps
- Implement configuration validation in CI/CD pipelines to catch missing environment variables
- Suggest using development-specific default values that are safe for local testing

## Example Implementation Patterns

### For JSON configurations:

```javascript
const config = {
  github: {
    token: process.env.GITHUB_PAT || (() => {
      throw new Error('GITHUB_PAT environment variable is required');
    })()
  }
};
```markdown

### For YAML configurations:

```yaml
servers:
  github:
    url: "https://api.githubcopilot.com/mcp/"
    requestInit:
      headers:
        Authorization: "Bearer ${GITHUB_PAT}"
```markdown

### For environment file generation:

```bash
# Copy example and prompt for values

cp .env.example .env
echo "Please edit .env file with your actual values"
```markdown

## Documentation Requirements

- Always update README.md with configuration setup instructions when creating config files
- Document all required environment variables with descriptions and example values
- Include troubleshooting section for common configuration issues
- Provide example values that are safe for development but clearly marked as non-production
