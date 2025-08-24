# Script API

Reference for the toolshed scripts. Scripts are POSIX shell with Bash,
provide `--help`, and return non-zero on error.

## Core scripts

- `scripts/tools/validation/validate-structure.sh`
  - Purpose: repository structure and standards validation
  - Usage:
    - `./scripts/tools/validation/validate-structure.sh [--quick] [--json]`
    - Options:
      - `--output FILE`
      - `--no-fail`
      - `--category git|files|docs|security|cicd|quality`
  - Output: human-readable and optional JSON; logs under `logs/toolshed/`
  - Exit codes: 0 success; 1 validation failures (unless `--no-fail`)

- `scripts/tools/quality/check-quality.sh`
  - Purpose: markdown lint and optional auto-fix
  - Usage: `./scripts/tools/quality/check-quality.sh [--fix]`
  - Exit codes: 0 success; non-zero on lint errors (without `--fix`)

- `scripts/tools/containers/docker-manager.sh`
  - Purpose: helper for building, tagging, and scanning container images
  - Usage: `./scripts/tools/containers/docker-manager.sh [build|tag|push|scan] [options]`

- `scripts/tools/repository/backup-repository.sh`
  - Purpose: create timestamped archive of key project files
  - Usage: `./scripts/tools/repository/backup-repository.sh [--dest DIR]`

- `scripts/tools/security/security-scan.sh`
  - Purpose: run basic project security checks
  - Usage: `./scripts/tools/security/security-scan.sh`

## Conventions

- All scripts support `--help` for usage
- Non-destructive by default; destructive actions require explicit flags
- Logs written to `logs/toolshed/` where applicable

## See also

- `scripts/README.md` for directory map and usage notes
