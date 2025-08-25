---
applyTo: "**/*.{py,js,ts,java,go,cs,rb,rs,php}"
priority: 50
category: "cross-cutting"

---

# Compliance and Regulatory-specific Copilot Instructions

## GDPR (General Data Protection Regulation) Compliance

- Implement privacy by design; minimize data collection to what is strictly necessary
- Provide clear, explicit consent mechanisms for all data processing activities
- Implement data subject rights: API endpoints for access/rectification, 30-day response SLA
- Maintain detailed records with ISO 27001-compliant documentation templates
- Implement DPIA using standardized questionnaires for automated risk scoring
- Use AES-256 encryption at rest, TLS 1.3 in transit, plus field-level tokenization
- Implement automated data retention: 7 years financial, 3 years marketing, with scheduler deletion
- Ensure lawful basis documentation with consent timestamps and legal basis tracking
- Implement privacy notices with <8th grade reading level, multi-language support
- Establish data processing agreements using standard GDPR clauses with SCC
- Implement breach notification with automated 72-hour reporting to supervisory authority
- Conduct quarterly compliance audits using automated scanning tools and checklists
- Implement data minimization with field-level access controls and purpose limitation
- Provide one-click opt-out with automated preference center and suppression lists
- Implement Standard Contractual Clauses (SCC) for EEA data transfers with adequacy decisions

## HIPAA (Health Insurance Portability and Accountability Act) Compliance

- Implement AES-256 encryption for PHI at rest, TLS 1.3 in transit, plus database-level encryption
- Use RBAC with principle of least privilege, session timeouts <30 minutes idle
- Implement comprehensive audit logging: user ID, timestamp, action, data accessed with 6-year retention
- Provide MFA using FIDO2/WebAuthn or TOTP with backup codes for PHI access
- Implement BAA with cloud providers including AWS, Azure, GCP HIPAA-compliant services
- Use encrypted messaging (Signal Protocol) and secure email gateways for PHI communications
- Implement automated PHI backup with 3-2-1 rule (3 copies, 2 media, 1 offsite) and <4 hour RTO
- Conduct annual penetration testing and quarterly vulnerability assessments with remediation SLA
- Implement role-based workforce training with annual recertification and access reviews
- Use safe harbor de-identification (remove 18 identifiers) or expert determination methods
- Implement secure media destruction using NIST 800-88 guidelines with certificate of destruction
- Maintain 24-hour breach notification procedures with risk assessment templates
- Implement physical access controls: badge systems, biometric locks, surveillance with 90-day retention
- Use OWASP Top 10 secure coding standards with automated SAST/DAST scanning in CI/CD
- Implement granular consent management with patient portal and preference tracking

## SOX (Sarbanes-Oxley Act) Compliance

- Implement segregation of duties for financial system access and operations
- Maintain detailed audit trails for all financial data changes and access
- Implement change management controls for financial reporting systems
- Use version control and code review processes for all financial system changes
- Implement automated testing for financial calculations and reporting logic
- Maintain documentation for all financial system controls and procedures
- Implement access controls with regular access reviews and certifications
- Use configuration management to ensure consistent financial system environments
- Implement data validation and reconciliation controls for financial transactions
- Maintain backup and recovery procedures for financial data and systems
- Implement monitoring and alerting for unusual financial system activities
- Use secure development practices for financial reporting applications
- Implement proper authorization workflows for financial system changes
- Maintain evidence of control effectiveness through automated monitoring
- Implement proper data retention policies for financial records and audit trails

## General Compliance Principles

- Implement privacy-preserving data processing techniques (differential privacy, homomorphic encryption)
- Use compliance frameworks (ISO 27001, NIST, CIS Controls) for security implementations
- Implement data governance policies with clear data ownership and stewardship
- Use automated compliance monitoring and reporting tools where possible
- Implement consent management platforms for complex consent requirements
- Maintain regulatory change monitoring and impact assessment procedures
- Use secure software development lifecycle (SSDLC) practices throughout development
- Implement third-party risk management procedures for vendor relationships
- Use penetration testing and vulnerability assessments for security validation
- Implement business continuity and disaster recovery plans for critical systems
- Maintain incident response procedures with regulatory notification requirements
- Use compliance-aware cloud service providers with appropriate certifications
- Implement data loss prevention (DLP) solutions for sensitive data protection
- Maintain regular compliance training for development and operations teams
- Use automated policy enforcement tools to ensure consistent compliance implementation
