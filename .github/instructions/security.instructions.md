---
applyTo: "**/*.{js,ts,py,rb,go,java,php,cs,rs,kt,swift}"
---

# Security Guidelines for All Code Files

## Security-First Development Standards

### Input Validation & Sanitization
- **Always validate input**: Implement strict input validation for all user data
- **Use parameterized queries**: Prevent SQL injection with prepared statements
- **Sanitize output**: Escape data before rendering in web contexts
- **Validate file uploads**: Check file types, sizes, and scan for malware

### Authentication & Authorization
- **Multi-factor authentication**: Implement MFA for sensitive operations
- **Role-based access control**: Use principle of least privilege
- **Session management**: Secure session handling with proper timeouts
- **JWT security**: Use secure algorithms and proper token validation

### Data Protection
- **Encrypt sensitive data**: Use AES-256 for data at rest
- **TLS 1.3 minimum**: Secure all data in transit
- **Key management**: Use proper key rotation and secure storage
- **PII handling**: Follow GDPR/CCPA compliance requirements

### Code Security Practices
- **Dependency scanning**: Regular security audits of third-party libraries
- **Static analysis**: Use security-focused code analysis tools
- **Secret management**: Never commit credentials or API keys
- **Error handling**: Avoid exposing sensitive information in error messages

### Security Testing Requirements

- **Automated security scanning**: Use `./scripts/tools/security/security-scan.sh` for
  comprehensive analysis
- **Dependency vulnerability monitoring**: Use
  `./scripts/tools/dependencies/dependency-manager.sh --security-only`
- **Container security scanning**: Use
  `./scripts/tools/containers/docker-manager.sh --security-scan`
- **Pre-commit security gates**: Use `./scripts/tools/hooks/setup-pre-commit.sh` for
  automated security checks
- **Penetration testing**: Required for production deployments
- **Security code review**: Mandatory for security-critical changes
- **Vulnerability assessment**: Regular automated security scans with SAST, dependency
  scanning, and IaC analysis
- **OWASP compliance**: Follow OWASP Top 10 guidelines

### Automated Security Tools Integration

- **SAST Analysis**: `security-scan.sh --sast-only` for static application security testing
- **Dependency Scanning**: `security-scan.sh --deps-only` for vulnerability detection
- **Container Security**: `security-scan.sh --containers-only` for Docker image analysis
- **Secrets Detection**: `security-scan.sh --secrets-only` for credential leak prevention
- **Comprehensive Analysis**: `security-scan.sh --all` for complete security assessment

**CRITICAL**: When security conflicts with performance or usability, security takes absolute precedence.
