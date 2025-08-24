'use strict';

/**
 * Severity ranking used to pick the highest severity across matched rules.
 * Higher number = higher severity.
 */
const SEVERITY_RANK = { high: 3, medium: 2, low: 1 };

/**
 * Build a lowercase text blob for simple keyword matching.
 * @param {{ title?: string, body?: string }} issue
 * @returns {string}
 */
function buildHaystack(issue) {
  const title = issue.title ? String(issue.title) : '';
  const body = issue.body ? String(issue.body) : '';
  return `${title} ${body}`.toLowerCase();
}

/**
 * Normalize a triage rule to predictable shapes.
 * @param {{ keyword?: string, label?: string, severity?: string }} rule
 * @returns {{ keyword: string, label?: string, severity?: string }}
 */
function normalizeRule(rule) {
  const keyword = String(rule.keyword || '').toLowerCase();
  const label = rule.label ? String(rule.label) : undefined;
  const severity = rule.severity && SEVERITY_RANK[rule.severity] ? rule.severity : undefined;
  return { keyword, label, severity };
}

/**
 * Get the highest severity from a collection of severities.
 * @param {Iterable<string>} severities
 * @returns {'high'|'medium'|'low'}
 */
function getHighestSeverity(severities) {
  let best = 'low';
  for (const s of severities) {
    if (SEVERITY_RANK[s] > SEVERITY_RANK[best]) best = s;
  }
  return best;
}

/**
 * Apply rules to a single issue, returning labels and computed severity.
 * Behavior-preserving: same outputs for same inputs as before refactor.
 * @param {{ id?: number, title?: string, body?: string }} issue
 * @param {Array<{ keyword?: string, label?: string, severity?: string }>} rules
 */
function applyRulesToIssue(issue, rules) {
  const haystack = buildHaystack(issue);
  const labels = [];
  const severities = [];

  for (const r of rules) {
    const rule = normalizeRule(r);
    if (!rule.keyword) continue;
    if (haystack.includes(rule.keyword)) {
      if (rule.label) labels.push(rule.label);
      if (rule.severity) severities.push(rule.severity);
    }
  }

  const uniqueLabels = [...new Set(labels)];
  const uniqueSeverities = [...new Set(severities)];
  const severity = uniqueSeverities.length ? getHighestSeverity(uniqueSeverities) : 'low';

  return { ...issue, labels: uniqueLabels, severity };
}

/**
 * Triage a list of issues using the provided rules.
 * @param {Array<object>} issues
 * @param {Array<{ keyword?: string, label?: string, severity?: string }>} rules
 * @returns {Array<object>}
 */
function triageIssues(issues, rules) {
  if (!Array.isArray(issues)) throw new TypeError('issues must be an array');
  if (!Array.isArray(rules)) throw new TypeError('rules must be an array');
  return issues.map((i) => applyRulesToIssue(i, rules));
}

module.exports = { triageIssues, SEVERITY_RANK };
