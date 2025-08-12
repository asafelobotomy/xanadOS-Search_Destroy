# Flathub Submission Guide for S&D - Search & Destroy

This guide walks you through the process of submitting S&D - Search & Destroy to Flathub.

## Prerequisites

- [x] Application is stable and fully functional
- [x] All required metadata files are present
- [x] Icons are properly sized and formatted
- [x] License is compatible with Flathub (MIT ✅)
- [x] Application follows Flatpak sandboxing principles

## Quick Start

1. **Prepare the submission:**
   ```bash
   ./scripts/prepare-flathub.sh
   ```

2. **Test the build locally:**
   ```bash
   ./scripts/test-flatpak-build.sh
   ```

3. **Submit to Flathub following the steps below.**

## Detailed Submission Process

### Step 1: Verify Local Build

Before submitting, ensure your Flatpak builds correctly:

```bash
# Test the build
./scripts/test-flatpak-build.sh

# Run the application
flatpak run org.xanados.SearchAndDestroy
```

### Step 2: Prepare Repository

1. Ensure all changes are committed and pushed:
   ```bash
   git add .
   git commit -m "feat: Prepare for Flathub submission"
   git push origin master
   ```

2. Create and push the release tag:
   ```bash
   git tag -a v2.4.1 -m "Release version 2.4.1 for Flathub"
   git push origin v2.4.1
   ```

### Step 3: Fork and Clone Flathub Repository

1. Fork the Flathub repository: https://github.com/flathub/flathub
2. Clone your fork:
   ```bash
   git clone --branch=new-pr git@github.com:YOUR_USERNAME/flathub.git
   cd flathub
   ```

### Step 4: Create Submission Branch

```bash
git checkout -b add-search-and-destroy new-pr
```

### Step 5: Copy Required Files

Create the app directory and copy files:

```bash
mkdir org.xanados.SearchAndDestroy
cd org.xanados.SearchAndDestroy

# Copy the required files from your project
cp /path/to/your/project/packaging/flatpak/org.xanados.SearchAndDestroy.yml .
cp /path/to/your/project/packaging/flatpak/org.xanados.SearchAndDestroy.metainfo.xml .
cp /path/to/your/project/packaging/flatpak/org.xanados.SearchAndDestroy.desktop .
cp /path/to/your/project/packaging/flatpak/python3-requirements.json .
cp /path/to/your/project/packaging/flatpak/flathub.json .
```

### Step 6: Update Manifest

Update the commit hash in the manifest:

```bash
# Get the actual commit hash from your repository
COMMIT_HASH=$(cd /path/to/your/project && git rev-parse v2.4.1)

# Update the manifest
sed -i "s/commit: REPLACE_WITH_ACTUAL_COMMIT_HASH/commit: $COMMIT_HASH/" org.xanados.SearchAndDestroy.yml
```

### Step 7: Validate the Submission

```bash
# Lint the manifest
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest org.xanados.SearchAndDestroy.yml

# Test build in the Flathub environment
flatpak run --command=flathub-build org.flatpak.Builder org.xanados.SearchAndDestroy.yml
```

### Step 8: Submit Pull Request

1. Commit and push your changes:
   ```bash
   git add .
   git commit -m "Add org.xanados.SearchAndDestroy"
   git push origin add-search-and-destroy
   ```

2. Open a pull request on GitHub:
   - Base branch: `new-pr` (NOT master!)
   - Title: "Add org.xanados.SearchAndDestroy"
   - Include a description of your application

## Required Files Checklist

- [x] `org.xanados.SearchAndDestroy.yml` - Main Flatpak manifest
- [x] `org.xanados.SearchAndDestroy.metainfo.xml` - AppStream metadata
- [x] `org.xanados.SearchAndDestroy.desktop` - Desktop entry file
- [x] `python3-requirements.json` - Python dependencies manifest
- [x] `flathub.json` - Architecture configuration

## Review Process

1. **Automated checks**: The Flathub bot will run automated validation
2. **Manual review**: Flathub maintainers will review your submission
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, your app will be built and published

## Common Issues and Solutions

### Build Failures

- **Missing dependencies**: Ensure all Python packages are included in `python3-requirements.json`
- **Network access**: Remember that builds have no network access
- **Permissions**: Use minimal required permissions in `finish-args`

### Metadata Issues

- **Invalid AppStream**: Validate your metainfo.xml file
- **Missing icons**: Ensure all icon sizes are present
- **License mismatch**: Ensure license in metainfo matches your repository

### Submission Rejection

- **Insufficient functionality**: Ensure your app provides significant value
- **Poor user experience**: Test thoroughly before submission
- **Security concerns**: Review and minimize permissions

## Post-Submission

Once your app is approved and published:

1. Monitor for user feedback and bug reports
2. Keep your app updated with new releases
3. Respond to Flathub maintenance requests
4. Consider joining the Flathub community discussions

## Resources

- [Flathub Documentation](https://docs.flathub.org/)
- [Flatpak Builder Reference](https://docs.flatpak.org/en/latest/flatpak-builder.html)
- [AppStream Metainfo Guidelines](https://www.freedesktop.org/software/appstream/docs/chap-Metadata.html)
- [Flathub Matrix Room](https://matrix.to/#/#flathub:matrix.org)

## Support

If you encounter issues during submission:

1. Check the [Flathub documentation](https://docs.flathub.org/)
2. Search existing issues in the [Flathub repository](https://github.com/flathub/flathub/issues)
3. Ask in the [Flathub Matrix room](https://matrix.to/#/#flathub:matrix.org)
4. Open an issue in the Flathub repository

Good luck with your submission! 🚀
