# Flathub Submission for S&D - Search & Destroy

## Fixed Issues from Previous Submission

Based on the review feedback from PR #6808, the following issues have been addressed:

### 1. Repository Layout ✅

- Files are now properly organized in the `org.xanados.SearchAndDestroy/` directory
- Correct file naming and structure for Flathub requirements

### 2. Runtime Version ✅

- Updated from `23.08`to`24.08` as requested by reviewer @bbhtt

### 3. Python Dependencies ✅

- Switched to using `com.riverbankcomputing.PyQt.BaseApp` base app
- Simplified dependency management as suggested

### 4. File Access Permissions ✅

- Added proper portal permissions for file access
- Maintained necessary filesystem access for antivirus scanning
- Added portal-based file chooser support

### 5. Screenshot URLs ✅

- Updated to use specific tag `v2.10.0` instead of master branch

### 6. Removed flathub.JSON ✅

- Removed as requested by reviewer

### 7. Updated Dependencies ✅

- Updated to latest version tag `v2.10.0`
- Corrected commit hash

## Files for Submission

The following files should be submitted to the Flathub repository:

```text
org.xanados.SearchAndDestroy/
├── org.xanados.SearchAndDestroy.yml        # Main manifest
├── org.xanados.SearchAndDestroy.metainfo.XML  # AppStream metadata
└── org.xanados.SearchAndDestroy.desktop     # Desktop entry
```

## Submission Process

1. Fork the flathub/flathub repository
2. Create a new branch: `add-search-and-destroy`
3. Add the files from the `org.xanados.SearchAndDestroy/` directory
4. Commit and create a pull request
5. Follow the submission template and confirm all requirements

## Key Changes Made

- **Runtime**: Updated to 24.08
- **Base App**: Using PyQt BaseApp for better dependency management
- **Portals**: Added proper portal support for file access
- **Version**: Updated to v2.10.0 with correct commit hash
- **Screenshots**: Fixed to use specific tag URLs
- **Structure**: Proper Flathub directory layout

## Testing

Before submission, you can test the build locally:

```bash
flatpak-builder build-dir org.xanados.SearchAndDestroy.yml --install --user --force-clean
```
