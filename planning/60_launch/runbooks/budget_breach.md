# Runbook: Budget Breach Response

**Runbook ID:** RB-LAUNCH-004
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** Business Persona + SRE
**Severity:** HIGH (Cost Control)

---

## Purpose

This runbook provides procedures for detecting, responding to, and preventing budget breaches during Multi-LLM Orchestrator expansion phases.

**Definition of Budget Breach:**
- Daily spend exceeds $50/day (Phase 6 budget), OR
- Weekly spend exceeds $350/week (Phase 6 budget), OR
- Single repo exceeds $5/feature average, OR
- Monthly projection exceeds $2,000 (Phase 6: $1,500 budget)

**Target Audience:** Business persona, SRE on-call, Product lead

---

## Budget Baseline & Thresholds

### Phase 6 Budget (10-Repo Soak, Nov 16-30)

**Daily Budget:**
- **Target:** $35/day (10 repos × 2 features/day × $1.75/feature)
- **Soft Limit:** $50/day (143% of target, alert threshold)
- **Hard Limit:** $75/day (214% of target, circuit breaker)

**Weekly Budget:**
- **Target:** $245/week
- **Soft Limit:** $350/week
- **Hard Limit:** $525/week

**Per-Repo Budget:**
- **Target:** $3.50/day per repo (2 features/day × $1.75/feature)
- **Soft Limit:** $5/day per repo
- **Hard Limit:** $10/day per repo (rollback repo)

**Total Phase 6 Budget (15 days):**
- **Allocated:** $1,500
- **Reserve:** $500 (contingency)
- **Total Available:** $2,000

---

### Phase 7 Budget (Org-Wide Rollout, Dec 9-20)

**Daily Budget:**
- **Target:** $200/day (50 repos × 3 features/day × $1.33/feature)
- **Soft Limit:** $300/day
- **Hard Limit:** $450/day

**Total Phase 7 Budget (12 days):**
- **Allocated:** $6,000
- **Reserve:** $2,000 (contingency)
- **Total Available:** $8,000

---

## Detection

### Automated Monitoring

**Grafana Alert: "Daily Budget Threshold Exceeded"**

```yaml
alert: DailyBudgetThresholdExceeded
expr: |
  sum(increase(flowengine_flow_cost_dollars_total[1d])) > 50
for: 1h
labels:
  severity: warning
  runbook: RB-LAUNCH-004
annotations:
  summary: "Daily spend exceeded soft limit ($50)"
  description: "Current: ${{ $value | humanize }}, Budget: $50/day"
```

**Alert Channels:**
- Slack: #ops-alerts (soft limit)
- Email: business@company.com, sre-oncall@company.com
- PagerDuty: Only for hard limit ($75/day)

---

**Grafana Alert: "Per-Repo Budget Exceeded"**

```yaml
alert: PerRepoBudgetExceeded
expr: |
  sum by (repo) (increase(flowengine_flow_cost_dollars_total[1d])) > 5
for: 2h
labels:
  severity: warning
  repo: "{{ $labels.repo }}"
annotations:
  summary: "Repo {{ $labels.repo }} exceeded budget"
  description: "Daily spend: ${{ $value | humanize }}, Budget: $5/day"
```

---

### Manual Monitoring

**Daily Budget Check (9 AM Standup):**

```bash
# Generate daily cost report
blocks metrics export \
  --metric flow_cost \
  --last-24h \
  --group-by repo \
  --format markdown \
  > /tmp/daily_cost_$(date +%Y%m%d).md

# View report
cat /tmp/daily_cost_$(date +%Y%m%d).md

# Expected output:
# | Repo | Flows | Avg Cost | Total Cost | Status |
# |------|-------|----------|------------|--------|
# | compliance-service | 2 | $1.51 | $3.02 | ✅ |
# | financial-reporting | 3 | $1.68 | $5.04 | ✅ |
# | customer-analytics | 2 | $1.72 | $3.44 | ✅ |
# | ... | ... | ... | ... | ... |
# | **TOTAL** | **22** | **$1.64** | **$36.08** | ✅ |

# Check against budget
DAILY_TOTAL=$(cat /tmp/daily_cost_$(date +%Y%m%d).md | grep "TOTAL" | awk '{print $7}' | tr -d '$')
if (( $(echo "$DAILY_TOTAL > 50" | bc -l) )); then
  echo "⚠️ BUDGET BREACH: Daily spend $${DAILY_TOTAL} exceeds soft limit ($50)"
else
  echo "✅ Within budget: Daily spend $${DAILY_TOTAL} / $50"
fi
```

---

## Triage & Investigation (First 15 Minutes)

### Step 1: Identify High-Cost Flows (5 minutes)

```bash
# Query top 10 most expensive flows (last 24h)
blocks metrics query \
  --metric flow_cost \
  --last 24h \
  --sort desc \
  --limit 10 \
  --format table

# Example output:
# | Flow ID | Repo | Duration | Cost | Models Used | Status |
# |---------|------|----------|------|-------------|--------|
# | flow-abc123 | customer-analytics | 145s | $8.42 | Claude×3, GPT-4×2 | ❌ Failed (retry) |
# | flow-def456 | risk-engine | 118s | $6.21 | Claude×2, GPT-4×3 | ✅ Success |
# | flow-ghi789 | financial-reporting | 132s | $5.88 | Claude×2, GPT-4×2, Gemini×1 | ✅ Success |

# Identify outliers:
# - Failed flows with retries (multiply cost by retry count)
# - Large code generation (>10K lines, high token usage)
# - Inefficient model selection (using expensive models for simple tasks)
```

---

### Step 2: Analyze Cost Drivers (5 minutes)

**Common Cost Drivers:**

#### Driver 1: Failed Flows with Retries

```bash
# Count retry attempts (last 24h)
blocks metrics query \
  --metric flow_retries_total \
  --last 24h \
  --group-by repo \
  --sort desc

# If any repo >3 retries/day, investigate failure cause
# Reference: RB-CORE-001 (flow_failure_response.md)
```

#### Driver 2: Context Size (Token Usage)

```bash
# Average context size by repo
blocks metrics query \
  --metric flow_context_size_bytes \
  --last 24h \
  --group-by repo \
  --aggregation avg

# Target: <180KB avg (pilot baseline: 156KB)
# If any repo >200KB avg, context pruning needed
```

#### Driver 3: Model Selection

```bash
# Cost breakdown by model provider
blocks metrics query \
  --metric flow_cost \
  --last 24h \
  --group-by model_provider \
  --format pie

# Expected distribution (pilot baseline):
# - Claude (Sonnet 4.5): 45% ($0.72/flow)
# - GPT-4 Turbo: 38% ($0.61/flow)
# - Gemini Pro: 17% ($0.27/flow)

# If Claude >60% or GPT-4 >50%, model routing suboptimal
```

#### Driver 4: Block Complexity

```bash
# Average flow duration by repo (proxy for complexity)
blocks metrics query \
  --metric flow_duration_seconds \
  --last 24h \
  --group-by repo \
  --aggregation avg

# Target: <120s avg (pilot baseline: 106s)
# If any repo >150s avg, large feature or inefficient block design
```

---

### Step 3: Determine Breach Severity (5 minutes)

**Classify Breach:**

#### Level 1: Minor Overage (Acceptable)
- Daily spend: $50-60 (120% of budget)
- Cause: Natural variance, one-time spike
- **Action:** Monitor, no intervention needed

#### Level 2: Moderate Overage (Alert)
- Daily spend: $60-75 (150% of budget)
- Cause: Multiple high-cost flows, retries, inefficient model use
- **Action:** Investigate + optimize (this runbook)

#### Level 3: Severe Overage (Circuit Breaker)
- Daily spend: >$75 (>150% of budget)
- Cause: Runaway cost (bug, misconfiguration, attack)
- **Action:** Immediate throttling or rollback

---

## Response Actions

### Level 1: Monitor (No Action)

```bash
# Log overage for tracking
echo "$(date +%Y-%m-%d),Minor Overage,$DAILY_TOTAL,$50,Natural variance" \
  >> planning/60_launch/evidence/budget_log.csv

# Continue monitoring at next standup (9 AM next day)
```

---

### Level 2: Investigate + Optimize (15-30 Minutes)

#### Action 1: Enable Context Pruning (If Not Enabled)

```bash
# Check if context pruning enabled globally
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="CONTEXT_PRUNING_ENABLED")].value}'

# If "false" or empty, enable globally
kubectl set env deployment/flowengine -n production \
  CONTEXT_PRUNING_ENABLED=true \
  CONTEXT_MAX_SIZE_KB=180

# OR enable per high-cost repo
blocks config set --repo <high_cost_repo> context-pruning true
blocks config set --repo <high_cost_repo> context-max-size-kb 180

# Expected impact: -15% cost (per pilot learnings)
```

---

#### Action 2: Optimize Model Routing

```bash
# Analyze current model routing
blocks metrics query \
  --metric model_selection \
  --last 24h \
  --group-by model,task_type

# Optimize routing strategy:
# - Use Gemini Pro for context retrieval (cheapest: $0.27/flow)
# - Use GPT-4 Turbo for implementation (balanced: $0.61/flow)
# - Use Claude Sonnet for architecture/review (highest quality but expensive: $0.72/flow)

# Update routing config
kubectl edit configmap model-routing-config -n production

# Example optimization:
# before:
#   context_retrieval: claude-sonnet-4-5
#   implementation: gpt-4-turbo
#   review: claude-sonnet-4-5
#
# after:
#   context_retrieval: gemini-pro  # Save 63% on context retrieval
#   implementation: gpt-4-turbo
#   review: claude-sonnet-4-5

# Restart FlowEngine to apply changes
kubectl rollout restart deployment/flowengine -n production

# Expected impact: -20% cost (if context retrieval 40% of flow time)
```

---

#### Action 3: Reduce Retry Attempts

```bash
# Check current retry config
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="MAX_RETRY_ATTEMPTS")].value}'

# If >3 retries, reduce to 2 (pilot baseline)
kubectl set env deployment/flowengine -n production \
  MAX_RETRY_ATTEMPTS=2

# Review retry causes (prevent retries at source)
blocks metrics query \
  --metric flow_retry_reason \
  --last 24h \
  --group-by reason

# Common reasons:
# - timeout: Enable context pruning
# - rate_limit: Enable circuit breaker
# - validation: Fix schema/config
```

---

#### Action 4: Throttle High-Cost Repo

**If single repo responsible for >40% of daily cost:**

```bash
# Identify high-cost repo
HIGH_COST_REPO=$(blocks metrics query \
  --metric flow_cost \
  --last 24h \
  --group-by repo \
  --sort desc \
  --limit 1 \
  --format csv | tail -1 | cut -d',' -f1)

# Set per-repo daily budget limit (circuit breaker)
blocks config set --repo $HIGH_COST_REPO daily-budget-limit 5

# When limit reached, pause new flows for repo
# Repo owner notified via Slack + email

# Notify repo owner
slack-cli dm --user <repo_owner> --message "
⚠️ **Budget Alert: $HIGH_COST_REPO**

Your repo exceeded the daily budget limit ($5/day).

**Current Spend:** $<amount>
**Flows Executed:** <count>
**Avg Cost:** $<avg>

**Action Taken:** New flows paused until tomorrow (9 AM PST).

**Recommendations:**
1. Review high-cost flows: planning/60_launch/evidence/cost_breakdown.md
2. Enable context pruning: blocks config set context-pruning true
3. Optimize feature size (smaller blocks = lower cost)

**Questions?** #blocks-help Slack or office hours (Thu 2-3 PM)

SRE Team"
```

---

### Level 3: Circuit Breaker / Rollback (Immediate)

**If daily spend >$75 (hard limit) OR weekly projection >$525:**

#### Option 1: Enable Global Circuit Breaker

```bash
# Pause all new flows across all repos
kubectl set env deployment/flowengine -n production \
  ENABLE_CIRCUIT_BREAKER=true \
  CIRCUIT_BREAKER_THRESHOLD=0  # Immediate pause (override 85% default)

# Verify circuit breaker active
kubectl logs deployment/flowengine -n production --tail=20 | grep "Circuit breaker"
# Expected: "Circuit breaker activated: all flows paused"

# Notify stakeholders
slack-cli post --channel ops-alerts --message "
🚨 **BUDGET BREACH: Circuit Breaker Activated**

Daily spend exceeded hard limit ($75).

**Current Spend:** $<amount> ({{ percent }}% over budget)
**Action:** All orchestrator flows paused until investigation complete.

**Team Mobilized:**
- Business: @business-persona
- SRE: @sre-oncall
- Product: @product-lead

**ETA for Update:** 30 minutes"
```

**Incident Response:**

```bash
# Follow mass failure runbook for investigation
# Reference: RB-LAUNCH-005 (mass_failure.md)

# Investigate:
# 1. Is this a legitimate spike (large batch of features)?
# 2. Is this a bug (infinite retry loop, misconfigured model)?
# 3. Is this an attack (malicious API usage)?

# If legitimate spike:
# - Request emergency budget increase (Business approval)
# - Disable circuit breaker after approval

# If bug/attack:
# - Execute rollback to pilot (RB-LAUNCH-002)
# - Fix issue in staging, re-deploy
```

---

#### Option 2: Rollback to Pilot Scope

**If budget breach cannot be resolved within 1 hour:**

```bash
# Execute rollback procedure
# Reference: RB-LAUNCH-002 (rollback_to_pilot.md)

# Rationale:
# - Pilot repo cost: $1.60/feature avg (well within budget)
# - Pilot daily cost: $3.20/day (for 2 features/day)
# - Provides time to investigate root cause without ongoing cost

# Log rollback decision
echo "$(date +%Y-%m-%d),Rollback to Pilot,Daily spend $DAILY_TOTAL exceeded $75 hard limit,Business + SRE decision" \
  >> planning/60_launch/evidence/budget_breach_log.csv
```

---

## Prevention

### Pre-Expansion Budget Validation

**Before Phase 6 (10-repo) or Phase 7 (50-repo) expansion:**

```bash
# Validate vendor quotas approved
# Expected Phase 6 quotas:
# - Anthropic: 2M tokens/day
# - OpenAI: 1.5M tokens/day
# - Google: 1M tokens/day

# Calculate budget headroom
PHASE6_DAILY_BUDGET=50
PILOT_DAILY_COST=$(blocks metrics query --metric flow_cost --last 7d --aggregation avg)
EXPANSION_FACTOR=10  # 10 repos vs 1 pilot repo

PROJECTED_DAILY_COST=$(echo "$PILOT_DAILY_COST * $EXPANSION_FACTOR" | bc)

if (( $(echo "$PROJECTED_DAILY_COST > $PHASE6_DAILY_BUDGET" | bc -l) )); then
  echo "⚠️ WARNING: Projected daily cost ($PROJECTED_DAILY_COST) exceeds budget ($PHASE6_DAILY_BUDGET)"
  echo "Recommendation: Delay expansion or request budget increase"
else
  echo "✅ Budget validated: Projected $PROJECTED_DAILY_COST / $PHASE6_DAILY_BUDGET daily"
fi
```

---

### Cost Optimization Checklist (Pre-Launch)

**Verify all cost controls enabled:**

- [ ] Context pruning enabled globally (`CONTEXT_PRUNING_ENABLED=true`)
- [ ] Context size limit set (`CONTEXT_MAX_SIZE_KB=180`)
- [ ] Circuit breaker configured (`CIRCUIT_BREAKER_THRESHOLD=85`)
- [ ] Retry limit set (`MAX_RETRY_ATTEMPTS=2`)
- [ ] Model routing optimized (Gemini for context, GPT-4 for implementation)
- [ ] Per-repo budget alerts configured (Grafana)
- [ ] Daily budget review scheduled (9 AM standup)

---

### Weekly Budget Review (Every Friday)

```bash
# Generate weekly cost report
blocks metrics export \
  --metric flow_cost \
  --last 7d \
  --group-by repo \
  --format pdf \
  > /tmp/weekly_cost_report_$(date +%Y%m%d).pdf

# Review with Business persona
# - Actual vs budget: $<actual> / $350 weekly
# - Trends: Cost increasing/decreasing?
# - Outliers: Any repos >$5/day avg?
# - Recommendations: Optimization opportunities

# If weekly cost >$350 (soft limit):
# - Investigate top 3 high-cost repos
# - Apply optimizations (context pruning, model routing)
# - Escalate to Business persona for budget increase (if justified)
```

---

## Cost Reporting

### Daily Cost Report (Automated)

**Email Recipients:** Business persona, Product lead, SRE on-call

**Email Template:**

```
Subject: Multi-LLM Orchestrator - Daily Cost Report ($(date +%Y-%m-%d))

**Daily Summary:**
- Total Cost: $<amount>
- Budget: $50/day (Phase 6)
- Status: <✅ Within budget / ⚠️ Over budget>
- Flows Executed: <count>
- Avg Cost/Flow: $<avg>

**Top 3 Repos by Cost:**
1. <repo_name>: $<amount> (<count> flows)
2. <repo_name>: $<amount> (<count> flows)
3. <repo_name>: $<amount> (<count> flows)

**Cost Breakdown by Model:**
- Claude Sonnet 4.5: $<amount> ({{ percent }}%)
- GPT-4 Turbo: $<amount> ({{ percent }}%)
- Gemini Pro: $<amount> ({{ percent }}%)

**Week-to-Date:** $<amount> / $350 weekly budget

**Full Report:** planning/60_launch/evidence/daily_cost_$(date +%Y%m%d).md

---
Automated Report | Multi-LLM Orchestrator Cost Monitoring
```

---

### Monthly ROI Report (Manual)

**Due:** First Friday of each month

**Template:** `planning/50_pilot/evidence/biz/monthly_roi_report_<YYYY-MM>.md`

```markdown
# Monthly ROI Report: <Month YYYY>

**Prepared By:** Business Persona
**Date:** <date>

## Cost Summary

**Actual Spend:** $<amount>
**Budgeted:** $<amount>
**Variance:** <+/- amount> (<+/- percent>%)

## ROI Calculation

**Baseline (Manual Development):**
- Avg time per feature: 12.5 days
- Avg cost per feature: $200 (engineer time)
- Features delivered: <count>
- **Total baseline cost:** $<amount>

**Orchestrator (AI-Assisted):**
- Avg time per feature: 8.2 days
- Avg cost per feature: $1.60 (model API + infra)
- Features delivered: <count>
- **Total orchestrator cost:** $<amount>

**ROI:** <X>× return ($<benefit> / $<investment>)

## Cost Trends

<Graph: Daily cost over time>
<Graph: Cost per feature by repo>
<Graph: Cost breakdown by model provider>

## Recommendations

1. <Recommendation 1>
2. <Recommendation 2>
3. <Recommendation 3>
```

---

## Escalation

### Budget Increase Request

**If sustained cost >$50/day justified (e.g., 15 repos instead of 10):**

```bash
# Prepare budget increase request
# Template: planning/60_launch/budget_increase_request.md

# Required data:
# - Justification (more repos, higher feature velocity, etc.)
# - Historical cost data (past 2 weeks)
# - Projected cost (next 2 weeks)
# - ROI validation (still ≥3× ROI at higher cost?)

# Approvers:
# - Business Persona (primary)
# - VP Engineering (secondary)
# - Finance (final approval if >$5K increase)
```

---

## Metrics & SLOs

**Budget Compliance:**
- Daily spend: ≤$50 (Phase 6), ≤$300 (Phase 7)
- Weekly spend: ≤$350 (Phase 6), ≤$2,100 (Phase 7)
- Cost variance: ±20% of budget (acceptable)

**Cost Efficiency:**
- Avg cost per feature: <$2.00 (Phase 6), <$1.50 (Phase 7)
- Cost trend: Decreasing over time (learning curve)

**Pilot Performance (Baseline):**
- Daily cost: $3.20/day (2 features)
- Avg cost per feature: $1.60
- Cost variance: ±18%

---

## Related Runbooks

- **RB-LAUNCH-002:** Rollback to Pilot (`planning/60_launch/runbooks/rollback_to_pilot.md`)
- **RB-LAUNCH-005:** Mass Failure Response (`planning/60_launch/runbooks/mass_failure.md`)
- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | Business + SRE | Initial version for Phase 6/7 cost control |

---

**Status:** ✅ Ready for Phase 6 (budget thresholds validated)
**Next Review:** Weekly (every Friday at budget review)
**Maintained By:** Business Persona + SRE

---

**Cost Control Philosophy:** Optimize for ROI, not minimum cost. Target: ≥3× ROI sustained at scale.
