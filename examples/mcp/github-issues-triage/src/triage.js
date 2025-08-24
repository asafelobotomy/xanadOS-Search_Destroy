'use strict';

const SEVERITY_RANK = { high: 3, medium: 2, low: 1 };

function pickHighestSeverity(severities) {
  let best = 'low';
  for (const s of severities) {
    if (SEVERITY_RANK[s] > SEVERITY_RANK[best]) best = s;
  }
  return best;
}

function applyRulesToIssue(issue, rules) {
  const haystack = `${issue.title} ${issue.body}`.toLowerCase();
  const labels = new Set();
  const severities = new Set();

  for (const rule of rules) {
    const keyword = String(rule.keyword || '').toLowerCase();
    if (!keyword) continue;
    if (haystack.includes(keyword)) {
      if (rule.label) labels.add(String(rule.label));
      if (rule.severity && SEVERITY_RANK[rule.severity]) severities.add(rule.severity);
    }
  }

  const severity = severities.size ? pickHighestSeverity([...severities]) : 'low';
  return {
    ...issue,
    labels: [...labels],
    severity
  };
}

function triageIssues(issues, rules) {
  if (!Array.isArray(issues)) throw new TypeError('issues must be an array');
  if (!Array.isArray(rules)) throw new TypeError('rules must be an array');
  return issues.map((i) => applyRulesToIssue(i, rules));
}

module.exports = { triageIssues, SEVERITY_RANK };
