# Documentation Awareness Quick Reference

## 🚨 CRITICAL: Check Documentation Repository First

Before creating ANY documentation, always check:

```bash
ls /docs/                                    # See available documentation
cat /docs/README.md                          # Full documentation index
find /docs/guides/ -name "*.md"              # List all user guides
```

## 📚 Essential Documentation Available

### User Guides (`/docs/guides/`)

- `ENHANCEMENTS.md` - Framework overview and capabilities
- `PROJECT_STRUCTURE.md` - Repository organization guide
- `organization-custom-instructions.md` - Enterprise deployment
- `model-targeting-guide.md` - AI model targeting (GPT-5, Claude, Gemini)
- `MCP.md` - Model Context Protocol integration
- `INSTALL_LINKS.md` - VS Code extension installation

### Templates (`/.GitHub/`)

- `chatmodes/` - 11 specialized AI conversation modes
- `prompts/` - 7 professional prompt templates
- `instructions/` - 6+ advanced instruction sets

### Archive System (`/archive/`)

- `README.md` - Archive policy and management
- `ARCHIVE_INDEX.md` - Complete content inventory
- Organized by deprecated/, legacy-versions/, superseded/

## 🎯 Agent Guidelines

### DO

✅ Check `/docs/README.md` for existing documentation
✅ Use existing guides: `cat /docs/guides/[topic].md`
✅ Update existing documentation instead of creating new
✅ Follow established patterns for new documentation

### DON'T

❌ Recreate documentation that exists in `/docs/`
❌ Write custom guides without checking existing content
❌ Create duplicate README files or setup instructions
❌ Ignore the comprehensive documentation repository

## 🔍 Quick Discovery Commands

```bash

## Find existing documentation

find /docs/ -name "_keyword_"
grep -r "topic" /docs/

## Check template availability

ls .GitHub/chatmodes/ | grep keyword
ls .GitHub/prompts/ | grep topic

## Verify documentation repository

test -d /docs && echo "✅ Docs available" || echo "❌ Missing docs"
```

## 📋 Common Documentation Topics Covered

- ✅ Framework overview and features
- ✅ Project structure and organization
- ✅ Enterprise deployment and setup
- ✅ AI model targeting and integration
- ✅ VS Code extension installation
- ✅ MCP (Model Context Protocol) setup
- ✅ Chat modes and prompt templates
- ✅ Archive management and policies

## Always check existing documentation before creating new content
