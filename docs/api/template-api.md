# Template API

Reference for template processing and validation used by the repository.

- Location: `.github/validation/templates/`
- Validator: `node .github/validation/templates/template-validation-system.js`
- Purpose: ensure docs and prompt templates conform to expected sections and style

Inputs and outputs

- Input: Markdown template files under relevant directories
- Output: JSON and Markdown reports under `.github/validation/reports/templates/`

Usage

- Via npm: `npm run validate`
- Direct: `node .github/validation/templates/template-validation-system.js`
