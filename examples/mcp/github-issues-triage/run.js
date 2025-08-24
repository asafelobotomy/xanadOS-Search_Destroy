'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { triageIssues } = require('./src/triage');

function readJSON(p) {
  const raw = fs.readFileSync(p, 'utf8');
  return JSON.parse(raw);
}

function main() {
  const baseDir = __dirname;
  const configPath = path.join(baseDir, 'config.json');
  const defaultIssuesPath = path.join(baseDir, 'data', 'issues.sample.json');
  const issuesPath = process.env.MCPEX_ISSUES_FILE || defaultIssuesPath;

  const config = readJSON(configPath);
  const issues = readJSON(issuesPath);

  const results = triageIssues(issues, config.rules || []);

  // Summary print
  for (const r of results) {
    const labels = (r.labels || []).join(', ') || 'none';
    console.log(`#${r.id} ${r.title} -> [${labels}] severity=${r.severity}`);
  }

  const totals = results.reduce(
    (acc, r) => {
      for (const l of r.labels || []) acc.labels[l] = (acc.labels[l] || 0) + 1;
      acc.severity[r.severity] = (acc.severity[r.severity] || 0) + 1;
      return acc;
    },
    { labels: {}, severity: {} }
  );

  console.log('\nTotals:', JSON.stringify(totals, null, 2));
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error('Error:', err.message);
    process.exitCode = 1;
  }
}
