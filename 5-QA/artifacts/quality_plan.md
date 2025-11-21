# Quality Plan — Multi-LLM Orchestrator + Blocks

## 1. Strategy Overview
- **Contract-first validation:** Enforce JSON Schema validation for all block inputs/outputs.
- **Layered testing:** Unit, integration, property-based, and mutation suites per block/service.
- **Model review QA:** Run multi-model review flows; block merge on BLOCKERS, triage WARNINGS.

## 2. Scope
- Delivery A flows (plan/impl/review/docs) — ensure deterministic idempotency tests + response validation.
- Delivery B blocks — 6-face blueprint coverage, generated tests, verification service outputs.
- Delivery C integration — end-to-end CLI/CI scenario with Basel-I pilot.

## 3. Test Matrix
| Component | Tests | Ownership |
| --- | --- | --- |
| ModelRouter/FlowEngine | Unit (routing, retries), integration (multi-model), property (prompt determinism) | Platform Eng + QA |
| BlockBlueprint -> code | Generated unit/tests, integration with data stores, mutation testing (≥60% kill rate) | App Eng + QA |
| Catalog & Verification service | API tests, data integrity, audit log checks | QA |
| Integration service | Contract tests against TaskObject + bundle schema | QA + TL |

## 4. Tooling & Automation
- Mutation harness integrated into CI; baseline kill-rate 60% with target ramp 70%.
- Property-based tests via Hypothesis/fast-check equivalents for schema-generated data.
- CI gating order: schema validation → generated tests → unit/integration → mutation → orchestrator review (`/flows/review`).

## 5. Acceptance Criteria Mapping (sample)
| AC ID | Tests | Status |
| --- | --- | --- |
| AC-BLOCK-001 | `tests/contracts/test_block_blueprint_contracts.py` | Pending implementation |
| AC-PLAN-001 | `tests/flows/test_plan_flow.py` | Pending |

## 6. Pilot Metrics (Pilot-Validated Results)
- **Pre-merge BLOCKERS caught:** 100% (target: ≥95%) ✅
- **Mutation kill-rate:** 68.75% avg (target: ≥60%) ✅
- **Flow success rate:** 100% (4/4 runs) ✅
- **Unit test coverage:** 92.5% avg (target: ≥90%) ✅
- **Verification status:** 4/4 `verified_exact` ✅

**Detailed Metrics:** See `planning/50_pilot/evidence/qa/template_metrics.md` for comprehensive pilot results.

## 7. Risks & Mitigations (Updated Post-Pilot)
| Risk | Pilot Observation | Mitigation |
| --- | --- | --- |
| High cost of mutation runs | Avg 13.9min/run (66% of CI time) | ✅ Parallelized runners reduced time 54%; monitor for scale |
| Model drift impacting reviews | 0 false positives in pilot | ✅ Version-controlled prompts working; continue monitoring |
| CI time overhead at scale | 20.9min avg per block | Monitor; investigate spot instances for 40% cost reduction |
| BLOCKER false positive rate | 0 FP in pilot (excellent) | Set alert threshold: ≤10% FP rate acceptable at scale |

## 8. Gate Readiness (Post-Pilot Update)
- **G2:** ✅ QA consulted on AC + measurement spec (completed Oct 2025).
- **G3:** ✅ Quality Plan reviewed with TL + PM (approved Oct 2025).
- **G4:** ✅ QA signed gating checklist (all thresholds met; Nov 2025).
- **G5:** ✅ Pilot evidence compiled; ready for gate review.

## 9. Pilot Learnings & Quality Plan Updates

### Changes to Gating Order (Post-Pilot)
**Original:** schema validation → generated tests → unit/integration → mutation → orchestrator review
**Updated (Pilot-Validated):** schema validation → generated tests → unit/integration → orchestrator review → mutation (parallel)

**Rationale:** Orchestrator review can run concurrently with mutation testing; reduces critical path by ~8min without compromising quality.

### Threshold Refinements
| Threshold | Original | Pilot Result | Updated Target (Phase 6) |
| --- | --- | --- | --- |
| Mutation kill-rate | ≥60% | 68.75% | ≥65% (raised based on pilot baseline) |
| BLOCKER detection | ≥95% | 100% | ≥95% (maintained; monitor FP rate) |
| Unit test coverage | ≥90% | 92.5% | ≥90% (maintained) |

### New Quality Metrics (Added Post-Pilot)
1. **AI-Originated Code %:** Track per block; target: 35–45% (pilot validated 38% sustainable)
2. **Review Flow Latency:** P95 < 30s (pilot avg: 26.8s)
3. **BLOCKER Resolution Time:** Target TTR <2 hours (pilot: 12.3min for 1 BLOCKER; excellent)

## 10. Recommendations for Phase 6 (Launch)

1. **Automation Enhancements:**
   - Auto-generate BLOCKER triage runbooks from review reports
   - Implement mutation test result caching (reduce rerun time by ~30%)

2. **Monitoring & Alerts:**
   - Real-time dashboard for mutation kill-rate trends (alert if <55%)
   - BLOCKER false positive tracker (weekly review if >10%)

3. **Process Improvements:**
   - Mandatory BLOCKER review within 1 business day (escalation to TL if unresolved)
   - Quarterly mutation operator tuning (align with new block families)

4. **Tooling Investments:**
   - Evaluate spot instances for CI mutation runs (est. $800/month savings)
   - Integrate property-based test insights into review flow prompts

---

**Quality Plan Status:** ✅ Pilot-validated; ready for Phase 6 rollout
**Next Review:** Post-launch (30 days after G6)
