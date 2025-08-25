# Stable Branch Auto-Update Setup

## Overview

The S&D - Search & Destroy application now supports automatic updates from a dedicated `stable` branch.
This approach provides better control over release stability by separating development work from production updates.

## Branch Structure

- **`master` branch**: Development and experimental features
- **`stable` branch**: Thoroughly tested, production-ready releases only

## How It Works

### 1. Auto-Update Configuration

The auto-updater is configured via `/config/update_config.JSON`:

```JSON
{
    "update_branch": "stable",
    "repo_owner": "asafelobotomy",
    "repo_name": "xanadOS-Search_Destroy",
    "check_interval_hours": 24,
    "auto_download": false,
    "include_prereleases": false,
    "description": "Auto-update configuration for S&D - Search & Destroy application"
}
```

### 2. Release Process

1. **Development**: Work happens on `master` branch
2. **Testing**: Thoroughly test features on `master`
3. **Stable Release**: When ready, merge tested code to `stable` branch
4. **Tag Release**: Create a Git tag on the `stable` branch
5. **User Updates**: Users automatically receive updates from `stable` branch only

### 3. Auto-Updater Features

- **Smart Branch Detection**: Only fetches releases available on the stable branch
- **Prerelease Filtering**: Excludes prereleases by default for stability
- **Fallback Protection**: Falls back to latest release if no stable releases found
- **Configuration-Driven**: Easy to change update source via config file

## Usage Instructions

### For Developers

#### Creating a Stable Release

1. **Test thoroughly on master**:

  ```bash
  Git checkout master

## Test all functionality

  ```

2. **Merge to stable**:

  ```bash
  Git checkout stable
  Git merge master
  ```

3. **Create and push tag**:

  ```bash
  Git tag -a v2.7.2 -m "Release version 2.7.2"
  Git push origin stable
  Git push origin v2.7.2
  ```

4. **Create GitHub Release**:
- Go to GitHub repository
- Create new release from the `v2.7.2` tag
- Target the `stable` branch
- Add release notes

### Emergency Hotfix to Stable

```bash
Git checkout stable

## Make minimal fix

Git add .
Git commit -m "Hotfix: Critical security update"
Git tag -a v2.7.3 -m "Hotfix release 2.7.3"
Git push origin stable
Git push origin v2.7.3

## Create GitHub release

```

### For Users

#### Automatic Updates

- Updates check every 24 hours by default
- Only stable, tested releases are downloaded
- User can control update frequency in Settings > Updates

#### Manual Update Check

- **Help Menu**→**Check for Updates**
- Forces immediate check regardless of timer
- Shows current vs. available version

#### Update Configuration

Users can modify `/config/update_config.JSON` to:

- Change update branch (stable/master/custom)
- Enable/disable prereleases
- Adjust check frequency
- Switch to different repository fork

## Technical Implementation

### Core Components

1. **AutoUpdater Class** (`app/core/auto_updater.py`)
- Handles GitHub API communication
- Manages version comparison
- Downloads and applies updates
2. **Update Configuration** (`config/update_config.JSON`)
- Centralizes update settings
- Allows easy customization
- Supports multiple environments
3. **Branch Validation**
- Verifies releases exist on target branch
- Prevents downloading from wrong branch
- Maintains release integrity

### API Endpoints Used

- `GET /repos/{owner}/{repo}/releases` - List all releases
- `GET /repos/{owner}/{repo}/Git/refs/tags/{tag}` - Verify tag exists
- `GET /repos/{owner}/{repo}/commits?sha={branch}` - Get branch commits
- `GET /archive/refs/heads/{branch}.zip` - Download stable branch

### Security Features

- **SSL/TLS verification** for all downloads
- **SHA verification** of downloaded files (future enhancement)
- **User confirmation** before applying updates
- **Backup creation** before applying updates

## Benefits

### For Developers 2

- **Clean separation** of development and production
- **Better testing control** before stable releases
- **Reduced user complaints** from unstable features
- **Easier hotfix deployment** to stable only

### For Users 2

- **More reliable updates** from tested code only
- **Reduced crash risk** from experimental features
- **Predictable update schedule** and quality
- **Emergency hotfix support** without waiting for full releases

## Configuration Options

### Update Branch Options

- `"stable"` - Production releases only (recommended)
- `"master"` - Latest development (for testers)
- `"beta"` - Beta testing branch (if created)

### Safety Options

- `"include_prereleases": false` - Skip alpha/beta releases
- `"auto_download": false` - Require user confirmation
- `"check_interval_hours": 24` - Update check frequency

## Migration Notes

### Existing Installations

- Existing users automatically switch to stable branch updates
- No manual configuration required
- Settings preserved during update

### Repository Setup

- `stable` branch created and pushed
- Auto-updater updated to use stable branch
- Configuration file added for customization

## Future Enhancements

- **Digital signature verification** for updates
- **Delta updates** for smaller downloads
- **Rollback functionality** if update fails
- **Update scheduling** for specific times
- **Multiple update channels** (stable/beta/alpha)

## Troubleshooting

### No Updates Found

- Check internet connection
- Verify `stable` branch has tagged releases
- Check GitHub repository accessibility

### Update Download Fails

- Check disk space for temporary files
- Verify write permissions to app directory
- Check firewall/antivirus blocking downloads

### Configuration Issues

- Verify `config/update_config.JSON` syntax
- Check file permissions
- Restore from backup if corrupted

## Command Reference

```bash

## View current branch

Git branch

## Switch to stable

Git checkout stable

## View recent tags

Git tag -l --sort=-version:refname | head -5

## Check tag on branch

Git tag --merged stable

## Create release tag

Git tag -a v2.7.2 -m "Release 2.7.2"

## Push everything

Git push origin stable --tags
```

This setup provides a robust, configurable auto-update system that prioritizes stability while maintaining flexibility for different use cases and environments.
