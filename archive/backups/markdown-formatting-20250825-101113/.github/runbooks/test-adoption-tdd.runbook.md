# Runbook: Test Adoption (TDD)

Adopt tests incrementally and use TDD to drive safe changes.
Use with Copilot agent mode.

## Prerequisites

- Project builds and runs locally
- Preferred test framework identified (e.g., Jest, PyTest, JUnit)

## Steps

1. Add test tooling and example test.
2. Identify a small unit to cover first (pure function or small module).
3. Write a failing test (describe intent and edge cases).
4. Implement the minimal code to pass the test.
5. Repeat for one or two more units.
6. Add test scripts and CI workflow to run on PRs.

## Prompts

- "Add a minimal test setup for `framework` with one sample test."
- "Generate unit tests for `file` covering happy path, boundary, and one error."
- "Refactor code only as needed to pass tests; show concise diffs."
- "Add a GitHub Actions workflow to run tests on pull requests."

## Success criteria

- Tests pass locally and in CI
- Coverage for at least 2-3 core units
- Clear next areas for test expansion
