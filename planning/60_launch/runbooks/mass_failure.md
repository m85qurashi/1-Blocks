# Runbook: Mass Failure Response

**Runbook ID:** RB-LAUNCH-005
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona + Incident Commander
**Severity:** CRITICAL (P1 Incident Response)

---

## Purpose

This runbook provides incident response procedures for mass concurrent failures across multiple repositories using the Multi-LLM Orchestrator.

**Definition of Mass Failure:**
- ≥5 flow failures within 1 hour across different repositories, OR
- ≥3 repositories experiencing concurrent failures (>50% failure rate), OR
- Single systemic issue causing cascading failures

**Target Audience:** SRE on-call, Incident Commander, Engineering TL

---

## Detection

### Automated Alerts

**PagerDuty Alert: "Mass Concurrent Failures Detected"**

**Trigger Conditions:**

```yaml
alert: MassConcurrentFailures
expr: |
  sum(increase(flowengine_flow_failures_total[1h])) >= 5
  OR
  count(
    rate(flowengine_flow_failures_total[5m]) > 0.5
  ) >= 3
for: 5m
labels:
  severity: critical
  runbook: RB-LAUNCH-005
annotations:
  summary: "Mass concurrent failures detected across multiple repos"
  description: "{{ $value }} failures in last hour OR {{ $value }} repos with >50% failure rate"
```

**Alert Channels:**
- PagerDuty: Page SRE on-call (immediate)
- Slack: Post to #incidents (immediate)
- Email: incident-team@company.com (immediate)

---

### Manual Detection

**Dashboard Review:**

```bash
# Open Reliability Dashboard
open https://grafana.company.com/d/flowengine-reliability

# Check metrics (last 1 hour):
# - Flow success rate: Should be ≥99%, if <95% = mass failure
# - Failed repos: Should be 0-1, if ≥3 = mass failure
# - Error rate: Should be <1%, if >5% = mass failure
```

---

## Triage & Response (First 5 Minutes)

### Step 1: Acknowledge Incident (30 seconds)

```bash
# Acknowledge PagerDuty alert
pagerduty ack --incident-key mass-failure-<timestamp>

# Post to #incidents Slack
slack-cli post --channel incidents --message "🚨 P1: Mass failure detected. Investigating.
On-Call: @<your-name>
ETA for update: 5 minutes"
```

---

### Step 2: Initial Assessment (3 minutes)

**Determine Scope:**

```bash
# Count affected repos (last 1h)
blocks metrics query \
  --metric flow_failures_total \
  --last 1h \
  --group-by repo \
  --sort desc

# Example output:
# financial-reporting: 12 failures
# customer-analytics: 8 failures
# risk-engine: 6 failures
# inventory-mgmt: 5 failures
# compliance-service: 0 failures (pilot repo unaffected)

# Total affected repos: 4
# Total failures: 31
```

**Identify Common Pattern:**

```bash
# Review error logs (last 100 errors)
kubectl logs deployment/flowengine -n production --tail=100 | grep "ERROR" > /tmp/errors.log

# Analyze error patterns
cat /tmp/errors.log | cut -d' ' -f5- | sort | uniq -c | sort -rn | head -10

# Common patterns:
# - "timeout exceeded" → likely model API latency/outage
# - "rate limit exceeded" → quota exhaustion
# - "validation failed" → schema issue (breaking change)
# - "connection refused" → database/infrastructure issue
# - "authentication failed" → API key issue
```

---

### Step 3: Escalate & Mobilize (2 minutes)

**Trigger Incident Response:**

```bash
# Page Incident Commander
pagerduty trigger \
  --severity critical \
  --title "Mass Failure: Multi-LLM Orchestrator" \
  --details "Affected repos: 4+, Total failures: 30+, Pattern: <pattern>"

# Create incident channel
slack-cli create-channel --name incident-mass-failure-$(date +%Y%m%d) \
  --members sre-oncall,eng-tl,product-lead,data-lead

# Post incident details
slack-cli post --channel incident-mass-failure-$(date +%Y%m%d) --message "
🚨 **P1 Incident: Mass Failure**
**Detected:** $(date)
**Affected Repos:** <list>
**Total Failures:** <count>
**Error Pattern:** <pattern>

**Team:**
- Incident Commander: @<name>
- SRE On-Call: @<name>
- Engineering TL: @<name>

**Next Steps:** Root cause analysis (5 min), Go/No-Go on rollback"
```

---

## Root Cause Analysis (Next 10 Minutes)

### Scenario 1: Model API Outage

**Symptoms:**
- Errors: "timeout exceeded", "connection refused", "503 Service Unavailable"
- Pattern: All 3 model providers OR single provider with high usage

**Verification:**

```bash
# Check model provider status
for provider in anthropic openai google; do
  curl -s https://status.$provider.com/api/v2/status.json | jq '.status.indicator'
done

# Expected: "none" (no issues)
# If "minor", "major", "critical" → provider outage confirmed

# Check provider health from FlowEngine
kubectl exec -n production deployment/flowengine -- \
  curl -s http://localhost:8080/health/models | jq

# Expected: All providers "healthy"
# If any "degraded" or "down" → provider issue
```

**Resolution:**

```bash
# Option 1: Wait for provider recovery (if ETA <30 min)
# Monitor provider status page for updates

# Option 2: Route around failed provider (if 1/3 providers down)
kubectl set env deployment/flowengine -n production \
  DISABLE_PROVIDERS=<failed_provider>

# Example: If Anthropic down
kubectl set env deployment/flowengine -n production \
  DISABLE_PROVIDERS=anthropic \
  FALLBACK_MODEL=gpt-4-turbo

# Verify routing
kubectl logs deployment/flowengine -n production --tail=20 | grep "Model routing"
# Expected: "Using fallback model: gpt-4-turbo"

# Option 3: Rollback to pilot (if all providers down OR ETA >30 min)
# Execute RB-LAUNCH-002 (rollback_to_pilot.md)
```

---

### Scenario 2: Rate Limit Exhaustion

**Symptoms:**
- Errors: "rate limit exceeded", "quota exhausted", "429 Too Many Requests"
- Pattern: Sudden spike in flow volume OR quota not increased for Phase 6/7

**Verification:**

```bash
# Check current quota usage
blocks quota show --all-providers

# Example output:
# Anthropic: 1.8M / 2M tokens (90% used) ⚠️
# OpenAI: 1.4M / 1.5M tokens (93% used) ⚠️
# Google: 800K / 1M tokens (80% used) ✅

# Check recent flow volume
blocks metrics query \
  --metric flow_executions_total \
  --last 24h \
  --group-by hour

# If spike detected (e.g., 10× normal volume), investigate cause
```

**Resolution:**

```bash
# Option 1: Enable circuit breaker (pause at 85% quota)
kubectl set env deployment/flowengine -n production \
  ENABLE_CIRCUIT_BREAKER=true \
  CIRCUIT_BREAKER_THRESHOLD=85

# Verify circuit breaker active
kubectl logs deployment/flowengine -n production --tail=20 | grep "Circuit breaker"
# Expected: "Circuit breaker activated: pausing new flows"

# Option 2: Request emergency quota increase (coordinate with Business persona)
# Contact provider support:
# - Anthropic: support@anthropic.com
# - OpenAI: help.openai.com
# - Google: cloud.google.com/support

# Option 3: Throttle flow execution (temporary)
kubectl set env deployment/flowengine -n production \
  MAX_CONCURRENT_FLOWS=5  # Reduce from 10-50

# Option 4: Rollback to pilot (if quota cannot be increased within 1h)
# Execute RB-LAUNCH-002
```

---

### Scenario 3: Schema Breaking Change

**Symptoms:**
- Errors: "validation failed", "schema mismatch", "contract violation"
- Pattern: All failures post-deployment OR specific block family affected

**Verification:**

```bash
# Check recent deployments
kubectl rollout history deployment/flowengine -n production

# Identify suspect deployment
SUSPECT_REVISION=$(kubectl rollout history deployment/flowengine -n production | tail -2 | head -1 | awk '{print $1}')

# Review deployment diff
kubectl rollout history deployment/flowengine -n production --revision=$SUSPECT_REVISION

# Check schema version
kubectl exec -n production deployment/flowengine -- \
  curl -s http://localhost:8080/api/schemas/version | jq '.version'

# Compare with last known good version (pilot: 20251104_001)
```

**Resolution:**

```bash
# Option 1: Rollback FlowEngine deployment
kubectl rollout undo deployment/flowengine -n production

# Wait for rollout
kubectl rollout status deployment/flowengine -n production --timeout=120s

# Verify schema reverted
kubectl exec -n production deployment/flowengine -- \
  curl -s http://localhost:8080/api/schemas/version | jq '.version'

# Test flow execution
blocks generate --repo compliance-service --config test.json --output /tmp/test/

# Option 2: Hot-patch schema (if rollback not feasible)
# Apply schema fix
kubectl apply -f schema-hotfix.yaml -n production

# Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production
```

---

### Scenario 4: Database Connection Pool Exhaustion

**Symptoms:**
- Errors: "connection refused", "too many connections", "connection pool exhausted"
- Pattern: High concurrency (many repos executing simultaneously)

**Verification:**

```bash
# Check database connections
kubectl exec -n production deployment/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "SELECT count(*) FROM pg_stat_activity WHERE datname='flowengine_db';"

# Expected for Phase 6: <100 connections (pool size: 200)
# If ≥180 connections → pool exhaustion

# Check FlowEngine connection config
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="DB_POOL_SIZE")].value}'

# Expected: 200 (Phase 6 scaling)
```

**Resolution:**

```bash
# Option 1: Increase connection pool (if DB can handle it)
kubectl set env deployment/flowengine -n production \
  DB_POOL_SIZE=300

# Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production

# Option 2: Scale up PostgreSQL (if DB CPU/memory saturated)
# Coordinate with DBA
# Expected time: 15-30 minutes

# Option 3: Throttle concurrent flows (temporary)
kubectl set env deployment/flowengine -n production \
  MAX_CONCURRENT_FLOWS=20  # Reduce from 50

# Option 4: Rollback to pilot (if scaling not feasible within 30 min)
# Execute RB-LAUNCH-002
```

---

### Scenario 5: Security Incident (Credential Leak)

**Symptoms:**
- Errors: "authentication failed", "unauthorized access"
- Pattern: Sudden failures across all repos
- Alert: Security team notification OR model provider suspension

**Verification:**

```bash
# Check for exposed credentials (recent commits)
git log --all --full-history --source --remotes --pretty=format:"%h %an %ad %s" -- "*secret*" "*key*" "*.env"

# Check model provider status (may suspend API keys if leak detected)
for provider in anthropic openai google; do
  curl -s https://api.$provider.com/v1/auth/test \
    -H "Authorization: Bearer $(kubectl get secret model-api-keys -n production -o jsonpath="{.data.$provider}" | base64 -d)"
done

# Expected: 200 OK
# If 401 Unauthorized → key revoked by provider
```

**Resolution:**

```bash
# IMMEDIATE: Rotate all API keys
# 1. Generate new keys from provider portals
# 2. Update Kubernetes secrets
kubectl create secret generic model-api-keys-new \
  --from-literal=anthropic=$NEW_ANTHROPIC_KEY \
  --from-literal=openai=$NEW_OPENAI_KEY \
  --from-literal=google=$NEW_GOOGLE_KEY \
  -n production

# 3. Update FlowEngine deployment
kubectl set env deployment/flowengine -n production \
  --from=secret/model-api-keys-new

# 4. Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production

# 5. Delete old secret
kubectl delete secret model-api-keys -n production

# 6. Rename new secret
kubectl get secret model-api-keys-new -n production -o yaml | \
  sed 's/model-api-keys-new/model-api-keys/' | \
  kubectl apply -f -

# 7. Notify InfoSec team
# Email: infosec@company.com
# Subject: "URGENT: API Key Rotation - Multi-LLM Orchestrator"

# 8. Conduct post-incident security review (within 24h)
```

---

## Go/No-Go Decision: Rollback to Pilot

**Decision Framework (15 minutes post-detection):**

### GO for Rollback (Execute RB-LAUNCH-002)

Execute rollback if ANY of these are true:

- [ ] Root cause identified but fix ETA >1 hour
- [ ] Root cause unidentified after 15 minutes of investigation
- [ ] ≥5 repos affected (>50% of Phase 6 scope)
- [ ] Pilot repo (compliance-service) also affected
- [ ] Security incident confirmed (credential leak, breach)
- [ ] Cost runaway (daily spend >$100, 2× budget)

### NO-GO for Rollback (Continue Mitigation)

Do NOT rollback if ALL of these are true:

- [ ] Root cause identified with fix ETA <30 minutes
- [ ] ≤3 repos affected (<30% of Phase 6 scope)
- [ ] Pilot repo unaffected
- [ ] No security concerns
- [ ] No cost concerns
- [ ] Mitigation in progress (e.g., circuit breaker enabled, quota increased)

### Decision Maker

**Accountable:** Incident Commander (or SRE Lead if IC not yet mobilized)

**Consultation Required:**
- SRE On-Call (technical feasibility)
- Engineering TL (fix timeline)
- Product Lead (business impact)

---

## Communication Protocol

### During Incident (Every 15 Minutes)

**Status Update Template:**

```bash
# Post to #incidents Slack
slack-cli post --channel incidents --message "
🚨 **P1 Incident Update** ($(date +%H:%M))
**Status:** <Investigating / Mitigating / Resolved>
**Affected Repos:** <count> (<list>)
**Root Cause:** <identified / under investigation>
**Mitigation:** <action taken>
**ETA:** <time to resolution / rollback>
**Next Update:** +15 min"
```

---

### Incident Resolution

**Resolution Criteria (All Must Be Met):**

- [ ] Flow success rate restored to ≥99% (last 30 min)
- [ ] All affected repos operational
- [ ] Root cause identified and documented
- [ ] Fix applied and verified (or rollback complete)
- [ ] Monitoring confirms no recurrence (30 min observation)

**Resolution Notification:**

```bash
# Post to #incidents Slack
slack-cli post --channel incidents --message "
✅ **P1 Incident RESOLVED** ($(date +%H:%M))
**Duration:** <start time> - <end time> (<total duration>)
**Affected Repos:** <count> (<list>)
**Root Cause:** <brief description>
**Resolution:** <action taken>
**Downtime:** <minutes> (if any)

**Next Steps:**
- Post-incident review: <date>
- RCA document: planning/60_launch/incidents/rca_<id>.md
- Preventive actions: <summary>

Thank you to the incident response team!
Incident Commander: @<name>"

# Email stakeholders
echo "Subject: ✅ RESOLVED: Multi-LLM Orchestrator Mass Failure

The mass failure incident affecting <count> repositories has been resolved.

**Summary:**
- Duration: <total duration>
- Root Cause: <brief>
- Resolution: <brief>
- Downtime: <minutes>

**Post-Incident Actions:**
- RCA session: <date>
- Prevention plan: <date>
- Affected users notified

Detailed RCA available at: planning/60_launch/incidents/rca_<id>.md

Contact: sre-oncall@company.com

Best,
SRE Team" | \
mail -s "✅ RESOLVED: Multi-LLM Orchestrator Incident" \
  product@company.com,engineering-tl@company.com,business@company.com
```

---

## Post-Incident Review (Within 48 Hours)

### Required Actions

#### 1. Root Cause Analysis (RCA) Document

**File:** `planning/60_launch/incidents/rca_<incident_id>.md`

```markdown
# Root Cause Analysis: Mass Failure Incident

**Incident ID:** INC-<date>-<number>
**Date:** <incident date>
**Severity:** P1 (Mass Failure)
**Duration:** <total duration>
**Affected Repos:** <count> (<list>)

## Executive Summary
<2-3 sentences: what happened, impact, resolution>

## Timeline
- <time>: Incident detected (automated alert / manual)
- <time>: Incident Commander mobilized
- <time>: Root cause identified
- <time>: Mitigation applied
- <time>: Incident resolved
- <time>: Post-incident review completed

## Impact
- **Affected Users:** <count> (repo owners + end users)
- **Failed Flows:** <count>
- **Downtime:** <minutes> (per repo)
- **Cost Impact:** $<amount> (failed flows, retries)

## Root Cause
<Detailed technical analysis>

## Contributing Factors
1. <Factor 1>
2. <Factor 2>
3. <Factor 3>

## What Went Well
- <Positive aspect 1>
- <Positive aspect 2>

## What Went Poorly
- <Issue 1>
- <Issue 2>

## Action Items
- [ ] <Owner>: <Preventive action 1> (Due: <date>)
- [ ] <Owner>: <Preventive action 2> (Due: <date>)
- [ ] <Owner>: <Monitoring improvement> (Due: <date>)

## Prevention
<How to prevent recurrence>

## Lessons Learned
<Key takeaways>
```

---

#### 2. Incident Metrics (Update Tracking)

**File:** `planning/60_launch/evidence/incident_log.csv`

```csv
Date,Incident ID,Severity,Type,Affected Repos,Duration (min),Root Cause,Resolution,Rollback?
2025-11-20,INC-001,P1,Mass Failure,4,45,Rate limit exhaustion,Circuit breaker enabled,No
```

---

#### 3. Preventive Actions (Track to Completion)

Create Jira tickets / GitHub issues for each action item:

```bash
# Example: Add pre-emptive circuit breaker alert
gh issue create \
  --repo <org>/<repo> \
  --title "Alert: Circuit breaker approaching threshold" \
  --body "Add alert at 75% quota (before 85% circuit breaker activation).
Linked to: INC-001 (Mass Failure RCA)
Priority: High
Owner: @sre-team" \
  --label incident-followup
```

---

## Metrics & SLOs

### Target Metrics (Phase 6/7)

**Incident Response:**
- Time to detection: <5 minutes (automated alert)
- Time to mobilization: <10 minutes (IC + team)
- Time to root cause: <15 minutes
- Time to mitigation: <30 minutes (or rollback initiated)
- Time to resolution: <60 minutes (total)

**Prevention:**
- Mass failure frequency: ≤1 per quarter (target: 0)
- Recurrence rate: 0% (same root cause)

### Actual Performance (Pilot)

**Pilot Incident (Run #2 Timeout):**
- Detection: 2 minutes (manual)
- Root cause: 8 minutes (context size issue)
- Mitigation: 2 minutes (context pruning enabled)
- Resolution: 12.3 minutes (total)

**Phase 6/7 Target:** <30 minutes (total resolution for mass failure)

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-LAUNCH-002:** Rollback to Pilot (`planning/60_launch/runbooks/rollback_to_pilot.md`)
- **RB-LAUNCH-001:** Repository Onboarding (`planning/60_launch/runbooks/repo_onboarding.md`)
- **RB-LAUNCH-004:** Budget Breach (TBD)

---

## Testing & Drills

### Tabletop Exercise (Nov 28, 2025)

**Scenario:** Simulated mass failure (10 concurrent flow failures across 5 repos)

**Participants:**
- SRE On-Call (primary responder)
- Incident Commander
- Engineering TL
- Product Lead

**Objectives:**
1. Practice incident detection and mobilization (<10 min)
2. Validate root cause analysis procedures
3. Test Go/No-Go rollback decision framework
4. Verify communication protocol effectiveness

**Success Criteria:**
- Complete simulated response in <30 minutes
- All participants understand their roles
- Identify 2-3 runbook improvements

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE Persona | Initial version for Phase 6/7 incident response |

---

**Status:** ✅ Ready for Phase 6 (validated via pilot incident response)
**Next Review:** Post-tabletop exercise (Nov 28, 2025)
**Maintained By:** SRE Persona + Incident Commander

---

**CRITICAL:** Mass failure = P1 incident. Mobilize team immediately. When in doubt, rollback.
