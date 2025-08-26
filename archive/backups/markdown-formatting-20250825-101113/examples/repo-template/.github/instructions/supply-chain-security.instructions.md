---
applyTo: "**/*.{yml,YAML,JSON,toml,lock,Dockerfile,Containerfile,tf,hcl}"
---

# Supply Chain Security-specific Copilot Instructions

## Software Bill of Materials (SBOM) Management

- Generate SPDX or CycloneDX format SBOMs for all releases using tools like syft, cdxgen, or FOSSA
- Include direct and transitive dependencies with exact versions and license information
- Automate SBOM generation in CI/CD pipelines and attach to release artifacts
- Validate SBOM completeness and accuracy before production deployments
- Implement SBOM storage and retrieval systems for incident response and compliance
- Use VEX (Vulnerability Exploitability eXchange) documents to communicate vulnerability status
- Implement SBOM signing and verification to ensure authenticity and integrity
- Maintain SBOM repositories with searchable metadata for dependency tracking
- Use SBOM analysis tools to identify licensing conflicts and security vulnerabilities
- Implement automated SBOM comparison between releases to identify changes
- Include container image SBOMs with base image and layer information
- Use SBOM data for supply chain risk assessment and vendor evaluation
- Implement SBOM sharing with customers and downstream consumers when required
- Maintain SBOM archival policies for long-term compliance and audit requirements
- Use SBOM data to accelerate vulnerability response and impact assessment

## Provenance and Attestation

- Implement SLSA (Supply Chain Levels for Software Artifacts) framework compliance
- Use in-toto attestations to record build steps and verify supply chain integrity
- Generate signed provenance statements using SLSA provenance format
- Implement hermetic builds with reproducible outputs and controlled environments
- Use build system attestations to verify build process integrity and authenticity
- Implement code signing for all artifacts using trusted certificate authorities
- Use hardware security modules (HSM) or secure key management for signing operations
- Implement multi-party attestations for critical components and releases
- Use witness testimony and predicate verification for build step validation
- Implement build environment isolation and ephemeral build infrastructure
- Use container image attestations with cosign or similar signing tools
- Implement dependency verification using lock files and integrity checksums
- Use build reproducibility testing to ensure consistent artifact generation
- Implement supply chain visualization and audit trails for compliance purposes
- Use attestation verification in deployment pipelines before production releases

## Dependency Security and Management

- Implement automated dependency scanning using tools like Snyk, OWASP Dependency-Check, or GitHub Advanced Security
- Use dependency pinning with exact versions in production configurations
- Implement automated security patch management with testing and validation
- Use private package repositories and artifact registries for internal dependencies
- Implement dependency license scanning and compliance verification
- Use software composition analysis (SCA) tools for continuous monitoring
- Implement dependency update policies with security, stability, and compatibility considerations
- Use dependency confusion attack prevention with private registry priorities
- Implement typosquatting detection and package name verification
- Use binary analysis and static analysis for third-party component evaluation
- Implement dependency quarantine and approval workflows for new components
- Use dependency graph analysis to understand transitive dependency risks
- Implement automated dependency removal for unused or deprecated packages
- Use package verification with checksums, signatures, and reputation scoring
- Implement supply chain attack detection with behavioral analysis and anomaly detection

## Build and Release Security

- Implement secure build environments with ephemeral, isolated infrastructure
- Use build system hardening with minimal attack surface and security controls
- Implement two-person integrity controls for critical releases and changes
- Use automated security testing in build pipelines (SAST, DAST, container scanning)
- Implement artifact signing and verification throughout the release pipeline
- Use secure artifact storage with access controls and audit logging
- Implement release approval workflows with security and compliance checkpoints
- Use build environment monitoring and intrusion detection systems
- Implement build system backup and disaster recovery procedures
- Use secure secrets management for build-time credentials and configurations
- Implement build artifact immutability and tamper detection mechanisms
- Use continuous compliance monitoring throughout the build and release process
- Implement security incident response procedures for supply chain compromises
- Use threat modeling for build and release infrastructure security design
- Implement supply chain security metrics and KPIs for continuous improvement

## Vendor and Third-Party Risk Management

- Implement vendor security assessment and due diligence procedures
- Use supplier questionnaires and security certifications for vendor evaluation
- Implement contract security requirements and service level agreements
- Use continuous vendor monitoring and risk assessment procedures
- Implement vendor access controls and privilege management systems
- Use vendor security incident notification and response procedures
- Implement third-party code review and security testing requirements
- Use vendor compliance monitoring and audit procedures
- Implement vendor data handling and privacy protection requirements
- Use supply chain mapping and risk visualization for strategic planning
- Implement vendor contingency planning and alternative supplier identification
- Use vendor security metrics and performance monitoring dashboards
- Implement vendor security training and awareness programs
- Use supply chain insurance and risk transfer mechanisms where appropriate
- Implement vendor lifecycle management with security considerations throughout
