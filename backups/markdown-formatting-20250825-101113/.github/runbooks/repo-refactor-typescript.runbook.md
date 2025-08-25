# Runbook: JS → TypeScript Incremental Refactor

Use with Copilot agent mode.

## Steps

1. Add TypeScript config and tooling incrementally.
2. Introduce types on leaf modules, keep any for edges.
3. Convert one module at a time, add basic tests.
4. Fix build and lint as you go.
5. Track TODOs for complex generics.

## Prompts

- "Add a minimal tsconfig and convert src/utils/*.js to .ts with inferred types."
- "Add tests for converted modules with edge cases."
