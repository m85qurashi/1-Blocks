Comprehensive Planning Framework (v1.0)
======================================

Who does what to take any idea from intake to an approved, execution-ready plan.

0) Roles
--------

- PM (Product Manager) – drives problem framing, outcomes, scope, AC, cross-team alignment; owns the Plan.
- TL/Architect – technical feasibility, target architecture, risks, effort & sequencing; approves technical plan.
- Platform Eng – orchestration/platform components, integration patterns, cost/latency guardrails.
- App Eng – domain implementation plan, estimates, constraints, tech choices.
- QA/Quality – test strategy, acceptance/test mapping, quality bars.
- SRE/Security – reliability/SLOs, security/PII controls, runbooks.
- Data/Analytics – metrics, instrumentation, dashboards, success measurement.
- Biz/Finance/Legal – ROI model, budget, vendor terms, compliance.
- Stakeholders – domain leads who will use/operate the outcome.

1) Phase model (who does what, outputs, gate)
--------------------------------------------

Each idea progresses through seven phases. Every phase has: Inputs → Activities (by role) → Outputs → Gate.

### Phase 0 — Idea Intake (1–2 days)

- **Inputs**: raw idea, user pain, initial context
- **Activities**
  - PM: capture Idea One-Pager; define problem, target users, success proxy metrics.
  - Biz: quantify opportunity size; identify constraints.
  - TL: quick feasibility notes, dependencies.
- **Outputs**: One-Pager, initial success criteria
- **Gate G0 (PM+TL)**: “Worth discovery?” yes/no

### Phase 1 — Discovery (≤1 week)

- **Inputs**: One-Pager
- **Activities**
  - PM: user journeys, JTBD, alternatives, RICE scoring; draft outcomes.
  - Biz/Finance: ROI hypothesis, cost envelopes.
  - TL/Platform/App Eng: spike list, risks, integration surfaces, model fit.
  - Data: measurement plan sketch.
- **Outputs**: Discovery Brief (journeys, outcomes, ROI hypothesis, risk list, spike plan)
- **Gate G1 (PM+TL+Biz)**: Prioritized scope approved

### Phase 2 — Definition (1 week)

- **Inputs**: Discovery Brief
- **Activities**
  - PM: PRD v1 with Acceptance Criteria (AC) and non-goals.
  - TL/Architect: target architecture outline, sequencing approach.
  - Platform/App Eng: component list, interfaces, estimates (T-shirt sizes).
  - QA: quality strategy outline; AC→test mapping draft.
  - SRE/Security: SLOs, privacy/PII and secrets posture.
  - Data: metrics & instrumentation spec (events, dashboards).
- **Outputs**:
  - PRD v1 (AC list + RTM stub)
  - Technical Definition (components, interfaces, sequencing)
  - Ops/Sec Definition (SLOs, privacy, access)
  - Measurement Spec
- **Gate G2 (PM accountable; TL/SRE/Sec approve)**: Definition locked for design

### Phase 3 — Design (1–2 weeks)

- **Inputs**: PRD v1, Technical Definition
- **Activities**
  - TL/Architect: sequence diagrams, integration contracts, effort & risk burn-down plan.
  - Platform/App Eng: API/Schema drafts, migration plan, tech choices finalized.
  - QA: test plan (unit/integration/property/mutation), quality bars.
  - SRE/Security: runbooks, threat model, change management.
  - PM: UX flow (CLI/VS Code/CI touchpoints), rollback criteria.
  - Data: dashboard mocks, success KPIs wiring.
- **Outputs**:
  - Design Dossier (diagrams, contracts, schemas, runbooks)
  - Delivery Plan (work packages, estimates, risks, mitigations)
- **Gate G3 (TL accountable; PM/SRE/Sec approve)**: Design sign-off

### Phase 4 — Planning for Execution (≤1 week)

- **Inputs**: Design Dossier, Delivery Plan
- **Activities**
  - PM: finalize scope, MVP cut, timeline, WBS and critical path; dependency map.
  - TL/Eng Leads: staff/owner assignments; interface change control.
  - QA: test data/fixtures readiness; gating policy in CI.
  - SRE: rollout strategy (canary), SLO monitoring plan.
  - Biz/Finance: budget, vendor routing if applicable.
- **Outputs**:
  - Execution Plan (WBS, timeline, owners, dependencies, risk register)
  - Go/No-Go criteria (quality, cost, schedule thresholds)
- **Gate G4 (PM accountable; TL/Biz approve)**: Ready to build

### Phase 5 — Pilot Plan (≤1 week)

- **Inputs**: Execution Plan
- **Activities**
  - PM: define pilot scope/users, success thresholds, feedback protocol.
  - TL/QA/SRE: pilot entry/exit gates; incident playbook.
  - Data: pilot dashboards.
- **Outputs**: Pilot Plan (scope, success metrics, evaluation schedule)
- **Gate G5 (PM+TL)**: Pilot authorized

### Phase 6 — Launch Plan (≤1 week, in parallel late in build)

- **Inputs**: Pilot learning loop
- **Activities**
  - PM: rollout stages, comms/training, change log.
  - SRE: capacity plan, oncall updates.
  - Biz: policy/pricing, procurement alignment.
- **Outputs**: Launch Runbook (rollout stages, comms, support, rollback)
- **Gate G6 (PM+SRE+TL)**: Launch readiness

2) Plan package (what “a comprehensive plan” must contain)
--------------------------------------------------------

- PRD v1 (problem, goals, AC, non-goals, personas, journeys)
- Architecture & Design Dossier (diagrams, interfaces, schemas, migrations, runbooks, security posture)
- Quality Plan (test strategy, AC→test RTM, thresholds)
- Measurement Plan (events, KPIs, dashboards)
- Execution Plan (WBS, timeline, owners, risks/mitigations, dependencies)
- Pilot Plan (scope, criteria, evaluation)
- Launch Runbook (rollout, comms, support, rollback)
- Approval Sheet (G2/G3/G4/G5/G6 sign-offs)

Owner of the full package: PM. Technical correctness sign-off: TL/Architect. Quality & Ops sign-off: QA + SRE/Security.

3) RACI by key artifact
-----------------------

| Artifact | PM | TL/Arch | Platform Eng | App Eng | QA | SRE/Sec | Data | Biz/Fin/Legal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Idea One-Pager | R/A | C | I | I | I | I | C | C |
| Discovery Brief | R/A | C | I | I | I | I | C | C |
| PRD v1 + AC | R/A | C | I | C | C | C | C | C |
| Technical Definition | C | R/A | C | C | I | C | I | I |
| Design Dossier | C | R/A | C | C | C | C | I | I |
| Quality Plan | C | C | I | I | R/A | C | I | I |
| Measurement Plan | C | C | I | I | I | I | R/A | I |
| Execution Plan (WBS) | R/A | C | C | C | C | C | C | C |
| Pilot Plan | R/A | C | I | I | C | C | C | I |
| Launch Runbook | R/A | C | I | I | C | R/A | C | C |

R = Responsible, A = Accountable/Approver, C = Consulted, I = Informed.

4) WBS template for the planning work (Level 1–3)
-------------------------------------------------

1. Planning Program Setup
   - 1.1 Governance & gates
   - 1.2 Repo/folder structure
   - 1.3 Templates

2. Discovery & Definition
   - 2.1 One-Pager
   - 2.2 Discovery Brief
   - 2.3 PRD v1
   - 2.4 AC & RTM
   - 2.5 Technical Definition
   - 2.6 Ops/Sec Definition
   - 2.7 Measurement Spec

3. Design
   - 3.1 Architecture diagrams
   - 3.2 Interface contracts
   - 3.3 Schema/migrations
   - 3.4 Runbooks (ops, incident)
   - 3.5 Quality Plan
   - 3.6 Dashboard designs

4. Execution Planning
   - 4.1 WBS & estimates
   - 4.2 Owners & staffing
   - 4.3 Dependency map
   - 4.4 Risk register & mitigations
   - 4.5 Critical path & timeline
   - 4.6 Go/No-Go thresholds

5. Pilot & Launch Planning
   - 5.1 Pilot scope & success criteria
   - 5.2 Pilot dashboards
   - 5.3 Launch stages
   - 5.4 Comms & training
   - 5.5 Rollback plan

6. Approvals & Handoffs
   - 6.1 G2 sign-off
   - 6.2 G3 sign-off
   - 6.3 G4 sign-off
   - 6.4 G5 sign-off
   - 6.5 G6 sign-off

Deliverables from Sections 2–6 comprise the “Comprehensive Plan” package.

5) Checklists (per phase)
------------------------

**G0 – Idea Intake**
- Problem framed, target users named, success proxies defined, alternatives listed.

**G1 – Discovery**
- Journeys mapped, ROI hypothesis written, risk list created, spikes identified.

**G2 – Definition**
- PRD v1 complete with AC; Technical & Ops/Sec definitions drafted; Measurement Spec ready.

**G3 – Design**
- Diagrams updated; contracts/specs frozen; test strategy & thresholds defined; runbooks drafted.

**G4 – Execution Planning**
- WBS with owners/dates; dependency map; risk mitigations; Go/No-Go thresholds documented.

**G5 – Pilot**
- Pilot scope/users; dashboards live; incident playbook; evaluation cadence.

**G6 – Launch**
- Training & comms assets; rollback path tested; oncall/SLOs configured.

6) Document structure (repo)
---------------------------

```
/planning/
  00_idea/
    one_pager.md
  10_discovery/
    discovery_brief.md
  20_definition/
    prd_v1.md
    acceptance_criteria.md
    technical_definition.md
    ops_security_definition.md
    measurement_spec.md
  30_design/
    architecture_diagrams/
    interface_contracts/
    schemas/
    runbooks/
    quality_plan.md
    dashboards_spec.md
  40_execution/
    wbs.xlsx
    critical_path.md
    risk_register.md
    dependencies.md
  50_pilot/
    pilot_plan.md
  60_launch/
    launch_runbook.md
  approvals/
    G2_signoff.md
    G3_signoff.md
    G4_signoff.md
    G5_signoff.md
    G6_signoff.md
```

7) Example assignment (who does what on day one)
-----------------------------------------------

- PM: create one_pager.md; schedule G0 review; open planning repo skeleton.
- TL: add feasibility_notes to one-pager; list spikes.
- Biz: fill ROI section of discovery brief.
- Data: draft success metrics & events.
- QA: propose initial quality bars for this idea class.
- SRE/Security: add constraints (PII, secrets, SLO expectations).

8) Definition of Done for the Plan
----------------------------------

- All required artifacts present and versioned.
- RACI resolved; owners assigned for every WBS work package.
- Risks and dependencies documented with mitigations.
- Gates G2–G6 signed by accountable roles.
- Plan package archived and linked in the tracker.
