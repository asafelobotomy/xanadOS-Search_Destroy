# Repository Organization Quick Reference

## 🚀 Quick Commands

```bash

## Check if repository is organized

python3 scripts/check-organization.py

## Fix organization issues

python3 dev/organize_repository_comprehensive.py

## Install Git hooks (one-time setup)

bash scripts/install-hooks.sh
```

## 📁 File Placement Rules

| What? | Where? |
|-------|--------|
| Application code | `app/` |
| Test scripts | `dev/` |
| Documentation | `docs/` |
| Configuration | `config/` |
| Build scripts | `scripts/` |
| Packaging | `packaging/` |

## 🛠️ Adding New Files

1. **Place in correct directory** (see rules above)
2. **Use proper naming**: `snake_case.py`, `SCREAMING_SNAKE_CASE.md`
3. **Add `**init**.py`** for new Python packages
4. **Update documentation** if needed

## ⚡ Git Hook Protection

- **Pre-commit hook** checks organization automatically
- **Commit blocked** if organization issues found
- **Fix with**: `python3 dev/organize_repository_comprehensive.py`

## 📋 Directory Structure

```text
xanadOS-Search_Destroy/
├── app/           # Application code
├── config/        # Configuration
├── dev/           # Development tools
├── docs/          # Documentation
├── packaging/     # Distribution
├── scripts/       # Build scripts
└── tests/         # Unit tests
```

## 🔍 Organization Check Results

### ✅ Good Organization

```text
✅ Repository is properly organized
```

### ❌ Issues Found

```text
❌ Organization issues found:

- Misplaced file: test.py - Test files should be in dev/ or tests/
- Missing **init**.py in app/new_module

```

**Fix with**: `python3 dev/organize_repository_comprehensive.py`

---

💡 **Tip**: The Git hook will automatically prevent commits with organization issues!
