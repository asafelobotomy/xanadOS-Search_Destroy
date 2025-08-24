# SBOM and Dependency Hygiene Runbook

Keep dependencies safe, licensed, and reproducible.

## Goals

- Generate an SBOM (CycloneDX/SPDX) for transparency.
- Track licenses and security advisories.
- Pin and update dependencies safely.

## Generate SBOM (options)

- Node (CycloneDX): use the CycloneDX npm tool or CI action to emit `bom.json`.
- Container images: `syft packages path/to/image -o cyclonedx-json`.
- Java: Maven/Gradle plugins for CycloneDX.

## Security scanning

- Use `npm audit` (baseline) and a dedicated scanner in CI for depth.
- Fail builds on high/critical issues; document temporary ignores with expiry.

## License compliance

- Collect licenses from SBOM; define allowed/denied policies.
- Flag unknown or copyleft licenses for legal review.

## Update strategy

- Dependabot/Renovate: scheduled, batched PRs with tests.
- Semantic versioning: prefer caret pins for libs, exact pins for apps when reproducibility matters.
- Avoid abandoned packages; prefer maintained forks or stdlib.

## Attestations and provenance

- Produce build provenance (SLSA) in CI where supported.
- Sign artifacts and container images.

## Records and audits

- Store SBOMs as build artifacts; keep a 6–12 month history.
- Review trends in vulnerabilities and updates during security reviews.
