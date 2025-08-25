---
applyTo: "**/backend/**/*.{py,js,ts,java,go,cs,rb,rs,php}"

---

# Advanced Backend Development Instructions

## Serverless-First Architecture (2024/2025 Patterns)

- Implement event-driven serverless designs with request-job-task models for scalability
- Use pre-warmed pods and DRAM pre-loading to minimize cold start latencies (target optimal for platform)
- Design microkernel-inspired architectures with NPU-centric execution for AI workloads
- Implement lightweight eBPF-based proxies instead of heavy container sidecars
- Use shared memory processing for high-performance inter-service communication
- Implement locality-aware placement to maximize shared memory benefits

## AI-Enhanced Backend Operations

- Integrate LLM-based agents for autonomous service maintenance and issue resolution
- Implement neural Granger causal discovery for root cause analysis in microservice failures
- Use AI-powered optimization for code performance improvements (target 50% perf gains)
- Implement intelligent scheduling with hierarchical workload-balanced task dispatching
- Use machine learning for adaptive urgency-guided request prioritization

## Next-Generation API Design

- Implement semantics-aware API completion with type-directed program synthesis
- Use comprehensive test suites for API functionality validation (99%+ coverage)
- Implement end-to-end exploit testing for security validation
- Design APIs with built-in rate limiting, circuit breakers, and bulkhead patterns
- Use OpenAPI 3.1+ with comprehensive schema validation and breaking change detection
- Implement API versioning with semantic versioning and backward compatibility guarantees

## Advanced Microservices Patterns

- Implement CQRS (Command Query Responsibility Segregation) with event sourcing
- Use distributed tracing with correlation IDs for complex request flows
- Implement service mesh with intelligent load balancing and failure detection
- Use event-driven architectures with reliable message delivery patterns
- Implement saga patterns for distributed transaction management
- Use circuit breaker patterns with adaptive thresholds and fallback strategies

## Performance & Scalability Optimization

- Target sub-100ms API response times with 99.9% availability SLOs
- Implement database connection pooling with optimal pool sizing strategies
- Use read replicas and write-through caching for database scaling
- Implement horizontal pod autoscaling based on custom metrics
- Use compression algorithms for network traffic optimization (gzip, brotli)
- Implement efficient pagination with cursor-based navigation for large datasets

## Modern Security Patterns

- Implement zero-trust architecture with service-to-service authentication
- Use JWT tokens with short expiration times and refresh token rotation
- Implement API gateway security with rate limiting per client/IP
- Use input validation with request/response schema enforcement
- Implement security headers (HSTS, CSP, CSRF protection) for all endpoints
- Use secrets management with automatic rotation and least-privilege access

## Data Processing & Streaming

- Implement event streaming with Apache Kafka or cloud-native alternatives
- Use stream processing for real-time analytics and data transformation
- Implement data validation pipelines with schema evolution support
- Use dead letter queues for failed message processing with retry policies
- Implement data compression and serialization optimization (Avro, Protocol Buffers)
- Use batch processing with optimal batch sizes for efficiency

## Observability & Monitoring

- Implement structured logging with correlation IDs and trace spans
- Use distributed tracing (OpenTelemetry) for request flow visualization
- Implement custom metrics with business-relevant KPIs and SLIs
- Use health checks with readiness and liveness probes
- Implement alerting with escalation policies and runbook automation
- Use performance profiling for CPU, memory, and I/O optimization

## Infrastructure as Code

- Use Terraform or equivalent for infrastructure provisioning with state management
- Implement GitOps workflows for deployment automation and rollback capabilities
- Use container orchestration (Kubernetes) with resource limits and requests
- Implement blue-green deployments with automated rollback on failure detection
- Use feature flags for progressive rollouts and A/B testing
- Implement chaos engineering for resilience testing and failure simulation

## Development Workflow Integration

- Implement automated code generation for boilerplate API endpoints
- Use contract-first development with OpenAPI specification driving implementation
- Implement automated performance testing with benchmarking and regression detection
- Use mutation testing for code quality validation beyond coverage metrics
- Implement automated security scanning in CI/CD pipelines
- Use dependency scanning with automated vulnerability patching where possible
