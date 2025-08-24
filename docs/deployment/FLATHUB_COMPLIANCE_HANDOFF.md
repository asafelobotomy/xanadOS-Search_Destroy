# Flathub Compliance Handoff

This document summarizes the repository-wide Flathub compliance effort.
It captures recent operations, tool results, the current working state,
and a concrete continuation plan.

## Overview

Goal:

- Ensure the application is fully compliant with Flathub submission requirements
- Align packaging and metadata
- Make runtime behavior Flatpak-safe
- Organize the repository
- Archive deprecations

Scope covered:

- Flatpak manifest, AppStream metadata, desktop entry, icons, scripts
- Runtime behavior adjustments for Flatpak (ClamAV integration)
- Repository organization and legacy assets
- Basic tests and lint hygiene for changed assets

## Requirements Checklist

- Repo-wide Flathub compliance review: Done
- Organize repo, archive deprecations: Done (legacy icon naming archived/documented)
- Align App ID and names across manifest/desktop/metainfo/icons: Done (io.github.asafelobotomy.SearchAndDestroy)
- Tighten permissions/finish-args and prefer portals: Done
- Flatpak-aware runtime behavior (no daemons/system paths; avoid freshclam): Done
- Dependency alignment between code and Flatpak manifest: Pending (see Risks)
- AppStream validation with lint tools: Pending
- Documentation cleanup for IDs and install guidance: Pending
- UX validation under portal-only file access: Pending

## Chronology (Recent to Older)

### Finalization and sanitation

- Fixed YAML indentation in manifest build-commands
- Resolved markdown lint issues (headings, escaped asterisks, link formatting)

### Packaging and metadata alignment

- Manifest: runtime/sdk set to org.kde.Platform 6.7 / org.kde.Sdk 6.7; PyQt BaseApp 6.7
- Finish-args: limited to ipc, wayland, fallback-x11, notifications, network
- Desktop: Name set to "Search and Destroy"; removed MimeType
- AppStream: added developer tag, unified licenses, ensured launchable and OARS present;
  Name set to "Search and Destroy"

### Code changes (Flatpak awareness)

- ClamAV wrapper: prefer /app/share/clamav; avoid clamd; skip freshclam updates;
  use --database for info commands when applicable

### Repository organization

- Scripts updated to `io.github.*` identifiers; packaging README added
- Legacy icon naming archived with README and notes
- Tests referencing icon filenames updated

## Technical Inventory

- App ID: `io.github.asafelobotomy.SearchAndDestroy`
- Runtime/SDK: org.kde.Platform 6.7 / org.kde.Sdk 6.7; BaseApp: com.riverbankcomputing.PyQt.BaseApp 6.7
- Packaging files:
  - `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.yml`
  - `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.metainfo.xml`
  - `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.desktop`
  - `packaging/flatpak/search-and-destroy.sh`
- Key modules touching Flatpak behavior: `app/core/clamav_wrapper.py`
- Icons: `io.github.*` naming; legacy `org.xanados.*` references archived

## Code and Packaging Changes (Highlights)

- Manifest: tightened finish-args; corrected file installs and IDs; fixed YAML; aligned names;
  removed aiohttp from pip section (pending dependency reconciliation)
- AppStream: added developer tag; unified licenses (kept metadata_license); naming consistent
- Desktop: Name aligned to app; removed unneeded MimeType
- ClamAV wrapper: Flatpak-aware database resolution; skip daemon and freshclam inside sandbox
- Scripts/Docs: updated to `io.github.*`; packaging README added; legacy icon docs added
- Tests: updated to new icon filenames

## Tool Results (In-Repo and In-Session)

- Packaging files located:
  - `packaging/flatpak/README.md`
  - `packaging/flatpak/search-and-destroy.sh`
  - `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.yml`
  - `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.metainfo.xml`
  - `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.desktop`

- Heavy/runtime-only dependencies imported in code (indicative; reconcile with manifest):
  - aiohttp (`app/core/web_protection.py`; `app/core/cloud_integration.py`;
    `app/core/automatic_updates.py`)
  - aiofiles (`app/core/cloud_integration.py`)
  - boto3 (`app/core/cloud_integration.py`)
  - numpy, pandas, matplotlib (`app/core/advanced_reporting.py`;
    `enhanced_real_time_protection.py`; `unified_security_engine.py`)

- Sanity checks: files edited validated locally; no syntax errors in changed
  Python/metadata were reported in-session.

## Current Status

- Packaging metadata and IDs are consistent and Flathub-style compliant
- Permissions are minimized; portals expected for file access
- Runtime behavior respects Flatpak constraints (no clamd or system DB; freshclam skipped)
- Repository has archived deprecations and updated helper scripts
- Gaps remain for dependency alignment and AppStream linting

## Risks and Pending Items

### Dependency alignment

- Code imports numpy, pandas, matplotlib, boto3, aiofiles, aiohttp (and their
  transitives), but the manifest currently installs only a subset.
  Options:
  - Add full offline sources (wheels or sdist + build-from-source) for all
    required packages and transitives
  - Or gate/disable features relying on them in Flatpak builds and remove those
    imports from the shipped app path

### ClamAV database provisioning

- Decide whether to bundle DBs under `/app/share/clamav` or start empty and
  communicate update strategy (via app updates)

### AppStream validation

- Run AppStream linter and ensure zero errors/warnings; verify screenshots and
  release entries

### Documentation updates

- Update docs/releases/user install instructions to reference `io.github.*` and
  Flatpak expectations

### UX validation

- Confirm portal-based scanning flows are acceptable without static filesystem
  permissions

## Quality Gates Snapshot

- Build: Not executed in-session for Flatpak bundle
- Lint/Typecheck: Metadata/markdown issues addressed; no current static analysis
  failures reported for changed files
- Unit tests: Packaging-related tests updated; full test run not executed here

## Continuation Plan

Short-term (prior to Flathub submission):

- Reconcile dependencies: either add complete offline dependencies to the
  manifest or gate features and remove imports from the Flatpak package path
- Decide and implement ClamAV DB strategy (bundle or empty + guidance)
- Run AppStream lint and Flatpak validation; correct any findings
- Update user/developer docs for `io.github.*` ID and Flatpak specifics

Optional refinements:

- Smoke test the Flatpak on Wayland and X11 fallback
- UX pass on file chooser portal flows for common scanning tasks

## Appendix: Key Files and Purposes

- `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.yml` — Flatpak build
  manifest
- `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.metainfo.xml` —
  AppStream metadata
- `packaging/flatpak/io.github.asafelobotomy.SearchAndDestroy.desktop` — Desktop
  launcher
- packaging/flatpak/search-and-destroy.sh — Runtime launcher script
- app/core/clamav_wrapper.py — ClamAV integration with Flatpak-aware logic
- archive/legacy-icons/README.md — Documentation for archived org.xanados.* icons
