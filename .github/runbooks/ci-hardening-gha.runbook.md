# Runbook: CI Hardening (GitHub Actions)

Establish a reliable, fast CI with caching and protections. Use with Copilot agent mode.

## Prerequisites

- Project has lint/test scripts

## Steps

1. Add a basic CI workflow (install, lint, test).
2. Enable caching for dependencies.
3. Parallelize jobs where helpful.
4. Enforce branch protections (review + status checks).
5. Add a status badge to README.

## Prompts

- "Create a GitHub Actions workflow to lint and test on push and PR."
- "Enable cache for npm/pip/gradle to speed up CI runs."
- "Add a README badge for CI status."

## Success criteria

- CI runs under 5 minutes on typical changes
- Required checks block merges when failing
