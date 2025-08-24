# Tracking Issue: Monitoring MCP - Custom Metrics Integration

- ID: monitoring-mcp-custom-metrics
- Owner: TBD
- Status: Open
- Target date: 2025-09-07
- Location of placeholder: `.github/mcp/servers/monitoring-mcp/index.js`
  (method `getCustomMetrics`)

## Summary

Define, implement, and document custom metrics for the Monitoring MCP server, replacing the
current placeholder in `getCustomMetrics`.

## Background

An initial placeholder was left for custom metrics integration to be defined later. This issue
tracks the work to finalize metric schema, sampling sources, and endpoints, and to wire them into
the MCP server with tests and docs.

## Scope

- Metrics schema and naming conventions
- Data sources and collection intervals
- Implementation in `getCustomMetrics`
- Tests (unit + small integration)
- Documentation updates

## Tasks

- [ ] Decide on metric set (latency, throughput, error rate, resource usage)
- [ ] Define schema (names, types, labels/tags)
- [ ] Identify data sources and collection cadence
- [ ] Implement `getCustomMetrics` with error handling and timeouts
- [ ] Add unit tests for schema and value presence
- [ ] Add a small integration test for end-to-end metrics retrieval
- [ ] Update `docs/guides/MCP.md` with metrics section
- [ ] Remove the placeholder comment

## Definition of Done

- Metrics are returned by `getCustomMetrics` with stable schema
- Tests pass locally and in CI
- Docs updated and cross-linked
- Placeholder removed and log entry updated if needed

## Links

- Placeholder log: `docs/reports/PLACEHOLDERS.md`
- MCP guide: `docs/guides/MCP.md`

## Notes

- Prefer minimal dependencies; rely on built-in Node where possible
- Include sensible defaults and guard rails (timeouts, fallbacks) to avoid blocking
