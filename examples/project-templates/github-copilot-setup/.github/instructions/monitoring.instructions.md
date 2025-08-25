---
applyTo: "**/monitoring/**/*.{py,js,ts,java,go,cs,rb,rs,yml,YAML}"

---

# Monitoring/Observability-specific Copilot Instructions

## Structured Logging Standards

- Include structured logging with JSON format: `{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "correlation_id": "uuid", "message": "...", "context": {...}}`
- Add metrics for business-critical operations: response times (p50, p95, p99), error rates (4xx, 5xx), throughput (requests/second)
- Implement health checks with detailed status: `{"status": "healthy", "version": "1.0.0", "uptime": 3600, "dependencies": {...}}`
- Use distributed tracing with OpenTelemetry, propagate trace context via HTTP headers (traceparent, tracestate)

## Log Levels & Context

- Log at specific levels: ERROR (system failures), WARN (degraded performance >2s response), INFO (significant business events), DEBUG (detailed flow)
- Include comprehensive context: `{"user_id": "123", "request_id": "uuid", "operation": "user_login", "duration_ms": 150, "ip_address": "192.168.1.1"}`
- Set up PagerDuty/Slack alerts: ERROR rate >1%, response time p95 >5s, dependency failure >5 minutes
- Use Prometheus naming conventions: `http_requests_total{method="GET",status="200"}`, `database_connection_pool_size`

## Infrastructure & Business Monitoring

- Implement Hystrix/resilience4j circuit breakers: 50% failure threshold, 30s timeout, exponential backoff
- Monitor resource utilization with alerts: CPU >80% for 5 minutes, memory >90%, disk >85%, network >1Gbps
- Track business metrics with custom gauges: conversion_rate, daily_active_users, revenue_per_request
- Include Sentry/Rollbar error tracking with 10KB context limit, PII scrubbing, source map support
- Set up Grafana dashboards with 4 golden signals: latency, traffic, errors, saturation
- Implement Pingdom/DataDog synthetic monitoring for critical paths: login, checkout, API health every 1 minute

## ⚠️ SECURITY OVERRIDE: Never log passwords, API keys, or PII. Scrub sensitive data before logging
