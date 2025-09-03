# Quality Tools

Professional-grade tools for maintaining code quality, formatting, and standards compliance.

## 🛠️ Tools Overview

### `fix-python.sh` - Comprehensive Python Code Quality Fixer

**Version**: 1.0.0 - **✅ Complete Python quality suite for pylint/pylance issues**

A professional-grade Python code quality tool that addresses the 1000+ pylint/pylance problems in
the repository.

### 🚀 Python Tool Features

- **Import Organization**: Intelligent import sorting and optimization using isort
- **Code Formatting**: Multiple formatter support (black, autopep8, ruff)
- **Linting Fixes**: Common Python linting issue resolution
- **Strategy-Based**: Safe, aggressive, and targeted fix modes
- **Backup System**: Automatic backup creation before modifications
- **Tool Detection**: Auto-detects and installs missing Python tools
- **Pylance Integration**: Addresses PyQt6 import issues and dependency problems

#### 📋 Usage Examples

```bash
# Basic safe fixes for current directory
./fix-python.sh

# Comprehensive aggressive fixes (recommended for major cleanup)
./fix-python.sh --strategy aggressive

# Test what would be changed
./fix-python.sh --dry-run --strategy aggressive

# Fix specific directory with verbose output
./fix-python.sh --target app/ --verbose --strategy aggressive

# Import organization only
./fix-python.sh --strategy imports-only

# Code formatting only
./fix-python.sh --strategy format-only
```

#### 🎯 Fix Strategies

| Strategy         | Description                | Use Case                                       |
| ---------------- | -------------------------- | ---------------------------------------------- |
| **safe**         | Only safe formatting fixes | Default, minimal risk                          |
| **aggressive**   | All available fixes        | Major cleanup, addresses pylint/pylance issues |
| **imports-only** | Import organization only   | Import-related problems                        |
| **format-only**  | Code formatting only       | Style consistency                              |

#### 🔧 Tool Support

- **ruff** (preferred): Modern Python linter and formatter
- **black**: Code formatting with configurable line length
- **isort**: Import sorting and organization
- **autopep8**: PEP 8 compliance formatting
- **Auto-installation**: Missing tools installed automatically

#### 📋 Python Usage Examples

````bash

---

### `fix-markdown.sh` - Comprehensive Markdown Formatter

**Version**: 3.0.0 - **✅ Covers ALL 59 markdownlint rules (MD001-MD059)**

A professional-grade Markdown fixing tool with comprehensive coverage for all markdownlint violations.

### 🚀 Key Features

- **Complete Rule Coverage**: Handles all 59 markdownlint rules (MD001-MD059)
- **Multiple Fix Strategies**: Safe, aggressive, and custom modes
- **Advanced Pattern Fixing**: Python-based intelligent fixes
- **Backup System**: Automatic backup creation with rollback support
- **Validation**: Post-fix validation with detailed reporting
- **Configuration Support**: `.markdownlint.JSON` and ignore patterns

#### 🎯 Comprehensive Rule Coverage

| Category | Rules Covered | Description |
|----------|---------------|-------------|
| **Headings** | MD001, MD003, MD018-MD026, MD036, MD041, MD043 | Structure, spacing, style consistency |
| **Lists** | MD004, MD005, MD007, MD029, MD030, MD032 | Formatting, indentation, spacing |
| **Code Blocks** | MD014, MD031, MD038, MD040, MD046, MD048 | Language specs, spacing, style |
| **Whitespace** | MD009, MD010, MD012, MD027, MD028, MD030, MD037-MD039 | Trailing spaces, tabs, blank lines |
| **Links & Images** | MD011, MD034, MD039, MD042, MD045, MD051-MD054, MD059 | Syntax, alt text, validation |
| **Tables** | MD055, MD056, MD058 | Formatting, column consistency |
| **Text Styles** | MD037, MD044, MD049, MD050 | Emphasis, proper names |
| **File Structure** | MD047 | Trailing newlines |
| **HTML & Quotes** | MD027, MD028, MD033, MD035 | Blockquotes, HTML handling |

#### 📋 Usage Examples

```bash

## Basic safe fixes

./fix-markdown.sh

## Comprehensive aggressive fixes (recommended)

./fix-markdown.sh --strategy aggressive

## Test what would be changed

./fix-markdown.sh --dry-run --strategy aggressive

## Fix specific directory

./fix-markdown.sh --target docs/ --strategy aggressive

## Custom line length

./fix-markdown.sh --strategy aggressive --line-length 100

## Verbose output with custom config

./fix-markdown.sh --verbose --config .markdownlint-strict.JSON
````

### 🔧 Fix Strategies

1. **Safe**: Uses only `markdownlint --fix` for guaranteed safe changes
2. **Aggressive**: Applies all comprehensive fixes including advanced patterns
3. **Custom**: Combines safe fixes with custom sed patterns and advanced Python fixes

## Installation and Dependencies

### Required Dependencies

```bash

## Install markdownlint-cli

npm install -g markdownlint-cli

## Ensure Python 3.7+ is available

python3 --version

## Standard Unix tools (usually pre-installed)

## sed, awk, find

```

### Script Location

The tool is located at: `scripts/tools/quality/fix-markdown.sh`

Make sure it's executable:

```bash
chmod +x scripts/tools/quality/fix-markdown.sh
```

## Usage

### Basic Usage

```bash

## Fix all Markdown files in repository (safe mode)

./scripts/tools/quality/fix-markdown.sh

## Preview changes without applying them

./scripts/tools/quality/fix-markdown.sh --dry-run

## Verbose output with detailed progress

./scripts/tools/quality/fix-markdown.sh --verbose
```

### Advanced Usage

```bash

## Aggressive fixing with custom line length

./scripts/tools/quality/fix-markdown.sh --strategy aggressive --line-length 100

## Fix specific directory only

./scripts/tools/quality/fix-markdown.sh --target docs/

## Use custom configuration file

./scripts/tools/quality/fix-markdown.sh --config .markdownlint-docs.JSON

## Custom strategy with ignore patterns

./scripts/tools/quality/fix-markdown.sh \
    --strategy custom \
    --ignore "*.tmp.md" \
    --ignore "legacy/*" \
    --ignore "archive/*"
```

### Configuration Options

```bash

## Disable backup creation (not recommended)

./scripts/tools/quality/fix-markdown.sh --no-backup

## Skip post-fix validation

./scripts/tools/quality/fix-markdown.sh --no-validation

## Continue on errors (force mode)

./scripts/tools/quality/fix-markdown.sh --force
```

## Configuration Files

### markdownlint Configuration

The tool supports standard markdownlint configuration files:

#### .markdownlint.JSON (JSON format)

```JSON
{
    "default": true,
    "MD013": {
        "line_length": 120
    },
    "MD025": {
        "front_matter_title": ""
    },
    "MD026": false,
    "MD033": false
}
```

#### .markdownlint.YAML (YAML format)

```YAML
default: true
MD013:
  line_length: 120
MD025:
  front_matter_title: ""
MD026: false
MD033: false
```

### Ignore Patterns

#### .markdownlintignore

```gitignore
node_modules/
*.tmp.md
backup-*/
archive/
legacy/
CHANGELOG.md
```

#### Command-line Ignore Patterns

```bash
./scripts/tools/quality/fix-markdown.sh \
    --ignore "*.backup.md" \
    --ignore "temp/*" \
    --ignore "vendor/"
```

## Output and Logging

### Log Files

- **Main Log**: `./Markdown-fixes.log` - Detailed operation log
- **Backup Directory**: `./.Markdown-backups/` - Timestamped file backups

### Progress Output

```bash
[INFO] Starting Markdown processing...
[INFO] Target: /path/to/repository
[INFO] Strategy: aggressive
[INFO] Dry run: false
[INFO] Found 45 Markdown files to process
[SUCCESS] Safe fixes applied successfully
[SUCCESS] Advanced fixes applied successfully
[SUCCESS] Validation passed: No Markdown issues found
[SUCCESS] Markdown processing completed successfully
[INFO] Processed 45 files
[INFO] Backups stored in: ./.Markdown-backups
[INFO] Log file: ./Markdown-fixes.log
```

### Error Handling

```bash
[ERROR] Missing required dependencies: markdownlint-cli
[ERROR]   npm install -g markdownlint-cli
[WARNING] Validation found 3 remaining issues
[DEBUG] Running: markdownlint --fix --config .markdownlint.JSON file.md
```

## Integration with Existing Tools

### Supersedes Previous Scripts

This tool consolidates and replaces legacy scripts. The following have been archived under
`archive/deprecated/scripts/tools/`:

- `scripts/tools/fix-markdown-formatting.sh`
- `scripts/tools/fix-markdown-targeted.sh`
- `scripts/tools/fix-markdown-advanced.sh`
- `scripts/tools/fix-markdown-final.sh`

Use `scripts/tools/quality/fix-markdown.sh` for all Markdown fixes.

### GitHub Copilot Instructions Integration

The tool follows patterns established in:

- `.GitHub/instructions/code-quality.instructions.md`
- `.GitHub/instructions/agent-workflow.instructions.md`
- `.GitHub/instructions/toolshed-usage.instructions.md`

### Workflow Integration

```bash

## Pre-commit workflow

./scripts/tools/quality/fix-markdown.sh --strategy safe
Git add -A
Git commit -m "docs: fix Markdown formatting"

## CI/CD validation

./scripts/tools/quality/fix-markdown.sh --dry-run --strategy aggressive

## Release preparation

./scripts/tools/quality/fix-markdown.sh --strategy custom --verbose
```

## Troubleshooting

### Common Issues

#### Missing Dependencies

```bash

## Check dependencies

./scripts/tools/quality/fix-markdown.sh --version

## Install markdownlint-cli 2

npm install -g markdownlint-cli

## Verify Python 3

python3 --version
```

### Permission Issues

```bash

## Make script executable

chmod +x scripts/tools/quality/fix-markdown.sh

## Check file permissions

ls -la scripts/tools/quality/fix-markdown.sh
```

### Configuration Issues

```bash

## Test with default configuration

./scripts/tools/quality/fix-markdown.sh --no-config

## Validate configuration file

markdownlint --config .markdownlint.JSON --help
```

### Advanced Debugging

```bash

## Maximum verbosity

./scripts/tools/quality/fix-markdown.sh --verbose --dry-run

## Check log file for details

tail -f ./Markdown-fixes.log

## Test specific files

./scripts/tools/quality/fix-markdown.sh --target specific-file.md
```

## Best Practices

### Repository Integration

1. **Add to toolshed usage**: Reference in `.GitHub/instructions/toolshed-usage.instructions.md`
2. **Configure appropriately**: Set up `.markdownlint.JSON` for your project
3. **Set up ignore patterns**: Use `.markdownlintignore` for generated or legacy files
4. **Integrate with CI/CD**: Use dry-run mode for validation

### Strategy Selection

- **Safe**: For automated/unattended usage
- **Aggressive**: For manual cleanup and improvement
- **Custom**: For special formatting requirements

### Backup Management

- Backups are stored in `./.Markdown-backups/` with timestamps
- Clean up old backups periodically
- Test rollback procedures before major operations

## Advanced Features

### Python Pattern Fixes

The tool includes sophisticated Python-based fixes for:

- **Line length management**: Intelligent breaking at sentence boundaries
- **Emphasis heading conversion**: Convert `**Text**`to`## Text`
- **List indentation**: Consistent 2-space indentation
- **Spacing fixes**: Remove trailing spaces and normalize blank lines

### Custom Sed Patterns

Custom strategy includes sed-based fixes for:

- Trailing whitespace removal
- Multiple blank line compression
- List marker normalization
- Basic indentation fixes

### Validation Integration

Post-fix validation using markdownlint ensures:

- All fixes were applied correctly
- No new issues were introduced
- Remaining issues are reported
- JSON output for programmatic use

## API Reference

### Command Line Options

| Option              | Description                          | Default            |
| ------------------- | ------------------------------------ | ------------------ |
| `-h, --help`        | Show help message                    | -                  |
| `--version`         | Show version info                    | -                  |
| `-v, --verbose`     | Enable verbose output                | false              |
| `-n, --dry-run`     | Preview mode                         | false              |
| `-s, --strategy`    | Fix strategy: safe/aggressive/custom | safe               |
| `-c, --config`      | Custom config file                   | .markdownlint.JSON |
| `-i, --ignore`      | Ignore pattern (repeatable)          | []                 |
| `-t, --target`      | Target path                          | workspace root     |
| `-l, --line-length` | Maximum line length                  | 120                |
| `--no-backup`       | Disable backups                      | false              |
| `--no-validation`   | Skip validation                      | false              |
| `--force`           | Continue on errors                   | false              |

### Exit Codes

| Code | Meaning                 |
| ---- | ----------------------- |
| 0    | Success                 |
| 1    | General error           |
| 2    | Invalid arguments       |
| 3    | Missing dependencies    |
| 4    | No Markdown files found |

## Version History

### v2.0.0 (Current)

- Initial toolshed release
- Comprehensive strategy system
- Advanced Python pattern fixes
- Professional CLI interface
- Full backup and validation system
- Integration with markdownlint ecosystem

## Contributing

### Reporting Issues

File issues related to this tool in the repository issue tracker with:

- Tool version: `./scripts/tools/quality/fix-markdown.sh --version`
- Command used
- Expected vs actual behavior
- Log file contents if relevant

### Enhancements

Follow the toolshed contribution guidelines in:

- `CONTRIBUTING.md`
- `.GitHub/instructions/toolshed-usage.instructions.md`

---

_This documentation is part of the GitHub Copilot Agent Toolshed - Quality Tools collection._
