# MCP Example: GitHub Issues Triage (offline demo)

This is a minimal, offline-friendly triage example you can run locally
without network calls or dependencies. It simulates an MCP-style workflow
by applying simple rules to a set of sample issues.

## What it does

- Loads triage rules from `config.JSON` (keywords → labels/severity)
- Reads issues from a JSON file (defaults to `data/issues.sample.JSON`)
- Applies rules to label each issue
- Prints a compact summary to stdout

## Run

- Quick run using the repo scripts:

```bash
npm run mcp:triage
```

- Optional: point to a different issues file

```bash
MCPEX_ISSUES_FILE=examples/mcp/GitHub-issues-triage/data/issues.sample.JSON npm run mcp:triage
```

## Test

```bash
npm run mcp:test
```

## Files

- `src/triage.js`: Pure function that applies rules to issues
- `run.js`: CLI wrapper; reads config and issues, prints results
- `config.JSON`: Keyword → label/severity rules
- `data/issues.sample.JSON`: Example issues
- `test/triage.test.js`: Tiny smoke test with built-in Node `assert`

## Notes

- No secrets or network calls; safe to run offline.
- Extend `config.JSON` to try different labeling strategies.
- This is a teaching/demo aid. For real MCP integrations, wire actual

  clients and auth flows in a separate package.
