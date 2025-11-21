# Runbooks & Rollback Procedures

**Module 4:** Operational Readiness for Production Incidents
**Duration:** 45 minutes (presentation + demo)
**Owner:** SRE
**Last Updated:** November 16, 2025

---

## Overview

Runbooks are step-by-step playbooks for responding to production incidents. This module teaches you to diagnose, mitigate, and recover from FlowEngine failures using validated runbooks from the pilot phase.

### What You'll Learn
- Navigate the 5 core runbooks (failure, timeout, rate limit, outage, security)
- Execute rollback procedures with zero downtime
- Use circuit breakers and fallback routing
- Document post-incident reviews

### Prerequisites
- Completed Module 1 (CLI Quick-Start)
- Access to production monitoring (Grafana dashboards)
- On-call rotation access (PagerDuty or equivalent)

---

## Runbook Index

| Runbook | Trigger | Severity | MTTR Target | Validation Status |
| --- | --- | --- | --- | --- |
| **1. Flow Failure Response** | >1% failure rate | P2 (High) | <15 min | ✅ Validated (1/1 incidents) |
| **2. Timeout Recovery** | Flow >120s | P3 (Medium) | <10 min | ✅ Validated (1/1 incidents) |
| **3. Rate Limit Exhaustion** | API quota >80% | P3 (Medium) | <20 min | 🧪 Tested (not triggered in pilot) |
| **4. Provider Outage** | Model API 5xx | P2 (High) | <30 min | 🧪 Tested (not triggered in pilot) |
| **5. Security Incident** | PII leak / audit failure | P1 (Critical) | <5 min | 🧪 Tested (not triggered in pilot) |

**Runbook Location:** `planning/30_design/runbooks/`

---

## Runbook 1: Flow Failure Response

**Full Runbook:** `planning/30_design/runbooks/flow_failure_response.md`

### When to Use
- Grafana alert "FlowFailureRate" fires (>1% failure over 1h window)
- CLI returns error with exit code 1
- TaskDB shows `status=failed`

### Quick Triage (5 minutes)

```bash
# Step 1: Identify recent failures
aws logs filter-pattern 'ERROR' \
  --log-group /aws/lambda/flowengine \
  --start-time -1h \
  | jq '.events[] | {timestamp, message}'

# Step 2: Check TaskDB for failed tasks
psql -c "
  SELECT task_id, flow_type, error_message, created_at
  FROM tasks
  WHERE status='failed'
  ORDER BY created_at DESC
  LIMIT 10;
"

# Step 3: Categorize failure type
# Common types:
# - Timeout (45s+): Context bundle too large
# - Rate Limit: Model API quota exceeded
# - Validation Error: Schema mismatch
# - Model API 5xx: Vendor outage
```

### Recovery Actions

**Timeout Failures (Most Common):**
```bash
# Check context bundle size
aws s3 ls s3://context-bundles/ctx_$(task_id).json --human-readable

# If >500KB, trigger context pruning
blocks flow retry $(task_id) --enable-pruning --max-context-size 180KB

# Expected: Retry succeeds in <60s
```

**Rate Limit Failures:**
```bash
# Check quota usage
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/usage

# If >80%, enable circuit breaker
kubectl set env deployment/flowengine ENABLE_CIRCUIT_BREAKER=true

# Wait 60s for circuit half-open, then retry
blocks flow retry $(task_id)
```

**Validation Errors:**
```bash
# Validate TaskObject against schema
blocks verify contract --task-id $(task_id) --verbose

# If schema version mismatch, rollback to compatible version
git log planning/30_design/schemas/ | head -20
kubectl rollout undo deployment/flowengine
```

### Escalation Path
- **0-15 min:** SRE on-call triages using runbook
- **15-30 min:** Page TL if multiple failures (>5 in 1h)
- **30-60 min:** Incident commander joins; consider rollback
- **60+ min:** Notify stakeholders; trigger post-incident review

---

## Runbook 2: Timeout Recovery

**Scenario:** Flow execution exceeds 120s P95 latency target.

### Detection

```bash
# Grafana alert: P95FlowLatency > 120s
# Or manual check:
blocks metrics latency --last-1h

# Output:
# P50: 112s
# P90: 124s
# P95: 138s ⚠️  (exceeds 120s target)
# P99: 156s
```

### Root Cause Analysis

```bash
# Step 1: Check for large context bundles
aws logs filter-pattern 'context_size_kb' \
  --log-group /aws/lambda/flowengine \
  --start-time -1h \
  | jq '.events[] | select(.message | contains("context_size_kb")) | .message' \
  | grep -oP 'context_size_kb=\K\d+'

# If >500KB context detected → apply context pruning (see below)

# Step 2: Check model API latency
blocks metrics model-latency --last-1h

# If Claude >40s or GPT-4 >30s → possible vendor slowdown

# Step 3: Check for resource contention
kubectl top pods -n flowengine
# If CPU >80% or Memory >3GB → scale up replicas
```

### Mitigation

**Option 1: Context Pruning (Preferred)**
```bash
# Enable automatic pruning for future flows
kubectl set env deployment/flowengine \
  CONTEXT_PRUNING_ENABLED=true \
  CONTEXT_MAX_SIZE_KB=180

# Retry stuck tasks with pruning
blocks flow retry $(task_id) --enable-pruning
```

**Option 2: Scale Infrastructure**
```bash
# Add FlowEngine replicas
kubectl scale deployment/flowengine --replicas=5

# Increase Postgres connection pool
kubectl set env deployment/flowengine \
  DB_POOL_SIZE=50 \
  DB_MAX_OVERFLOW=20
```

**Option 3: Fallback to Faster Model**
```bash
# Switch from Claude Sonnet 4.5 to GPT-4 Turbo (faster, lower quality)
kubectl set env deployment/flowengine \
  FALLBACK_MODEL=gpt-4-turbo \
  FALLBACK_THRESHOLD_LATENCY=30

# This applies to new flows only; retry stuck tasks:
blocks flow retry $(task_id) --model gpt-4-turbo
```

### Validation

```bash
# Wait 15 minutes, then check P95 latency
blocks metrics latency --last-15min

# Expected: P95 <120s
# If still >120s, escalate to TL
```

---

## Runbook 3: Rate Limit Exhaustion

**Scenario:** Model API quota reaches 80%, risking service degradation.

### Detection

```bash
# Check quota usage (all providers)
blocks quota show --all

# Output:
# Provider: Anthropic (Claude)
#   Used: 820,000 / 1,000,000 tokens (82%) ⚠️
#   Resets: 2025-11-16 23:59:59 UTC (8h 23m)
#
# Provider: OpenAI (GPT-4)
#   Used: 450,000 / 1,000,000 tokens (45%) ✅
#   Resets: 2025-11-16 18:00:00 UTC (3h 12m)
```

### Immediate Actions

**Step 1: Enable Circuit Breaker (Prevents Quota Exhaustion)**
```bash
# Circuit breaker pauses new requests when quota >threshold
kubectl set env deployment/flowengine \
  ENABLE_CIRCUIT_BREAKER=true \
  CIRCUIT_BREAKER_THRESHOLD=85  # Pause at 85%

# Check circuit breaker status
kubectl logs -l app=flowengine | grep "CircuitBreaker"
# Expected: "CircuitBreaker: HALF_OPEN (monitoring quota)"
```

**Step 2: Route to Secondary Provider**
```bash
# Route architect role from Claude to GPT-4 (temporary downgrade)
kubectl set env deployment/flowengine \
  ARCHITECT_FALLBACK_MODEL=gpt-4-turbo

# This applies to new flows; existing flows continue with Claude
```

**Step 3: Notify Stakeholders**
```bash
# Post to #ops-alerts channel
blocks notify slack \
  --channel ops-alerts \
  --message "⚠️  Claude quota at 82%. Circuit breaker enabled. ETA to normal: quota reset in 8h."
```

### Long-Term Mitigation

```bash
# Request quota increase from vendor
# (Business to submit request with justification)

# Or optimize context size to reduce token usage
blocks config set context.max_size_kb 120  # Reduce from 180KB
```

---

## Runbook 4: Provider Outage

**Scenario:** Model API returns 5xx errors (vendor outage).

### Detection

```bash
# Grafana alert: ModelAPI5xxRate > 5%
# Or check recent errors:
aws logs filter-pattern '5xx' \
  --log-group /aws/lambda/flowengine \
  --start-time -15m
```

### Immediate Actions

**Step 1: Check Vendor Status Pages**
- Anthropic: https://status.anthropic.com
- OpenAI: https://status.openai.com
- Google AI: https://status.cloud.google.com

**Step 2: Enable Fallback Routing**
```bash
# Route all traffic to healthy provider
# Example: Claude down → fallback to GPT-4
kubectl set env deployment/flowengine \
  FALLBACK_MODEL=gpt-4-turbo \
  FALLBACK_ON_5XX=true

# Verify fallback working
blocks test-flow --model auto
# Expected: Uses GPT-4 automatically
```

**Step 3: If All Providers Down (Rare)**
```bash
# Enable manual review mode (human-in-the-loop)
kubectl set env deployment/flowengine \
  MANUAL_REVIEW_MODE=true

# This queues flows for manual architect review
# Operators use web UI to manually approve/reject plans
```

### Communication

```bash
# Notify users via status page
blocks status update \
  --status degraded \
  --message "Model API outage affecting Claude. Using GPT-4 fallback. ETA: 2h per vendor status."

# Page SRE + TL if outage >30min
```

---

## Runbook 5: Security Incident

**Scenario:** PII leaked, audit log failure, or unauthorized access detected.

### Detection

```bash
# Security scan flags PII in context bundle
blocks security scan --task-id $(task_id)

# Or audit log gap detected
psql -c "
  SELECT COUNT(*) FROM audit_logs
  WHERE created_at > NOW() - INTERVAL '1 hour';
"
# Expected: >0; if 0 → audit log failure
```

### Immediate Actions (CRITICAL: <5 min)

**Step 1: Halt All Flows**
```bash
# Stop FlowEngine immediately
kubectl scale deployment/flowengine --replicas=0

# Confirm no active flows
blocks status flows --active
# Expected: 0 active flows
```

**Step 2: Isolate Affected Artifacts**
```bash
# Quarantine context bundles containing PII
aws s3 mv s3://context-bundles/ctx_$(task_id).json \
  s3://quarantine-bucket/ctx_$(task_id).json

# Revoke S3 access for FlowEngine service account
aws iam attach-user-policy \
  --user-name flowengine-sa \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

**Step 3: Page Security Team + TL**
```bash
# PagerDuty high-urgency alert
blocks incident create \
  --severity P1 \
  --title "Security Incident: PII Leak Detected" \
  --assignee security-team

# Notify compliance officer (if Basel-I impacted)
```

### Investigation (Within 1 Hour)

```bash
# Audit trail review
psql -c "
  SELECT * FROM audit_logs
  WHERE task_id = '$(task_id)'
  ORDER BY created_at DESC;
"

# Check for unauthorized access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=context-bundles \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
```

### Recovery

```bash
# After investigation, re-enable FlowEngine with PII redaction
kubectl set env deployment/flowengine \
  PII_REDACTION_ENABLED=true \
  PII_PATTERNS='email,ssn,credit_card'

kubectl scale deployment/flowengine --replicas=3

# Validate PII redaction working
blocks test-flow --input test_with_pii.md --dry-run
# Expected: PII redacted in context bundle
```

---

## Rollback Procedures

### Zero-Downtime Rollback (Validated in Pilot)

**Scenario:** New FlowEngine version causes regressions.

```bash
# Step 1: Check current version
kubectl get deployment flowengine -o jsonpath='{.spec.template.spec.containers[0].image}'
# Example: flowengine:v1.1.0

# Step 2: Rollback to previous version
kubectl rollout undo deployment/flowengine

# Step 3: Monitor rollback status
kubectl rollout status deployment/flowengine
# Expected: "deployment 'flowengine' successfully rolled out" (within 45s)

# Step 4: Verify previous version active
kubectl get pods -l app=flowengine
# All pods should show age <1m

# Step 5: Test rolled-back version
blocks test-flow --input test_case.md
# Expected: Flow succeeds with previous version
```

**Pilot Validation (Nov 9, 2025):**
- Simulated regression in v1.1.0
- Rollback completed in 45 seconds
- Zero downtime (seamless traffic cutover)
- Previous version (v1.0) handled traffic successfully

### Canary Deployment (Pre-Production Testing)

**Scenario:** Test new version with 10% traffic before full rollout.

```bash
# Step 1: Deploy canary version
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flowengine-canary
spec:
  replicas: 1  # 10% of traffic (1 of 10 replicas)
  template:
    spec:
      containers:
      - name: flowengine
        image: flowengine:v1.2.0-canary
EOF

# Step 2: Monitor canary metrics (48 hours)
blocks metrics compare \
  --baseline flowengine \
  --canary flowengine-canary \
  --duration 48h

# If canary metrics acceptable, promote to 100%:
kubectl set image deployment/flowengine flowengine=flowengine:v1.2.0

# If canary fails, delete and rollback:
kubectl delete deployment flowengine-canary
```

**Pilot Validation (Oct 28, 2025):**
- Deployed v1.0 to 10% traffic for 48 hours
- Metrics: Zero errors, latency within SLO
- Promoted to 100% without issues

---

## Post-Incident Review (PIR)

After every P1/P2 incident, conduct a PIR within 48 hours.

### PIR Template

```markdown
# Post-Incident Review: [Incident Title]

**Date:** [Incident Date]
**Severity:** P1 / P2 / P3
**Duration:** [Start Time] – [End Time] ([Duration])
**Incident Commander:** [Name]

## Timeline
- [HH:MM] Detection: [How incident was detected]
- [HH:MM] Triage: [Initial diagnosis]
- [HH:MM] Mitigation: [Action taken]
- [HH:MM] Resolution: [Service restored]

## Root Cause
[1-2 paragraphs describing root cause]

## Impact
- Users affected: [Number or "None"]
- Flows failed: [Count]
- Revenue impact: [$Amount or "None"]

## What Went Well
- [Runbook effectiveness]
- [Team response time]

## What Went Wrong
- [Detection delay]
- [Mitigation complexity]

## Action Items
1. [Action] — Owner: [Name] — Due: [Date]
2. [Action] — Owner: [Name] — Due: [Date]

## Lessons Learned
[Key takeaways for future incidents]
```

### Example PIR (Pilot Incident: Nov 6, 2025)

```markdown
# Post-Incident Review: Context Bundle Timeout (Run #2)

**Date:** November 6, 2025
**Severity:** P3 (Medium)
**Duration:** 14:32:18 – 14:44:36 (12.3 minutes)
**Incident Commander:** SRE Persona

## Timeline
- 14:32 Detection: Grafana alert "FlowTimeout" fired (impl flow >45s)
- 14:33 Triage: Checked context bundle size (512KB; exceeds 500KB)
- 14:35 Mitigation: Triggered context pruning via runbook
- 14:44 Resolution: Retry succeeded (context pruned to 180KB)

## Root Cause
Context bundle included large dependencies (node_modules), exceeding 500KB threshold.

## Impact
- Users affected: 0 (internal pilot)
- Flows failed: 1 (retry succeeded)
- Revenue impact: $0

## What Went Well
- Runbook detected issue immediately
- Context pruning resolved issue in <10min

## What Went Wrong
- Default context pruning was disabled (should be enabled by default)

## Action Items
1. Enable context pruning by default in v1.1 — Owner: Engineering — Due: Nov 10
2. Add .contextignore to template repos — Owner: Product — Due: Nov 12

## Lessons Learned
- Runbook effectiveness: 100% (resolved via documented procedure)
- Context pruning should be opt-out, not opt-in
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Alert Threshold | Severity | Runbook |
| --- | --- | --- | --- |
| Flow failure rate | >1% over 1h | P2 | Runbook 1 |
| P95 latency | >120s | P3 | Runbook 2 |
| Model API quota | >80% | P3 | Runbook 3 |
| Model API 5xx rate | >5% | P2 | Runbook 4 |
| Audit log gap | >5min gap | P1 | Runbook 5 |

**Dashboard:** https://grafana.company.com/d/flowengine-slo

### On-Call Rotation

- **Primary:** SRE Persona (24/7 PagerDuty)
- **Secondary:** Engineering TL (escalation path)
- **Incident Commander:** SRE Lead (P1/P2 incidents)

---

## Best Practices

1. **Run Tabletop Exercises:** Simulate incidents quarterly to validate runbooks
2. **Update Runbooks:** After every PIR, update runbook with learnings
3. **Automate Recovery:** Where possible, automate mitigation (e.g., circuit breaker)
4. **Document Everything:** Log all actions in incident tracker

---

## Next Steps

1. **Access Runbooks:** Clone `planning/30_design/runbooks/` to your workstation
2. **Join On-Call:** Add yourself to PagerDuty rotation
3. **Practice:** Run simulated incident during office hours (Module 5)
4. **Monitor Dashboards:** Familiarize with Grafana SLO dashboard (Module 5)

---

**Module 4 Complete!** Proceed to Module 5: Metrics & Dashboards
