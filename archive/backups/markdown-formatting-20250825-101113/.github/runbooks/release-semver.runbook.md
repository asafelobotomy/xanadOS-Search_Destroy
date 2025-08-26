# Runbook: Releases with SemVer and Changelog

Automate versioning and changelogs using conventional commits.
Use with Copilot agent mode.

## Prerequisites

- Conventional commits in use or planned

## Steps

1. Choose a release tool (release-please or semantic-release).
2. Configure version bump rules (feat = minor, fix = patch, breaking = major).
3. Generate changelog and GitHub release on merge to main.
4. Optionally publish artifacts or packages.

## Prompts

- "Set up release-please for this repo with GitHub Actions."
- "Configure conventional commit rules and PR labels."
- "Create a release workflow that updates CHANGELOG.md and tags versions."

## Success criteria

- Automated PR suggests next version and changelog
- Merge triggers tag and GitHub release
