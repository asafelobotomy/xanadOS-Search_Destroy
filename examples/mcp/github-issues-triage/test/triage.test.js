'use strict';

const assert = require('node:assert');
const { triageIssues } = require('../src/triage');

(function testBasicRules() {
  const rules = [
    { keyword: 'bug', label: 'bug', severity: 'high' },
    { keyword: 'docs', label: 'documentation', severity: 'low' },
  ];
  const issues = [
    { id: 1, title: 'Bug: crash', body: 'app bug present' },
    { id: 2, title: 'Docs update', body: 'docs need love' },
  ];
  const out = triageIssues(issues, rules);
  assert.equal(out[0].severity, 'high');
  assert.ok(out[0].labels.includes('bug'));
  assert.equal(out[1].severity, 'low');
  assert.ok(out[1].labels.includes('documentation'));
  console.log('triage.test.js: basic rules PASS');
})();
