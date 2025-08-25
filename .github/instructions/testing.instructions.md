---
applyTo: "**/{test,tests,spec,**tests**}/**/*"

---

# Testing Excellence Standards

## Copilot usage quick cues

- Ask: scaffolding test cases, edge-case brainstorming, quick fixture ideas.
- Edit: convert a failing spec to passing; request minimal diff + rationale.
- Agent: create/organize tests across folders and wire CI; require a run summary.

### Model routing

- Reasoning model: test strategy, partitioning, flaky diagnostics.
- Claude Sonnet class: TDD, refactors with safety nets, code review of tests.
- Gemini Pro class: large cross-language refactors or summarizing long logs.
- Fast general model: small spec additions and assertion tweaks.

### Token economy tips

- Share only the function under test and a short signature of dependencies.
- Prefer table outputs for coverage deltas and flaky-test stats.

## Comprehensive Testing Requirements

### Test modification policy (MANDATORY)

- Do not alter tests just to make them pass. Fix the underlying issue in the

  implementation or configuration instead.

- If a test is actually broken or deprecated, repair or update the test first

  (minimal diff, clear rationale), then address any newly reported failures.

- Avoid skipping or xfail-ing tests. If unavoidable, add a temporary quarantine

  tag with a linked issue and an explicit removal date.

- When a product bug is found via a failing test, add or keep a regression test

  that proves the fix.

### Test Coverage Standards

- **Minimum 80% code coverage** for all new code
- **100% coverage** for security-critical functions
- **Branch coverage**: Test all code paths and edge cases
- **Integration coverage**: Test component interactions

### Test Quality Standards

- **Descriptive test names**: Use clear, specific test descriptions
- **AAA Pattern**: Arrange, Act, Assert structure
- **Independent tests**: Each test should be isolated and repeatable
- **Fast execution**: Tests should complete in <5 seconds

### Testing Types Required

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete user workflows
- **Performance tests**: Validate response times and throughput
- **Security tests**: Validate authentication and authorization

### Test Data Management

- **Test fixtures**: Use consistent, realistic test data
- **Data isolation**: Clean up test data after each test
- **Mock external services**: Use mocks for external dependencies
- **Environment consistency**: Tests should work in all environments

### Continuous Testing

- **Pre-commit hooks**: Run tests before code commits
- **CI/CD integration**: Automated test execution in pipelines
- **Parallel execution**: Optimize test runtime with parallelization
- **Flaky test management**: Monitor and fix unstable tests

**Best Practice**: Write tests first (TDD) to ensure better code design and coverage.

## 🧰 Automated Testing Tools Integration

### Pre-Built Testing and Quality Tools

Before creating custom testing scripts, GitHub Copilot agents MUST use the
comprehensive testing and quality tools available in the toolshed:

#### Pre-Commit Testing Hooks

```bash

## Setup comprehensive pre-commit testing hooks

./scripts/tools/hooks/setup-pre-commit.sh --languages Python,JavaScript,java
./scripts/tools/hooks/setup-pre-commit.sh --testing-frameworks --dry-run
./scripts/tools/hooks/setup-pre-commit.sh --help  # View all options

```text

### Quality and Code Coverage Validation

```bash

## Comprehensive quality checking with test coverage validation

./scripts/tools/quality/check-quality.sh --test-coverage --threshold 80
./scripts/tools/quality/check-quality.sh --lint-tests --fix
./scripts/tools/quality/check-quality.sh --validate-test-structure

```text

### Security Testing Integration

```bash

## Security testing for test environments and code

./scripts/tools/security/security-scan.sh --test-env-only
./scripts/tools/security/security-scan.sh --sast-tests  # Static analysis of test code

```text

### Performance Testing and Monitoring

```bash

## Performance testing and benchmarking

./scripts/tools/monitoring/performance-monitor.sh --test-mode --duration 120
./scripts/tools/monitoring/performance-monitor.sh --benchmark-tests

```text

### Container Testing Support

```bash

## Container-based testing environments

./scripts/tools/containers/Docker-manager.sh --test-environment
./scripts/tools/containers/Docker-manager.sh --test-cleanup

```text

### Repository Structure Validation for Tests

```bash

## Validate test organization and structure

./scripts/tools/validation/validate-structure.sh --category testing
./scripts/tools/validation/validate-structure.sh --test-coverage-report

```text

### Tool Benefits for Testing

- **Automated Setup**: Pre-commit hooks ensure tests run before every commit
- **Multi-Language Support**: Support for Python, JavaScript, Java, and more
- **Quality Integration**: Combined testing and code quality validation
- **Security Testing**: Automated security analysis of test code and environments
- **Performance Monitoring**: Benchmark testing and performance regression detection
- **Container Support**: Isolated testing environments with Docker integration

### Testing Workflow Integration

1. **Setup Phase**: Use `setup-pre-commit.sh` to configure automated testing
2. **Development Phase**: Run `check-quality.sh --test-coverage` during development
3. **Security Phase**: Apply `security-scan.sh --test-env-only` for secure testing
4. **Performance Phase**: Use `performance-monitor.sh --test-mode` for benchmarks
5. **Validation Phase**: Run `validate-structure.sh --category testing` for compliance

### Advanced Testing Patterns

#### Test Environment Management

- **Isolated Environments**: Use container tools for clean test environments
- **Dependency Management**: Leverage dependency tools for test package management
- **Database Testing**: Apply database tools for test data setup and cleanup

#### Continuous Integration

- **Automated Pipelines**: All tools support CI/CD integration
- **Parallel Execution**: Tools optimized for parallel test execution
- **Reporting**: Comprehensive test reports and coverage analysis

**Reference**: See `scripts/tools/README.md` for complete testing tool documentation.
