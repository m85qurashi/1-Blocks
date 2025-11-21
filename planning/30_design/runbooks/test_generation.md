# Generated Test Plan

## Overview
- Source: BlockBlueprint + JSON Schemas produce deterministic test suites stored under `tests/generated/{block_id}/`.
- Generator tool consumes `planning/30_design/schemas/block_blueprint.schema.json` and per-block contracts (e.g., `contracts/structure_trio/input.v1.json`).

## Pipelines
1. Parse blueprint → emit schema diffs.
2. Generate unit/property tests covering required vs optional fields.
3. Configure mutation harness to target generated unit tests automatically.

## Outputs
- `tests/generated/{block_id}/test_contracts.py`
- `tests/generated/{block_id}/test_property.py`
- Manifest linking AC IDs to generated test files.

## Ownership
- QA + App Eng maintain generator logic; TL approves schema changes.
