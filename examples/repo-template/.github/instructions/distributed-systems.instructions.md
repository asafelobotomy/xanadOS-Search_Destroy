---
applyTo: "**/*.{py,js,ts,java,go,cs,rb,rs,yml,YAML,tf}"

---

# Distributed Systems & Resilience Instructions

## Event-Driven Architecture Patterns

- Implement event sourcing with immutable event logs for complete system state reconstruction
- Use CQRS (Command Query Responsibility Segregation) to separate read and write models
- Design event schemas with backward and forward compatibility using schema evolution
- Implement event versioning with semantic versioning for breaking changes
- Use event replay capabilities for system recovery and debugging
- Implement event deduplication with idempotency keys to handle duplicate events

## Fault Tolerance & Resilience

- Implement circuit breaker patterns with 50% failure threshold over 10 requests, 30-second recovery timeout
- Use bulkhead patterns to isolate critical resources with separate thread pools (min 10, max 50 threads)
- Implement retry policies with exponential backoff (base 100ms, max 30s) plus 10% jitter
- Use timeout patterns: API calls 5s, database queries 10s, external services 30s
- Implement graceful degradation with cached fallback responses (5-minute TTL minimum)
- Use health checks with 30s readiness probe, 10s liveness probe, 3-failure threshold

## Distributed Data Management

- Implement eventual consistency patterns with vector clocks for conflict resolution
- Use distributed caching with Redis, 1-hour default TTL, pub/sub invalidation
- Implement database sharding with consistent hashing (SHA-256, 1024 virtual nodes)
- Use read replicas with <1s replication lag monitoring, automatic failover
- Implement distributed transactions with saga patterns, 2-hour timeout maximum
- Use optimistic locking with version fields, retry 3 times with exponential backoff

## Service Communication Patterns

- Implement asynchronous messaging with message queues and reliable delivery guarantees
- Use publish-subscribe patterns for loose coupling between services
- Implement request-reply patterns with correlation IDs for tracking responses
- Use service discovery with health checking and load balancing
- Implement API composition patterns for data aggregation across services
- Use content-based routing for intelligent message distribution

## Scalability & Performance

- Implement horizontal scaling with stateless service designs
- Use load balancing with appropriate algorithms (round-robin, least connections, weighted)
- Implement connection pooling with optimal pool sizes and connection lifecycle management
- Use compression for network communications (gzip, lz4, snappy)
- Implement data partitioning strategies for improved query performance
- Use materialized views for read-heavy workloads with appropriate refresh strategies

## Monitoring & Observability

- Implement distributed tracing with trace sampling and span correlation
- Use structured logging with correlation IDs and contextual information
- Implement metrics collection with RED (Rate, Errors, Duration) and USE (Utilization, Saturation, Errors) methodologies
- Use alerting with SLI/SLO-based thresholds and escalation policies
- Implement chaos engineering with controlled failure injection and blast radius limitation
- Use synthetic monitoring for proactive issue detection

## Security in Distributed Systems

- Implement service-to-service authentication with mutual TLS or JWT tokens
- Use API gateway patterns for centralized authentication and authorization
- Implement secret management with rotation and least-privilege access
- Use network segmentation with micro-segmentation for service isolation
- Implement audit logging for security events and compliance requirements
- Use encryption in transit and at rest with appropriate key management

## Development & Deployment Patterns

- Implement blue-green deployments with automated rollback on health check failures
- Use canary deployments with traffic splitting and automated promotion/rollback
- Implement feature flags for progressive rollouts and A/B testing
- Use infrastructure as code with version control and change approval processes
- Implement automated testing at service boundaries with contract testing
- Use deployment pipelines with quality gates and approval workflows

## Data Consistency Patterns

- Implement two-phase commit (2PC) for strong consistency requirements
- Use three-phase commit (3PC) to handle coordinator failures
- Implement consensus algorithms (Raft, PBFT) for distributed decision making
- Use vector clocks for conflict-free replicated data types (CRDTs)
- Implement operational transformation for real-time collaborative editing
- Use merkle trees for efficient data synchronization and integrity verification

## Modern Architecture Patterns

- Implement serverless patterns with function composition and event triggers
- Use edge computing patterns for reduced latency and improved user experience
- Implement multi-region deployments with data locality and regulatory compliance
- Use container orchestration with resource quotas and horizontal pod autoscaling
- Implement service mesh architecture with traffic management and security policies
- Use API-first design with contract-driven development and mock services
