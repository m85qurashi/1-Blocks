# PRD v1 — Multi-LLM Orchestrator + Blocks

Canonical source: `3- Product/artifacts/prd_v1.md`. This copy summarizes key sections for the planning package.

## Goals & Context
Deliver Delivery Plans A (orchestrator), B (blocks), and C (integration) to cut idea→verified cycle time by 30% while maintaining cost/quality guardrails.

## Users & Journeys
- Platform/App engineers (CLI/CI flows)
- PM/Architect reviewers (plan/review outputs)
- QA/SRE teams (verification + ops)

Journeys: plan→impl→review→docs orchestration; block authoring + catalog; Basel-I pilot run.

## Requirements Snapshot
| ID | Requirement |
| --- | --- |
| FR-1 | `/flows/plan|impl|review|docs` APIs + CLI/CI integration |
| FR-2 | 6-face BlockBlueprint + JSON Schema contracts |
| FR-3 | Block Catalog with verification outcomes |
| FR-4 | Integration layer TaskObject↔Blueprint |
| FR-5 | Dashboards for tokens, latency, BLOCKERS |

Non-functional: security (secrets, PII redaction), performance (≥99% success, P95 latency targets), cost (token caps), reliability (replayable runs).

## Acceptance Criteria Seeds
- AC-PLAN-001: Planner flow returns ordered work packages tied to TaskObject IDs.
- AC-BLOCK-001: Blueprint generates contract tests automatically.
- AC-CAT-001: Catalog publish requires verification decision + artifacts.
- AC-INTEG-001: Basel-I pilot run completes plan→docs with single CLI command.

## Risks
Adoption, cost overruns, model drift. Mitigations: training, cost guards, prompt versioning.
