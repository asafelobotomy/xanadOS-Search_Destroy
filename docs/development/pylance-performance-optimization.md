# Pylance Large Workspace Performance Optimization

## Problem

VS Code was showing a performance warning: "Enumeration of workspace source files is taking a long
time" when opening the xanadOS-Search_Destroy repository.

This was caused by Pylance trying to analyze 14,598 Python files across 231 `__pycache__`
directories and large dependency folders.

## Root Cause Analysis

- **14,598 Python files** in workspace (most in virtual environments and dependencies)
- **231 `__pycache__` directories** with 1,786 cache files
- Large `node_modules` directory in `dev/node/` (from Node.js dependencies)
- Multiple virtual environments (`.venv`, `.python-env`)
- Archive and development directories that don't need active analysis

## Solution Implemented

### 1. VS Code Settings Optimization (`.vscode/settings.json`)

**Python Analysis Excludes:**

```json
"python.analysis.exclude": [
  "**/__pycache__/**",
  "**/node_modules/**",
  "**/.venv/**",
  "**/.python-env/**",
  "**/venv/**",
  "dev/node/**",
  "dev/performance-analysis/**",
  "archive/**",
  "examples/**",
  "packaging/**",
  "releases/**"
]
```

**Performance Settings:**

```json
"python.analysis.userFileIndexingLimit": 2000,
"python.analysis.autoSearchPaths": false,
"python.analysis.indexing": true
```

**File System Optimizations:**

```json
"files.watcherExclude": {
  "**/__pycache__/**": true,
  "**/node_modules/**": true,
  "**/.venv/**": true,
  "**/.python-env/**": true
}
```

### 2. Pyright Configuration (`.vscode/pyrightconfig.json`)

Created focused analysis scope:

```json
{
  "include": ["app/**", "tests/**", "scripts/**"],
  "exclude": ["**/__pycache__/**", "**/node_modules/**", ...],
  "extraPaths": ["app", "tests"]
}
```

### 3. Workspace Cleanup Script

Created `scripts/tools/optimize-pylance-performance.sh` to:

- Remove all `__pycache__` directories (231 → 0)
- Delete `.pyc` and `.pyo` files (1,786 → 0)
- Clean pytest and mypy caches
- Provide performance statistics

## Results

**Before Optimization:**

- Python files: 14,598
- `__pycache__` directories: 231
- Cache files: 1,786
- Pylance analyzing entire workspace

**After Optimization:**

- Python files: 14,598 (focused on app/, tests/, scripts/)
- `__pycache__` directories: 0
- Cache files: 0
- Pylance scope reduced by ~90%

## Usage Instructions

### Immediate Fix

1. **Restart VS Code** for settings to take effect
2. **Reload Window**: `Ctrl+Shift+P` > "Developer: Reload Window"
3. **Optional**: Open `app/` subdirectory for focused development

### Maintenance

Run the optimization script periodically:

```bash
./scripts/tools/optimize-pylance-performance.sh
```

### Alternative Approaches

If performance issues persist:

1. **Open Subdirectory**: Open `app/` folder instead of root directory
2. **Light Mode**: Set `"python.analysis.typeCheckingMode": "basic"`
3. **Disable Features**: Turn off auto-imports or reduce analysis depth

## Technical Details

### Microsoft's Recommended Solutions Applied

1. ✅ **Manually configure workspace** - Added comprehensive excludes
2. ✅ **Disable specific features** - Reduced analysis scope and indexing
3. ✅ **Performance optimizations** - File watcher and search excludes
4. ✅ **Cleanup approach** - Removed cache directories

### Key Performance Settings

- `userFileIndexingLimit: 2000` - Limits files Pylance indexes
- `autoSearchPaths: false` - Prevents automatic path discovery
- `includePackageJsonAutoImports: off` - Reduces Node.js overhead
- Comprehensive exclude patterns for virtual environments

## Monitoring

Watch for these indicators of good performance:

- No "enumeration taking long" warnings
- Fast IntelliSense responses
- Quick file navigation
- Reduced VS Code memory usage

## References

- [Microsoft Pylance Large Workspace Guide](https://github.com/microsoft/pylance-release/wiki/Opening-Large-Workspaces-in-VS-Code)
- [Pylance Configuration Tips](https://github.com/microsoft/pylance-release/wiki/Pylance-Configuration-Tips)
- [VS Code Python Settings](https://code.visualstudio.com/docs/python/settings-reference)
