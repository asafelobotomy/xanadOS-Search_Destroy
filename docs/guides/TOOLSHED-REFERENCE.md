# GitHub Copilot Toolshed - Quick Reference

*Essential reference for GitHub Copilot agents to avoid recreating functionality*

## 🚨 **CRITICAL REMINDER: Always Check Toolshed First**

Before creating ANY script or automation, GitHub Copilot agents MUST check the existing toolshed in `scripts/tools/`.

## 📂 **Available Tools at a Glance**

### ⚡ **Most Used Tools**

| Tool | Purpose | Usage |
|------|---------|-------|
| `scripts/tools/git/setup-repository.sh` | Complete Git repository setup | `./scripts/tools/git/setup-repository.sh --help` |
| `scripts/tools/validation/validate-structure.sh` | Repository validation (97% compliance) | `./scripts/tools/validation/validate-structure.sh --quick` |
| `scripts/tools/quality/check-quality.sh` | Code quality with auto-fix | `./scripts/tools/quality/check-quality.sh --fix` |
| `scripts/tools/implement-toolshed.sh` | Deploy toolshed to new repos | `./scripts/tools/implement-toolshed.sh --help` |

### 🔧 **Tool Categories**

- **Git Tools**: `scripts/tools/git/` - Repository setup, workflows, automation
- **Validation Tools**: `scripts/tools/validation/` - Structure validation, compliance
- **Quality Tools**: `scripts/tools/quality/` - Code quality, formatting, standards
- **Repository Tools**: `scripts/tools/repository/` - Backup, organization, management
- **Documentation Tools**: `scripts/tools/documentation/` - Doc generation, maintenance

## 🚀 **Quick Commands**

```bash
# Check what tools are available
ls scripts/tools/
cat scripts/tools/README.md

# Get help for any tool
./scripts/tools/[category]/[tool-name].sh --help

# Most common workflows
./scripts/tools/git/setup-repository.sh              # Setup repo
./scripts/tools/validation/validate-structure.sh     # Validate
./scripts/tools/quality/check-quality.sh --fix       # Quality check
```

## ✅ **Agent Checklist**

Before creating scripts, always:

1. ✅ Check `scripts/tools/README.md`
2. ✅ Search for existing tools: `find scripts/tools/ -name "*keyword*"`
3. ✅ Test relevant tools with `--help`
4. ✅ Use existing tools instead of recreating
5. ✅ Extend existing tools rather than duplicating

## 📚 **Documentation**

- **Complete Catalog**: `scripts/tools/README.md`
- **Usage Instructions**: `.github/instructions/toolshed-usage.instructions.md`
- **Implementation Guide**: `.github/copilot-instructions.md`

---

**Remember: The toolshed prevents redundant work and ensures consistency!** 🛠️
