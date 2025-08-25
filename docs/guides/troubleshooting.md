# Troubleshooting Guide

## Common Issues and Solutions

### Repository Setup Issues

#### Problem: GitFlow initialization fails

**Solution**: This repository uses GitHub Flow (main branch only). Avoid GitFlow setup:

```bash

## Use GitHub Flow instead

Git checkout main
Git pull origin main
Git checkout -b feature/your-feature

```text

### Problem: Validation scripts not found

**Solution**: Use correct script paths:

```bash

## Correct path

./scripts/validation/verify-structure.sh

## NOT: ./scripts/verify-structure.sh

```text

### Development Workflow Issues

#### Problem: Markdownlint errors

**Solution**: Run lint check and fix common issues:

```bash
npm run lint

## Fix indentation, line length, and heading issues

```text

### Problem: Spellcheck failures

**Solution**: Add technical terms to `.cspell.JSON`:

```JSON
{
  "words": [
    "your-technical-term",
    "framework-name"
  ]
}

```text

### GitHub Actions Issues

#### Problem: Workflow YAML syntax errors

**Solution**: Check proper indentation in `.GitHub/workflows/`:

```YAML
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

```text

#### Problem: Missing dependencies

**Solution**: Ensure Node.js 18+ and required packages:

```bash
node --version  # Should be 18+
npm install

```text

### File Organization Issues

#### Problem: Files in wrong directories

**Solution**: Follow organization policy:

- Documentation → `docs/guides/`
- Scripts → `scripts/tools/`
- Examples → `examples/`
- Archive → `archive/`

#### Problem: Duplicate functionality

**Solution**: Check existing tools first:

```bash

## Check toolshed before creating new scripts

ls scripts/tools/
cat scripts/tools/README.md

```text

### Model and AI Issues

#### Problem: GitHub Copilot not using instructions

**Solution**: Ensure proper frontmatter and file placement:

```YAML

---
applyTo: "**/*.js"

---

```text

#### Problem: Poor code suggestions

**Solution**: Use specialized chatmodes:

- Architecture: `.GitHub/chatmodes/architect.chatmode.md`
- Security: `.GitHub/chatmodes/security.chatmode.md`
- Testing: `.GitHub/chatmodes/testing.chatmode.md`

## Getting Help

1. **Check Documentation**: Review `docs/guides/` for comprehensive guides
2. **Validate Structure**: Run `./scripts/validation/verify-structure.sh`
3. **Check Quality**: Run `npm run lint`and`npm run validate`
4. **Review Examples**: Check `examples/` for working configurations

## Escalation Path

1. Review this troubleshooting guide
2. Check existing documentation in `docs/`
3. Validate repository structure
4. Create issue with detailed error information
