---
applyTo: "**/*.{py,js,ts,java,go,cs,rb,rs,php,sh,yml,yaml,json,env}"
priority: 60
category: "cross-cutting"
---

# Security-specific Copilot Instructions

## Secret Management

- Never hardcode secrets, API keys, passwords, or tokens in source code; use HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault
- When working with `.example` or `.template` configuration files, automatically create the actual config file with environment variable references
- Use `.env.example` files to document required environment variables without exposing actual values
- Add actual configuration files (`.env`, `mcp.json`, etc.) to `.gitignore` to prevent accidental secret exposure

## Input Validation & Sanitization

- Validate all user inputs using schema validation (JSON Schema, Joi, Yup) with whitelist approach
- Sanitize before database queries using parameterized queries (never string concatenation)
- Implement input length limits: usernames 3-50 chars, emails <254 chars, text fields <10KB
- Use Content Security Policy (CSP) headers with nonce/hash for inline scripts

## Access Control & Authentication

- Apply principle of least privilege with role-based access control (RBAC)
- Include security headers: CSP, HSTS (max-age=31536000), X-Frame-Options: DENY, X-Content-Type-Options: nosniff
- Use HTTPS/TLS 1.3 minimum for all external communications; implement certificate pinning for mobile apps
- Implement MFA using FIDO2/WebAuthn or TOTP with backup codes

## Monitoring & Incident Response

- Log security events with correlation IDs but never log sensitive data (passwords, tokens, PII)
- Implement rate limiting: 100 requests/minute per IP, 1000 requests/hour per authenticated user
- Use parameterized queries with prepared statements for all database operations
- Scan dependencies weekly using OWASP Dependency Check, Snyk, or GitHub Dependabot

**⚠️ CRITICAL: This instruction file overrides performance optimizations when security conflicts arise**
- Follow OWASP guidelines for secure coding practices
