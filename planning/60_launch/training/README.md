# Training & Enablement Assets

**Program:** Multi-LLM Orchestrator + Verified Blocks
**Phase:** G6 Launch Readiness
**Last Updated:** November 16, 2025
**Status:** ✅ Training materials complete; sessions scheduled for Week of Nov 18-22, 2025

---

## Overview

This directory contains comprehensive training materials for the Multi-LLM Orchestrator, designed to enable platform engineers, application engineers, and stakeholders to adopt the system in production.

### Training Objectives

1. **Platform Engineers:** Integrate orchestrator flows into CI/CD pipelines
2. **Application Engineers:** Author production-ready 6-face blocks
3. **QA/SRE/Data:** Understand quality gates, runbooks, and dashboards
4. **PM/Leadership:** Interpret ROI metrics and make investment decisions

---

## Directory Structure

```
training/
├── README.md                    ← This file
├── enablement_plan.md           ← Module roadmap, owners, timeline
├── recordings.md                ← Session recordings & links
├── guides/                      ← Written quick-starts, FAQs
│   ├── 01_cli_quickstart.md           (30 min read)
│   ├── 02_block_authoring.md          (45 min read + workshop)
│   ├── 03_quality_ci_gating.md        (60 min read + lab)
│   ├── 04_runbooks_rollback.md        (45 min read)
│   └── 05_metrics_dashboards.md       (45 min read)
└── slides/                      ← Presentation decks
    ├── 01_cli_quickstart_slides.md    (24 slides)
    └── 02_to_05_combined_slides.md    (Modules 2-5 combined)
```

---

## Training Modules

### Module 1: Orchestrator CLI Quick-Start

**Duration:** 30 minutes
**Format:** Live demo + hands-on
**Owner:** Product + Engineering
**Status:** ✅ Complete

**Artifacts:**
- **Guide:** `guides/01_cli_quickstart.md` (241 lines)
- **Slides:** `slides/01_cli_quickstart_slides.md` (24 slides)

**Topics Covered:**
- Installation & configuration (3 steps)
- First flow execution (Basel-I compliance block in 90s)
- Quality gates overview (5 gates)
- Context bundles for audit compliance
- Best practices & troubleshooting

**Learning Outcomes:**
- Install CLI and configure API keys
- Execute first orchestrator flow
- Interpret quality verification reports
- Understand context bundle immutability

---

### Module 2: Block Blueprint Authoring

**Duration:** 45 minutes
**Format:** Workshop (hands-on coding)
**Owner:** Engineering + QA
**Status:** ✅ Complete

**Artifacts:**
- **Guide:** `guides/02_block_authoring.md` (394 lines)
- **Slides:** `slides/02_to_05_combined_slides.md` (Module 2 section)

**Topics Covered:**
- 6-face block architecture (Structure, UI, Integration, Logic, Input, Output)
- JSON Schema contract design
- Property-based testing with Hypothesis
- Immutability patterns (S3 Object Lock for 7-year retention)
- Catalog registration

**Workshop Exercise:**
- Build a Basel-I compliance attestation block from scratch (30 minutes)
- Implement all 6 faces
- Add property-based tests
- Register in catalog

**Learning Outcomes:**
- Design contract-first blocks using JSON Schema
- Implement 6-face architecture
- Write property-based tests for edge case coverage
- Enforce immutability for compliance

---

### Module 3: Quality & CI Gating

**Duration:** 60 minutes
**Format:** Hands-on lab
**Owner:** QA
**Status:** ✅ Complete

**Artifacts:**
- **Guide:** `guides/03_quality_ci_gating.md` (448 lines)
- **Slides:** `slides/02_to_05_combined_slides.md` (Module 3 section)

**Topics Covered:**
- 5 quality gates (contract validation, unit coverage, mutation testing, security scan, logic review)
- Mutation testing deep dive (Mutmut)
- GitHub Actions CI integration
- Handling BLOCKER-level findings
- Automated triage runbooks

**Lab Exercise:**
- Fix weak tests to achieve ≥60% mutation kill-rate (20 minutes)
- Integrate quality gates into CI/CD pipeline
- Interpret mutation testing results

**Learning Outcomes:**
- Configure 5 quality gates in CI pipeline
- Understand mutation testing mechanics
- Triage and fix quality gate failures
- Integrate `blocks verify` into GitHub Actions

---

### Module 4: Runbooks & Rollback Procedures

**Duration:** 45 minutes
**Format:** Presentation + live demo
**Owner:** SRE
**Status:** ✅ Complete

**Artifacts:**
- **Guide:** `guides/04_runbooks_rollback.md` (372 lines)
- **Slides:** `slides/02_to_05_combined_slides.md` (Module 4 section)

**Topics Covered:**
- 5 core runbooks (flow failure, timeout, rate limit, provider outage, security incident)
- Zero-downtime rollback procedures (validated in pilot)
- Circuit breakers & fallback routing
- Post-incident review template
- On-call rotation procedures

**Demo:**
- Live rollback simulation (10 minutes)
- Circuit breaker activation
- Fallback model routing

**Learning Outcomes:**
- Navigate runbooks for incident response
- Execute zero-downtime rollback
- Configure circuit breakers
- Conduct post-incident reviews

---

### Module 5: Metrics & Dashboards

**Duration:** 45 minutes
**Format:** Screenshot tour + hands-on
**Owner:** Data
**Status:** ✅ Complete

**Artifacts:**
- **Guide:** `guides/05_metrics_dashboards.md` (502 lines)
- **Slides:** `slides/02_to_05_combined_slides.md` (Module 5 section)

**Topics Covered:**
- 3 core dashboards (ROI, Quality, Reliability)
- Key metrics from pilot (cycle time -34%, ROI 3.6×, quality 94.2%)
- Custom alerts (budget burn rate, quality degradation)
- Executive reporting (monthly ROI reports)
- Custom instrumentation with OpenTelemetry

**Hands-On:**
- Set up custom budget burn rate alert (10 minutes)
- Export monthly ROI report for stakeholders

**Learning Outcomes:**
- Interpret ROI, quality, and reliability dashboards
- Set up custom alerts for proactive monitoring
- Export executive reports (PDF/CSV)
- Add custom instrumentation to blocks

---

## Training Schedule

### Week of November 18-22, 2025

| Date | Time | Module | Duration | Location |
| --- | --- | --- | --- | --- |
| **Nov 18** | 10:00 AM | Module 1: CLI Quick-Start | 30 min | Zoom + Conference Room A |
| **Nov 19** | 2:00 PM | Module 2: Block Authoring | 45 min | Zoom + Conference Room B |
| **Nov 20** | 10:00 AM | Module 3: Quality & CI | 60 min | Zoom + Conference Room A |
| **Nov 21** | 2:00 PM | Module 4: Runbooks | 45 min | Zoom + Conference Room B |
| **Nov 22** | 10:00 AM | Module 5: Dashboards | 45 min | Zoom + Conference Room A |

**Total Training Time:** 3 hours 45 minutes (excluding office hours)

### Ongoing Support

**Office Hours:** Thursdays 2:00 PM – 3:00 PM (starting Nov 21)
- Q&A + live troubleshooting
- All sessions recorded

**Certification Quiz:** Available Nov 23, 2025
- URL: https://training.blocks-orchestrator.com/quiz
- Duration: 20 minutes
- Pass rate: 80% (8/10 questions)

---

## Materials Summary

### Comprehensive Training Guides (5 Files)

| File | Lines | Topics | Exercises |
| --- | --- | --- | --- |
| `01_cli_quickstart.md` | 241 | Installation, first flow, quality gates | 1 (Basel-I block) |
| `02_block_authoring.md` | 394 | 6-face architecture, schemas, testing | 1 (compliance block workshop) |
| `03_quality_ci_gating.md` | 448 | 5 quality gates, mutation testing, CI | 1 (fix weak tests lab) |
| `04_runbooks_rollback.md` | 372 | 5 runbooks, rollback, incident response | 1 (rollback demo) |
| `05_metrics_dashboards.md` | 502 | 3 dashboards, alerts, reporting | 1 (custom alert setup) |
| **Total** | **1,957 lines** | **25+ topics** | **5 hands-on exercises** |

### Presentation Slides (2 Files)

| File | Slides | Coverage |
| --- | --- | --- |
| `01_cli_quickstart_slides.md` | 24 | Module 1 (detailed) |
| `02_to_05_combined_slides.md` | 50+ | Modules 2-5 (combined) |
| **Total** | **70+ slides** | **All 5 modules** |

---

## Key Training Outcomes

### By Module Completion, Participants Will:

1. **Install & Configure:** Set up orchestrator CLI in <10 minutes
2. **Generate Blocks:** Create production-ready blocks in ~90 seconds
3. **Enforce Quality:** Integrate 5 quality gates into CI pipeline
4. **Respond to Incidents:** Use runbooks to resolve issues in <15 minutes
5. **Monitor ROI:** Interpret dashboards and generate executive reports

### Certification Criteria

- Complete all 5 modules (attendance or watch recordings)
- Pass certification quiz (≥80% score)
- Generate at least 1 production block
- Submit feedback survey

---

## Pilot Results (Context for Training)

Training materials reference real pilot data (Nov 4-12, 2025):

| Metric | Baseline | Pilot | Improvement |
| --- | --- | --- | --- |
| **Cycle Time** | 12.5 days | 8.2 days | -34% ⬇️ |
| **Cost/Feature** | $200 | $1.60 | -99.2% ⬇️ |
| **AI Code %** | 15% | 38% | +23 pts ⬆️ |
| **Quality Score** | 68% | 94.2% | +26 pts ⬆️ |
| **ROI** | — | 3.6× | Target: ≥2× ✅ |

**Pilot Success Metrics:**
- Flow success rate: 100% (4/4 runs)
- Mutation kill-rate: 68.75% average
- Zero critical incidents
- SLO compliance: 97.7%

---

## Feedback & Iteration

### Post-Training Survey (Nov 23-30, 2025)

Participants will be asked to rate:
1. Content clarity (1-5)
2. Hands-on exercise value (1-5)
3. Instructor effectiveness (1-5)
4. Material completeness (1-5)

**Target:** ≥4.5/5.0 average across all modules

### Continuous Improvement

- **Monthly Showcase:** Share success stories (first Friday of each month)
- **Quarterly Review:** Update materials based on feedback and new features
- **Advanced Topics:** Plan follow-up sessions (Jan 2026) on cost optimization, model evaluation, multi-block compositions

---

## Getting Started (For New Participants)

### Pre-Requisites

1. **System Access:**
   - GitHub account with repo access
   - Grafana credentials (request via #ops-access)
   - API keys (Anthropic, OpenAI, Google) — obtain from API vendor portals

2. **Software:**
   - Python 3.9+ or Node.js 16+
   - Git CLI
   - Docker (optional, for local testing)

3. **Pre-Reading:**
   - `planning/50_pilot/pilot_plan.md` (Pilot Reporting & Narrative section)
   - `planning/approvals/G5_signoff.md` (Evidence package summary)

### Registration

- **Training Calendar:** https://calendar.company.com/blocks-training
- **Slack:** Join #blocks-training for announcements
- **Email:** training@company.com for questions

---

## Contact & Support

**Training Coordination:**
- **Owner:** Product Persona
- **Email:** training@company.com
- **Slack:** #blocks-training

**Technical Questions:**
- **Slack:** #blocks-help
- **Office Hours:** Thursdays 2-3 PM
- **Documentation:** https://docs.blocks-orchestrator.com

**Access Issues:**
- **IT Support:** support@company.com
- **Slack:** #it-help

---

## Appendix: File Manifest

### Created Training Assets (Nov 16, 2025)

```
planning/60_launch/training/
├── enablement_plan.md                    (32 lines, existing)
├── recordings.md                         (160 lines, updated Nov 16)
├── README.md                             (This file, 347 lines)
├── guides/
│   ├── 01_cli_quickstart.md              (241 lines, created Nov 16)
│   ├── 02_block_authoring.md             (394 lines, created Nov 16)
│   ├── 03_quality_ci_gating.md           (448 lines, created Nov 16)
│   ├── 04_runbooks_rollback.md           (372 lines, created Nov 16)
│   └── 05_metrics_dashboards.md          (502 lines, created Nov 16)
└── slides/
    ├── 01_cli_quickstart_slides.md       (24 slides, created Nov 16)
    └── 02_to_05_combined_slides.md       (50+ slides, created Nov 16)
```

**Total Lines of Training Content:** 2,549 lines (guides + slides + metadata)
**Total Files Created:** 9 files (5 guides + 2 slide decks + 2 metadata files)

---

**Status:** ✅ All training materials complete and ready for delivery (Week of Nov 18-22, 2025)
**Next Milestone:** G6 gate review (Dec 5, 2025) — launch readiness validation

---

**Last Updated:** November 16, 2025
**Maintained By:** Product Persona + Training Team
