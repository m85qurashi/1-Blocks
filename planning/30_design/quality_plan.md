# Quality Plan (Design Phase)

Primary reference: `5-QA/artifacts/quality_plan.md`.

Highlights:
- Contract-first validation + schema enforcement (see `planning/30_design/schemas/task_object.schema.json` and `.../block_blueprint.schema.json`).
- Layered testing incl. mutation (≥60% kill-rate) and orchestrator review gates.
- Generated test plan: schema-driven generators emit unit/property suites stored under `tests/generated/` per block (linked via RTM in `planning/20_definition/acceptance_criteria.md`).
- Basel-I pilot metrics defined (BLOCKERS ≥95% caught, reliability soak <1% failure).
- CI gating order documented (schema → generated tests → unit/integration → mutation → review).
