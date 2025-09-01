import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { TemplateValidationSystem } from '../template-validation-system.js';
import { promises as fs } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

const testDir = join(tmpdir(), 'template-validation-test-' + Date.now());

// Setup test environment
test.before(async () => {
  await fs.mkdir(testDir, { recursive: true });

  // Create test template files
  const templatesDir = join(testDir, '.github', 'chatmodes');
  await fs.mkdir(templatesDir, { recursive: true });

  // Valid chat mode template
  const validChatMode = `# Expert Advisor Chat Mode

## Description
This chat mode transforms the assistant into an expert advisor.

## Role
Act as a knowledgeable expert advisor who provides detailed guidance.

## Response Style
- Professional and authoritative tone
- Structured responses with clear recommendations
- Evidence-based advice

## Examples
**User**: How should I structure my project?
**Assistant**: Based on best practices, I recommend...

## Constraints
- Provide factual information only
- Acknowledge limitations when uncertain
`;

  await fs.writeFile(join(templatesDir, 'expert-advisor.md'), validChatMode);

  // Invalid chat mode template (missing sections)
  const invalidChatMode = `# Incomplete Chat Mode

## Description
This is an incomplete template.

## Role
Some role definition.
`;

  await fs.writeFile(join(templatesDir, 'incomplete.md'), invalidChatMode);
});

// Cleanup test environment
test.after(async () => {
  await fs.rm(testDir, { recursive: true, force: true });
});

test('TemplateValidationSystem - Constructor', () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  assert.ok(validator);
  assert.equal(validator.rootPath, testDir);
  assert.ok(validator.templateSchemas);
  assert.ok(validator.templateSchemas.has('chat-mode'));
});

test('TemplateValidationSystem - Template Discovery', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const files = await validator.discoverTemplateFiles();
  assert.ok(Array.isArray(files));
  assert.ok(files.length >= 2);
  assert.ok(files.some(f => f.includes('expert-advisor.md')));
  assert.ok(files.some(f => f.includes('incomplete.md')));
});

test('TemplateValidationSystem - Template Type Detection', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const chatModeFile = join(testDir, '.github', 'chatmodes', 'expert-advisor.chatmode.md');
  const content = await fs.readFile(chatModeFile, 'utf8');

  const type = validator.determineTemplateType(chatModeFile, content);
  assert.equal(type, 'chat-mode');
});

test('TemplateValidationSystem - Schema Validation - Valid Template', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const content = `# Expert Advisor Chat Mode

## Description
This chat mode transforms the assistant into an expert advisor.

## Role
Act as a knowledgeable expert advisor.

## Response Style
Professional and authoritative tone.

## Examples
Sample interactions.

## Constraints
Provide factual information only.
`;

  const schema = validator.templateSchemas.get('chat-mode');
  const result = validator.validateAgainstSchema(content, schema);

  assert.equal(result.isValid, true);
  assert.equal(result.errors.length, 0);
});

test('TemplateValidationSystem - Schema Validation - Invalid Template', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const content = `# Incomplete Template

## Description
Missing required sections.
`;

  const schema = validator.templateSchemas.get('chat-mode');
  const result = validator.validateAgainstSchema(content, schema);

  assert.equal(result.isValid, false);
  assert.ok(result.errors.length > 0);
  assert.ok(result.errors.some(e => e.includes('role')));
});

test('TemplateValidationSystem - Content Standards - Accessibility', () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const goodContent = `# Title

## Section

Here is an image with alt text: ![Description](image.jpg)

[Descriptive link text](https://example.com)
`;

  const result = validator.validateAccessibility(goodContent);
  assert.ok(result.score > 0.8);
  assert.equal(result.issues.length, 0);

  const badContent = `# Title

### Skipped Level

![](image.jpg)

[Click here](https://example.com)
`;

  const badResult = validator.validateAccessibility(badContent);
  assert.ok(badResult.score < 0.8);
  assert.ok(badResult.issues.length > 0);
});

test('TemplateValidationSystem - Content Standards - Formatting', () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const goodContent = `# Title

## Section

Here's a code block:

\`\`\`javascript
console.log('Hello');
\`\`\`

- List item 1
- List item 2

`;

  const result = validator.validateFormatting(goodContent);
  assert.ok(result.score > 0.8);

  const badContent = `# Title

## Section

\`\`\`
console.log('No language');
\`\`\`
- List without spacing
- More items
Text immediately after
`;

  const badResult = validator.validateFormatting(badContent);
  assert.ok(badResult.score < 1.0);
  assert.ok(badResult.issues.length > 0);
});

test('TemplateValidationSystem - Content Standards - Style Guide', () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const goodContent = `# Title

## Section

This is a well-written sentence. It follows good style guidelines. The content is clear and concise.
`;

  const result = validator.validateStyleGuide(goodContent);
  assert.ok(result.score > 0.7);

  const badContent = `# Title

## Section

This is an extremely long sentence that goes on and on and on and contains way too many words and clauses and should definitely be broken up into smaller, more manageable sentences that readers can actually follow and understand without getting lost.

The document was written by the team and was reviewed by the manager and was approved by the director.
`;

  const badResult = validator.validateStyleGuide(badContent);
  assert.ok(badResult.score < 1.0);
  assert.ok(badResult.issues.length > 0);
});

test('TemplateValidationSystem - Content Standards - Internationalization', () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const goodContent = `# Title

## Section

This content follows international standards. Dates are in ISO format: 2024-01-15.
`;

  const result = validator.validateI18n(goodContent);
  assert.ok(result.score > 0.8);

  const badContent = `# Title

## Section

This costs $50 and measures 10 feet. The temperature is 72°F. Date: 12/31/2024.
`;

  const badResult = validator.validateI18n(badContent);
  assert.ok(badResult.score < 1.0);
  assert.ok(badResult.issues.length > 0);
});

test('TemplateValidationSystem - Full Validation', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const result = await validator.validateTemplateSystem();

  assert.ok(result);
  assert.ok(result.metrics);
  assert.ok(result.results);
  assert.ok(Array.isArray(result.results));

  // Should have validation results for our test files
  assert.ok(validator.validationResults.length > 0);

  // Should have found at least one valid template
  const validResults = validator.validationResults.filter(r => r.status === 'passed');
  assert.ok(validResults.length > 0);

  // Should have found the invalid template
  const invalidResults = validator.validationResults.filter(r => r.status === 'error');
  assert.ok(invalidResults.length > 0);
});

test('TemplateValidationSystem - Performance Metrics', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  // Run a subset of validation to test performance tracking
  await validator.runPerformanceTests();

  assert.ok(validator.performanceMetrics);
  assert.ok(typeof validator.performanceMetrics.totalValidationTime === 'number');
  assert.ok(typeof validator.performanceMetrics.averageFileProcessingTime === 'number');
  assert.ok(typeof validator.performanceMetrics.filesProcessed === 'number');
  assert.ok(typeof validator.performanceMetrics.throughput === 'number');
});

test('TemplateValidationSystem - Recommendation Generation', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  // Add some mock validation results
  validator.validationResults = [
    {
      type: 'template-structure',
      status: 'error',
      message: 'Missing required sections'
    },
    {
      type: 'content-standards',
      status: 'warning',
      message: 'Content quality issues'
    }
  ];

  validator.integrationTests = [
    {
      type: 'mcp-server',
      status: 'failed',
      message: 'MCP server test failed'
    }
  ];

  const recommendations = validator.generateRecommendations();

  assert.ok(Array.isArray(recommendations));
  assert.ok(recommendations.length > 0);

  // Should have high priority recommendation for structure errors
  const highPriorityRecs = recommendations.filter(r => r.priority === 'high');
  assert.ok(highPriorityRecs.length > 0);
});

test('TemplateValidationSystem - Report Generation', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  // Mock some data for report generation
  validator.metrics = {
    templatesValidated: 2,
    schemasValidated: 4,
    integrationTestsPassed: 1,
    complianceChecksPassed: 1,
    errors: 1,
    warnings: 1
  };

  validator.qualityMetrics = {
    overallScore: 0.75,
    validationCoverage: 0.8,
    complianceRate: 0.7,
    integrationSuccess: 0.5
  };

  validator.performanceMetrics = {
    totalValidationTime: 1000,
    averageFileProcessingTime: 50,
    filesProcessed: 2,
    throughput: 2
  };

  validator.complianceStatus = {
    score: 0.75,
    isCompliant: true,
    checks: {}
  };

  const mockReport = {
    timestamp: new Date().toISOString(),
    summary: validator.metrics,
    qualityMetrics: validator.qualityMetrics,
    performanceMetrics: validator.performanceMetrics,
    complianceStatus: validator.complianceStatus,
    validationResults: [],
    integrationTests: [],
    recommendations: []
  };

  const readableReport = validator.generateReadableReport(mockReport);

  assert.ok(typeof readableReport === 'string');
  assert.ok(readableReport.includes('# Template Validation Report'));
  assert.ok(readableReport.includes('Executive Summary'));
  assert.ok(readableReport.includes('Quality Metrics'));
  assert.ok(readableReport.includes('Performance Metrics'));
});

// Integration tests (when MCP servers are available)
test('TemplateValidationSystem - MCP Server Detection', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  // This will return empty array since we don't have MCP servers in test env
  const mcpServers = await validator.findMCPServers();
  assert.ok(Array.isArray(mcpServers));
});

test('TemplateValidationSystem - Chat Mode Detection', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: testDir
  });

  const chatModes = await validator.findChatModes();
  assert.ok(Array.isArray(chatModes));
  assert.ok(chatModes.length >= 2); // Should find our test chat modes
});

test('TemplateValidationSystem - Error Handling', async () => {
  const validator = new TemplateValidationSystem({
    rootPath: '/nonexistent/path'
  });

  // Should handle non-existent paths gracefully
  const files = await validator.discoverTemplateFiles();
  assert.ok(Array.isArray(files));
  assert.equal(files.length, 0);
});
