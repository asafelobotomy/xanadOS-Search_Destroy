---
applyTo: "**/{test,tests,spec,__tests__}/**/*"
---

# Testing Excellence Standards

## Comprehensive Testing Requirements

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
