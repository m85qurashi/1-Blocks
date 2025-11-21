# Multi-LLM Block Engineering Playbook (v1.0)
Standard for reviewing and implementing ideas using a 4-model orchestrator and 6-face verified blocks.

## 0) Purpose and Scope
- Establish a repeatable, auditable process from idea → verified, composable blocks → shipped outcomes.
- Enforce “ask = delivered” through contracts, tests, and multi-model verification.
- Keep Delivery A (Orchestrator) and Delivery B (Blocks) decoupled and integrated via Delivery C (Platform Integration).

## 1) Core Principles
1. **Contract-first:** Every block defines typed input/output (JSON Schema) before code.
2. **Separation of concerns:** Orchestrator responsibilities (routing, context) are independent from block semantics.
3. **Multi-model cross-check:** Distinct models own roles; no single model is authoritative.
4. **Versioned truth:** Blueprints, prompts, flows, and artifacts are versioned; updates produce new versions.
5. **Gatekeeping by evidence:** Merge only with passing contracts/tests, zero BLOCKERS, and ADR-backed rationale.
6. **Observability & cost:** All flows emit metrics (latency, tokens, defects) and run under defined budgets.

## 2) Roles and Governance (RACI Summary)
| Role | Responsibilities | Approvals |
| --- | --- | --- |
| Product Manager (PM) | Problem framing, PRD, AC/RTM ownership, prioritization | G2 (Definition), G5 (Pilot Go/No-Go) |
| Tech Lead/Architect | Architecture, security, contracts, CI gates, ADRs | G3 (Design), G4 (Build Exit) |
| Platform Engineering | Orchestrator, prompts/routing, cost guards, metrics | G4 |
| Application Engineering | Block implementation, mapping blocks, fixes | — |
| QA/Quality | Test strategy (property/mutation), data seeding, pass/fail calls | G4 |
| SRE/Security | Secrets, PII policy, reliability SLOs, incident runbooks | G3/G6 |

## 3) Stage-Gated Lifecycle
Each phase requires the listed artifacts before the exit gate.

### Phase 0 — Idea
- **Artifacts:** One-pager (problem, target users, success criteria), Lean Canvas.
- **Gate G0:** One-pager approved.

### Phase 1 — Discovery
- **Artifacts:** Competitive scan, ROI hypothesis, journey map, feasibility notes.
- **Gate G1:** Prioritized scope + outcome metrics.

### Phase 2 — Definition
- **Artifacts:** PRD v1 (A + B), BlockBlueprint schema (6 faces) + I/O JSON Schemas, TaskObject schema, Security/PII policy, secrets plan.
- **Gate G2:** PRD approved; contracts frozen (v1.0).

### Phase 3 — Design
- **Artifacts:** Detailed architecture (A/B/C), sequence diagrams, data model (TaskDB, Block Catalog), prompt packs per role with budgets, UX flows (CLI/VS Code/CI).
- **Gate G3:** Design review passed (security, reliability, cost).

### Phase 4 — Build
- **Artifacts:**
  - **A:** ModelRouter, FlowEngine, ContextBuilder, ResponseMerger, APIs/CLI/CI hook.
  - **B:** Catalog, validators, generators, test harness (unit/integration/property/mutation), verification service.
  - **C:** Integration service, context bundle schema, artifact registry.
- **Gate G4:** Contracts validated; tests green; mutation kill-rate ≥ threshold; review report BLOCKERS = 0; cost within budget; logs/metrics enabled.

### Phase 5 — Validate (Pilot)
- **Artifacts:** Pilot report (quality, cost, productivity), tuned prompts/routes.
- **Gate G5:** Pilot success metrics met; rollout approval.

### Phase 6 — Launch
- **Artifacts:** Runbooks, dashboards, playbooks, training packages.
- **Gate G6:** Launch readiness sign-off.

### Phase 7 — Operate / Scale
- **Artifacts:** Quarterly review, model evaluations, deprecation/upgrade notes, roadmap updates.
- **Gate G7:** Next-stage investment approval.

## 4) Delivery A Standard — Model Specialty & Orchestration
**Objective:** Vendor-agnostic control plane with role-based routing.

### A.1 Roles → Models (Default)
- Planner/Implementer: ChatGPT primary; 4th model secondary (tests/drafts).
- Architect/Reviewer: Claude primary.
- Context Analyst: Gemini primary.
- Test Designer: 4th model primary.

### A.2 Required Artifacts
- `models.yaml` (providers, models, token limits, budgets).
- Prompt templates per role (versioned).
- Flow specs: plan, impl, review, docs (inputs/outputs, retries, fallbacks).
- Observability spec: logging, metrics, cost tracking.

### A.3 Quality & Safety Bars
- Retry policy with idempotent request IDs.
- PII redaction / default deny list in prompts.
- Cost guards: per-flow token caps; per-project budgets.
- SLIs/SLOs: success rate, P95 latency, cost/flow.

## 5) Delivery B Standard — Blocks Implementation & Testing
**Objective:** 6-face verified blocks, contract-first.

### B.1 Six Faces (must be explicit)
1. Bottom (Structure)
2. Front (UI)
3. Back (Integration)
4. Top (Logic)
5. Left (Input)
6. Right (Output)

### B.2 Mandatory Artifacts per Block
- BlockBlueprint (YAML/JSON, versioned).
- Acceptance Criteria (AC) + RTM (AC→tests→files).
- Generated tests: unit, integration, property-based, mutation.
- Verification report (model reviews, test summary, decision: `verified_exact` / `verified_equivalent` / `needs_revision`).
- Catalog entry (block_id@version, contracts, artifacts, owners, tags).

### B.3 Quality Gates (default thresholds)
- JSON Schemas validate sample payloads.
- Unit + integration test coverage ≥ baseline (e.g., 80% line/branch where meaningful).
- Mutation kill-rate ≥ 60% (ramp to 70%+).
- BLOCKERS = 0; WARNINGS triaged.
- Performance budgets defined/met per block type.

## 6) Delivery C Standard — Platform Integration (Connect A + B)
**Objective:** Bind A and B with minimal coupling.

### C.1 Contracts
- Context bundle from B → A: blueprint slices, repo tree/diffs, selected files, test results, constraints.
- Artifact registry from A → B: SRS drafts, implementation guides, review reports, generated patches, documentation packs (immutable links).

### C.2 Idempotency & Traceability
- Stable Task IDs and Block IDs across flows.
- Every artifact links to Task/Block version + CI run.
- Replayable runs (same inputs → same outputs modulo model nondeterminism).

## 7) Templates (Authoritative)
### 7.1 Idea Intake (Phase 0)
```
Title:
Problem:
Target users/personas:
Desired outcomes & metrics:
Why now / alternatives:
Risks & constraints:
Initial scope (A/B/C):
```

### 7.2 PRD (Phase 2)
- Context & goals
- Non-goals
- Personas & journeys
- Functional requirements (prioritized)
- Non-functional requirements (SLOs, security, cost)
- Acceptance Criteria (AC#)
- Analytics/metrics
- Rollout & risks
- Open questions

### 7.3 BlockBlueprint (Six Faces)
```
block_id: structure_trio_block
version: 1.0.0
purpose: "Manage Basel-I structure: master, levels, allowed sets"
faces:
  bottom_structure_spec: {...}
  front_ui_spec: { type: wizard, steps: [master, levels, allowed_sets], validations: [...] }
  back_integration_spec: { sinks: [...], modes: [insert, update] }
  top_logic_spec: { rules: ["..."], invariants: ["..."] }
  left_input_contract: { json_schema_ref: contracts/structure_trio/input.v1.json }
  right_output_contract: { json_schema_ref: contracts/structure_trio/output.v1.json }
acceptance_criteria:
  - id: AC-001
    text: "Duplicate structure_key rejected with S_409"
traceability:
  - ac_id: AC-001
    tests: [test_dup_key.py::test_dup]
    files: [src/structure/service.py]
```

### 7.4 TaskObject
```
task_id: T-2025-0001
goal: "Deliver structure_trio_block v1"
artifacts:
  blueprint_ref: blueprints/structure_trio/1.0.0.yaml
  review_reports: []
  test_results: []
metadata:
  repo: git@.../basel-structure.git
  branch: feature/structure-trio
```

### 7.5 Review Rubric (Model Reviewers)
- Sections: BLOCKERS, WARNINGS, NICE_TO_HAVE, Minimal patch suggestions.
- Scoring dimensions: Correctness, Security/Compliance, Performance, Readability, Test Adequacy.

### 7.6 CI Gating Policy (Default)
1. Validate JSON Schemas.
2. Generate tests from AC where possible.
3. Run unit + integration + property-based tests.
4. Run mutation testing; enforce threshold.
5. Trigger orchestrator `/flows/review`; fail on BLOCKERS.
6. Block merge if any gate fails.

## 8) Measurement & Targets
| Dimension | Metric | Pilot Target |
| --- | --- | --- |
| Productivity | Idea→Verified (days) | −30% vs baseline |
| Quality | Pre-merge BLOCKERS caught | ≥ 95% |
| Quality | Post-merge defects (30 days) | ≤ baseline |
| Testing | Mutation kill-rate | ≥ 60% |
| Cost | Tokens/feature | Within budget |
| Adoption | PRs using review flow | ≥ 80% pilot repos |
| Reliability | Flow success rate | ≥ 99% |
| Reliability | P95 flow latency | Under SLO |

## 9) Risk & Compliance Controls
- PII/sensitive data: prompt redaction; classification tags on artifacts.
- Secrets: never in prompts; use vault + short-lived tokens.
- Model drift: version prompts/routes; canary + rollback plan.
- Vendor risk: secondary models configured; budget caps; circuit breakers.
- Audit: immutable logs for Task/Block/Flow with artifact hashes.

## 10) Project-Management WBS (Standardized)
Level-1 packages: Program governance, Delivery A, Delivery B, Delivery C, QA/Security/Compliance, Enablement & Change.

**Milestone checklist**
- G2: PRD + contracts + security plan approved.
- G3: Design sign-off; SLOs/budgets set.
- G4: CI green; zero BLOCKERS; thresholds met.
- G5: Pilot success; rollout Go.
- G6: Launch readiness.
- G7: Quarterly review + next plan.

## 11) Operating Model
- **Cadence:** Weekly triage (ideas/issues), bi-weekly pilot review, monthly metrics/ROI, quarterly model evals.
- **Change control:**
  - Blueprint changes → new version + migration plan.
  - Prompt/routing changes → version bump + canary & metrics.
  - Deprecations → 2-cycle notice, mapping blocks provided.
- **Knowledge:** ADR per major decision; searchable artifact registry.

## 12) Quick-Start (First Use)
1. Submit Idea Intake.
2. Create PRD + BlockBlueprint + I/O Schemas.
3. Run plan → impl → review → docs flows on pilot block.
4. Enforce CI gates; achieve `verified_exact` / `verified_equivalent`.
5. Publish to Block Catalog; define first sequence.
6. Capture metrics; hold G5 review; proceed to rollout.

## 13) Glossary
- **Block:** Unit of delivery with six faces and typed I/O.
- **Blueprint:** Versioned spec for a block.
- **Catalog:** Registry of verified blocks and versions.
- **TaskObject:** Orchestrator state for a work item.
- **BLOCKER:** Review finding preventing merge.
- **Mutation kill-rate:** % injected mutations caught by tests.

> This playbook is the authoritative standard. All initiatives must produce the specified artifacts, meet the gates, and adhere to thresholds before merge or launch.
