---
applyTo: "**/*.{js,jsx,ts,tsx}"
priority: 70
category: "language-specific"

---

# JS/TS-specific Copilot Instructions

## Technology Recommendations

- Use `vitest`for new projects,`jest` for existing projects for testing
- Use `prettier`for formatting and`eslint` for linting
- Use TypeScript strict mode for type checking

## Error Handling

- Use Error objects with proper stack traces
- Implement error boundaries in React components
- Return Result/Maybe types for functional programming
- Prefer TypeScript when the repo uses it; add types/interfaces and narrow `any`.
- Put tests under `tests/`or`**tests**/` mirroring source structure.
- Follow existing formatter (`prettier`) and linter (`eslint`); don't mass-reformat.
- Avoid introducing new build tools without justification.
- Use strict mode; prefer const/let over var.
- Use async/await over .then() chains for readability.
- Prefer named exports for better tree-shaking.o: "**/*.{js,jsx,ts,tsx}"

---

## JS/TS-specific Copilot Instructions 2

- Prefer TypeScript when the repo uses it; add types/interfaces and narrow `any`.
- Use `vitest`/`jest`aligned with existing config; put tests under`tests/`or`**tests**/` mirroring source.
- Follow existing formatter (`prettier`) and linter (`eslint`); don’t mass-reformat.
- Avoid introducing new build tools without justification.
