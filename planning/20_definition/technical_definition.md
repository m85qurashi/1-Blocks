# Technical Definition

Based on Engineering SRS (`4-Engineering/artifacts/srs.md`).

## Components
- **Delivery A:** ModelRouter, FlowEngine, ContextBuilder, ResponseMerger, TaskDB, CLI/CI adapters.
- **Delivery B:** BlockBlueprint schema + validators, test generators, verification service, Catalog.
- **Delivery C:** Integration service, context bundle schema, artifact registry.

## Interfaces
- REST APIs `/flows/{plan,impl,review,docs}`.
- CLI commands mirroring API endpoints.
- Catalog CRUD endpoints for `block_id@version`.
- Context bundle schema connecting TaskObject ↔ BlockBlueprint artifacts.

## Sequencing (High-level)
1. Define schemas (TaskObject, BlockBlueprint, context bundle).
2. Build ModelRouter + FlowEngine with instrumentation.
3. Implement Catalog + verification service.
4. Deliver integration service and CLI/CI experiences.

## Dependencies
- Model provider credentials and budgets.
- Data telemetry stack for metrics.
- QA mutation harness integration.
