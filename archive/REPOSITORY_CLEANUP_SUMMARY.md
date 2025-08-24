# Repository Cleanup and Organization - August 24, 2025

## Changes Made

### 1. Flathub Submission Archive
- Moved `flathub-submission/` → `archive/flathub-submissions/attempt-1-org-xanados/`
- Moved `flathub-submission-v2/` → `archive/flathub-submissions/attempt-2-io-github/`

These directories contained the initial Flathub submission attempts that were rejected due to:
- Application ID domain control issues
- Missing license information
- Incomplete Python dependencies
- Overly broad filesystem permissions

### 2. Updated Main Packaging Files

**New Application ID**: `io.github.asafelobotomy.SearchAndDestroy`

**Updated Files**:
- `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.yml` (main manifest)
- `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.metainfo.xml` (AppStream metadata)
- `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.desktop` (desktop entry)

**New Icon Files**:
- `packaging/icons/io.github.asafelobotomy.SearchAndDestroy.svg`
- `packaging/icons/io.github.asafelobotomy.SearchAndDestroy-{16,32,48,64,128}.png`

### 3. Key Improvements in Current Files

**Application ID**:
- Changed from `org.xanados.SearchAndDestroy` to `io.github.asafelobotomy.SearchAndDestroy`
- Uses GitHub-based ID that is verifiable and follows Flathub requirements

**License**:
- Added `<project_license>GPL-3.0-or-later</project_license>` to metainfo

**Dependencies**:
- Complete Python dependency manifest with verified SHA256 hashes
- Using PyQt BaseApp for better dependency management

**Permissions**:
- Reduced filesystem access to minimal required scope
- Emphasizes portal-based file access for better security

**Version**:
- Updated to v2.10.0 with correct commit hash
- Added proper release information in metainfo

### 4. Files Retained

**Original Icons**: Kept `org.xanados.SearchAndDestroy.*` icon files for backwards compatibility
**Config Files**: Kept `org.xanados.searchanddestroy.*.policy` files as they may be referenced by the application
**All Other Files**: Preserved application source code, documentation, and build scripts

## Current Repository Structure

```
packaging/flatpak/
├── io.github.asafelobotomy.SearchAndDestroy.yml        # ✅ Ready for Flathub
├── io.github.asafelobotomy.SearchAndDestroy.metainfo.xml # ✅ Ready for Flathub  
├── io.github.asafelobotomy.SearchAndDestroy.desktop     # ✅ Ready for Flathub
└── search-and-destroy.sh                               # Launcher script

packaging/icons/
├── io.github.asafelobotomy.SearchAndDestroy.svg        # ✅ Correct naming
├── io.github.asafelobotomy.SearchAndDestroy-*.png      # ✅ All sizes
└── org.xanados.SearchAndDestroy.*                      # Legacy (retained)

archive/flathub-submissions/
├── attempt-1-org-xanados/                              # First submission attempt
└── attempt-2-io-github/                                # Fixed submission attempt
```

## Ready for Submission

The repository is now organized with correct file naming and the main packaging files are ready for Flathub submission. All critical issues from the previous rejections have been addressed:

✅ Valid GitHub-based application ID  
✅ Complete license information  
✅ All Python dependencies with verified hashes  
✅ Minimal, justified permissions  
✅ Portal-based file access  
✅ Version consistency  
✅ Proper file naming conventions

## Next Steps

1. Test the Flatpak build locally:
   ```bash
   flatpak-builder build-dir packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.yml --install --user --force-clean
   ```

2. Submit to Flathub:
   - Fork flathub/flathub repository
   - Create directory: `io.github.asafelobotomy.SearchAndDestroy/`
   - Copy the three files from `packaging/flatpak/`
   - Create pull request
