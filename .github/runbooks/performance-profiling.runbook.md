# Runbook: Performance Profiling and Optimization

Measure before optimizing; adopt repeatable profiling. Use with Copilot agent mode.

## Prerequisites

- Project runs with sample inputs or fixtures

## Steps

1. Add a micro-benchmark or profiling harness.
2. Identify hotspots with a simple scenario.
3. Optimize one bottleneck at a time with small diffs.
4. Add CI job for perf smoke tests if feasible.
5. Document before/after metrics.

## Prompts

- "Add a basic benchmark for `function` with realistic inputs."
- "Profile `path`or`module` and list top bottlenecks."
- "Optimize `bottleneck` and show performance delta."

## Success criteria

- Measurable improvement with small, safe changes
- Repeatable perf checks documented
