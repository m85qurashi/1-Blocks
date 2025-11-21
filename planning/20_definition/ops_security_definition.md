# Ops & Security Definition

Source references: `7-SRE/artifacts/sre_ops_plan.md`.

## SLOs
- FlowEngine success rate ≥99%, P95 latency ≤90s plan/impl.
- Catalog availability ≥99.5%.

## Security Posture
- Secrets via vault with short-lived tokens.
- PII redaction + prompt deny-lists enforced before sending to models.
- Artifact registry encrypted at rest; RBAC enforcement.

## Runbook/Incident Prep
- Categories: flow failure, provider outage, budget breach, security anomaly.
- Each includes detection, mitigation, rollback, comms.

## Rollout Strategy
- Canary per flow type; auto-rollback on success <98% or budget breach >15%.
- Basel-I pilot limited scope prior to general availability.

## Compliance & Audit
- Immutable logs (Task, Block, Flow) with hashes.
- Retention ≥1 year, accessible for audit readiness.
