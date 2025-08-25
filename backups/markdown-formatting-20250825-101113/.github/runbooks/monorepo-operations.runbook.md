# Monorepo Operations Runbook

A lightweight reference for managing a JS/TS monorepo with workspaces.

## Layout

- `package.JSON`with`workspaces`or`pnpm-workspace.YAML`.
- Packages under `packages/_`(libs), apps under`apps/_`.
- Shared configs under `configs/` (eslint, tsconfig, jest).

## Common tasks

- Add a package: create folder, add `package.JSON`, link via workspace.
- Local dev: run tasks from the root (e.g., `npm run -w @scope/pkg build`).
- Cross-package changes: keep commits scoped; update changelogs via changesets.

## Tooling options

- Nx or Turborepo for task orchestration and caching.
- npm/Yarn/PNPM workspaces for linking and hoisting controls.
- Changesets for versioning and release PRs.

## CI tips

- Cache node_modules and build outputs; key by lockfile + task graph.
- Affected builds: detect changed packages and run only necessary tasks.
- Enforce lint/test/typecheck gates before publish.

## Versioning

- Prefer independent versioning for libraries; lockstep for tightly-coupled apps.
- Automate release PRs; ensure changelog generation and tags.

## Pitfalls

- Hidden implicit deps: enforce explicit `dependencies`and`peerDependencies`.
- Circular deps: detect via tooling and refactor boundaries.
- Massive root scripts: move package-specific logic to package-level scripts.
