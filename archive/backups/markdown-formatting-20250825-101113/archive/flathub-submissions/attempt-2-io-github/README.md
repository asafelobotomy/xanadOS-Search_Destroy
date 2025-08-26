# Flathub Submission v2 for S&D - Search & Destroy

## Critical Issues Fixed

Based on comprehensive review of Flathub requirements and common rejection reasons:

### ✅ **Fixed Critical Issues:**

1. **Application ID Domain Control**
- Changed from `org.xanados.SearchAndDestroy`to`io.GitHub.asafelobotomy.SearchAndDestroy`
- Uses GitHub-based ID which is verifiable and follows Flathub requirements
2. **Missing License Information**
- Added `<project_license>GPL-3.0-or-later</project_license>` to metainfo.XML
3. **Complete Python Dependencies**
- Added all missing Python packages with valid SHA256 hashes
- Includes: pyclamd, requests, Python-dotenv, psutil, schedule, aiohttp, dnspython, Markdown
4. **Reduced Filesystem Permissions**
- Removed overly broad `--filesystem=home:ro` permission
- Limited to specific XDG directories for better security
- Emphasizes portal-based file access
5. **Updated Version Information**
- Added v2.10.0 release information in metainfo
- Matches the version being built from the repository
6. **Added Content Rating**
- Added OARS content rating as required for software store listings
7. **Corrected File Names**
- All files now use the correct `io.GitHub.asafelobotomy.SearchAndDestroy` naming convention

### ✅ **Previously Fixed Issues (from first review):**

- Runtime version updated to 24.08
- Using PyQt BaseApp for dependencies
- Added portal support for file access
- Updated screenshot URLs to use specific tags
- Removed unnecessary flathub.JSON file
- Proper repository structure

## Submission Files

```text
io.GitHub.asafelobotomy.SearchAndDestroy/
├── io.GitHub.asafelobotomy.SearchAndDestroy.yml        # Main manifest
├── io.GitHub.asafelobotomy.SearchAndDestroy.metainfo.XML  # AppStream metadata
└── io.GitHub.asafelobotomy.SearchAndDestroy.desktop     # Desktop entry
```

## Validation Checks Passed

- ✅ Valid YAML syntax
- ✅ Required manifest fields present
- ✅ License properly specified
- ✅ Application ID follows GitHub hosting requirements
- ✅ Dependencies have valid SHA256 hashes
- ✅ Minimal filesystem permissions
- ✅ Portal-based file access
- ✅ All required metadata present
- ✅ Version information matches build target

## Common Rejection Reasons Addressed

1. **Domain Control Issues** → Fixed with GitHub-based ID
2. **Missing License** → Added GPL-3.0-or-later license
3. **Overly Broad Permissions** → Reduced to minimal required permissions
4. **Missing Dependencies** → All Python packages included with hashes
5. **Version Mismatches** → MetaInfo updated to match v2.10.0
6. **Poor Security Practices** → Portal-first approach implemented

## Next Steps

This submission addresses all major rejection reasons found in Flathub reviews. The application:

- Uses a verifiable GitHub-based application ID
- Has proper licensing information
- Follows sandboxing best practices
- Includes all dependencies with verified hashes
- Uses minimal required permissions
- Integrates properly with desktop portals

Ready for resubmission to Flathub.
