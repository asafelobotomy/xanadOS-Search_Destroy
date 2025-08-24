---
applyTo: "**/*"
---

# Placeholder/TODO Tracking - MANDATORY

- Purpose: single place to quickly find and resolve placeholders, stubs, and TODOs.
- Scope: code and docs across the repository.

## How to add entries

Add entries when you must introduce a placeholder/stub:

- ID: short identifier (e.g., `docs-api-cleanup`)
- Location: file path and line/context (e.g., `docs/api/script-api.md: L12`)
- Marker: copy the exact TODO/PLACEHOLDER line
- Issue: link to tracking issue (if any)
- ETA: target date for removal

## Current entries

- ID: monitoring-mcp-custom-metrics
	- Location: `.github/mcp/servers/monitoring-mcp/index.js` (method `getCustomMetrics`)
	- Marker: `// Placeholder for custom metrics integration`
	- Issue: (none yet) — consider opening a tracking issue to define data sources/endpoints
	- ETA: 2025-09-07 (proposed)
