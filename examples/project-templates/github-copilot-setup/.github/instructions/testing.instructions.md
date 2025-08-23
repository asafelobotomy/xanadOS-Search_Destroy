---
applyTo: "**/te- Implement chaos engineering practices for distributed systems testing

## Context-Aware Testing Strategies

**Small Projects (<1K LOC)**: Focus on unit tests with >80% coverage, minimal integration tests
**Medium Projects (1K-10K LOC)**: Add integration tests, contract testing for APIs, performance tests for critical paths
**Large Projects (>10K LOC)**: Implement full testing pyramid, chaos engineering, mutation testing, end-to-end tests
**Microservices**: Emphasize contract testing, service virtualization, distributed tracing in tests
**Monoliths**: Focus on module boundaries, integration tests, database testing with testcontainers

## Preferred Testing Frameworks (per language)

- **Python**: Use `pytest` for all unit and integration tests.
- **JavaScript/TypeScript**: Use `vitest` for new projects, `jest` for existing projects.
- **Java**: Use `JUnit 5` for unit and integration tests.
- **Go**: Use Go's built-in testing package with table-driven tests.
- **.NET**: Use `xUnit` or `NUnit` as per repo standard.
- **Ruby**: Use `RSpec`.
- **Rust**: Use Rust's built-in test framework.

**⚠️ SECURITY OVERRIDE: Always include security-specific tests for authentication, authorization, input validation, and data sanitization**y,js,ts,java,go,cs,rb,rs}"
---

# Testing Strategy-specific Copilot Instructions

- Follow the testing pyramid: many unit tests, some integration tests, few e2e tests
- Write tests that are fast, reliable, and independent of external services
- Use test doubles (mocks, stubs, fakes) appropriately; avoid over-mocking
- Include property-based testing for complex algorithms and data transformations
- Test error conditions and edge cases, not just happy paths
- Use descriptive test names that explain the scenario and expected outcome
- Group related tests with clear setup and teardown patterns
- Implement contract testing for API integrations and service boundaries
- Use test fixtures and factories to create consistent test data
- Mock external dependencies (APIs, databases, file systems) in unit tests
- Include smoke tests for critical user journeys in CI/CD pipeline
- Test performance characteristics for algorithms with known complexity requirements
- Use mutation testing to verify test coverage quality, not just line coverage
- Implement chaos engineering practices for distributed systems testing

## Preferred Testing Frameworks (per language)

- **Python**: Use `pytest` for all unit and integration tests.
- **JavaScript/TypeScript**: Use `vitest` for new projects, `jest` for existing projects.
- **Java**: Use `JUnit 5` for unit and integration tests.
- **Go**: Use Go’s built-in testing package with table-driven tests.
- **.NET**: Use `xUnit` or `NUnit` as per repo standard.
- **Ruby**: Use `RSpec`.
- **Rust**: Use Rust’s built-in test framework.
