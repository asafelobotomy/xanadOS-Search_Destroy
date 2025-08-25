---
applyTo: "**/API/**/*.{py,js,ts,java,go,cs,rb,rs,php}"
---

# API Design-specific Copilot Instructions

## Context-Aware API Patterns

**Internal APIs**: Use simplified auth (service tokens), relaxed rate limits, detailed error messages
**Public APIs**: Implement strict auth (OAuth2), aggressive rate limiting (100 req/min), sanitized error messages
**Partner APIs**: Use API keys with scoped permissions, moderate rate limits (1000 req/hour), SLA guarantees
**Microservices**: Implement circuit breakers, distributed tracing, service mesh integration

## API Standards

- Use RESTful conventions with OpenAPI 3.0+ documentation, include response examples
- Implement consistent error response formats: `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": [...]}}`
- Use semantic HTTP status codes: 200 (success), 201 (created), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 409 (conflict), 422 (validation error), 500 (server error)
- Include rate limiting headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Version APIs using URL versioning (/API/v1/) with sunset headers for deprecated versions
- Implement cursor-based pagination for large datasets: `{"data": [...], "pagination": {"next_cursor": "...", "has_more": true}}`
- Use consistent naming conventions: snake_case for JSON responses, camelCase for JavaScript clients
- Include comprehensive request/response examples in OpenAPI documentation with schema validation
- Implement input validation with JSON Schema, return detailed validation errors with field-level messages
- Add health check endpoints: `/health`(basic),`/ready`(dependencies),`/live` (process health)
- Use content negotiation with `Accept: application/JSON`default, support`application/XML` for legacy
- Implement JWT authentication for stateless APIs, OAuth2 for user-facing APIs, API keys for service-to-service
- Log API requests with correlation IDs (UUID v4), include request duration and response status
- Include API deprecation warnings with `Sunset` header and 6-month minimum deprecation timeline

## ⚠️ SECURITY OVERRIDE: All API endpoints must implement authentication, input validation, and rate limiting regardless of performance impact
