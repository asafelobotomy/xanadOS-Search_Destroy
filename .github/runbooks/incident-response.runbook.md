# Incident Response Runbook

Use this runbook to drive a fast, consistent response to production incidents.

## Scope and principles

- Minimize customer impact; restore service first, then root-cause.
- Clear roles: Incident Commander (IC), Communications, Ops, Subject Matter Experts (SMEs).
- One source of truth: incident doc or channel with timestamped updates.

## Severity levels

- Sev1: Critical outage, data loss, security incident.
- Sev2: Partial outage, severe degradation.
- Sev3: Degraded but workarounds exist.

## Immediate actions (first 5 minutes)

1. Acknowledge alert; page on-call. Assign IC.
2. Declare severity; open incident channel and shared doc.
3. Freeze risky deploys; enable feature flags to mitigate if possible.
4. Start timeline with UTC timestamps.

## Triage and stabilization

- Gather symptoms, blast radius, impacted services/customers.
- Roll back last known risky change if correlated.
- Capture logs/metrics/dashboards links; snapshot evidence if volatile.
- Apply mitigations (scale up, rate limit, feature flag off) to restore service.

## Communication

- Internal: updates every 15 minutes in the incident channel.
- External (if needed): status page updates every 30–60 minutes.
- Record who, what, when; keep customer language clear and non-technical.

## Escalation

- Page secondary teams per runbook; involve security/legal for data or auth issues.
- Engage vendors if third-party is involved.

## Decision log

- For each action: who executed, exact command/change, expected vs actual results.

## Verification

- Define objective recovery metrics (error rate, latency, saturation) and exit criteria.
- Monitor for 30–60 minutes post-restore for regression.

## Post-incident

- Schedule blameless postmortem within 48 hours.
- Collect artifacts: logs, PRs, commits, dashboards, chats.
- Create tracked actions: detection, defense-in-depth, tests, docs.

## Quick commands (optional)

````bash

## create an incident scratch doc (optional placeholder)

DATE=$(date -u +%Y-%m-%dT%H:%MZ); echo "Incident $DATE" > /tmp/incident-$DATE.md

## capture top resource usage on a host

uptime; free -m; df -h; top -b -n1 | head -n 20

```text
````
