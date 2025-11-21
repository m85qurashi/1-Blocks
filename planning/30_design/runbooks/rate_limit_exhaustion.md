# Runbook: Rate Limit Exhaustion

**Runbook ID:** RB-CORE-003
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona
**Severity:** HIGH (Service Degradation)

---

## Purpose

This runbook provides procedures for detecting, responding to, and preventing model API rate limit exhaustion in the Multi-LLM Orchestrator.

**Rate Limit Exhaustion Definition:**
- Model provider quota usage exceeds 85% (circuit breaker threshold)
- Flow failures due to "429 Too Many Requests" errors
- Sustained quota usage >90% for >1 hour

**Target Audience:** SRE on-call, Business persona

---

## Background

### Model Provider Quotas

**Phase 6 Quotas (10-Repo Soak, Nov 16-30):**

| Provider | Daily Quota | Avg Flow Usage | Flows/Day Capacity | Circuit Breaker Threshold |
| --- | --- | --- | --- | --- |
| **Anthropic (Claude)** | 2M tokens/day | 45K tokens | ~44 flows | 1.7M tokens (85%) |
| **OpenAI (GPT-4)** | 1.5M tokens/day | 35K tokens | ~42 flows | 1.28M tokens (85%) |
| **Google (Gemini)** | 1M tokens/day | 20K tokens | ~50 flows | 850K tokens (85%) |

**Expected Daily Load (Phase 6):**
- 10 repos × 3-5 flows/day = 30-50 flows/day
- Projected token usage: 1.5M Anthropic, 1.1M OpenAI, 700K Gemini
- Headroom: 25% Anthropic, 27% OpenAI, 30% Gemini ✅

---

**Phase 7 Quotas (50+ Repos, Dec 9-20):**

| Provider | Daily Quota | Flows/Day Capacity | Circuit Breaker Threshold |
| --- | --- | --- | --- |
| **Anthropic (Claude)** | 10M tokens/day | ~222 flows | 8.5M tokens (85%) |
| **OpenAI (GPT-4)** | 7.5M tokens/day | ~214 flows | 6.38M tokens (85%) |
| **Google (Gemini)** | 5M tokens/day | ~250 flows | 4.25M tokens (85%) |

**Expected Daily Load (Phase 7):**
- 50 repos × 3-5 flows/day = 150-250 flows/day
- Projected token usage: 7M Anthropic, 5.5M OpenAI, 3.5M Gemini
- Headroom: 30% Anthropic, 27% OpenAI, 30% Gemini ✅

---

## Detection

### Automated Alerts

**Alert: Circuit Breaker Threshold Approaching**

```yaml
alert: CircuitBreakerThresholdApproaching
expr: |
  (
    sum(increase(flowengine_model_tokens_total{provider="anthropic"}[1d])) /
    scalar(flowengine_model_quota_total{provider="anthropic"})
  ) > 0.75
for: 1h
labels:
  severity: warning
  runbook: RB-CORE-003
annotations:
  summary: "Anthropic quota approaching circuit breaker (>75%)"
  description: "Current usage: {{ $value | humanizePercentage }}"
```

**Alert: Circuit Breaker Activated**

```yaml
alert: CircuitBreakerActivated
expr: |
  flowengine_circuit_breaker_status == 1
for: 1m
labels:
  severity: critical
  runbook: RB-CORE-003
annotations:
  summary: "Circuit breaker activated - flows paused"
  description: "Quota usage exceeded 85% threshold"
```

**Alert: Rate Limit Errors**

```yaml
alert: RateLimitErrorsHigh
expr: |
  rate(flowengine_model_api_errors_total{error_type="rate_limit"}[10m]) > 0.1
for: 10m
labels:
  severity: warning
  runbook: RB-CORE-003
annotations:
  summary: "High rate of 429 errors from model providers"
  description: "{{ $value }} rate limit errors/sec"
```

---

### Manual Detection

```bash
# Check current quota usage (all providers)
blocks quota show --all-providers

# Example output:
# | Provider | Used | Quota | % Used | Status | Reset Time |
# |----------|------|-------|--------|--------|------------|
# | Anthropic | 1.7M | 2M | 85% | ⚠️ Circuit Breaker | 23:59 UTC |
# | OpenAI | 1.1M | 1.5M | 73% | ✅ Healthy | 23:59 UTC |
# | Google | 700K | 1M | 70% | ✅ Healthy | 23:59 UTC |

# Check circuit breaker status
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="CIRCUIT_BREAKER_STATUS")].value}'

# Expected: "inactive"
# If "active", flows are paused
```

---

## Root Cause Analysis

### Common Causes

#### Cause 1: Unexpected Load Spike (40%)

**Indicators:**
- Flow volume 2-3× normal
- Sudden spike in flow executions (e.g., batch job, repo onboarding)

**Verification:**

```bash
# Check flow volume (last 24h)
blocks metrics query \
  --metric flow_executions_total \
  --last 24h \
  --group-by hour

# Compare to baseline (Phase 6: 30-50 flows/day)
# If >100 flows/day, unexpected spike
```

---

#### Cause 2: Retry Storm (30%)

**Indicators:**
- High retry rate (>20% of flows retried)
- Same flows retried multiple times

**Verification:**

```bash
# Check retry rate
blocks metrics query \
  --metric flow_retries_total \
  --last 1h \
  --group-by repo

# If any repo >5 retries/hour, retry storm likely

# Identify retried flows
blocks flow list --status retried --last 1h

# Common retry causes:
# - Timeout (context size issue) → Enable context pruning
# - Validation failure (schema issue) → Fix schema
# - Rate limit (circular: retrying rate-limited flows) → Disable retries temporarily
```

---

#### Cause 3: Inefficient Token Usage (20%)

**Indicators:**
- High tokens per flow (>80K tokens, 2× baseline)
- Large context sizes (>200KB)

**Verification:**

```bash
# Average tokens per flow (last 24h)
blocks metrics query \
  --metric model_tokens_per_flow \
  --last 24h \
  --aggregation avg

# Expected: ~100K tokens/flow (45K Anthropic, 35K OpenAI, 20K Gemini)
# If >150K tokens/flow, inefficient usage

# Breakdown by provider
blocks metrics query \
  --metric model_tokens_total \
  --last 24h \
  --group-by provider,repo
```

---

#### Cause 4: Quota Not Increased for Phase 6/7 (10%)

**Indicators:**
- Phase 6/7 expansion started but quotas still at pilot levels
- Expected load exceeds pilot quotas

**Verification:**

```bash
# Check if quota increase request was approved
cat planning/60_launch/evidence/quota_increase_confirmations.txt

# Expected for Phase 6:
# Anthropic: 500K → 2M tokens/day ✅
# OpenAI: 400K → 1.5M tokens/day ✅
# Google: 250K → 1M tokens/day ✅

# If quotas not increased, contact providers (urgent)
```

---

## Response Actions

### Immediate Response (0-5 Minutes)

#### Step 1: Verify Circuit Breaker Status

```bash
# Check if circuit breaker already activated
kubectl logs deployment/flowengine -n production --tail=50 | grep "Circuit breaker"

# If activated:
# Expected log: "Circuit breaker activated: quota usage 87% (threshold: 85%)"

# If not activated but quota >85%, circuit breaker should trigger within 1 min
# If circuit breaker fails to activate, manual intervention needed:
kubectl set env deployment/flowengine -n production \
  CIRCUIT_BREAKER_STATUS=active
```

---

#### Step 2: Notify Stakeholders

```bash
# Post to #ops-alerts Slack
slack-cli post --channel ops-alerts --message "
⚠️ **Rate Limit Alert: Circuit Breaker Activated**

**Provider:** Anthropic (Claude)
**Quota Usage:** 87% (1.74M / 2M tokens)
**Status:** Flows paused until quota reset (23:59 UTC)

**Impact:**
- New flows: Paused
- In-flight flows: Completing normally
- ETA for resume: <X> hours (quota reset)

**On-Call:** @sre-oncall
**Next Update:** +30 min"

# Email Business persona (budget/cost owner)
echo "Circuit breaker activated due to rate limit exhaustion.
Provider: Anthropic
Quota: 87% used (1.74M / 2M tokens)
Flows paused until quota reset.

Options:
1. Wait for quota reset (23:59 UTC, <X> hours)
2. Request emergency quota increase (contact provider, ETA 2-4h)
3. Route to alternate providers (OpenAI, Google)

Recommendation: <recommendation based on situation>

SRE Team" | \
mail -s "⚠️ Rate Limit: Circuit Breaker Activated" business@company.com,product@company.com
```

---

### Short-Term Response (5-30 Minutes)

#### Option 1: Wait for Quota Reset (Low Urgency)

**When to use:**
- Time until quota reset <6 hours
- No critical flows blocked
- Alternate providers available

```bash
# Calculate time to quota reset
RESET_TIME=$(blocks quota show --provider anthropic --format json | jq -r '.reset_time')
CURRENT_TIME=$(date -u +%s)
HOURS_UNTIL_RESET=$(( ($RESET_TIME - $CURRENT_TIME) / 3600 ))

echo "Quota resets in $HOURS_UNTIL_RESET hours"

# Monitor quota usage until reset
watch -n 300 'blocks quota show --provider anthropic'

# When quota resets, circuit breaker auto-deactivates
# Verify:
kubectl logs deployment/flowengine -n production --tail=20 | grep "Circuit breaker deactivated"
```

---

#### Option 2: Route to Alternate Providers (Medium Urgency)

**When to use:**
- One provider exhausted, others have headroom
- Cannot wait for quota reset

```bash
# Check alternate provider availability
blocks quota show --all-providers

# Example:
# Anthropic: 87% (exhausted) ❌
# OpenAI: 73% (27% headroom) ✅
# Google: 70% (30% headroom) ✅

# Disable exhausted provider, route to alternates
kubectl set env deployment/flowengine -n production \
  DISABLE_PROVIDERS=anthropic \
  FALLBACK_MODEL=gpt-4-turbo  # OpenAI
  CONTEXT_MODEL=gemini-pro    # Google (cheaper)

# Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production

# Deactivate circuit breaker (manual override)
kubectl set env deployment/flowengine -n production \
  CIRCUIT_BREAKER_STATUS=inactive

# Monitor alternate provider usage
watch -n 60 'blocks quota show --provider openai,google'

# Re-enable Anthropic after quota reset
```

---

#### Option 3: Request Emergency Quota Increase (High Urgency)

**When to use:**
- Critical flows blocked
- All providers approaching limits
- Cannot wait for quota reset

**Anthropic Emergency Contact:**

```bash
# Email template
cat > /tmp/quota_increase_request.txt <<EOF
Subject: URGENT: Emergency Quota Increase Request

To: support@anthropic.com
CC: business@company.com

Hello Anthropic Support,

We are experiencing a production outage due to quota exhaustion and request an emergency quota increase.

**Account Details:**
- Account ID: <account_id>
- API Key: <key_prefix>***
- Current Quota: 2M tokens/day

**Requested Quota:**
- Temporary Increase: 4M tokens/day (2× current)
- Duration: 24 hours (until <date>)

**Justification:**
- Unexpected load spike: 87% quota used in 18 hours (normal: 75% in 24h)
- Root Cause: <brief description, e.g., "Batch onboarding of 5 new repos">
- Business Impact: <impact, e.g., "30 critical compliance flows blocked">

**Contact:**
- Primary: <sre_oncall_phone>
- Secondary: <business_persona_email>

We appreciate your urgent assistance. Please confirm increase within 2 hours if possible.

Thank you,
<Your Name>
SRE Team
EOF

# Send email
mail -s "URGENT: Emergency Quota Increase" support@anthropic.com < /tmp/quota_increase_request.txt

# Expected response time: 2-4 hours (business hours), 8-12 hours (after hours)
```

**OpenAI Emergency Contact:**

```bash
# Via support portal: https://help.openai.com
# Or account rep (if enterprise customer)
```

**Google Emergency Contact:**

```bash
# Via GCP Console: Support → Create Case → Priority: P1
# Or account rep (if enterprise customer)
```

---

### Long-Term Response (1-4 Hours)

#### Step 1: Analyze Root Cause

```bash
# Generate quota usage report
blocks quota report \
  --last 24h \
  --breakdown-by repo,hour,provider \
  --output /tmp/quota_usage_$(date +%Y%m%d).md

# Review report
cat /tmp/quota_usage_$(date +%Y%m%d).md

# Identify:
# 1. Which repos consumed most tokens?
# 2. What time did spike occur?
# 3. Was there a triggering event (onboarding, batch job, etc.)?
# 4. Were retries a factor?
```

---

#### Step 2: Optimize Token Usage

**Enable Context Pruning (if not enabled):**

```bash
# Check global setting
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="CONTEXT_PRUNING_ENABLED")].value}'

# If "false" or empty, enable
kubectl set env deployment/flowengine -n production \
  CONTEXT_PRUNING_ENABLED=true \
  CONTEXT_MAX_SIZE_KB=180

# Expected impact: -15% token usage (per pilot data)
```

**Optimize Model Routing:**

```bash
# Use cheaper models for context retrieval
kubectl edit configmap model-routing-config -n production

# Change:
# context_retrieval: claude-sonnet-4-5  # 45K tokens, expensive
# To:
# context_retrieval: gemini-pro         # 20K tokens, 55% cheaper

# Expected impact: -20% overall token usage
```

**Reduce Retry Attempts:**

```bash
# Check retry config
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="MAX_RETRY_ATTEMPTS")].value}'

# If >2, reduce to 2 (pilot baseline)
kubectl set env deployment/flowengine -n production \
  MAX_RETRY_ATTEMPTS=2

# For rate limit failures specifically, disable retries (prevents retry storm)
kubectl set env deployment/flowengine -n production \
  RETRY_ON_RATE_LIMIT=false

# Expected impact: -10% token usage (if retry storm occurring)
```

---

#### Step 3: Implement Quota Monitoring

**Set up proactive alerts (if not configured):**

```yaml
# File: quota-alerts.yaml
groups:
  - name: quota_monitoring
    interval: 15m
    rules:
      # Alert at 75% (before circuit breaker)
      - alert: QuotaUsage75Percent
        expr: |
          sum(increase(flowengine_model_tokens_total[1d])) /
          scalar(flowengine_model_quota_total) > 0.75
        for: 30m
        labels:
          severity: info
        annotations:
          summary: "Quota usage >75% (circuit breaker at 85%)"
          description: "Consider optimizing token usage or requesting increase"

      # Alert at 85% (circuit breaker threshold)
      - alert: QuotaUsage85Percent
        expr: |
          sum(increase(flowengine_model_tokens_total[1d])) /
          scalar(flowengine_model_quota_total) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker threshold reached (85%)"
          description: "Flows will be paused. Take action immediately."

      # Alert at 95% (approaching hard limit)
      - alert: QuotaUsage95Percent
        expr: |
          sum(increase(flowengine_model_tokens_total[1d])) /
          scalar(flowengine_model_quota_total) > 0.95
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Quota usage >95% - provider may enforce hard limit"
          description: "Request emergency quota increase immediately"
```

```bash
# Apply alerts
kubectl apply -f quota-alerts.yaml -n monitoring

# Test alert firing
blocks test alert --alert QuotaUsage75Percent
```

---

## Prevention

### Pre-Phase 6/7 Quota Validation

**Before expanding to 10 repos (Phase 6) or 50 repos (Phase 7):**

```bash
# Calculate required quota
PILOT_TOKENS_PER_DAY=$(blocks metrics query --metric model_tokens_total --last 7d --aggregation avg)
EXPANSION_FACTOR=10  # Phase 6: 10 repos vs 1 pilot repo

REQUIRED_QUOTA=$(echo "$PILOT_TOKENS_PER_DAY * $EXPANSION_FACTOR * 1.3" | bc)  # +30% buffer

echo "Pilot avg: $PILOT_TOKENS_PER_DAY tokens/day"
echo "Required for Phase 6: $REQUIRED_QUOTA tokens/day (with 30% buffer)"

# Compare to requested quota increase
# Phase 6 target: 2M tokens/day Anthropic
# If required > target, request higher quota before expansion
```

---

### Circuit Breaker Best Practices

**Configure circuit breaker (default settings):**

```yaml
env:
  - name: ENABLE_CIRCUIT_BREAKER
    value: "true"
  - name: CIRCUIT_BREAKER_THRESHOLD
    value: "85"  # Pause at 85% quota
  - name: CIRCUIT_BREAKER_BEHAVIOR
    value: "pause"  # Options: pause, throttle, route_alternate

# "pause": Stop all new flows (safest, prevents quota overrun)
# "throttle": Reduce flow rate by 50% (allows some flows to continue)
# "route_alternate": Disable exhausted provider, use alternates
```

---

### Daily Quota Monitoring

**Automated daily report (9 AM standup):**

```bash
# Generate daily quota report
blocks quota report \
  --last 24h \
  --format markdown \
  > /tmp/daily_quota_$(date +%Y%m%d).md

# Email to Business + SRE
cat /tmp/daily_quota_$(date +%Y%m%d).md | \
mail -s "Daily Quota Report - $(date +%Y-%m-%d)" \
  business@company.com,sre-oncall@company.com

# Report includes:
# - Current usage vs quota (all 3 providers)
# - Trend: Usage increasing/decreasing?
# - Projection: Will quota be sufficient for next 7 days?
# - Recommendations: Request increase, optimize usage, etc.
```

---

## Recovery Validation

**After circuit breaker deactivation:**

```bash
# Verify quota reset
blocks quota show --all-providers

# Expected: All providers <50% usage (quota reset at midnight UTC)

# Test flow execution
blocks generate \
  --repo compliance-service \
  --family compliance \
  --block-type attestation \
  --config test.json \
  --output /tmp/test/

# Expected: Flow completes successfully, no rate limit errors

# Monitor for 1 hour
watch -n 300 'blocks quota show --provider anthropic'

# Expected: Usage increasing linearly (normal flow execution)
```

---

## Metrics & SLOs

**Quota Usage SLO:**
- Daily peak usage: <85% (circuit breaker threshold)
- Sustained usage: <75% (healthy headroom)
- Rate limit error rate: <0.1% of flows

**Circuit Breaker Activation:**
- Target frequency: 0 per month
- Acceptable: 1 per month (with mitigation <1 hour)
- Critical: >2 per month (indicates chronic underprovisioning)

**Pilot Performance (Baseline):**
- Peak quota usage: 78% Anthropic, 68% OpenAI, 62% Gemini ✅
- Circuit breaker activations: 0 ✅
- Rate limit errors: 0 ✅

---

## Escalation

### L1: SRE On-Call (Auto-Response)
- **Action:** Circuit breaker activates automatically at 85%
- **SLA:** <1 minute (automated)

### L2: SRE On-Call (Manual Intervention)
- **Action:** Route to alternate providers, optimize token usage
- **SLA:** <30 minutes

### L3: Business Persona + Provider Support
- **Action:** Request emergency quota increase
- **SLA:** 2-4 hours (provider response time)

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-CORE-002:** Timeout Recovery (`planning/30_design/runbooks/timeout_recovery.md`)
- **RB-LAUNCH-004:** Budget Breach Response (`planning/60_launch/runbooks/budget_breach.md`)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE Persona | Initial version for Phase 6/7 rate limit management |

---

**Status:** ✅ Ready for Phase 6 (circuit breaker validated in stress testing)
**Next Review:** Post-Phase 6 retrospective (Dec 1, 2025)
**Maintained By:** SRE Persona

---

**Key Principle:** Proactive quota monitoring prevents circuit breaker activation. Target: <75% sustained usage.
