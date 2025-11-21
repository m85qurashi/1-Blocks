# Runbook: Repository Onboarding

**Runbook ID:** RB-LAUNCH-001
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE + Product
**Applies To:** Phase 6 (10-repo soak) & Phase 7 (org-wide rollout)

---

## Purpose

This runbook provides step-by-step procedures for onboarding new repositories to the Multi-LLM Orchestrator during Phase 6 (10-repo soak observation) and Phase 7 (org-wide rollout).

**Target Audience:** SRE on-call, Product team, repo owners

---

## Overview

**Onboarding Timeline:** 30-60 minutes per repository
**Prerequisites:** Training Module 1 completed by repo owner
**Success Criteria:** First flow execution within 24h of onboarding

---

## Pre-Onboarding Checklist

### 1. Validate Repository Eligibility

**Criteria (All Must Be Met):**

- [ ] Repository has CI/CD pipeline (GitHub Actions, Jenkins, etc.)
- [ ] Repository owner completed Training Module 1 (CLI Quick-Start)
- [ ] Repository has at least 1 feature planned for orchestrator use
- [ ] Repository has API key access (Anthropic, OpenAI, Google)
- [ ] Repository is not on exclusion list (security-sensitive repos)

**Validation Commands:**

```bash
# Check if repo has CI/CD
gh repo view <org>/<repo> | grep "workflows"

# Check training completion
blocks training status --user <repo_owner_email>
# Expected: Module 1 completed, ≥80% quiz score

# Check repo status
blocks config show --repo <repo_name>
# Expected: eligible: true
```

**If Ineligible:**
- Missing training: Direct owner to https://training.blocks-orchestrator.com
- No CI/CD: Defer onboarding until CI/CD configured
- API key issues: Escalate to IT (#it-help)

---

### 2. Communicate with Repo Owner

**Email Template:**

```
Subject: Multi-LLM Orchestrator Onboarding - <repo_name>

Hi <owner_name>,

Congratulations! Your repository <repo_name> has been selected for the Multi-LLM
Orchestrator expansion (Phase 6).

**Next Steps:**
1. Schedule 30-min kickoff call (Calendar link: https://cal.company.com/blocks-onboarding)
2. Review onboarding guide: planning/60_launch/training/guides/01_cli_quickstart.md
3. Prepare first use case (feature to implement with orchestrator)

**Expected Timeline:**
- Kickoff call: Within 48h
- First flow execution: Within 24h of onboarding
- Ongoing support: #blocks-help Slack channel

**Contact:**
- SRE On-Call: sre-oncall@company.com
- Product Lead: product@company.com

Looking forward to working with you!

Best,
[Your Name]
SRE Team
```

**Kickoff Call Agenda (30 minutes):**
1. Overview: Orchestrator value prop (3.6× ROI, -34% cycle time) — 5 min
2. Demo: First flow execution (Basel-I compliance block) — 10 min
3. Onboarding: Install CLI, configure repo — 10 min
4. Q&A: Troubleshooting, next steps — 5 min

---

## Onboarding Procedure

### Phase 1: Environment Setup (15 minutes)

#### Step 1: Install Orchestrator CLI

**On Repo Owner's Machine:**

```bash
# Install CLI
pip install blocks-orchestrator
# OR
npm install -g @blocks/orchestrator

# Verify installation
blocks --version
# Expected: v1.2.0 or higher

# Configure API keys
blocks config set-api-key anthropic $ANTHROPIC_API_KEY
blocks config set-api-key openai $OPENAI_API_KEY
blocks config set-api-key google $GOOGLE_API_KEY

# Verify configuration
blocks config show
# Expected: All 3 API keys configured (masked)
```

**If Installation Fails:**
- Python version check: `python --version` (required: ≥3.9)
- Node.js version check: `node --version` (required: ≥16.0)
- Permission issues: Use `sudo` or virtual environment
- Escalate: #blocks-help Slack

---

#### Step 2: Repository Registration

**By SRE On-Call:**

```bash
# Register repository in orchestrator
blocks repo register \
  --name <repo_name> \
  --org <org_name> \
  --owner <owner_email> \
  --ci-pipeline github-actions \
  --phase phase-6

# Verify registration
blocks repo show <repo_name>
# Expected:
# - status: active
# - phase: phase-6
# - owner: <owner_email>
# - quality_gates: enabled (strict mode)

# Add repo to allowlist (FlowEngine deployment)
kubectl set env deployment/flowengine \
  REPO_ALLOWLIST=$(kubectl get deployment/flowengine -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="REPO_ALLOWLIST")].value}'),<repo_name>

# Verify allowlist
kubectl get deployment/flowengine -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="REPO_ALLOWLIST")].value}'
# Expected: compliance-service,<repo_name>,...
```

**If Registration Fails:**
- Duplicate repo name: Choose unique name or namespace
- Database error: Check TaskDB connection (`kubectl logs deployment/flowengine`)
- Escalate: Page Engineering TL

---

#### Step 3: CI/CD Integration

**GitHub Actions Integration (Most Common):**

Create `.github/workflows/blocks-orchestrator.yml`:

```yaml
name: Blocks Orchestrator

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  orchestrator-flow:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Install Blocks CLI
        run: |
          pip install blocks-orchestrator

      - name: Configure API Keys
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          blocks config set-api-key anthropic $ANTHROPIC_API_KEY
          blocks config set-api-key openai $OPENAI_API_KEY
          blocks config set-api-key google $GOOGLE_API_KEY

      - name: Run Orchestrator Flow
        run: |
          blocks generate \
            --family compliance \
            --block-type attestation \
            --config compliance-config.json \
            --output src/generated/

      - name: Verify Quality Gates
        run: |
          blocks verify \
            --path src/generated/ \
            --strict

      - name: Upload Context Bundle
        if: success()
        run: |
          blocks context upload \
            --flow-id ${{ github.run_id }} \
            --repo ${{ github.repository }}
```

**Validate CI/CD Integration:**

```bash
# Trigger test workflow
gh workflow run blocks-orchestrator.yml --repo <org>/<repo>

# Monitor workflow
gh run list --workflow=blocks-orchestrator.yml --repo <org>/<repo>

# Check logs
gh run view <run_id> --repo <org>/<repo> --log
```

**If CI/CD Integration Fails:**
- Secrets not configured: Add API keys to GitHub repo secrets
- Workflow syntax error: Validate YAML with `yamllint`
- CLI install failure: Check Python/Node version in runner
- Escalate: #blocks-help Slack

---

### Phase 2: First Flow Execution (10 minutes)

#### Step 4: Execute First Flow (Live Demo)

**With Repo Owner:**

```bash
# Navigate to repo
cd /path/to/<repo_name>

# Create compliance configuration
cat > compliance-config.json <<EOF
{
  "regulation": "Basel-I",
  "jurisdiction": "US",
  "attestation_type": "capital_adequacy",
  "retention_years": 7
}
EOF

# Execute first flow
blocks generate \
  --family compliance \
  --block-type attestation \
  --config compliance-config.json \
  --output src/generated/ \
  --verbose

# Expected output:
# ✅ Flow completed successfully
# Duration: ~90s
# Cost: ~$1.60
# Quality Gates: 5/5 passed
# Context Bundle: s3://blocks-context/sha256-abc123...
```

**Verify Quality Gates:**

```bash
blocks verify --path src/generated/ --strict

# Expected:
# ✅ Contract Validation: 100% (JSON Schema valid)
# ✅ Unit Test Coverage: ≥90% (92.5%)
# ✅ Mutation Testing: ≥60% kill-rate (68.75%)
# ✅ Security Scan: 0 HIGH findings
# ✅ Logic Review: 0 BLOCKERs
```

**If First Flow Fails:**
- Timeout (>120s): Enable context pruning (`blocks config set context-pruning true`)
- API rate limit: Check quota (`blocks quota show`)
- Quality gate failure: Review report (`blocks verify --report`)
- Escalate: Use RB-CORE-001 (flow_failure_response.md)

---

#### Step 5: Validate Telemetry & Dashboards

**By SRE On-Call:**

```bash
# Check telemetry ingestion
curl -s https://grafana.company.com/api/datasources/proxy/1/api/v1/query \
  --data-urlencode 'query=flowengine_flow_duration_seconds{repo="<repo_name>"}' | jq

# Expected: 1 data point (first flow)

# Verify dashboard visibility
open https://grafana.company.com/d/flowengine-adoption?var-repo=<repo_name>

# Expected metrics:
# - Flows executed: 1
# - Success rate: 100%
# - Avg duration: ~90s
# - Avg cost: ~$1.60
```

**If Telemetry Missing:**
- Check OpenTelemetry agent: `kubectl logs deployment/otel-collector`
- Verify repo label: `blocks config show <repo_name>` (should have `telemetry: enabled`)
- Flush cache: `kubectl rollout restart deployment/otel-collector`
- Escalate: Page Data team (#data-alerts)

---

### Phase 3: Post-Onboarding (10 minutes)

#### Step 6: Configure Monitoring & Alerts

**By SRE On-Call:**

```bash
# Create repo-specific alert rules
cat > /tmp/alert_rules_<repo_name>.yml <<EOF
groups:
  - name: <repo_name>_alerts
    interval: 60s
    rules:
      - alert: FlowFailureRate
        expr: |
          rate(flowengine_flow_failures_total{repo="<repo_name>"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          repo: <repo_name>
        annotations:
          summary: "High flow failure rate in <repo_name>"
          description: "Failure rate: {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(flowengine_flow_duration_seconds_bucket{repo="<repo_name>"}[5m])
          ) > 120
        for: 10m
        labels:
          severity: warning
          repo: <repo_name>
        annotations:
          summary: "High P95 latency in <repo_name>"
          description: "P95 latency: {{ $value }}s (threshold: 120s)"

      - alert: HighCost
        expr: |
          rate(flowengine_flow_cost_dollars_total{repo="<repo_name>"}[1d]) > 5
        for: 1h
        labels:
          severity: info
          repo: <repo_name>
        annotations:
          summary: "High daily cost in <repo_name>"
          description: "Daily cost: ${{ $value }} (threshold: $5/day)"
EOF

# Apply alert rules
kubectl apply -f /tmp/alert_rules_<repo_name>.yml -n monitoring

# Verify alerts configured
kubectl get prometheusrule <repo_name>-alerts -n monitoring -o yaml
```

**Test Alert Firing:**

```bash
# Simulate failure (optional, for validation)
blocks test alert --repo <repo_name> --alert FlowFailureRate

# Check PagerDuty / Slack
# Expected: Alert notification received within 2 min
```

---

#### Step 7: Onboarding Completion Checklist

**By SRE + Repo Owner (Joint Review):**

- [ ] CLI installed and configured (API keys set)
- [ ] Repository registered in orchestrator
- [ ] CI/CD workflow integrated (GitHub Actions / Jenkins)
- [ ] First flow executed successfully (quality gates 5/5)
- [ ] Telemetry visible in Grafana dashboards
- [ ] Monitoring alerts configured (3 alerts: failure rate, latency, cost)
- [ ] Repo owner trained on troubleshooting (flow_failure_response.md)
- [ ] Repo owner joined #blocks-help Slack channel

**Document Onboarding:**

```bash
# Log onboarding completion
blocks repo update <repo_name> --status onboarded --onboarding-date $(date +%Y-%m-%d)

# Append to onboarding log
echo "$(date +%Y-%m-%d) | <repo_name> | <owner_email> | SUCCESS | First flow: 90s, $1.60" \
  >> planning/60_launch/evidence/onboarding_log.csv
```

---

## Post-Onboarding Support

### Week 1: Active Monitoring (Daily Standup)

**By SRE On-Call:**

```bash
# Daily report for newly onboarded repo
blocks metrics export \
  --repo <repo_name> \
  --last-24h \
  --format markdown \
  > /tmp/<repo_name>_daily_$(date +%Y%m%d).md

# Review report at 9 AM standup
cat /tmp/<repo_name>_daily_$(date +%Y%m%d).md

# Expected metrics:
# - Flows executed: 1-5/day
# - Success rate: ≥95%
# - P95 latency: <120s
# - Avg cost: <$2/feature
```

**Proactive Outreach:**

Send daily status email to repo owner for first 3 days:

```
Subject: <repo_name> Orchestrator Status - Day <N>

Hi <owner>,

Here's your daily orchestrator status for <repo_name>:

✅ Flows executed: <N>
✅ Success rate: <X>%
✅ Avg latency: <Y>s
✅ Avg cost: $<Z>

**Any issues?** Reply to this email or ping #blocks-help.

Best,
SRE Team
```

---

### Common Issues & Resolutions

#### Issue 1: Flow Timeout (>120s)

**Symptoms:**
- Flow fails with "timeout exceeded" error
- Logs show large context bundle (>200KB)

**Resolution:**

```bash
# Enable context pruning
blocks config set --repo <repo_name> context-pruning true
blocks config set --repo <repo_name> context-max-size-kb 180

# Retry flow
blocks generate --config <config.json> --retry
```

**Reference:** RB-CORE-002 (timeout_recovery.md)

---

#### Issue 2: Quality Gate Failure (BLOCKERs)

**Symptoms:**
- Flow completes but quality gates fail
- Logic review shows BLOCKER findings

**Resolution:**

```bash
# Review BLOCKER details
blocks verify --path src/generated/ --report --format json > blocker_report.json

# Common BLOCKERs:
# - Hardcoded credentials (BLOCKER-SEC-001)
# - SQL injection vulnerability (BLOCKER-SEC-002)
# - Missing error handling (BLOCKER-LOGIC-001)

# Escalate to Engineering TL for manual review
# Expected TTR: <30 min (per pilot results)
```

**Reference:** Training Module 3 (Quality & CI Gating)

---

#### Issue 3: High Cost (>$5/feature)

**Symptoms:**
- Daily cost exceeds $5 for single repo
- Cost dashboard shows spike

**Resolution:**

```bash
# Identify high-cost flows
blocks metrics query \
  --repo <repo_name> \
  --metric flow_cost \
  --sort desc \
  --limit 5

# Common causes:
# - Large code generation (>10K lines)
# - Multiple retries (context pruning disabled)
# - Model API inefficiency (wrong model selection)

# Optimize:
# - Use Gemini Pro for context (cheaper)
# - Enable circuit breaker (pause at 85% quota)
# - Tune block scope (smaller features)
```

**Reference:** RB-LAUNCH-004 (budget_breach.md)

---

## Rollback Procedure

**If Onboarding Causes Issues:**

### Emergency Rollback (Disable Repo)

```bash
# Disable orchestrator for repo
blocks repo disable <repo_name> --reason "Production issue, rolling back"

# Remove from allowlist
kubectl set env deployment/flowengine \
  REPO_ALLOWLIST=$(kubectl get deployment/flowengine -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="REPO_ALLOWLIST")].value}' | sed "s/<repo_name>,//g")

# Verify disabled
blocks config show --repo <repo_name>
# Expected: status: disabled

# Notify repo owner
echo "Orchestrator temporarily disabled for <repo_name> due to: <reason>.
Investigating. ETA: <X> hours." | mail -s "Orchestrator Rollback - <repo_name>" <owner_email>
```

**Recovery Time:** <5 minutes (validated in pilot)

---

## Success Metrics (Per Repo)

**Target Metrics (First 7 Days Post-Onboarding):**

- [ ] Flows executed: ≥3 flows
- [ ] Success rate: ≥95%
- [ ] P95 latency: <120s
- [ ] Avg cost: <$2/feature
- [ ] Quality gates: 5/5 passed (all flows)
- [ ] Zero P1 incidents
- [ ] Repo owner satisfaction: ≥4.0/5.0 (1-week survey)

**If Metrics Not Met:**
- Schedule follow-up training (office hours, Thursdays 2-3 PM)
- Review use cases (may need different block family)
- Consider deferring to Phase 7 (not ready for Phase 6)

---

## Phase 6 Onboarding Targets

**10-Repo Soak Observation (Nov 16-30, 2025):**

| Week | Target | Cumulative | Status |
| --- | --- | --- | --- |
| Week 1 (Nov 16-22) | 5 repos | 5 repos | 🚧 In progress |
| Week 2 (Nov 23-30) | 5 repos | 10 repos | 🕒 Pending |

**Expected Onboarding Rate:** 2 repos/day (staggered to avoid overload)

**Capacity Limits:**
- FlowEngine replicas: 5 (can handle 10-50 concurrent flows)
- SRE capacity: 2 onboardings/day max
- Daily monitoring: 9 AM standup + 4 PM status check

---

## Escalation Paths

### L1: Repo Owner Self-Service
- **Resources:** Training guides, #blocks-help Slack
- **SLA:** Best effort, community support

### L2: SRE On-Call
- **Contact:** @sre-oncall (Slack), sre-oncall@company.com
- **SLA:** Response <30 min (business hours), <2h (after hours)
- **Scope:** Onboarding issues, first flow failures, telemetry problems

### L3: Engineering TL
- **Contact:** @engineering-tl (Slack)
- **SLA:** Response <1h (business hours only)
- **Scope:** BLOCKER triage, infrastructure issues, schema bugs

### L4: Incident Commander
- **Contact:** PagerDuty (severity: high)
- **SLA:** Response <15 min (24/7)
- **Scope:** P1 incidents only (FlowEngine down, mass failures)

---

## Appendix: Onboarding Log Template

**File:** `planning/60_launch/evidence/onboarding_log.csv`

```csv
Date,Repo,Owner,Status,First Flow Duration,First Flow Cost,Notes
2025-11-18,financial-reporting,alice@company.com,SUCCESS,94s,$1.42,Smooth onboarding
2025-11-19,customer-analytics,bob@company.com,SUCCESS,118s,$1.79,Minor timeout (resolved with context pruning)
2025-11-20,inventory-mgmt,carol@company.com,DEFERRED,N/A,N/A,CI/CD not ready; rescheduled for Nov 25
...
```

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-CORE-002:** Timeout Recovery (TBD)
- **RB-LAUNCH-002:** Rollback to Pilot (`planning/60_launch/runbooks/rollback_to_pilot.md`)
- **RB-LAUNCH-004:** Budget Breach (TBD)
- **RB-LAUNCH-005:** Mass Failure (TBD)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE Persona | Initial version for Phase 6 onboarding |

---

**Status:** ✅ Ready for Phase 6 (10-repo soak observation)
**Next Review:** Dec 1, 2025 (post Phase 6 retrospective)
**Maintained By:** SRE Persona
