# Runbook: Timeout Recovery

**Runbook ID:** RB-CORE-002
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona
**Severity:** MEDIUM (Performance Issue)

---

## Purpose

This runbook provides procedures for diagnosing and recovering from flow execution timeouts in the Multi-LLM Orchestrator.

**Timeout Definition:**
- Flow execution exceeds 120 seconds (P95 latency SLO)
- Flow execution exceeds 180 seconds (hard timeout, terminates flow)

**Target Audience:** SRE on-call, repo owners

---

## Symptoms

### User-Reported
- "Flow timed out after 180 seconds"
- "Orchestrator is slow, taking >2 minutes"
- "Got timeout error in CI/CD pipeline"

### System-Detected
- Alert: "P95 Latency SLO Violation" (>120s for >10 min)
- Alert: "Flow Timeout Rate High" (>5% flows timing out)
- Grafana dashboard shows latency spike

---

## Detection

### Automated Alert

```yaml
alert: FlowTimeoutRateHigh
expr: |
  rate(flowengine_flow_timeouts_total[10m]) /
  rate(flowengine_flow_executions_total[10m]) > 0.05
for: 10m
labels:
  severity: warning
  runbook: RB-CORE-002
annotations:
  summary: "Flow timeout rate >5%"
  description: "{{ $value | humanizePercentage }} of flows timing out"
```

```yaml
alert: P95LatencySLOViolation
expr: |
  histogram_quantile(0.95, rate(flowengine_flow_duration_seconds_bucket[10m])) > 120
for: 10m
labels:
  severity: warning
  runbook: RB-CORE-002
annotations:
  summary: "P95 latency exceeds SLO (120s)"
  description: "P95 latency: {{ $value }}s"
```

---

### Manual Detection

```bash
# Check recent flow duration
blocks metrics query \
  --metric flow_duration_seconds \
  --last 1h \
  --aggregation p95

# Expected: <120s (SLO)
# If >120s sustained, investigate

# Check timeout count (last 1h)
blocks metrics query \
  --metric flow_timeouts_total \
  --last 1h \
  --group-by repo

# If any repo >1 timeout/hour, investigate
```

---

## Root Cause Analysis

### Common Causes (By Frequency)

1. **Large Context Size (60%)** — Context bundle >200KB, excessive token usage
2. **Model API Latency (20%)** — Provider-side latency spike
3. **Database Contention (10%)** — Slow queries, connection pool exhaustion
4. **Network Issues (5%)** — Connectivity problems, packet loss
5. **Code Complexity (5%)** — Generating very large code files (>10K lines)

---

## Diagnostic Procedures

### Step 1: Identify Affected Flow (2 minutes)

```bash
# Get flow ID from error message or logs
FLOW_ID="<flow_id>"

# View flow details
blocks flow show $FLOW_ID --verbose

# Expected output:
# Flow ID: flow-abc123
# Repo: customer-analytics
# Start Time: 2025-11-16 14:23:15
# Duration: 187s (TIMEOUT)
# Status: failed
# Error: "execution exceeded 180s timeout"
# Context Size: 245KB
# Models Used: Claude×2, GPT-4×3
```

---

### Step 2: Check Context Size (3 minutes)

**Most common cause of timeouts**

```bash
# Get context bundle size for flow
blocks flow show $FLOW_ID --format json | jq '.context_bundle_size_bytes'

# Expected: <180KB (pilot optimized threshold)
# If >200KB, context pruning needed

# Breakdown of context by source
blocks context analyze $FLOW_ID

# Expected output:
# | Source | Size | % of Total |
# |--------|------|------------|
# | Codebase files | 120KB | 49% |
# | Dependencies | 80KB | 33% |
# | Documentation | 30KB | 12% |
# | Schemas | 15KB | 6% |
# | **TOTAL** | **245KB** | **100%** |

# If codebase files >150KB, too many files included
```

**Resolution: Enable Context Pruning**

```bash
# Option 1: Enable globally (recommended)
kubectl set env deployment/flowengine -n production \
  CONTEXT_PRUNING_ENABLED=true \
  CONTEXT_MAX_SIZE_KB=180

# Option 2: Enable per repo
blocks config set --repo <repo_name> context-pruning true
blocks config set --repo <repo_name> context-max-size-kb 180

# Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production

# Retry flow
blocks flow retry $FLOW_ID

# Expected: Duration <120s, context size <180KB
```

---

### Step 3: Check Model API Latency (3 minutes)

```bash
# Check model provider response times (last 1h)
blocks metrics query \
  --metric model_api_latency_seconds \
  --last 1h \
  --group-by provider \
  --aggregation p95

# Expected:
# Anthropic (Claude): <30s
# OpenAI (GPT-4): <25s
# Google (Gemini): <20s

# If any provider >60s, check provider status
for provider in anthropic openai google; do
  curl -s https://status.$provider.com/api/v2/status.json | \
    jq '{provider: "'$provider'", status: .status.indicator}'
done

# Expected: "none" (no issues)
# If "minor", "major", "critical" → provider degradation
```

**Resolution: Route Around Slow Provider**

```bash
# If Anthropic degraded, disable temporarily
kubectl set env deployment/flowengine -n production \
  DISABLE_PROVIDERS=anthropic \
  FALLBACK_MODEL=gpt-4-turbo

# Verify routing
kubectl logs deployment/flowengine -n production --tail=20 | grep "Model routing"
# Expected: "Disabled provider: anthropic, Using fallback: gpt-4-turbo"

# Monitor provider status, re-enable when recovered
```

---

### Step 4: Check Database Performance (5 minutes)

```bash
# Identify slow queries
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT
      pid,
      now() - query_start as duration,
      substring(query, 1, 100) as query_snippet,
      state
    FROM pg_stat_activity
    WHERE state = 'active'
      AND query NOT LIKE '%pg_stat_activity%'
      AND (now() - query_start) > interval '10 seconds'
    ORDER BY duration DESC
    LIMIT 5;"

# Expected: 0-1 queries >10s
# If multiple queries >30s, database contention

# Check connection pool usage
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT count(*) as active_connections
    FROM pg_stat_activity
    WHERE datname='flowengine_db';"

# Expected Phase 6: <200 connections (<67% of pool)
# If >180 connections, pool near exhaustion
```

**Resolution: Scale Database**

```bash
# Increase connection pool size
kubectl set env deployment/flowengine -n production \
  DB_POOL_SIZE=300  # Increase from 200

# If queries still slow, add database indexes
# (coordinate with Engineering TL, requires schema change)

# If persistent issue, scale PostgreSQL instance
# Reference: RB-LAUNCH-003 (capacity_scaling.md)
```

---

### Step 5: Check Network Connectivity (5 minutes)

```bash
# Test connectivity to model providers from FlowEngine pod
for provider in api.anthropic.com api.openai.com generativelanguage.googleapis.com; do
  kubectl exec -n production deployment/flowengine -- \
    curl -o /dev/null -s -w "Provider: $provider, Time: %{time_total}s, HTTP: %{http_code}\n" \
    https://$provider/
done

# Expected: Time <1s, HTTP 200 or 401 (auth required, but reachable)
# If Time >5s or HTTP 000 (no response), network issue

# Check DNS resolution
kubectl exec -n production deployment/flowengine -- \
  nslookup api.anthropic.com

# Expected: Resolves to valid IP in <100ms
```

**Resolution: Network Issue**

```bash
# If provider unreachable, check egress firewall rules
kubectl get networkpolicy -n production

# If DNS resolution fails, check CoreDNS
kubectl logs -n kube-system deployment/coredns --tail=50

# Escalate to Infrastructure team if network issue confirmed
```

---

## Recovery Actions

### Action 1: Enable Context Pruning (Immediate)

**Success Rate: 90% (based on pilot)**

```bash
# Enable context pruning globally (if not already enabled)
kubectl set env deployment/flowengine -n production \
  CONTEXT_PRUNING_ENABLED=true \
  CONTEXT_MAX_SIZE_KB=180

# Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production

# Expected impact:
# - Context size: 245KB → 165KB (-33%)
# - Flow duration: 187s → 98s (-48%)
# - Timeout rate: 15% → 0%
```

**Validation:**

```bash
# Retry failed flow
blocks flow retry $FLOW_ID

# Monitor duration
blocks flow show $FLOW_ID --follow

# Expected: Duration <120s, Status: success
```

---

### Action 2: Adjust Timeout Threshold (Temporary)

**Use only if context pruning insufficient**

```bash
# Increase hard timeout from 180s to 240s (temporary)
kubectl set env deployment/flowengine -n production \
  FLOW_TIMEOUT_SECONDS=240

# Note: This is a workaround, not a fix.
# Root cause (large context, slow model API, etc.) should still be addressed.

# Revert to 180s once root cause resolved
```

---

### Action 3: Optimize Block Complexity

**Long-term solution for repos with consistently large features**

```bash
# Analyze feature size for timeout-prone repo
blocks metrics query \
  --metric flow_generated_lines_of_code \
  --last 7d \
  --filter repo=<repo_name> \
  --aggregation avg

# Expected: <5K lines/flow
# If >10K lines/flow, features too large

# Recommendation to repo owner:
# - Break down large features into smaller blocks
# - Use multi-block composition (generate 2-3 smaller blocks instead of 1 large block)
# - Target: <5K lines per block
```

**Communication to Repo Owner:**

```
Hi <owner>,

We've noticed timeout issues with flows in <repo_name>. Root cause analysis shows:

**Issue:** Generated code >10K lines/flow (target: <5K lines)

**Impact:**
- Flow duration: >150s (SLO: <120s)
- Timeout rate: 15% (target: <1%)

**Recommendation:**
1. Break down large features into smaller, composable blocks
2. Example: Instead of "Implement full user authentication system" (15K lines),
   split into:
   - "User login API endpoint" (3K lines)
   - "Password hashing & validation" (2K lines)
   - "Session management" (4K lines)

**Support:**
- Training Module 2: Block Authoring (multi-block composition)
- Office Hours: Thursdays 2-3 PM (#blocks-help)

Let me know if you'd like help refactoring!

Best,
SRE Team
```

---

## Prevention

### Pre-Flight Checks (Before Flow Execution)

```bash
# Validate context size before execution
blocks context estimate \
  --repo <repo_name> \
  --config <config.json>

# Expected output:
# Estimated context size: 165KB
# Status: ✅ Within limit (180KB)

# If >180KB, warning displayed:
# ⚠️ Context size exceeds limit. Enable pruning or reduce scope.
```

---

### Context Pruning Best Practices

**Enable globally for all production repos:**

```yaml
# File: flowengine-config.yaml
env:
  - name: CONTEXT_PRUNING_ENABLED
    value: "true"
  - name: CONTEXT_MAX_SIZE_KB
    value: "180"
  - name: CONTEXT_PRUNING_STRATEGY
    value: "smart"  # Preserves most relevant files

# Smart pruning algorithm:
# 1. Include: Schema files, config files (always)
# 2. Prioritize: Recently modified files, directly referenced files
# 3. Exclude: Test files, documentation, generated code
# 4. Trim: Large files (>50KB) to first/last 20KB (preserves structure)
```

---

### Timeout Monitoring Dashboard

**URL:** https://grafana.company.com/d/flowengine-timeouts

**Key Panels:**
- P95 latency over time (SLO line at 120s)
- Timeout rate by repo (identify problem repos)
- Context size distribution (histogram)
- Model API latency by provider (identify slow providers)

**Alert on Dashboard:**
- P95 latency >120s for >10 min → Warning
- Timeout rate >5% → Warning
- Timeout rate >10% → Critical (page on-call)

---

## Metrics & SLOs

**Latency SLO:**
- P95 latency: <120s (99% of the time)
- P99 latency: <180s (hard timeout)

**Timeout Rate:**
- Target: <1% of flows
- Acceptable: <5% of flows
- Critical: >10% of flows (requires immediate investigation)

**Pilot Performance (Baseline):**
- P95 latency: 118s ✅
- P99 latency: 142s ✅
- Timeout rate: 7% initially, 0% after context pruning ✅

**Phase 6 Target:**
- P95 latency: <120s across all 10 repos
- Timeout rate: <1%

---

## Escalation

### L1: Repo Owner (Self-Service)
- **Action:** Enable context pruning per repo
- **SLA:** Resolved within 1 flow retry (<5 min)

### L2: SRE On-Call
- **Action:** Global context pruning, model routing, database tuning
- **SLA:** Resolved within 30 minutes

### L3: Engineering TL
- **Action:** Schema optimization, algorithm changes, infrastructure scaling
- **SLA:** Resolved within 4 hours (or escalate to VP Engineering)

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-CORE-003:** Rate Limit Exhaustion (TBD)
- **RB-LAUNCH-003:** Capacity Scaling (`planning/60_launch/runbooks/capacity_scaling.md`)

---

## Appendix: Context Pruning Algorithm

**Smart Pruning Strategy (Default):**

```python
def prune_context(files, max_size_kb=180):
    """
    Intelligently prune context files to stay within size limit.

    Priority (descending):
    1. Schema files (*.json, *.yaml in schemas/) - ALWAYS include
    2. Config files (*config.json, *.env) - ALWAYS include
    3. Recently modified files (<7 days) - HIGH priority
    4. Files referenced in prompt - HIGH priority
    5. Core logic files (src/, lib/) - MEDIUM priority
    6. Test files (test/, *_test.py) - LOW priority
    7. Documentation (docs/, *.md) - LOW priority
    8. Generated code (build/, dist/) - EXCLUDE

    Trimming strategy for large files (>50KB):
    - Keep first 20KB (imports, class definitions)
    - Keep last 20KB (main logic, exports)
    - Replace middle with "... <trimmed X lines> ..."
    """
    included_files = []
    total_size = 0

    # Sort by priority
    sorted_files = sort_by_priority(files)

    for file in sorted_files:
        if total_size + file.size > max_size_kb * 1024:
            if file.priority == "HIGH":
                # Trim large file
                file_content = trim_large_file(file)
                file.size = len(file_content)
            else:
                # Skip low-priority file
                continue

        included_files.append(file)
        total_size += file.size

    return included_files
```

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE Persona | Initial version based on pilot learnings |

---

**Status:** ✅ Ready for production (validated in pilot Run #2 timeout recovery)
**Next Review:** Post-Phase 6 retrospective (Dec 1, 2025)
**Maintained By:** SRE Persona

---

**Key Learning from Pilot:** Context pruning resolves 90% of timeout issues. Enable by default.
