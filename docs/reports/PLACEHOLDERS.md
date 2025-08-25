---
applyTo: "**/*"

---

# Placeholder/TODO Tracking - MANDATORY

- Purpose: single place to quickly find and resolve placeholders, stubs, and TODOs.
- Scope: code and docs across the repository.

## How to add entries

Add entries when you must introduce a placeholder/stub:

- ID: short identifier (e.g., `docs-API-cleanup`)
- Location: file path and line/context (e.g., `docs/API/script-API.md: L12`)
- Marker: copy the exact TODO/PLACEHOLDER line
- Issue: link to tracking issue (if any)
- ETA: target date for removal

## Current entries

- ID: monitoring-mcp-custom-metrics
- Location: `.GitHub/mcp/servers/monitoring-mcp/index.js`(method`getCustomMetrics`)
- Marker: `// Placeholder for custom metrics integration`
- Issue: `docs/reports/issues/issue-monitoring-mcp-custom-metrics.md`
- ETA: 2025-09-07 (proposed)
