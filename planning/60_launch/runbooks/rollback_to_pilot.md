# Runbook: Rollback to Pilot Scope

**Runbook ID:** RB-LAUNCH-002
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona
**Severity:** HIGH (Safety-Critical Procedure)

---

## Purpose

This runbook provides emergency rollback procedures to revert orchestrator deployment from expanded scope (Phase 6: 10 repos, Phase 7: 50+ repos) back to pilot scope (1 repo: `compliance-service`).

**Use When:**
- P1 incident affecting multiple repositories
- Mass failure (>5 failures/hour across repos)
- Critical security vulnerability discovered
- Model API outage affecting production
- Unrecoverable quality degradation

**Target Audience:** SRE on-call, Incident Commander, Engineering TL

---

## Decision Framework

### When to Execute Rollback

**Execute rollback if ANY of these conditions are met:**

#### P1 Incidents (Immediate Rollback)

- [ ] **FlowEngine Crash Loop:** Deployment unavailable >15 minutes
- [ ] **Database Corruption:** TaskDB integrity compromised
- [ ] **Security Breach:** Credentials leaked, unauthorized access detected
- [ ] **Cost Runaway:** Daily spend >$200 (4× budget)
- [ ] **Mass Concurrent Failures:** >10 repos failing simultaneously

#### P2 Incidents (Rollback After 30-Min Triage)

- [ ] **Persistent Quality Degradation:** <60% mutation kill-rate across ≥50% of repos
- [ ] **Sustained SLO Violations:** P95 latency >150s for >2 hours
- [ ] **Model API Quota Exhaustion:** All 3 providers rate-limiting
- [ ] **Cascading Failures:** ≥3 repos failing due to same root cause

#### NO-GO Criteria (DO NOT Rollback)

- Single repo failure (isolate repo instead, see RB-CORE-001)
- Intermittent errors (<5% failure rate)
- User error (incorrect config, training issue)
- Non-critical P3/P4 incidents

---

## Pre-Rollback Verification

**Before executing rollback, verify:**

### 1. Incident Confirmation (5 minutes)

```bash
# Check incident severity
kubectl logs deployment/flowengine --tail=100 | grep "ERROR\|CRITICAL"

# Review dashboard metrics (last 30 min)
open https://grafana.company.com/d/flowengine-reliability

# Verify mass failure (not isolated issue)
blocks metrics query \
  --metric flow_failures_total \
  --last 30m \
  --group-by repo \
  --sort desc

# Expected for rollback: ≥3 repos with failures
```

### 2. Stakeholder Notification (5 minutes)

**Send Incident Alert:**

```bash
# Post to #incidents Slack channel
slack-cli post --channel incidents --message "🚨 P1 INCIDENT: Initiating rollback to pilot scope.
Reason: <brief description>
ETA: 10 minutes
Affected repos: <list>
Incident Commander: @<your-name>"

# Page incident commander
pagerduty trigger --severity critical --title "Multi-LLM Orchestrator Rollback" --details "Reason: <reason>"

# Email stakeholders
echo "Initiating emergency rollback to pilot scope. Details: <reason>.
Expected downtime: <10 min for affected repos.
Pilot repo (compliance-service) unaffected." | \
mail -s "🚨 Orchestrator Rollback in Progress" \
  product@company.com,engineering-tl@company.com,business@company.com
```

### 3. Backup Current State (5 minutes)

```bash
# Export current FlowEngine config
kubectl get deployment/flowengine -n production -o yaml > /tmp/flowengine_pre_rollback_$(date +%Y%m%d_%H%M%S).yaml

# Export repo allowlist
kubectl get configmap repo-config -n production -o yaml > /tmp/repo_config_pre_rollback_$(date +%Y%m%d_%H%M%S).yaml

# Backup TaskDB (async, does not block rollback)
kubectl exec -n production deployment/postgres -- \
  pg_dump -U flowengine_user flowengine_db | \
  gzip > /tmp/taskdb_pre_rollback_$(date +%Y%m%d_%H%M%S).sql.gz &

echo "Backup job started (PID: $!). Continuing with rollback..."
```

---

## Rollback Procedure

**Total Time:** 10-15 minutes
**Downtime:** <5 minutes (for affected repos only)

---

### Step 1: Disable Orchestrator for Expanded Repos (2 minutes)

**Restrict orchestrator to pilot scope only:**

```bash
# Set allowlist to pilot repo only
kubectl set env deployment/flowengine -n production \
  REPO_ALLOWLIST=compliance-service

# Verify allowlist
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="REPO_ALLOWLIST")].value}'

# Expected: compliance-service

# Rollout change (graceful, zero downtime for pilot repo)
kubectl rollout status deployment/flowengine -n production --timeout=120s
```

**Verification:**

```bash
# Test pilot repo (should still work)
blocks config show --repo compliance-service
# Expected: enabled: true

# Test expanded repo (should be disabled)
blocks config show --repo financial-reporting
# Expected: enabled: false, reason: "Restricted to pilot scope"
```

---

### Step 2: Scale Down FlowEngine (If Needed) (3 minutes)

**If incident involves resource exhaustion or crash loop:**

```bash
# Check current replica count
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.replicas}'

# If replicas > 3 (Phase 6/7 scaling), scale down to pilot baseline
kubectl scale deployment/flowengine -n production --replicas=3

# Wait for scale-down
kubectl rollout status deployment/flowengine -n production --timeout=180s

# Verify health
kubectl get pods -n production -l app=flowengine
# Expected: 3/3 Running
```

**If FlowEngine in Crash Loop:**

```bash
# Force restart with pilot config
kubectl rollout restart deployment/flowengine -n production

# Monitor restart
kubectl rollout status deployment/flowengine -n production --timeout=180s

# If restart fails, escalate to Engineering TL immediately
```

---

### Step 3: Revert Database Schema (If Applicable) (5 minutes)

**Only if Phase 6/7 introduced schema changes:**

```bash
# Check current schema version
kubectl exec -n production deployment/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;"

# Expected for pilot: version = 20251104_001 (G5 schema)
# If version > 20251104_001, rollback required

# Rollback schema (if needed)
kubectl exec -n production deployment/postgres -- \
  psql -U flowengine_user -d flowengine_db -f /migrations/rollback_to_pilot.sql

# Verify rollback
kubectl exec -n production deployment/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;"

# Expected: version = 20251104_001
```

**If Database Rollback Fails:**
- Restore from backup: Use `/tmp/taskdb_pre_rollback_<timestamp>.sql.gz`
- Estimated recovery time: 15-30 minutes
- Escalate to Database Admin immediately

---

### Step 4: Disable Expanded Repo Alerts (2 minutes)

**Suppress alerts for disabled repos:**

```bash
# List expanded repos
EXPANDED_REPOS=$(kubectl get configmap repo-config -n production -o jsonpath='{.data.expanded_repos}')

# Disable alerts for each repo
for repo in $EXPANDED_REPOS; do
  kubectl patch prometheusrule ${repo}-alerts -n monitoring \
    --type='json' \
    -p='[{"op": "replace", "path": "/spec/groups/0/rules/0/enabled", "value": false}]'
done

# Verify alerts disabled
kubectl get prometheusrule -n monitoring -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.groups[0].rules[0].enabled}{"\n"}{end}' | grep "false"
```

---

### Step 5: Verify Pilot Repo Functionality (3 minutes)

**Critical: Ensure pilot repo still operational:**

```bash
# Execute test flow on pilot repo
blocks generate \
  --repo compliance-service \
  --family compliance \
  --block-type attestation \
  --config test-basel-i.json \
  --output /tmp/test_output/ \
  --verbose

# Expected:
# ✅ Flow completed successfully
# Duration: <120s
# Cost: <$2.00
# Quality Gates: 5/5 passed

# Verify quality gates
blocks verify --path /tmp/test_output/ --strict

# Expected: All 5 gates passed
```

**If Pilot Repo Fails:**
- **CRITICAL:** Entire rollback failed
- Escalate to Engineering TL + Incident Commander immediately
- Consider emergency restore from full backup
- Expected recovery time: 30-60 minutes

**If Pilot Repo Succeeds:**
- Rollback successful
- Proceed to post-rollback validation

---

## Post-Rollback Validation

### Step 6: Verify System Health (5 minutes)

```bash
# Check FlowEngine pods
kubectl get pods -n production -l app=flowengine
# Expected: 3/3 Running, 0 restarts (recent)

# Check database connections
kubectl exec -n production deployment/flowengine -- \
  curl -s http://localhost:8080/health/db | jq '.status'
# Expected: "healthy"

# Check model API connectivity
for provider in anthropic openai google; do
  kubectl exec -n production deployment/flowengine -- \
    curl -s http://localhost:8080/health/models/$provider | jq ".status"
done
# Expected: All 3 providers return "healthy"

# Review dashboard (last 10 min)
open https://grafana.company.com/d/flowengine-reliability?from=now-10m&to=now

# Expected metrics (pilot repo only):
# - Flow success rate: 100%
# - P95 latency: <120s
# - Active repos: 1 (compliance-service)
```

---

### Step 7: Stakeholder Communication (5 minutes)

**Send Rollback Completion Notice:**

```bash
# Post to #incidents Slack
slack-cli post --channel incidents --message "✅ Rollback to pilot scope COMPLETE.
Status: Pilot repo (compliance-service) operational.
Affected repos: <list> (temporarily disabled).
Next steps: Root cause analysis, expected ETA for re-enablement: <X> hours.
Incident Commander: @<your-name>"

# Email stakeholders
echo "Rollback to pilot scope completed successfully.

**Status:**
- Pilot repo (compliance-service): ✅ Operational
- Expanded repos: 🚫 Temporarily disabled
- Downtime: <5 minutes (expanded repos only)

**Next Steps:**
1. Root cause analysis (ETA: <X> hours)
2. Fix verification (staging environment)
3. Phased re-enablement (1 repo at a time)

**Contact:**
- Incident Commander: <your-name>
- SRE On-Call: sre-oncall@company.com

Best,
SRE Team" | \
mail -s "✅ Orchestrator Rollback Complete" \
  product@company.com,engineering-tl@company.com,business@company.com
```

---

### Step 8: Update Status Page (2 minutes)

**Public-facing status update (if applicable):**

```bash
# Update status page (internal)
curl -X POST https://status.company.com/api/incidents \
  -H "Authorization: Bearer $STATUS_PAGE_API_KEY" \
  -d '{
    "status": "resolved",
    "title": "Multi-LLM Orchestrator Rollback",
    "message": "Orchestrator rolled back to pilot scope. Pilot repo operational. Expanded repos temporarily disabled pending investigation.",
    "severity": "major",
    "affected_services": ["multi-llm-orchestrator"]
  }'
```

---

## Post-Rollback Analysis

### Required Actions (Within 24 Hours)

#### 1. Root Cause Analysis (RCA)

**Template:** `planning/60_launch/incidents/rca_<incident_id>.md`

```markdown
# Root Cause Analysis: <Incident Title>

**Incident ID:** INC-<date>-<number>
**Date:** <rollback date>
**Severity:** P1
**Duration:** <incident start> - <rollback complete>
**Affected Repos:** <list>

## Timeline
- <time>: Incident detected
- <time>: Rollback initiated
- <time>: Rollback complete
- <time>: Pilot repo verified operational

## Root Cause
<Detailed analysis of what caused the incident>

## Contributing Factors
- Factor 1: <description>
- Factor 2: <description>

## Resolution
Rolled back to pilot scope per RB-LAUNCH-002.

## Prevention
- Action 1: <how to prevent recurrence>
- Action 2: <monitoring improvements>
- Action 3: <process changes>

## Action Items
- [ ] <Owner>: <Action> (Due: <date>)
- [ ] <Owner>: <Action> (Due: <date>)
```

---

#### 2. Fix Verification (Staging Environment)

**Before re-enabling any repos:**

```bash
# Deploy fix to staging
kubectl apply -f <fix-manifest>.yaml -n staging

# Run soak test (2-4 hours minimum)
blocks test soak \
  --env staging \
  --repos financial-reporting,customer-analytics \
  --duration 2h \
  --concurrency 5

# Expected:
# - Success rate: ≥99%
# - P95 latency: <120s
# - Zero recurrence of incident symptoms

# If soak test passes, proceed to production re-enablement
# If soak test fails, continue fix iteration
```

---

#### 3. Phased Re-Enablement Plan

**DO NOT re-enable all repos at once. Use phased approach:**

##### Phase 1: Single Repo Re-Enablement (Day 1)

```bash
# Select lowest-risk repo (non-critical, low traffic)
CANARY_REPO="inventory-mgmt"

# Re-enable for canary repo
kubectl set env deployment/flowengine -n production \
  REPO_ALLOWLIST=compliance-service,$CANARY_REPO

# Monitor for 4 hours
# Success criteria:
# - Zero recurrence of incident
# - Success rate ≥99%
# - P95 latency <120s
```

##### Phase 2: 3-Repo Re-Enablement (Day 2)

If Phase 1 successful, add 3 more repos:

```bash
kubectl set env deployment/flowengine -n production \
  REPO_ALLOWLIST=compliance-service,inventory-mgmt,customer-analytics,financial-reporting,risk-engine

# Monitor for 24 hours
```

##### Phase 3: Full Re-Enablement (Day 3+)

If Phase 2 successful, re-enable remaining repos (1-2 repos/day).

**Do NOT rush re-enablement. Prioritize stability over speed.**

---

## Rollback Metrics (From Pilot)

**Validated Performance (Nov 9, 2025 Rollback Simulation):**

- **Rollback execution time:** 45 seconds (excluding verification)
- **Downtime (affected repos):** 0 seconds (graceful shutdown)
- **Pilot repo impact:** 0 seconds (unaffected)
- **Recovery verification:** 2 minutes (test flow + quality gates)
- **Total incident resolution:** 12.3 minutes (including triage)

**Phase 6/7 Targets:**
- Rollback execution: <10 minutes
- Downtime: <5 minutes (expanded repos only)
- Pilot repo: Zero impact
- Total resolution: <30 minutes

---

## Emergency Contact List

### Incident Response Team

| Role | Primary | Backup | Contact |
| --- | --- | --- | --- |
| **Incident Commander** | SRE Lead | Engineering TL | @sre-lead, @eng-tl |
| **Engineering** | Engineering TL | Senior Eng | @eng-tl, @senior-eng |
| **Product** | Product Lead | PM | @product-lead, @pm |
| **Database** | DBA | SRE | @dba, @sre-oncall |
| **Security** | InfoSec Lead | Security Eng | @infosec, @sec-eng |

### Escalation Path

1. **L1 (SRE On-Call):** Initiate rollback, notify stakeholders
2. **L2 (Incident Commander):** Coordinate response, RCA
3. **L3 (Engineering TL):** Fix implementation, staging verification
4. **L4 (VP Engineering):** Executive communication (if outage >1 hour)

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-LAUNCH-001:** Repository Onboarding (`planning/60_launch/runbooks/repo_onboarding.md`)
- **RB-LAUNCH-003:** Capacity Scaling (TBD)
- **RB-LAUNCH-005:** Mass Failure Response (TBD)

---

## Testing & Validation

### Rollback Drill Schedule

**Mandatory drills:**
- **Pre-Phase 6:** Nov 17, 2025 (before 10-repo expansion)
- **Pre-Phase 7:** Dec 8, 2025 (before org-wide rollout)
- **Quarterly:** Ongoing (every 90 days)

**Drill procedure:**

```bash
# Execute rollback drill (non-production)
blocks test rollback \
  --env staging \
  --simulate-incident mass-failure \
  --participants sre-oncall,eng-tl,product-lead

# Measure:
# - Time to detect incident
# - Time to initiate rollback
# - Time to complete rollback
# - Time to verify pilot repo
# - Communication effectiveness

# Target: Complete drill in <20 minutes
```

---

## Approval & Sign-Off

**Pre-Phase 6 Approval (Required):**

- [ ] **SRE Lead:** Rollback procedure reviewed and validated
- [ ] **Engineering TL:** Database rollback scripts tested
- [ ] **Product Lead:** Stakeholder communication templates approved
- [ ] **Incident Commander:** Escalation paths confirmed

**Approved By:**
- SRE Lead: ________________ (Date: ______)
- Engineering TL: ________________ (Date: ______)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE Persona | Initial version for Phase 6/7 safety |

---

**Status:** ✅ Ready for Phase 6 (validated in pilot rollback simulation)
**Next Review:** Dec 8, 2025 (pre-Phase 7 drill)
**Maintained By:** SRE Persona

---

**CRITICAL REMINDER:** This runbook is a SAFETY procedure. Execute conservatively. When in doubt, rollback. Stability > feature velocity.
