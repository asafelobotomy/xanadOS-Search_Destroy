# Runbook: Greenfield Next.js App (Agent Mode)

Use this with Copilot agent mode. Paste steps and execute sequentially.

## Steps

1. Initialize project

- Create Next.js (App Router) with TypeScript and ESLint.
- Add Tailwind CSS.

2. Baseline quality

- Add Prettier, lint-staged, and Husky with pre-commit hooks.
- Add Jest with React Testing Library and one sample test.

3. Structure

- Create features/home with a simple page and component.
- Add layout, metadata, and basic SEO.

4. CI

- Add GitHub Actions: install, lint, test on push PR.

5. Docs

- Add README quickstart and scripts.

## Prompts

- "Create a Next.js app (latest App Router) with TypeScript and Tailwind CSS."
- "Add Jest + RTL with a sample test and wire npm test."
- "Add GitHub Actions workflow to lint and test on PR."
