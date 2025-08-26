# Repository Custom Instructions for GitHub Copilot

These instructions apply across this repository.
For file- or folder-scoped rules, see `.GitHub/instructions/`.

Core directives

- Always prefer reusing and extending existing code over creating new files.

Only create new modules when cohesion and boundaries clearly require it.

- Propose tests alongside code changes.

If a test suite exists, extend it; otherwise, scaffold minimal tests under `tests/`mirroring`src/`.

- Follow the project’s coding standard and formatting tools.

Don’t change unrelated code formatting in the same PR.

- Keep diffs small and focused. If a refactor is needed, isolate it as a separate change with tests.
- Include a short contract for public functions: inputs, outputs, error modes, edge cases.

Directory structure

- Source code under `src/` (or the repository’s prevailing convention).
- Tests under `tests/`mirroring the`src/` structure.
- CI and automation in `.GitHub/workflows/`.
- Developer tools and scripts in `tools/`or`scripts/`.
- Docs in `docs/`.

Testing

- Write at least one happy-path and one edge-case test for new behavior.
- Favor fast, deterministic tests. Use fixtures over network calls when feasible.

Reuse rules

- Search the codebase for similar functions before adding new ones.

Extend or generalize existing code where appropriate.

- If deprecating code, migrate call sites and remove dead code or create a follow-up issue with a TODO comment linking it.

Pull request etiquette

- Ensure code builds, lints, and tests pass locally.
- Describe assumptions and tradeoffs in PR description.

Interaction style

- Be concise. For multi-step tasks, provide a small checklist

Prefer concrete edits and tests over general advice.

When asked for your name, respond with "GitHub Copilot".
