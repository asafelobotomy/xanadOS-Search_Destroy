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

```text

2. **Test the build locally:**

  ```bash
  ./scripts/test-flatpak-build.sh
```text

3. **Submit to Flathub following the steps below.**

## Detailed Submission Process

### Step 1: Verify Local Build

Before submitting, ensure your Flatpak builds correctly:

```bash

## Test the build

./scripts/test-flatpak-build.sh

## Run the application

flatpak run io.GitHub.asafelobotomy.SearchAndDestroy

```text

### Step 2: Prepare Repository

1. Ensure all changes are committed and pushed:

  ```bash
  Git add .
  Git commit -m "feat: Prepare for Flathub submission"
  Git push origin master

```text

2. Create and push the release tag:

  ```bash
  Git tag -a v2.5.0 -m "Release version 2.5.0 for Flathub"
  Git push origin v2.5.0
```text

### Step 3: Fork and Clone Flathub Repository

1. Fork the Flathub repository: <HTTPS://GitHub.com/flathub/flathub>
2. Clone your fork:

  ```bash
  Git clone --branch=new-pr Git@GitHub.com:YOUR_USERNAME/flathub.Git
  cd flathub

```text

### Step 4: Create Submission Branch

```bash

Git checkout -b add-search-and-destroy new-pr

```text

### Step 5: Copy Required Files

Create the app directory and copy files:

```bash

mkdir io.GitHub.asafelobotomy.SearchAndDestroy
cd io.GitHub.asafelobotomy.SearchAndDestroy

## Copy the required files from your project

cp /path/to/your/project/packaging/flatpak/io.GitHub.asafelobotomy.SearchAndDestroy.yml .
cp /path/to/your/project/packaging/flatpak/io.GitHub.asafelobotomy.SearchAndDestroy.metainfo.XML .
cp /path/to/your/project/packaging/flatpak/io.GitHub.asafelobotomy.SearchAndDestroy.desktop .

```text

### Step 6: Update Manifest

Update the commit hash in the manifest:

```bash

## Get the actual commit hash from your repository

COMMIT_HASH=$(cd /path/to/your/project && Git rev-parse v2.5.0)

## Update the manifest

sed -i "s/commit: REPLACE_WITH_ACTUAL_COMMIT_HASH/commit: $COMMIT_HASH/" io.GitHub.asafelobotomy.SearchAndDestroy.yml

```text

### Step 7: Validate the Submission

```bash

## Lint the manifest

flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest io.GitHub.asafelobotomy.SearchAndDestroy.yml

## Test build in the Flathub environment

flatpak run --command=flathub-build org.flatpak.Builder io.GitHub.asafelobotomy.SearchAndDestroy.yml

```text

### Step 8: Submit Pull Request

1. Commit and push your changes:

  ```bash
  Git add .
  Git commit -m "Add io.GitHub.asafelobotomy.SearchAndDestroy"
  Git push origin add-search-and-destroy
```text

2. Open a pull request on GitHub:
- Base branch: `new-pr` (NOT master!)
- Title: "Add `io.GitHub.asafelobotomy.SearchAndDestroy`"
- Include a description of your application

## Required Files Checklist

- [x] `io.GitHub.asafelobotomy.SearchAndDestroy.yml` - Main Flatpak manifest
- [x] `io.GitHub.asafelobotomy.SearchAndDestroy.metainfo.XML` - AppStream metadata
- [x] `io.GitHub.asafelobotomy.SearchAndDestroy.desktop` - Desktop entry file

## Review Process

1. **Automated checks**: The Flathub bot will run automated validation
2. **Manual review**: Flathub maintainers will review your submission
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, your app will be built and published

## Common Issues and Solutions

### Build Failures

- **Missing dependencies**: Ensure all Python packages are included in `python3-requirements.JSON`
- **Network access**: Remember that builds have no network access
- **Permissions**: Use minimal required permissions in `finish-args`

### Metadata Issues

- **Invalid AppStream**: Validate your metainfo.XML file
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

- [Flathub Documentation](HTTPS://docs.flathub.org/)
- [Flatpak Builder Reference](HTTPS://docs.flatpak.org/en/latest/flatpak-builder.HTML)
- [AppStream Metainfo Guidelines](HTTPS://www.freedesktop.org/software/appstream/docs/chap-Metadata.HTML)
- [Flathub Matrix Room](HTTPS://matrix.to/#/#flathub:matrix.org)

## Support

If you encounter issues during submission:

1. Check the [Flathub documentation](HTTPS://docs.flathub.org/)
2. Search existing issues in the [Flathub repository](HTTPS://GitHub.com/flathub/flathub/issues)
3. Ask in the [Flathub Matrix room](HTTPS://matrix.to/#/#flathub:matrix.org)
4. Open an issue in the Flathub repository

Good luck with your submission! 🚀
