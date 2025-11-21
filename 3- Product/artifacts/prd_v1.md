# PRD v1 — Multi-LLM Orchestrator + Verified Blocks

## 1. Context & Goals
Deliver Delivery Plans A (Orchestrator) and B (Blocks) with Platform Integration (C) to reduce idea→verified block cycle time by 30% while ensuring quality/cost guardrails defined in the governance framework.

## 2. Problem Statement
Engineers lack a unified orchestration layer and contract-first blocks, causing fragmented workflows, inconsistent AI outputs, and poor traceability.

## 3. Target Users & Personas
- Application engineers building domain blocks.
- Platform engineers operating orchestration flows.
- Product managers/architects reviewing AI-generated plans.
- QA/SRE teams validating contracts, SLOs.

## 4. User Journeys
1. **Plan → Implement → Review → Docs Flow** via CLI/CI orchestrator.
2. **Block Authoring Flow**: Create 6-face blueprint, generate tests, pass verification, publish to catalog.
3. **Pilot Basel-I Flow**: Rebuild Structure Trio block end-to-end and mark `verified_exact`.

## 5. Functional Requirements (Prioritized)
| ID | Requirement | Priority | Acceptance Criteria |
| --- | --- | --- | --- |
| FR-1 | Provide `/flows/{plan,impl,review,docs}` APIs + CLI/CI integration | P0 | Flow spec executed with role-specific models; outputs stored in TaskObject |
| FR-2 | Support BlockBlueprint authoring (6 faces) with JSON Schema contracts | P0 | Valid schema references; AC linked to tests |
| FR-3 | Catalog service to publish `block_id@version` with verification status | P0 | Blocks searchable; metadata includes faces, tests, decision |
| FR-4 | Integration layer to map TaskObject↔Blueprint artifacts | P1 | Context bundle schema validated; artifact links immutable |
| FR-5 | Dashboards for tokens, latency, BLOCKERS | P1 | Metrics accessible per flow/block |

## 6. Non-Functional Requirements
- **Security/Privacy:** Secrets plan, PII redaction policies enforced before G2.
- **Performance:** Flow success rate ≥99%, P95 latency under SLO defined in playbook.
- **Cost:** Token caps and budgets enforced; ability to override with approval.
- **Reliability:** Replayable runs; incident runbooks prior to Launch.

## 7. Scope & Phasing
- **Phase 0–2:** Complete PRD v1, blueprint schema, TaskObject spec, AC/RTM stub.
- **Phase 3:** UX flows (CLI, VS Code extension stub, CI) and prompt packs.
- **Phase 4:** Implement orchestrator services, block catalog, integration service.
- **Phase 5:** Pilot on Basel-I Structure Trio; capture success metrics.
- **Phase 6–7:** Launch runbooks, training, quarterly reviews.

## 8. Acceptance Criteria (Sample)
| AC ID | Description | Verification |
| --- | --- | --- |
| AC-PLAN-001 | Planner flow returns ordered work packages with referenced TaskObject IDs | Unit + integration tests; reviewer QA |
| AC-BLOCK-001 | BlockBlueprint with schemas auto-generates contract tests | Automated test harness |
| AC-CAT-001 | Publishing to catalog requires verification decision + artifacts | CI gating |
| AC-INTEG-001 | Basel-I pilot run from single CLI command completes plan→docs with no manual steps | Pilot report |

## 9. Analytics & Measurement
- Track Idea→Verified duration, % AI-originated code, token spend, flow success rate, mutation kill-rate.

## 10. Rollout & Risks
- **Pilot:** Basel-I within first 6 weeks; success metrics defined per playbook.
- **Rollout:** Stage to additional repos after G5.
- **Risks:** Adoption lag, cost overruns, model drift. Mitigations align with playbook §9 and §11.

## 11. Scope Deltas (Updated During Build)

**Added to Scope (Post-G2):**
- **FR-6:** Basel-I specific contracts for Compliance Attestation, Observability Dashboard, and Financial Reporting blocks (see `planning/30_design/schemas/contracts/*`). Added to support pilot completeness; approved at design review.
- **NFR-7:** Artifact immutability enforcement via SHA-256 content hashing in context bundles (Engineering raised during Phase 3; TL approved).
- **UX-2:** Enhanced CLI error messaging with suggested fixes for common BLOCKER patterns (QA feedback; P1 → P0 for pilot UX).

**Descoped (Moved to Post-Pilot Backlog):**
- VS Code extension (complex IDE integration) → deferred to Phase 7; CLI + CI sufficient for pilot.
- 4th model (tests specialist) → pilot uses GPT-4 Turbo for test generation; dedicated model evaluation moved to Q1 2026.
- Multi-repo orchestration dashboard → single-repo view sufficient for Basel-I pilot; consolidated view pushed to GA.

**Linked AC Updates:**
- AC-PLAN-001, AC-IMPL-001, AC-REVIEW-001 → expanded with artifact hash validation (see RTM `planning/20_definition/acceptance_criteria.md:5-7`).

## 12. Open Questions (Resolved)
1. ~~Exact budget per flow for pilot?~~ → **Resolved:** $200/feature envelope; actual $142 pilot avg (Biz evidence).
2. ~~Which 4th model (tests specialist)?~~ → **Resolved:** GPT-4 Turbo reused; dedicated model deferred.
3. ~~Scope of VS Code integration?~~ → **Resolved:** Descoped for MVP; CLI/CI only.

## 13. References
- Governance Framework v1.0
- Multi-LLM Block Engineering Playbook v1.0
- Orchestrator + Blocks framework doc
- Pilot ROI evidence: `planning/50_pilot/evidence/biz/roi_template.md`
- Architecture diagrams: `planning/30_design/architecture_diagrams/*.png`
