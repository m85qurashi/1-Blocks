# Launch Runbook: Multi-LLM Orchestrator Production Rollout

**Program:** Multi-LLM Orchestrator + Verified Blocks (Delivery A/B/C)
**Version:** 2.0 (Post-G5)
**Last Updated:** November 16, 2025
**Owner:** SRE Persona + Product Persona
**Status:** 🚧 Ready for 10-Repo Soak (Nov 16-30) → Production Rollout (Dec 9+)

---

## Executive Summary

This runbook guides the phased rollout of the Multi-LLM Orchestrator from pilot (1 repo, 4 flows) → 10-repo expansion (50+ flows) → org-wide production (50+ repos, 500+ flows). It includes pre-flight checklists, go-live procedures, monitoring protocols, rollback triggers, and post-launch support.

**Rollout Phases:**
1. **Phase 5 (Complete):** Pilot validation (1 repo, 4 flows) — ✅ Nov 4-12, 2025
2. **Phase 6 (Current):** 10-repo soak observation (50+ flows) — 🚧 Nov 16-30, 2025
3. **Phase 7 (Planned):** Org-wide rollout (50+ repos) — 📦 Dec 9-20, 2025 (post-G6)

---

## Table of Contents

1. [Pre-Rollout Checklist](#pre-rollout-checklist)
2. [Phase 6: 10-Repo Soak Observation](#phase-6-10-repo-soak-observation)
3. [Phase 7: Org-Wide Rollout](#phase-7-org-wide-rollout)
4. [Go-Live Day Procedures](#go-live-day-procedures)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Launch Support](#post-launch-support)
8. [Incident Response](#incident-response)
9. [Communications](#communications)
10. [Success Criteria](#success-criteria)

---

## Pre-Rollout Checklist

### Infrastructure Readiness

**FlowEngine (Kubernetes Deployment):**
- [ ] FlowEngine scaled to 5 replicas (from pilot: 3)
- [ ] Resource limits: CPU 2 cores, Memory 4GB per pod
- [ ] Health checks configured (liveness: `/health`, readiness: `/ready`)
- [ ] Horizontal Pod Autoscaler (HPA): min 5, max 20, target CPU 70%

**Database (PostgreSQL):**
- [ ] Connection pool increased to 200 (from pilot: 100)
- [ ] Max overflow: 50 connections
- [ ] Backup retention: 30 days (point-in-time recovery enabled)
- [ ] Read replicas: 2 (for analytics queries)

**Storage (S3):**
- [ ] Context bundles bucket: `s3://context-bundles-prod/`
- [ ] Object Lock enabled (COMPLIANCE mode, 7-year retention)
- [ ] Versioning enabled (immutability)
- [ ] Lifecycle policy: archive to Glacier after 1 year

**Model API Access:**
- [ ] Anthropic (Claude) quota: 2M tokens/day (increased from 1M)
- [ ] OpenAI (GPT-4) quota: 1.5M tokens/day (increased from 1M)
- [ ] Google AI (Gemini) quota: 500K tokens/day (unchanged)
- [ ] Circuit breaker enabled: pause at 85% quota

**Verification:**
```bash
# Check FlowEngine replicas
kubectl get deployment flowengine -n production
# Expected: 5/5 ready

# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='flowengine';"
# Expected: <50 (healthy baseline)

# Check S3 Object Lock
aws s3api get-object-lock-configuration --bucket context-bundles-prod
# Expected: Mode=COMPLIANCE, Years=7
```

---

### Configuration Readiness

**Environment Variables (FlowEngine Deployment):**
```yaml
env:
  # Model Configuration
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: model-api-keys
        key: anthropic
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: model-api-keys
        key: openai
  - name: GOOGLE_API_KEY
    valueFrom:
      secretKeyRef:
        name: model-api-keys
        key: google

  # Orchestrator Configuration
  - name: ARCHITECT_MODEL
    value: "claude-sonnet-4-5"
  - name: IMPLEMENTATION_MODEL
    value: "gpt-4-turbo"
  - name: CONTEXT_MODEL
    value: "gemini-pro"

  # Circuit Breaker
  - name: ENABLE_CIRCUIT_BREAKER
    value: "true"
  - name: CIRCUIT_BREAKER_THRESHOLD
    value: "85"  # Pause at 85% quota

  # Context Pruning (Learned from Pilot)
  - name: CONTEXT_PRUNING_ENABLED
    value: "true"
  - name: CONTEXT_MAX_SIZE_KB
    value: "180"  # Prevent timeouts

  # Quality Gates
  - name: QUALITY_GATE_MODE
    value: "strict"  # contract, coverage, mutation, security, review
  - name: MIN_MUTATION_KILL_RATE
    value: "60"
  - name: MIN_UNIT_COVERAGE
    value: "90"

  # Database
  - name: DB_POOL_SIZE
    value: "200"
  - name: DB_MAX_OVERFLOW
    value: "50"

  # Monitoring
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector:4317"
```

**Verification:**
```bash
kubectl get secret model-api-keys -n production -o yaml
# Verify all 3 keys present

kubectl get deployment flowengine -n production -o yaml | grep -A 2 "CONTEXT_PRUNING_ENABLED"
# Expected: value: "true"
```

---

### Training & Documentation

**Training Completion (Module 1-5, Nov 18-22):**
- [ ] ≥30 participants certified (≥80% pass rate)
- [ ] ≥4.5/5.0 average feedback score
- [ ] All session recordings published

**Documentation Available:**
- [ ] CLI Quick-Start Guide: `planning/60_launch/training/guides/01_cli_quickstart.md`
- [ ] Block Authoring Guide: `planning/60_launch/training/guides/02_block_authoring.md`
- [ ] Quality & CI Guide: `planning/60_launch/training/guides/03_quality_ci_gating.md`
- [ ] Runbooks: `planning/30_design/runbooks/`
- [ ] FAQ: `planning/60_launch/training/FAQ.md` (to be created)

**Verification:**
```bash
# Check training completion
cat planning/60_launch/training/certification_results.md
# Expected: ≥30 certified, ≥80% pass rate
```

---

### Monitoring & Alerting

**Dashboards Live:**
- [ ] ROI Dashboard: https://grafana.company.com/d/flowengine-roi
- [ ] Quality Dashboard: https://grafana.company.com/d/flowengine-quality
- [ ] Reliability Dashboard: https://grafana.company.com/d/flowengine-slo
- [ ] Adoption Dashboard: https://grafana.company.com/d/flowengine-adoption (new for Phase 6)
- [ ] Cost Breakdown Dashboard: https://grafana.company.com/d/flowengine-cost (new for Phase 6)

**Alerts Configured:**
- [ ] Budget Burn Rate: Daily spend >$50 → Slack #ops-alerts
- [ ] Quality Degradation: Mutation kill-rate <60% → PagerDuty SRE
- [ ] SLO Violation: P95 latency >150s → PagerDuty SRE
- [ ] Mass Failure: >5 failures/hour → PagerDuty incident commander

**Verification:**
```bash
# Test alert firing
curl -X POST https://grafana.company.com/api/v1/alerts/test \
  -d '{"alert_id": "budget_burn_rate"}'
# Expected: Alert received in #ops-alerts within 30s
```

---

### On-Call Rotation

**Rotation Established:**
- [ ] Primary: 3 SRE engineers (1-week shifts)
- [ ] Secondary: 2 Engineering TLs (escalation path)
- [ ] Incident Commander: SRE Lead (P1/P2 incidents)

**Training Complete:**
- [ ] Module 4: Runbooks & Rollback (Nov 21)
- [ ] Tabletop exercise: P1 incident simulation (Nov 28)
- [ ] Runbook review session (Dec 2)

**PagerDuty Configuration:**
- [ ] Escalation policy: Primary (5 min) → Secondary (10 min) → Incident Commander (15 min)
- [ ] Schedule: https://company.pagerduty.com/schedules/flowengine-oncall

**Verification:**
```bash
# Trigger test page
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -d '{"routing_key": "flowengine-test", "event_action": "trigger"}'
# Expected: Primary on-call receives page within 1 min
```

---

## Phase 6: 10-Repo Soak Observation

**Timeline:** November 16-30, 2025 (14 days)
**Goal:** Validate orchestrator at 10× pilot scale (10 repos, 50+ flows)
**Status:** 🚧 In Progress

---

### 10-Repo Selection Criteria

**Repos Selected by PM + TL (due: Nov 17):**

1. **High-Value Domains:** Compliance, financial reporting, observability (pilot-validated)
2. **Diverse Use Cases:** Data pipelines, API gateways, auth services, analytics
3. **Representative Teams:** Mix of experienced + new teams (training validation)
4. **Risk Mitigation:** No critical-path production services (rollback safe)

**Confirmed 10-Repo List:**
- [ ] 1. `compliance-service` (Basel-I domain, high priority)
- [ ] 2. `financial-reporting` (revenue-critical, tight deadlines)
- [ ] 3. `observability-platform` (telemetry + dashboards)
- [ ] 4. `data-pipelines` (ETL + data quality)
- [ ] 5. `api-gateway` (high-traffic, performance-sensitive)
- [ ] 6. `auth-service` (security-critical, well-tested)
- [ ] 7. `notification-system` (async workflows)
- [ ] 8. `analytics-platform` (data science + ML)
- [ ] 9. `infra-automation` (IaC + Terraform)
- [ ] 10. `devops-tooling` (CI/CD pipelines)

---

### Onboarding Procedure (Per Repo)

**Day 1: Pre-Flight Checklist**
1. **Repo Owner Notification:**
   - Send onboarding email (see [Communications](#communications))
   - Schedule 30-min kickoff call (show CLI demo)

2. **Technical Setup:**
   ```bash
   # Repo owner runs:
   cd /path/to/repo
   blocks init

   # Creates:
   # - .blocks/config.yml
   # - .blocks/catalog/
   # - .blocks/schemas/
   ```

3. **API Keys Configuration:**
   ```bash
   # Set in repo CI/CD secrets
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=... (optional)
   ```

4. **First Flow Execution (Guided):**
   - Repo owner submits feature request (provided template)
   - SRE monitors execution (Grafana dashboard)
   - Validate quality gates passed

**Day 2-14: Observation Period**
- Repo owner generates 5-10 flows (natural pace)
- SRE monitors daily (see [Monitoring Protocol](#monitoring-protocol))
- Collect feedback via #blocks-help Slack

---

### Monitoring Protocol (Daily Standup, 9:00 AM)

**Daily Checklist (SRE + PM):**
1. **Review Dashboard Metrics (Last 24h):**
   - Flow success rate: Target ≥99%
   - P95 latency: Target <120s
   - Cost/feature: Target <$2.00
   - Quality score: Target ≥90%

2. **Check Incidents:**
   - Any P1/P2 incidents? (Review PagerDuty)
   - Runbook effectiveness? (TTR <15 min)

3. **Stakeholder Feedback:**
   - Any blockers reported in #blocks-help?
   - Training gaps identified?

4. **Risk Assessment:**
   - Model API quota: Any provider >70%?
   - Concurrency: Any flows queued >5 min?
   - Cost variance: Daily spend within budget?

**Weekly Review (Fridays, 2:00 PM):**
- Aggregate metrics (week-over-week)
- Identify trends (latency creep, cost increases)
- Adjust for next week (scale infra, tune configs)

**Verification:**
```bash
# Generate daily report
blocks metrics export --last-24h --format markdown > daily_report_$(date +%Y%m%d).md

# Check for anomalies
grep "❌" daily_report_$(date +%Y%m%d).md
# Expected: 0 lines (no failures)
```

---

### Soak Observation Success Criteria

**Phase 6 Exit Criteria (Nov 30, 2025):**
- [ ] All 10 repos onboarded and active
- [ ] ≥50 flows executed successfully
- [ ] Flow success rate: ≥99% (baseline: 100% in pilot)
- [ ] P95 latency: <120s (baseline: 118s in pilot)
- [ ] Cost/feature: <$2.00 (baseline: $1.60 in pilot)
- [ ] SLO compliance: ≥95% (baseline: 97.7% in pilot)
- [ ] Zero P1 incidents (P2/P3 acceptable with runbook resolution)
- [ ] Stakeholder feedback: ≥4.0/5.0

**Evidence Package (For G6, Dec 5):**
- [ ] Soak observation report: `planning/50_pilot/evidence/sre/10_repo_soak_results.md`
- [ ] Cost analysis: `planning/50_pilot/evidence/biz/10_repo_cost_analysis.md`
- [ ] Quality metrics: `planning/50_pilot/evidence/qa/10_repo_quality_metrics.md`
- [ ] Incident log (if any): `planning/60_launch/incidents/soak_incidents.md`

---

## Phase 7: Org-Wide Rollout

**Timeline:** December 9-20, 2025 (10 business days)
**Goal:** Enable orchestrator for 50+ repos (500+ flows)
**Prerequisites:** G6 gate approved (Dec 5, 2025)

---

### Rollout Strategy (Phased)

**Week 1: Dec 9-13 (25 repos)**
- **Day 1 (Mon):** Announce rollout (see [Communications](#communications))
- **Day 1-5:** Onboard 5 repos/day (staggered)
- **Monitoring:** Daily standup + Slack #ops-alerts

**Week 2: Dec 16-20 (25 repos)**
- **Day 6-10:** Onboard 5 repos/day (staggered)
- **Monitoring:** Daily standup + executive summary (Fridays)

**Risk Mitigation:**
- No more than 5 repos onboarded per day (prevent overload)
- Pause if any P1 incident (investigate + resolve before resuming)
- Monitor model API quotas (request vendor increases if >70%)

---

### Onboarding Automation (Self-Service)

**Self-Service Portal:**
- [ ] URL: https://blocks.company.com/onboarding
- [ ] Repo owner fills form (repo name, domain, team lead)
- [ ] Automated checks:
  - GitHub repo exists
  - CI/CD configured (GitHub Actions / GitLab CI)
  - Team lead approved (via Slack DM)

**Auto-Provisioning (Terraform):**
```bash
# Triggered by onboarding form
terraform apply \
  -var="repo_name=new-repo" \
  -var="team_lead=alice@company.com"

# Creates:
# - .blocks/ directory in repo
# - CI secrets (API keys)
# - PagerDuty integration
# - Grafana dashboard (repo-specific)
```

**Onboarding Confirmation Email:**
```
Subject: [Blocks Orchestrator] Onboarding Complete: {repo_name}

Hi {team_lead},

Your repo "{repo_name}" is now enabled for the Multi-LLM Orchestrator!

Next Steps:
1. Run your first flow: `cd {repo_name} && blocks flow run --input feature_request.md`
2. Review training materials: https://docs.blocks-orchestrator.com/training
3. Join #blocks-help for support

Dashboards:
- Your repo dashboard: https://grafana.company.com/d/{repo_name}
- Org-wide dashboard: https://grafana.company.com/d/flowengine-adoption

Questions? Reply to this email or post in #blocks-help.

-- Blocks Orchestrator Team
```

---

### Go-Live Day Procedures

**Day 1 (Dec 9, 2025): Launch Day**

**8:00 AM — Pre-Flight Checks**
```bash
# 1. Verify infrastructure health
kubectl get pods -n production | grep flowengine
# Expected: All pods Running (5/5)

# 2. Check model API quotas
blocks quota show --all
# Expected: All providers <50% (fresh daily quota)

# 3. Verify dashboards loading
curl -f https://grafana.company.com/d/flowengine-adoption
# Expected: HTTP 200

# 4. Test alert firing
blocks alerts test budget_burn_rate
# Expected: Alert received in #ops-alerts within 30s
```

**9:00 AM — Launch Announcement**
- [ ] Post to #engineering Slack (see [Communications](#communications))
- [ ] Email to eng-all@ mailing list
- [ ] Update status page: https://status.company.com

**9:30 AM — First Batch Onboarding (5 Repos)**
- [ ] Trigger onboarding for repos 1-5 (self-service portal)
- [ ] Monitor #blocks-help for incoming questions
- [ ] SRE watches Grafana dashboards (real-time)

**12:00 PM — Midday Check-In**
- [ ] Review first 5 repos: Any flows executed?
- [ ] Check for any incidents (PagerDuty)
- [ ] Adjust onboarding pace if needed (pause / accelerate)

**3:00 PM — Second Batch Onboarding (5 Repos)**
- [ ] Trigger onboarding for repos 6-10

**5:00 PM — End-of-Day Review**
- [ ] Generate daily report (see [Monitoring Protocol](#monitoring-protocol))
- [ ] Post summary to #ops-alerts
- [ ] Identify any issues for overnight monitoring

**6:00 PM — Handoff to On-Call**
- [ ] SRE on-call briefed (Slack DM + PagerDuty notes)
- [ ] Escalation contacts confirmed (PM, TL available via phone)

---

## Monitoring & Alerting

### Real-Time Monitoring (Grafana)

**Critical Dashboards (Auto-Refresh: 30s):**
1. **Adoption Dashboard:** https://grafana.company.com/d/flowengine-adoption
   - Repos onboarded (target: 10 → 50+)
   - Flows executed (target: 50 → 500+)
   - Active users (team leads generating flows)

2. **Reliability Dashboard:** https://grafana.company.com/d/flowengine-slo
   - Flow success rate (target: ≥99%)
   - P95 latency (target: <120s)
   - Model API uptime (target: ≥99.9%)

3. **Cost Dashboard:** https://grafana.company.com/d/flowengine-cost
   - Daily spend (budget: $50/day)
   - Cost by model (Claude, GPT-4, Gemini)
   - Cost by repo (identify high-spend repos)

**Alert Thresholds (PagerDuty / Slack):**
- 🚨 **P1 (Critical):** >10% flow failure rate (>1 hour) → Page incident commander
- ⚠️ **P2 (High):** P95 latency >150s (>30 min) → Page SRE on-call
- ⚠️ **P3 (Medium):** Daily spend >$50 → Slack #ops-alerts
- ℹ️ **Info:** Mutation kill-rate <60% (any flow) → Slack #blocks-help

---

### Metrics Collection (OpenTelemetry)

**Instrumentation Points:**
```python
# FlowEngine instrumentation (already deployed)
from opentelemetry import metrics, trace

meter = metrics.get_meter(__name__)
tracer = trace.get_tracer(__name__)

# Metrics emitted:
flow_duration = meter.create_histogram("flow.duration_seconds")
flow_cost = meter.create_histogram("flow.cost_usd")
flow_status = meter.create_counter("flow.status", unit="1")
quality_gate_result = meter.create_counter("quality_gate.result", unit="1")

# Traces (end-to-end flow)
with tracer.start_as_current_span("orchestrator_flow") as span:
    span.set_attribute("flow_type", "plan_impl_review_docs")
    span.set_attribute("block_family", "compliance")
    # ... flow execution
```

**Query Examples (Prometheus):**
```promql
# Flow success rate (last 1h)
rate(flow_status{status="success"}[1h]) / rate(flow_status[1h]) * 100

# P95 latency (last 1h)
histogram_quantile(0.95, rate(flow_duration_seconds_bucket[1h]))

# Daily cost projection
sum(rate(flow_cost_usd[1h])) * 24
```

---

## Rollback Procedures

### Rollback Trigger Criteria

**Automatic Rollback (Circuit Breaker):**
- Flow failure rate >10% for >1 hour
- Model API quota >95% (prevent exhaustion)
- Database connection pool exhausted (>190/200 connections)

**Manual Rollback Decision (Incident Commander):**
- Any P1 incident unresolved after 30 minutes
- Data loss or security incident detected
- Stakeholder request (PM, TL, or Business)

---

### Rollback to Pilot Scope (Emergency)

**Scenario:** Phase 6/7 rollout causing widespread issues → revert to pilot (1 repo)

**Procedure (30 minutes):**

**Step 1: Halt New Onboarding (5 min)**
```bash
# Disable self-service portal
kubectl scale deployment onboarding-portal --replicas=0

# Post to #engineering
blocks notify slack --channel engineering \
  --message "🚨 Orchestrator rollback in progress. New onboarding paused. Existing flows will continue."
```

**Step 2: Identify Affected Repos (5 min)**
```bash
# Query repos onboarded after pilot
psql -c "
  SELECT repo_name, onboarded_at
  FROM repos
  WHERE onboarded_at > '2025-11-12'
  ORDER BY onboarded_at DESC;
"

# Expected: List of Phase 6/7 repos (9-50 repos)
```

**Step 3: Disable Orchestrator for Affected Repos (10 min)**
```bash
# For each repo, disable CLI
for repo in $(cat affected_repos.txt); do
  # Set environment flag
  kubectl set env deployment/flowengine \
    REPO_ALLOWLIST=compliance-service  # Pilot repo only
done

# Verify
blocks config show --repo compliance-service
# Expected: enabled: true

blocks config show --repo financial-reporting
# Expected: enabled: false (rollback complete)
```

**Step 4: Communicate Rollback (5 min)**
```bash
# Post to #engineering
blocks notify slack --channel engineering \
  --message "✅ Rollback complete. Orchestrator enabled only for pilot repo (compliance-service). Investigation ongoing."

# Email affected repo owners
blocks notify email --to affected_repos@company.com \
  --subject "[Blocks Orchestrator] Temporary Rollback" \
  --body "Your repo has been temporarily disabled from the orchestrator due to [reason]. We'll re-enable once the issue is resolved. Manual code review available in the meantime."
```

**Step 5: Root Cause Analysis (Next 24h)**
- [ ] Review incident timeline (PagerDuty + Grafana)
- [ ] Identify failure pattern (specific repo? block family? model?)
- [ ] Document findings in PIR (Post-Incident Review)
- [ ] Prepare mitigation plan

**Step 6: Re-Onboarding Decision (48h after rollback)**
- [ ] Issue resolved? (Validated in pilot repo)
- [ ] Stakeholder approval? (PM, TL, SRE unanimous GO)
- [ ] Re-onboard 1 repo at a time (slow rollout)

---

### Rollback to Previous FlowEngine Version

**Scenario:** New FlowEngine version (e.g., v1.2) causing regressions → revert to stable (v1.1)

**Procedure (15 minutes):**

**Step 1: Rollback Deployment (5 min)**
```bash
# Rollback to previous version
kubectl rollout undo deployment/flowengine -n production

# Monitor rollback progress
kubectl rollout status deployment/flowengine -n production
# Expected: "deployment 'flowengine' successfully rolled out" within 45s
```

**Step 2: Verify Previous Version (5 min)**
```bash
# Check image version
kubectl get deployment flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].image}'
# Expected: flowengine:v1.1 (previous stable)

# Test flow execution
blocks test-flow --input test_case.md
# Expected: Flow succeeds with v1.1
```

**Step 3: Communicate Rollback (5 min)**
```bash
# Post to #ops-alerts
blocks notify slack --channel ops-alerts \
  --message "✅ FlowEngine rolled back to v1.1 (stable). All flows operating normally."
```

---

### Rollback to Manual Review (Last Resort)

**Scenario:** Orchestrator unavailable → teams revert to manual code review

**Procedure:**
```bash
# Disable orchestrator CLI globally
kubectl scale deployment/flowengine --replicas=0

# Post announcement
blocks notify slack --channel engineering \
  --message "🚨 Orchestrator temporarily unavailable. Please use manual code review until further notice. ETA: [X hours]"

# Teams continue with:
# - Manual coding (Copilot suggestions still available)
# - Manual test writing
# - Manual code review (GitHub PR reviews)
```

---

## Post-Launch Support

### Office Hours (Week 1-2 Post-Launch)

**Schedule:** Daily, Dec 9-20, 2:00 PM – 3:00 PM
**Format:** Zoom + Slack #blocks-help
**Attendees:** Product, Engineering, QA, SRE, Data (rotating)

**Agenda:**
- Q&A (live troubleshooting)
- Common issues review (FAQ updates)
- Feature requests collection

---

### Support Channels

**Primary Support: Slack #blocks-help**
- Response SLA: <2 hours (business hours)
- Escalation: @blocks-oncall (SRE)

**Secondary Support: Email**
- support@blocks-orchestrator.com
- Response SLA: <24 hours

**Emergency: PagerDuty**
- P1 incidents only (>10% failure rate, data loss, security)
- Escalation path: SRE → TL → Incident Commander

---

### FAQ (Common Issues)

**Q: "Context bundle exceeds 500KB" error?**
A: Enable context pruning:
```bash
blocks config set context.pruning.enabled true
blocks config set context.max_size_kb 180
```

**Q: "Model API rate limit exceeded"?**
A: Circuit breaker will pause automatically. Wait for quota reset (hourly). Or use fallback model:
```bash
blocks config set fallback.model gpt-4-turbo
```

**Q: "Quality gate BLOCKER: contract validation failed"?**
A: View detailed validation errors:
```bash
blocks verify show task_abc123 --verbose
```
Fix schema or implementation, then retry.

---

## Incident Response

### Severity Levels

| Severity | Definition | MTTR Target | Notification |
| --- | --- | --- | --- |
| **P1 (Critical)** | >10% flow failure, data loss, security incident | <15 min | PagerDuty incident commander + Slack #incidents |
| **P2 (High)** | P95 latency >150s, model API outage | <30 min | PagerDuty SRE on-call |
| **P3 (Medium)** | Budget breach, quality degradation | <2 hours | Slack #ops-alerts |
| **P4 (Low)** | Documentation gaps, feature requests | <24 hours | Slack #blocks-help |

---

### Incident Response Playbook

**P1 Incident (Critical):**

1. **Detection (0-5 min):**
   - PagerDuty alert fires
   - Incident commander joins #incidents channel

2. **Triage (5-10 min):**
   - Run diagnostic commands:
     ```bash
     blocks status flows --failed --last-1h
     kubectl logs -l app=flowengine --tail=100
     ```
   - Identify failure pattern (specific repo? block family? model?)

3. **Mitigation (10-15 min):**
   - Apply relevant runbook (see `planning/30_design/runbooks/`)
   - If no runbook match: Escalate to TL + PM
   - If mitigation fails: Trigger rollback (see [Rollback Procedures](#rollback-procedures))

4. **Communication (15-30 min):**
   - Post to status page: https://status.company.com
   - Update #engineering Slack with ETA
   - Email affected repo owners

5. **Resolution (30-60 min):**
   - Verify issue resolved (monitor dashboards)
   - Post resolution to #incidents
   - Schedule PIR (Post-Incident Review) within 48h

---

### Post-Incident Review (PIR) Template

**Location:** `planning/60_launch/incidents/PIR_YYYY-MM-DD.md`

```markdown
# Post-Incident Review: [Incident Title]

**Date:** [Date]
**Severity:** P1 / P2 / P3
**Duration:** [Start] – [End] ([Duration])
**Incident Commander:** [Name]

## Timeline
- [HH:MM] Detection: [How detected]
- [HH:MM] Triage: [Diagnosis]
- [HH:MM] Mitigation: [Action taken]
- [HH:MM] Resolution: [Service restored]

## Root Cause
[1-2 paragraphs]

## Impact
- Repos affected: [Count or list]
- Flows failed: [Count]
- Users impacted: [Count]

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
[Key takeaways]
```

---

## Communications

### Launch Announcement (Dec 9, 2025)

**Slack #engineering:**
```
🚀 **Multi-LLM Orchestrator Now Available!**

After a successful pilot (3.6× ROI, 34% faster cycle times), we're rolling out the orchestrator to all engineering teams!

**What is it?**
Generate production-ready blocks in ~90 seconds using Claude + GPT-4 + Gemini. Contract-validated, test-covered, audit-ready.

**Get Started:**
1. Onboard your repo: https://blocks.company.com/onboarding
2. Watch training videos: https://docs.blocks-orchestrator.com/training
3. Run your first flow: `blocks flow run --input feature_request.md`

**Support:**
- Office hours: Daily 2-3 PM (Dec 9-20)
- Slack: #blocks-help
- Docs: https://docs.blocks-orchestrator.com

**Pilot Results:**
- Cycle time: 12.5d → 8.2d (-34%)
- Cost: $200 → $1.60 (-99%)
- Quality: 94.2% (mutation kill-rate: 68.75%)

Questions? Reply in thread or join #blocks-help!

-- Product + Engineering Teams
```

**Email to eng-all@:**
```
Subject: [Launch] Multi-LLM Orchestrator Available for All Teams

Hi Engineering,

We're excited to announce the launch of the Multi-LLM Orchestrator, now available for all teams!

After a successful 2-week pilot with the compliance team, we validated:
- 3.6× ROI (first-year)
- 34% faster cycle times (12.5d → 8.2d)
- 99% cost reduction ($200 → $1.60 per feature)
- 94% quality score (zero critical defects)

[Read more about the pilot results here: link to G5_signoff.md]

**How to Get Started:**
1. Onboard your repo: https://blocks.company.com/onboarding (self-service, 5 min)
2. Complete 30-min training: https://docs.blocks-orchestrator.com/training/cli-quickstart
3. Generate your first block: `blocks flow run --input feature_request.md`

**Support During Rollout:**
- Office hours: Daily 2-3 PM, Dec 9-20 (Zoom link: [link])
- Slack: #blocks-help (monitored 24/7 by on-call SRE)
- Docs: https://docs.blocks-orchestrator.com

**Rollout Schedule:**
- Week 1 (Dec 9-13): 25 repos
- Week 2 (Dec 16-20): 25 repos
- Self-service onboarding available immediately

We're here to support you every step of the way. Looking forward to seeing what you build!

Best,
Product, Engineering, and SRE Teams
```

---

### Weekly Status Update (Fridays)

**Slack #engineering:**
```
📊 **Orchestrator Weekly Update: Week of Dec 9-13**

**Rollout Progress:**
- Repos onboarded: 25 / 50 (50%)
- Flows executed: 150 total
- Success rate: 98.7% (target: ≥99%)

**Highlights:**
- financial-reporting team generated 8 blocks in 3 days (prev: 15 days)
- Zero P1 incidents this week
- Training completion: 32 certified (≥80% pass rate)

**Metrics:**
- Cycle time: 8.5d avg (target: <10d) ✅
- Cost/feature: $1.72 avg (target: <$2) ✅
- Quality score: 92.3% (target: ≥90%) ✅

**Next Week:**
- Onboard remaining 25 repos (Dec 16-20)
- Continue daily office hours (2-3 PM)

Questions? #blocks-help

-- Product Team
```

---

## Success Criteria

### Phase 6 (10-Repo Soak) — Success Metrics

**By Nov 30, 2025:**
- [ ] Flow success rate: ≥99% (actual: TBD)
- [ ] P95 latency: <120s (actual: TBD)
- [ ] Cost/feature: <$2.00 (actual: TBD)
- [ ] SLO compliance: ≥95% (actual: TBD)
- [ ] Zero P1 incidents
- [ ] Stakeholder feedback: ≥4.0/5.0

**Evidence for G6 Gate (Dec 5):**
- [ ] Soak observation report completed
- [ ] Cost analysis within budget
- [ ] Quality metrics aggregate (50+ flows)
- [ ] Incident log (if any, with PIR)

---

### Phase 7 (Org-Wide Rollout) — Success Metrics

**By Dec 20, 2025:**
- [ ] Repos onboarded: ≥50 (target: 100% eligible repos)
- [ ] Flows executed: ≥500
- [ ] Adoption rate: ≥80% of onboarded teams actively using
- [ ] Training completion: ≥75% of teams certified
- [ ] Support backlog: <10 open tickets (manageable load)

**Long-Term (Q1 2026):**
- [ ] ROI sustained: ≥3× (measured quarterly)
- [ ] Cost controls: Daily spend <$50 avg
- [ ] Quality maintained: ≥90% quality score
- [ ] Incident rate: <1 P2/month avg

---

## Appendix

### Runbook Index

**Core Runbooks (Validated in Pilot):**
1. `planning/30_design/runbooks/flow_failure_response.md` (validated 1/1 incidents)
2. `planning/30_design/runbooks/timeout_recovery.md` (to be created)
3. `planning/30_design/runbooks/rate_limit_exhaustion.md` (to be created)
4. `planning/30_design/runbooks/provider_outage.md` (to be created)
5. `planning/30_design/runbooks/security_incident.md` (to be created)

**Launch-Specific Runbooks (To Be Created):**
6. `planning/60_launch/runbooks/repo_onboarding.md`
7. `planning/60_launch/runbooks/rollback_to_pilot.md`
8. `planning/60_launch/runbooks/capacity_scaling.md`
9. `planning/60_launch/runbooks/budget_breach.md`
10. `planning/60_launch/runbooks/mass_failure.md`

---

### Contact & Escalation

**Primary Contacts:**
- **Product:** Product Persona (product@company.com)
- **Engineering:** Engineering Persona (engineering-tl@company.com)
- **SRE:** SRE Persona (sre-oncall@company.com)

**Escalation Path:**
1. **P4/P3:** Slack #blocks-help → SRE on-call (PagerDuty)
2. **P2:** SRE on-call → Engineering TL
3. **P1:** Incident commander → PM + TL + Business (war room)

**Emergency Contacts (24/7):**
- PagerDuty: https://company.pagerduty.com/services/flowengine
- Phone: [SRE on-call hotline TBD]

---

**Runbook Version:** 2.0 (Post-G5)
**Last Updated:** November 16, 2025
**Next Review:** December 5, 2025 (G6 gate)
**Maintained By:** SRE Persona + Product Persona

---

**Status:** ✅ Ready for Phase 6 (10-repo soak, Nov 16-30)
**Next Milestone:** G6 gate review (Dec 5, 2025) → Phase 7 rollout approval
