# File Organization and Directory Structure Policy

## Copilot usage quick cues

- Ask: correct location for a new file or category; request a brief placement rationale.
- Edit: fix misplacements and update indexes; ask for minimal diffs only.
- Agent: multi-folder moves and archival; require a compliance checklist and summary.

### Model routing

- Reasoning model: ambiguous placement, policy exceptions, reorg planning.
- Claude Sonnet class: review diffs for accidental moves or missing updates.
- Gemini Pro class: summarize large trees or cross-reference docs and code.
- Fast general model: quick moves and index touch-ups.

### Token economy tips

- Reference `archive/`and`docs/` policies instead of pasting long sections.
- Ask for a file move plan table: source → target → reason.

## 🎯 **Mandatory File Placement Rules**

All GitHub Copilot agents **MUST** follow these directory placement rules to maintain a clean,
organized repository structure. **NO FILES** should be created in the root directory unless
explicitly specified in this policy.

## 📁 **Directory Structure and File Placement**

### **Root Directory - RESTRICTED**

### Only these files are allowed in the root directory

````Markdown
/
├── README.md                    # Main project documentation
├── CONTRIBUTING.md              # Contribution guidelines
├── .gitignore                   # Git ignore patterns
├── .editorconfig               # Cross-platform editor settings
├── .prettierrc                 # Code formatting configuration
├── .markdownlint.JSON          # Markdown linting rules
├── .prettierignore             # Prettier exclusion patterns
├── package.JSON                # Node.js dependencies (if needed)
├── package-lock.JSON           # Locked dependency versions
└── .gitattributes              # Git file handling rules

```Markdown

### **Documentation Files → `/docs/`**

| File Type | Destination | Example |
|-----------|-------------|---------|
| Implementation reports | `docs/implementation-reports/`|`MISSION-ACCOMPLISHED.md` |
| User guides | `docs/guides/`|`PROJECT_STRUCTURE.md` |
| Analysis documents | `docs/analysis/`|`architecture-analysis.md` |
| Project overview | `docs/README.md` | Main documentation index |

### **Scripts and Automation → `/scripts/`**

| File Type | Destination | Example |
|-----------|-------------|---------|
| Shell scripts | `scripts/`|`validate-policies.sh` |
| Build scripts | `scripts/build/`|`deploy.sh` |
| Utility scripts | `scripts/utils/`|`cleanup.sh` |
| CI/CD scripts | `ci/`or`.GitHub/workflows/`|`ci-pipeline.yml` |

### **Configuration Files → Appropriate Directories**

| File Type | Destination | Example |
|-----------|-------------|---------|
| GitHub configurations | `.GitHub/`|`Copilot-instructions.md` |
| Copilot instructions | `.GitHub/instructions/`|`code-quality.instructions.md` |
| Chat modes | `.GitHub/chatmodes/`|`expert-developer.chatmode.md` |
| Prompts | `.GitHub/prompts/`|`code-review.prompt.md` |
| VS Code settings | `.VS Code/`|`settings.JSON` |
| Docker configs | `Docker/`or root |`Dockerfile` |

### **Archive Content → `/archive/`**

| File Type | Destination | Example |
|-----------|-------------|---------|
| Deprecated files | `archive/deprecated/`|`old-implementation.md` |
| Legacy versions | `archive/legacy-versions/`|`v1-backup/` |
| Superseded content | `archive/superseded/`|`replaced-by-v2.md` |

### **Examples and Samples → `/examples/`**

| File Type | Destination | Example |
|-----------|-------------|---------|
| Code samples | `examples/`|`sample-implementation.js` |
| Configuration examples | `examples/configs/`|`example.prettierrc` |
| Template files | `examples/templates/`|`chatmode-template.md` |

## 🚫 **PROHIBITED: Root Directory Clutter**

### These file types MUST NOT be created in the root directory

- ❌ Implementation reports (`IMPLEMENTATION_*`)
- ❌ Mission summaries (`MISSION_*`)
- ❌ Organization documents (`ORGANIZATION_*`)
- ❌ Project structure files (`PROJECT_*`)
- ❌ Analysis documents (`ANALYSIS_*`)
- ❌ Temporary files (`temp**`, `tmp**`)
- ❌ Log files (`*.log`)
- ❌ Backup files (`_.backup`, `_.bak`)

## 📝 **Agent Compliance Requirements**

### **Before Creating Any File:**

1. **Identify file purpose** (documentation, script, config, etc.)
2. **Check directory placement rules** in this policy
3. **Use appropriate destination directory**
4. **Create necessary parent directories** if they don't exist
5. **Never default to root directory**

### **File Naming Conventions:**

- **Documentation**: `kebab-case.md`in appropriate`/docs/` subdirectory
- **Scripts**: `kebab-case.sh`in`/scripts/` directory
- **Configurations**: Standard config names (`.prettierrc`, `tsconfig.JSON`) in appropriate locations
- **Implementation Reports**: `feature-implementation.md`in`docs/implementation-reports/`

### **Validation Commands:**

```bash

## Check for root directory clutter

ls -la | grep -E "\.(md|txt|log|tmp|backup)$" | grep -v "README.md\|CONTRIBUTING.md"

## Validate directory structure

./scripts/validate-policies.sh

```Markdown

## 🛠️ **Cleanup and Migration**

### **Immediate Actions Required:**

```bash

## Move misplaced documentation

mv *.md docs/implementation-reports/ 2>/dev/null || true
mv PROJECT_*.md docs/guides/ 2>/dev/null || true

## Remove duplicate configurations

rm -f .prettierrc.JSON .eslintrc.duplicate

## Validate final structure

./scripts/validate-policies.sh

```Markdown

### **VS Code Integration:**

Add to `.VS Code/settings.JSON`:

```JSON
{
  "files.defaultLanguage": "Markdown",
  "explorer.sortOrder": "type",
  "files.exclude": {
    "**/node_modules": true,
    "**/.Git": true,
    "**/TEMP_*": true,
    "**/TMP_*": true
  }
}

```Markdown

## 🎯 **Enforcement Policy**

### **Mandatory for All Agents:**

- **Pre-file Creation Check**: Always determine proper directory before creating files
- **Root Directory Protection**: Keep root clean and organized
- **Validation Requirement**: Run validation after file operations
- **Directory Structure Respect**: Follow established organizational patterns

### **Quality Gates:**

- ✅ All documentation in `/docs/` subdirectories
- ✅ All scripts in `/scripts/` directory
- ✅ All configurations in proper locations
- ✅ Root directory contains only essential project files
- ✅ No temporary or implementation files in root

## 📊 **Success Metrics**

- **Root Directory Count**: Maximum 10 essential files
- **Documentation Organization**: 100% in `/docs/` structure
- **Script Organization**: 100% in `/scripts/` directory
- **Configuration Placement**: 100% compliance with standards
- **Zero Clutter**: No temporary or misplaced files in root

---

**This policy is MANDATORY for all GitHub Copilot agents working on this
repository to maintain professional organization and prevent directory
clutter.**
````
