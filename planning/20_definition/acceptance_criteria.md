# Acceptance Criteria & Requirements Traceability Matrix (RTM)

## RTM Overview
This matrix links functional requirements (FR), acceptance criteria (AC), test files, and verification status for Delivery A/B/C.

| AC ID | FR Link | Description | Test File(s) | Verification Status | Owner |
| --- | --- | --- | --- | --- | --- |
| AC-PLAN-001 | FR-1 | Planner flow outputs ordered work packages referencing TaskObject IDs (validated by `planning/30_design/schemas/task_object.schema.json`) | `src/tests/flows/test_plan_flow.py`<br>`src/tests/flows/test_plan_integration.py` | ✅ Passed (pilot) | Product + Eng |
| AC-IMPL-001 | FR-1 | Implementation flow applies context bundle and returns code patch + rationale | `src/tests/flows/test_impl_flow.py`<br>`src/tests/flows/test_context_application.py` | ✅ Passed (pilot) | Eng |
| AC-REVIEW-001 | FR-1 | Review flow emits BLOCKERS/WARNINGS using rubric, fails pipeline on BLOCKERS | `src/tests/flows/test_review_flow.py`<br>`src/tests/flows/test_blocker_detection.py` | ✅ Passed (pilot) | QA |
| AC-BLOCK-001 | FR-2 | BlockBlueprint autoproduces JSON Schemas + generated contract tests (refs `planning/30_design/schemas/block_blueprint.schema.json`) | `src/tests/contracts/test_block_blueprint_contracts.py`<br>`src/tests/contracts/test_schema_generation.py` | ✅ Passed (pilot) | QA + App Eng |
| AC-BLOCK-002 | FR-2 | Verification service records mutation kill-rate ≥60% | `src/tests/verification/test_mutation_harness.py`<br>`src/tests/verification/test_kill_rate_calculation.py` | ✅ Passed (68% avg) | QA |
| AC-CAT-001 | FR-3 | Catalog publish gated on verification decision + artifact links | `src/tests/catalog/test_publish.py`<br>`src/tests/catalog/test_publish_validation.py` | ✅ Passed (pilot) | Eng |
| AC-INTEG-001 | FR-4 | Basel-I pilot command executes plan→impl→review→docs end-to-end | `src/tests/e2e/test_basel_pilot_scenario.py`<br>`src/tests/e2e/test_artifact_immutability.py` | ✅ Passed (4 runs) | Eng + PM |
| AC-HASH-001 | NFR-7 | Context bundle artifacts hashed (SHA-256) and verified immutable | `src/tests/integration/test_artifact_hashing.py` | ✅ Passed (pilot) | Eng |
| AC-DASH-001 | FR-5 | Dashboards display token usage, latency, BLOCKER counts per flow | Manual verification + Grafana snapshots | ✅ Validated (Data) | Data + SRE |

## Additional Pilot-Specific AC (Basel-I)

| AC ID | Description | Test File(s) | Verification Status | Notes |
| --- | --- | --- | --- | --- |
| AC-BASEL-001 | Structure Trio block reproduces golden output (exact match) | `src/tests/pilot/test_structure_trio_golden.py` | ✅ `verified_exact` | 4/4 pilot runs matched |
| AC-BASEL-002 | Compliance Attestation block validates contract I/O schemas | `src/tests/pilot/test_compliance_attestation_contract.py` | ✅ Passed | Schema validation 100% |
| AC-BASEL-003 | Observability Dashboard block generates valid Grafana JSON | `src/tests/pilot/test_observability_dashboard_output.py` | ✅ Passed | Output validated vs spec |
| AC-BASEL-004 | Financial Reporting block calculates metrics per Basel-I spec | `src/tests/pilot/test_financial_reporting_calculations.py` | ✅ Passed | Calculation accuracy verified |

## RTM Summary
- **Total AC:** 13 (9 core + 4 pilot-specific)
- **Verified/Passed:** 13/13 (100%)
- **Test Coverage:** 23 test files mapped
- **Pilot Status:** All Basel-I AC met; ready for G5 gate

## References
- Test suite root: `src/tests/`
- Schema definitions: `planning/30_design/schemas/`
- Pilot evidence: `planning/50_pilot/evidence/qa/`
