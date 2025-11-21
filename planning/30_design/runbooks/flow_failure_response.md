# Runbook: Flow Failure Response

**Owner:** SRE Persona
**Severity:** P2 (High)
**Last Updated:** Nov 13, 2025

---

## Scope
Handles FlowEngine execution failures (plan/impl/review/docs flows)

## Detection
- **Alert:** Grafana alert "FlowFailureRate" fires when >1% failure rate over 1-hour window
- **Symptoms:** CLI returns error; CI pipeline fails; TaskDB shows `status=failed`

## Triage Steps

### 1. Identify Failure Type (5 min)
```bash
# Query recent failures
aws logs filter-pattern 'ERROR' --log-group /aws/lambda/flowengine --start-time -1h

# Check TaskDB for failed tasks
psql -c "SELECT task_id, flow_type, error_message FROM tasks WHERE status='failed' ORDER BY created_at DESC LIMIT 10;"
```

**Common Failure Types:**
- **Timeout (45s+):** Context bundle too large
- **Rate Limit:** Model API quota exceeded
- **Validation Error:** Invalid TaskObject schema
- **Model API 5xx:** Vendor outage

### 2. Timeout Failures
**Root Cause:** Context bundle >500KB

**Resolution:**
```bash
# Check bundle size
aws s3 ls s3://context-bundles/$(task_id).json --human-readable

# If >500KB, trigger context pruning
flow exec prune-context --task-id $(task_id) --max-size 180KB
```

**Prevention:** Context pruning enabled by default (ADR-002)

### 3. Rate Limit Failures
**Root Cause:** Model API quota exceeded

**Resolution:**
```bash
# Check current quota usage
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/usage

# If >80%, enable circuit breaker
kubectl set env deployment/flowengine ENABLE_CIRCUIT_BREAKER=true

# Wait 60s for circuit half-open, retry
```

**Escalation:** If quota critically low, page on-call to request vendor limit increase

### 4. Validation Errors
**Root Cause:** TaskObject schema mismatch

**Resolution:**
```bash
# Validate TaskObject against schema
schema validate --input task_$(task_id).json --schema planning/30_design/schemas/task_object.schema.json

# If invalid, check for schema version mismatch
git log planning/30_design/schemas/task_object.schema.json | head -20
```

**Fix:** Rollback to compatible schema version or update FlowEngine to latest

### 5. Model API Outages
**Root Cause:** Vendor 5xx errors

**Resolution:**
1. Check vendor status pages:
   - Anthropic: https://status.anthropic.com
   - OpenAI: https://status.openai.com
   - Google AI: https://status.cloud.google.com

2. Enable fallback routing (if available):
```bash
# Route to secondary model
kubectl set env deployment/flowengine FALLBACK_MODEL=gpt-4-turbo
```

3. If critical, enable manual review mode:
```bash
kubectl set env deployment/flowengine MANUAL_REVIEW_MODE=true
```

**Escalation:** Page SRE + TL if outage >30min; notify stakeholders

---

## Recovery Steps

### Retry Failed Tasks
```bash
# Retry with exponential backoff
flow exec retry --task-id $(task_id) --max-attempts 3
```

### Rollback (if widespread failures)
```bash
# Rollback FlowEngine to previous version
kubectl rollout undo deployment/flowengine

# Verify rollback success
kubectl rollout status deployment/flowengine
```

---

## Post-Incident Review
- Document root cause in incident tracker
- Update runbook if new failure mode discovered
- Add monitoring/alerting if detection gap identified

**Pilot Evidence:** 1 timeout failure in Run #2 (resolved in 12.3min via context pruning)
