# Copilot Brushes

Short, reliable prompts to apply targeted transformations. Copy into Copilot Chat
or Inline Chat when working on a file or selection.

## Security hardening

- Prompt: "Harden this code for security: validate inputs, avoid injection,

  handle secrets properly, add error handling, and explain changes briefly."

- Use when adding endpoints, parsing input, or handling auth/config.

## Performance optimization

- Prompt: "Optimize for performance: reduce allocations, avoid needless work,

  prefer streaming/iterators, batch I/O, and measure hotspots. Provide a
  micro-benchmark suggestion."

- Use on hot code paths, loops, and I/O heavy sections.

## Readability and cleanup

- Prompt: "Improve readability without changing behavior: simplify branches,

  extract helpers, use clear names, and add concise docstrings. Show a minimal
  diff and rationale."

- Use before reviews or when code smells accumulate.

## Test generation

- Prompt: "Generate unit tests for this module: include happy path, boundary,

  and one failure case. Use the project’s test framework conventions."

- Use when adding features or preventing regressions.

## API contract check

- Prompt: "From the code, infer precise function contracts: inputs, outputs,

  errors, side effects. Add guards and update docstrings accordingly."

- Use to enforce interfaces and maintainability.

## Logging and observability

- Prompt: "Add structured logging at info/warn/error with correlation IDs and

  redaction for PII. Include one tracing hook if supported."

- Use to aid debugging in production.

## Migration assist (TypeScript, framework, or API)

- Prompt: "Migrate this file to \<target\>: update imports, types, APIs, and

  idioms. Note any TODOs that require manual follow-up."

- Use for incremental migrations with clear TODOs.
