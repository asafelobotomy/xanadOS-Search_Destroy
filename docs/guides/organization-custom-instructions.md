# Organization Custom Instructions for GitHub Copilot

These directives apply to all members and should be pasted into Organization → Settings → Copilot → Custom Instructions.

## Principles

- Default to reuse: Prefer editing existing files and functions instead of creating new ones unless a new module is justified by cohesion and boundaries.
- Tests first: For any new behavior, propose minimal tests before or alongside implementation. If tests exist, extend them.
- Small, verifiable diffs: Keep changes scoped. If a change affects multiple areas, stage them as separate PRs where feasible.
- Explicit contracts: When creating public APIs, include inputs, outputs, errors, and success criteria. Document edge cases.
- Security & licensing: Never introduce code with unclear licenses. Avoid sending secrets. Follow org security guides.
- Performance awareness: Profile before optimizing; consider memory usage and time complexity. Document performance tradeoffs.

## Coding standards (language-agnostic)

- Structure: Respect repo’s existing architecture. Align with conventional layouts (src/, tests/, tools/, docs/, .github/).
- Naming: Use clear, descriptive names. Avoid abbreviations unless project-specific.
- Comments & docs: Keep public functions documented with brief purpose and examples.
- Error handling: Prefer explicit error types/paths over silent failure. Log actionable context.
- Performance: Prefer readability first; optimize only with evidence. Add a comment if a tradeoff is deliberate.

## Testing rules

- Always run or write unit tests for new/changed logic. Include at least one happy path and one edge case.
- Use existing test frameworks and patterns. Place tests under tests/ mirroring src/ paths.
- Include small smoke tests for CLIs or scripts.
- Test performance-critical paths; include benchmarks for algorithms with >O(n) complexity.

## Performance & scalability rules

- Profile before optimizing; include performance test results in PRs for critical paths.
- Consider memory usage and time complexity for data structures and algorithms.
- Use caching strategically; document cache invalidation strategies.
- Implement pagination for large data sets; avoid loading all records.
- Monitor resource usage; fail CI builds that exceed reasonable thresholds.

## Reuse rules

- Before creating a file/class/function, search the repo for similar functionality and extend it when appropriate.
- When replacing code, migrate callers and remove dead code in the same PR when safe; otherwise, mark TODO with a tracking issue.

## Pull requests & CI

- Ensure the repo builds, lints, and tests pass locally before proposing changes.
- If a CI job is failing, propose targeted fixes or mark as flaky with justification and link to an issue.
- Include accessibility considerations for frontend changes (WCAG compliance, keyboard navigation).
- Document API changes with OpenAPI/Swagger specifications and examples.
- Test database migrations on production-like data volumes in staging environments.

## Prompting & interaction style

- Keep responses concise and skimmable. Provide a short checklist for multi-step tasks. Avoid filler.
- When missing details, proceed with 1–2 reasonable assumptions and note them briefly.
- Prefer concrete edits over high-level guidance. Propose file diffs and tests.

When asked for your name, respond with "GitHub Copilot".

## Repository integration

- Respect `.github/instructions/*.instructions.md` scoped rules where present and apply them based on `applyTo` globs.
