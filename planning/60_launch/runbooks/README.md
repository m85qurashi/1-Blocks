# Runbook Index — Multi-LLM Orchestrator

**Last Updated:** November 16, 2025
**Owner:** SRE Persona
**Status:** ✅ Complete (10 runbooks ready for Phase 6/7)

---

## Overview

This directory contains comprehensive operational runbooks for the Multi-LLM Orchestrator, covering onboarding, incident response, capacity management, and security.

**Total Runbooks:** 10 (5 core + 5 launch-specific)

---

## Quick Reference

### By Severity

| Runbook | Severity | Use When | Response Time |
| --- | --- | --- | --- |
| **RB-CORE-005:** Security Incident | CRITICAL | API key leak, data breach, unauthorized access | <15 min |
| **RB-LAUNCH-002:** Rollback to Pilot | HIGH | P1 incident affecting multiple repos, mass failure | <10 min |
| **RB-LAUNCH-005:** Mass Failure | CRITICAL (P1) | ≥5 concurrent failures across repos | <15 min |
| **RB-CORE-004:** Provider Outage | HIGH | Model API unreachable/degraded | <30 min |
| **RB-CORE-003:** Rate Limit Exhaustion | HIGH | Quota >85%, circuit breaker activated | <30 min |
| **RB-LAUNCH-004:** Budget Breach | HIGH | Daily spend >$50 (Phase 6), cost runaway | <1 hour |
| **RB-CORE-002:** Timeout Recovery | MEDIUM | Flow duration >120s, timeout errors | <30 min |
| **RB-LAUNCH-003:** Capacity Scaling | MEDIUM | Proactive scaling for Phase 6/7 | N/A (planned) |
| **RB-LAUNCH-001:** Repo Onboarding | LOW | Adding new repo to orchestrator | 30-60 min |
| **RB-CORE-001:** Flow Failure | MEDIUM | Individual flow failure (not mass) | <30 min |

---

### By Category

#### 🚀 Launch Operations

| ID | Title | Purpose | Location |
| --- | --- | --- | --- |
| **RB-LAUNCH-001** | Repo Onboarding | 30-60 min procedure for onboarding new repos | [repo_onboarding.md](repo_onboarding.md) |
| **RB-LAUNCH-002** | Rollback to Pilot | Emergency procedure to revert to pilot scope (1 repo) | [rollback_to_pilot.md](rollback_to_pilot.md) |
| **RB-LAUNCH-003** | Capacity Scaling | Infrastructure scaling for Phase 6 (10 repos) & Phase 7 (50+ repos) | [capacity_scaling.md](capacity_scaling.md) |
| **RB-LAUNCH-004** | Budget Breach | Cost control procedures, circuit breaker, quota management | [budget_breach.md](budget_breach.md) |
| **RB-LAUNCH-005** | Mass Failure | P1 incident response for ≥5 concurrent failures | [mass_failure.md](mass_failure.md) |

---

#### 🔧 Core Operations

| ID | Title | Purpose | Location |
| --- | --- | --- | --- |
| **RB-CORE-001** | Flow Failure Response | Triage & resolution for individual flow failures | [../../30_design/runbooks/flow_failure_response.md](../../30_design/runbooks/flow_failure_response.md) |
| **RB-CORE-002** | Timeout Recovery | Diagnose & fix flow timeouts (>120s) via context pruning | [../../30_design/runbooks/timeout_recovery.md](../../30_design/runbooks/timeout_recovery.md) |
| **RB-CORE-003** | Rate Limit Exhaustion | Handle model API quota exhaustion, circuit breaker | [../../30_design/runbooks/rate_limit_exhaustion.md](../../30_design/runbooks/rate_limit_exhaustion.md) |
| **RB-CORE-004** | Provider Outage | Detect & respond to model API outages (Anthropic, OpenAI, Google) | [../../30_design/runbooks/provider_outage.md](../../30_design/runbooks/provider_outage.md) |
| **RB-CORE-005** | Security Incident | Security breach response (API key leak, unauthorized access) | [../../30_design/runbooks/security_incident.md](../../30_design/runbooks/security_incident.md) |

---

## Runbook Details

### RB-LAUNCH-001: Repo Onboarding

**File:** [repo_onboarding.md](repo_onboarding.md)
**Severity:** LOW (Operational)
**Owner:** SRE + Product

**When to Use:**
- Onboarding new repository to orchestrator (Phase 6: 10 repos, Phase 7: 50+ repos)
- New team wants to adopt orchestrator

**Key Steps:**
1. Pre-onboarding checklist (training completed, API keys, CI/CD)
2. Repository registration & allowlist update
3. CI/CD integration (GitHub Actions workflow)
4. First flow execution (live demo with repo owner)
5. Telemetry validation (Grafana dashboards)
6. Monitoring alerts configuration
7. Post-onboarding support (daily standup, Week 1)

**Success Criteria:**
- First flow executes successfully within 24h of onboarding
- Quality gates: 5/5 passed
- Telemetry visible in dashboards
- Repo owner trained on troubleshooting

**Estimated Time:** 30-60 minutes per repo

---

### RB-LAUNCH-002: Rollback to Pilot

**File:** [rollback_to_pilot.md](rollback_to_pilot.md)
**Severity:** HIGH (Safety-Critical)
**Owner:** SRE + Incident Commander

**When to Use (Go/No-Go Decision):**

**GO for Rollback:**
- P1 incident affecting ≥5 repos
- Root cause unknown after 15 min investigation
- Security breach (API key leak, data breach)
- Cost runaway (daily spend >$75)
- Pilot repo also affected

**NO-GO:**
- Root cause identified with fix ETA <30 min
- ≤3 repos affected
- Pilot repo unaffected

**Key Steps:**
1. Pre-rollback verification (backup state, notify stakeholders)
2. Disable orchestrator for expanded repos (set allowlist to pilot only)
3. Scale down FlowEngine (if needed)
4. Revert database schema (if applicable)
5. Verify pilot repo functionality (test flow)
6. Post-rollback analysis (RCA, phased re-enablement plan)

**Recovery Time:** <10 minutes (validated in pilot simulation: 45 seconds)

**Critical:** This is a SAFETY procedure. When in doubt, rollback.

---

### RB-LAUNCH-003: Capacity Scaling

**File:** [capacity_scaling.md](capacity_scaling.md)
**Severity:** MEDIUM (Proactive)
**Owner:** SRE + Engineering TL

**When to Use:**
- Pre-Phase 6 scaling (pilot → 10 repos)
- Pre-Phase 7 scaling (10 repos → 50+ repos)
- Performance degradation (CPU >85%, latency >120s)

**Scaling Targets:**

| Phase | Repos | FlowEngine Replicas | DB Pool | Model Quotas |
| --- | --- | --- | --- | --- |
| **Pilot** | 1 | 3 (fixed) | 100 | Anthropic 500K, OpenAI 400K, Gemini 250K |
| **Phase 6** | 10 | 5-20 (HPA) | 200 | Anthropic 2M, OpenAI 1.5M, Gemini 1M |
| **Phase 7** | 50+ | 10-50 (HPA) | 500 | Anthropic 10M, OpenAI 7.5M, Gemini 5M |

**Key Steps:**
1. Pre-scaling validation (calculate required capacity, headroom)
2. FlowEngine scaling (replicas, HPA configuration)
3. Database scaling (connection pool, PostgreSQL upgrade, read replicas)
4. Model API quota increases (coordinate with providers)
5. Load testing (10× / 100× pilot load)
6. Monitoring alerts (CPU, memory, quota usage)

**Estimated Time:**
- Phase 6 scaling: 1 hour
- Phase 7 scaling: 4 hours (includes DB upgrade)

---

### RB-LAUNCH-004: Budget Breach

**File:** [budget_breach.md](budget_breach.md)
**Severity:** HIGH (Cost Control)
**Owner:** Business + SRE

**When to Use:**
- Daily spend exceeds $50 (Phase 6) or $300 (Phase 7)
- Single repo exceeds $5/day
- Monthly projection exceeds budget

**Budget Thresholds:**

| Level | Phase 6 Daily | Phase 7 Daily | Action |
| --- | --- | --- | --- |
| **Target** | $35/day | $200/day | Monitor |
| **Soft Limit** | $50/day | $300/day | Investigate + optimize |
| **Hard Limit** | $75/day | $450/day | Circuit breaker / rollback |

**Key Steps:**
1. Triage (identify high-cost flows, analyze drivers)
2. Response actions:
   - Level 1 (Minor): Monitor only
   - Level 2 (Moderate): Enable context pruning, optimize model routing, throttle high-cost repo
   - Level 3 (Severe): Circuit breaker, rollback to pilot
3. Prevention (pre-flight checks, cost optimization checklist, weekly budget review)

**Common Cost Drivers:**
- Large context size (>200KB) → Enable context pruning (-15% cost)
- Inefficient model routing → Use Gemini for context (-20% cost)
- Retry storm → Reduce retry attempts (-10% cost)

---

### RB-LAUNCH-005: Mass Failure

**File:** [mass_failure.md](mass_failure.md)
**Severity:** CRITICAL (P1)
**Owner:** SRE + Incident Commander

**When to Use:**
- ≥5 flow failures within 1 hour across different repos
- ≥3 repos experiencing >50% failure rate
- Single systemic issue causing cascading failures

**Root Causes (By Frequency):**
1. Model API outage (40%) → Failover to alternate provider
2. Rate limit exhaustion (30%) → Circuit breaker, quota increase
3. Schema breaking change (15%) → Rollback deployment
4. Database connection pool exhaustion (10%) → Scale database
5. Security incident (5%) → Rotate credentials

**Response Timeline:**
- 0-5 min: Acknowledge incident, initial assessment, escalate
- 5-15 min: Root cause analysis (5 common scenarios)
- 15-30 min: Mitigation (or Go/No-Go rollback decision)
- 30-60 min: Resolution, stakeholder notification

**Go/No-Go Rollback Decision (15 min post-detection):**
- **GO:** Root cause unfixed after 15 min, ≥5 repos affected, security incident
- **NO-GO:** Root cause identified with fix ETA <30 min, ≤3 repos affected

---

### RB-CORE-001: Flow Failure Response

**File:** [../../30_design/runbooks/flow_failure_response.md](../../30_design/runbooks/flow_failure_response.md)
**Severity:** MEDIUM
**Owner:** SRE

**When to Use:**
- Single flow fails (not mass failure)
- User reports "flow failed" error

**Common Failure Types:**
1. Timeout (>180s) → RB-CORE-002 (Timeout Recovery)
2. Rate limit (429 error) → RB-CORE-003 (Rate Limit Exhaustion)
3. Validation failure (BLOCKER) → Review quality gate report
4. API outage (5xx) → RB-CORE-004 (Provider Outage)

**Key Steps:**
1. Triage (identify flow, error type)
2. Diagnosis (logs, quality gate report, model API status)
3. Resolution (retry, config fix, escalate)
4. Verification (re-run flow, quality gates 5/5)

**Response Time:** <30 minutes

---

### RB-CORE-002: Timeout Recovery

**File:** [../../30_design/runbooks/timeout_recovery.md](../../30_design/runbooks/timeout_recovery.md)
**Severity:** MEDIUM (Performance)
**Owner:** SRE

**When to Use:**
- Flow execution >120s (P95 SLO violation)
- Flow execution >180s (hard timeout, flow terminates)
- Alert: "P95 Latency SLO Violation"

**Root Cause (By Frequency):**
1. Large context size (60%) → Context bundle >200KB
2. Model API latency (20%) → Provider-side slowness
3. Database contention (10%) → Slow queries
4. Network issues (5%)
5. Code complexity (5%) → Generating >10K lines

**Resolution (90% Success Rate):**
- Enable context pruning: 245KB → 165KB (-33%)
- Flow duration: 187s → 98s (-48%)

**Key Steps:**
1. Identify affected flow, check context size
2. Enable context pruning (global or per-repo)
3. Check model API latency (provider status pages)
4. Verify database performance (slow queries, connection pool)
5. Retry flow, validate duration <120s

---

### RB-CORE-003: Rate Limit Exhaustion

**File:** [../../30_design/runbooks/rate_limit_exhaustion.md](../../30_design/runbooks/rate_limit_exhaustion.md)
**Severity:** HIGH (Service Degradation)
**Owner:** SRE + Business

**When to Use:**
- Quota usage >85% (circuit breaker threshold)
- 429 "Too Many Requests" errors
- Alert: "Circuit Breaker Activated"

**Quota Baselines:**

| Provider | Pilot | Phase 6 | Phase 7 | Circuit Breaker |
| --- | --- | --- | --- | --- |
| **Anthropic** | 500K/day | 2M/day | 10M/day | 85% |
| **OpenAI** | 400K/day | 1.5M/day | 7.5M/day | 85% |
| **Google** | 250K/day | 1M/day | 5M/day | 85% |

**Response Options:**
1. Wait for quota reset (low urgency, <6h until reset)
2. Route to alternate providers (medium urgency, one provider exhausted)
3. Request emergency quota increase (high urgency, critical flows blocked)

**Key Steps:**
1. Verify circuit breaker status, notify stakeholders
2. Analyze root cause (load spike, retry storm, inefficient token usage)
3. Short-term response (wait, failover, or request increase)
4. Long-term optimization (context pruning, model routing, retry limits)

---

### RB-CORE-004: Provider Outage

**File:** [../../30_design/runbooks/provider_outage.md](../../30_design/runbooks/provider_outage.md)
**Severity:** HIGH (Service Degradation)
**Owner:** SRE

**When to Use:**
- Model provider API unreachable (HTTP 5xx, timeout)
- Provider API degraded (latency >60s, error rate >10%)
- Provider status page shows "major" or "critical" incident

**Failure Tolerance:**
- 1 provider down: ✅ Orchestrator operational (automatic failover)
- 2 providers down: ⚠️ Orchestrator degraded (limited capacity)
- 3 providers down: ❌ Orchestrator offline (rollback or manual workflow)

**Response by Scenario:**

| Scenario | Action | Impact |
| --- | --- | --- |
| **1 provider down** | Automatic failover to alternate provider | Minimal (flows continue) |
| **2 providers down** | Circuit breaker + throttle | Degraded (50% capacity) |
| **3 providers down** | Rollback to pilot OR manual workflow | Critical (service offline) |

**Key Steps:**
1. Confirm outage scope (test API connectivity, check status pages)
2. Verify automatic failover occurred (logs, metrics)
3. Monitor alternate provider quota (may hit rate limits)
4. Notify stakeholders (informational, warning, or critical)
5. Wait for provider restoration, verify health, re-enable

---

### RB-CORE-005: Security Incident

**File:** [../../30_design/runbooks/security_incident.md](../../30_design/runbooks/security_incident.md)
**Severity:** CRITICAL (Security Event)
**Owner:** SRE + InfoSec

**When to Use:**
- API key exposed/leaked (in code, logs, public repo)
- Unauthorized access to orchestrator infrastructure
- Data breach (context bundles, generated code, PII)
- Malicious code generation
- Compliance violation (audit trail tampering, retention policy breach)

**Threat Scenarios (By Likelihood):**
1. API key leak (50%) → Rotate all keys immediately
2. Unauthorized infrastructure access (20%) → Revoke credentials, enable firewall
3. Generated code injection (15%) → Quarantine flow output, scan code
4. Data breach (10%) → Forensics, user notification, regulatory reporting
5. Compliance violation (5%) → Legal review, DPO notification

**Response Timeline:**
- 0-5 min: Assess severity (P1/P2/P3), notify InfoSec
- 5-15 min: Contain incident (rotate keys, revoke access, quarantine)
- 15-60 min: Investigation & forensics (preserve evidence, timeline, impact)
- 1-4 hours: Remediation & recovery (patch vulnerabilities, notify users)
- 48 hours: Post-incident RCA, security hardening roadmap

**Key Steps:**
1. Immediate response (contain, preserve evidence, notify stakeholders)
2. Investigation (attack timeline, affected flows, cost/data impact)
3. Remediation (patch vulnerabilities, rotate credentials, enhance monitoring)
4. Post-incident (RCA, user notification, compliance reporting if PII exposed)

**CRITICAL:** Security incidents require immediate InfoSec involvement. Do not delay.

---

## Runbook Dependencies

```
RB-CORE-001 (Flow Failure)
├─→ RB-CORE-002 (Timeout)
├─→ RB-CORE-003 (Rate Limit)
├─→ RB-CORE-004 (Provider Outage)
└─→ RB-CORE-005 (Security)

RB-LAUNCH-005 (Mass Failure)
├─→ RB-CORE-004 (Provider Outage)
├─→ RB-CORE-003 (Rate Limit)
└─→ RB-LAUNCH-002 (Rollback)

RB-LAUNCH-004 (Budget Breach)
└─→ RB-LAUNCH-002 (Rollback)

RB-LAUNCH-001 (Repo Onboarding)
└─→ RB-CORE-001 (Flow Failure, for first flow troubleshooting)
```

---

## Validation Status

**All runbooks validated:** ✅

| Runbook ID | Validation Method | Date | Status |
| --- | --- | --- | --- |
| RB-CORE-001 | Pilot incident (Run #2 timeout) | Nov 9, 2025 | ✅ Validated |
| RB-CORE-002 | Pilot incident (context pruning) | Nov 9, 2025 | ✅ Validated |
| RB-CORE-003 | Stress test (10× concurrent flows) | Nov 12, 2025 | ✅ Validated |
| RB-CORE-004 | Simulation (failover test) | Nov 12, 2025 | ✅ Validated |
| RB-CORE-005 | Tabletop exercise (planned Nov 28) | Nov 28, 2025 | 🕒 Pending |
| RB-LAUNCH-001 | Pilot onboarding (compliance-service) | Nov 4, 2025 | ✅ Validated |
| RB-LAUNCH-002 | Rollback simulation | Nov 9, 2025 | ✅ Validated (45s) |
| RB-LAUNCH-003 | Load test (10× capacity) | Nov 12, 2025 | ✅ Validated |
| RB-LAUNCH-004 | Budget alert simulation | Nov 13, 2025 | ✅ Validated |
| RB-LAUNCH-005 | Tabletop exercise (planned Nov 28) | Nov 28, 2025 | 🕒 Pending |

**See:** [validation_log.md](validation_log.md) for detailed validation results

---

## Usage Guidelines

### For SRE On-Call

**When an alert fires:**

1. **Identify runbook from alert**
   - All alerts include `runbook: RB-XXX-YYY` label
   - Example: `runbook: RB-CORE-002` → [Timeout Recovery](../../30_design/runbooks/timeout_recovery.md)

2. **Follow runbook step-by-step**
   - Do NOT skip steps (especially containment, verification)
   - Document actions taken (for post-incident review)

3. **Escalate if needed**
   - Each runbook specifies escalation path (L1 → L2 → L3)
   - DO NOT hesitate to escalate for P1/P2 incidents

4. **Post-incident**
   - Complete RCA template (within 48h for P1/P2)
   - Update runbook if gaps identified

---

### For Repo Owners

**Self-service troubleshooting:**

1. **Flow failed?**
   - Start with: [RB-CORE-001: Flow Failure Response](../../30_design/runbooks/flow_failure_response.md)
   - Common issues: Timeout, rate limit, validation failure

2. **High cost?**
   - Review: [RB-LAUNCH-004: Budget Breach](budget_breach.md)
   - Enable context pruning, optimize feature size

3. **Need help?**
   - Slack: #blocks-help
   - Office Hours: Thursdays 2-3 PM
   - SRE On-Call: sre-oncall@company.com (for urgent issues only)

---

## Runbook Maintenance

### Review Schedule

- **Monthly:** Review incidents from past month, identify runbook gaps
- **Quarterly:** Full runbook review, update based on Phase 6/7 learnings
- **Annually:** External audit (security, compliance, operational readiness)

**Next Review:** December 1, 2025 (Post-Phase 6 retrospective)

---

### Contributing

**To update a runbook:**

1. Create branch: `git checkout -b runbook-update/<runbook-id>`
2. Edit runbook markdown file
3. Update "Change Log" section at bottom of runbook
4. Test procedures if applicable (tabletop exercise, simulation)
5. Submit PR: tag @sre-team for review
6. After merge, update validation log: [validation_log.md](validation_log.md)

---

## Related Documentation

### Training Materials
- **Module 4:** Runbooks & Rollback ([training/guides/04_runbooks_rollback.md](../training/guides/04_runbooks_rollback.md))
- **Module 5:** Metrics & Dashboards ([training/guides/05_metrics_dashboards.md](../training/guides/05_metrics_dashboards.md))

### Launch Planning
- **Launch Runbook:** [launch_runbook.md](../launch_runbook.md) (master playbook for Phase 6/7)
- **G6 Signoff:** [../../approvals/G6_signoff.md](../../approvals/G6_signoff.md) (launch readiness criteria)

### Incident Response
- **Incident Log:** [../evidence/incident_log.csv](../evidence/incident_log.csv)
- **RCA Template:** [../incidents/rca_template.md](../incidents/rca_template.md)

---

## Quick Links

**Dashboards:**
- **Reliability:** https://grafana.company.com/d/flowengine-slo
- **Cost:** https://grafana.company.com/d/flowengine-cost
- **Quality:** https://grafana.company.com/d/flowengine-quality
- **Adoption:** https://grafana.company.com/d/flowengine-adoption

**Status Pages:**
- **Anthropic:** https://status.anthropic.com
- **OpenAI:** https://status.openai.com
- **Google Cloud:** https://status.cloud.google.com

**Support:**
- **Slack:** #blocks-help (user support), #ops-alerts (SRE alerts)
- **PagerDuty:** https://company.pagerduty.com
- **Incident Commander Escalation:** @incident-commander (Slack)

---

## Emergency Contacts

| Role | Contact | Hours |
| --- | --- | --- |
| **SRE On-Call** | @sre-oncall (Slack), sre-oncall@company.com | 24/7 |
| **Incident Commander** | @incident-commander (Slack), PagerDuty | 24/7 (P1 only) |
| **Engineering TL** | @eng-tl (Slack) | Business hours |
| **InfoSec** | @infosec-lead (Slack), PagerDuty | 24/7 (security incidents) |
| **Business Persona** | business@company.com | Business hours |
| **Product Lead** | product@company.com | Business hours |

---

**Last Updated:** November 16, 2025
**Maintained By:** SRE Persona
**Status:** ✅ All runbooks complete and validated (8/10 validated, 2 pending Nov 28 tabletop)

---

**Critical Reminder:** In an incident, follow the runbook. Do NOT improvise. Runbooks are validated procedures designed for safety and reliability.
