# System Requirements Specification (SRS)
## 1. Overview
Defines system-level requirements for Delivery A (Model Orchestrator), Delivery B (Verified Blocks), and Delivery C (Platform Integration) supporting the Multi-LLM Block Engineering Playbook v1.0.

## 2. System Context
- **Actors:** Developers (CLI/VS Code/CI), Orchestrator services, Block Catalog, Integration service, Metrics stack.
- **Interfaces:** REST APIs `/flows/{plan,impl,review,docs}`, CLI commands, CI hooks, catalog CRUD endpoints, context bundle storage.

## 3. Functional Requirements
### 3.1 Orchestrator (Delivery A)
| ID | Requirement |
| --- | --- |
| A-FR-1 | Support `models.yaml` with role assignments (planner, implementer, reviewer, analyst, tester) and token budgets. |
| A-FR-2 | FlowEngine executes plan→impl→review→docs pipelines using TaskObject inputs; persists artifacts in TaskDB. |
| A-FR-3 | ContextBuilder compiles repo state (files, diffs, blueprints) per request with deterministic hashing. |
| A-FR-4 | ResponseMerger aggregates multi-model outputs, preserving provenance. |
| A-FR-5 | CLI/CI integration triggers flows with idempotent request IDs and exposes status. |

### 3.2 Blocks (Delivery B)
| ID | Requirement |
| --- | --- |
| B-FR-1 | BlockBlueprint schema captures six faces + metadata; validated before storing. |
| B-FR-2 | JSON Schemas for left/right faces auto-generate contract tests. |
| B-FR-3 | Verification service executes unit, integration, property, mutation suites; stores mutation kill-rate. |
| B-FR-4 | Catalog publishes `block_id@version` once verification decision recorded and artifacts linked. |
| B-FR-5 | Supports verification outcomes `verified_exact`, `verified_equivalent`, `needs_revision`. |

### 3.3 Integration (Delivery C)
| ID | Requirement |
| --- | --- |
| C-FR-1 | Mapping layer translates TaskObject outputs to BlockBlueprint inputs via context bundle schema. |
| C-FR-2 | Artifact registry stores SRS drafts, review reports, ADRs with immutable links. |
| C-FR-3 | End-to-end CLI command executes plan→impl→review→docs using both orchestrator and block services, producing replayable run metadata. |

## 4. Non-Functional Requirements
- **Performance:** Flow success rate ≥99%; P95 latency threshold defined by PM (target < 90s per plan/impl cycle for pilot).
- **Reliability:** Retry policies; audit logs; Task/Block IDs stable; ability to replay flows.
- **Security:** Secrets isolated; prompts sanitized; compliance with PII policy.
- **Scalability:** Support concurrent flows (min 10) with isolated budgets.
- **Observability:** Emit metrics (tokens, latency, BLOCKERS, mutation rates) to dashboards defined in Delivery Plan A/B.

## 5. Data Requirements
- TaskDB schema storing TaskObject, artifacts, run metadata.
- Block Catalog schema storing block metadata, verification status, contract URIs.
- Context bundle schema (JSON) including blueprint slices, file diffs, test results.

## 6. External Constraints
- Vendor limits for LLM APIs; budget enforcement required.
- Compliance: secrets plan, audit requirements from Governance Framework.
- Tooling: CLI must run in developer workstations and CI containers.

## 7. Verification & Validation
- CI gating pipeline validates JSON Schemas, runs generated tests, triggers orchestrator review flows, enforces mutation thresholds.
- Basel-I Structure Trio is canonical pilot scenario verifying cross-system behavior.

## 8. Traceability
| Source | Requirement IDs |
| --- | --- |
| PRD v1 (Product) | FR-1..FR-5, AC mapping |
| Playbook | Contract-first, mutation thresholds, multi-model roles |
| Governance Framework | Gate requirements G2–G6 |

## 9. Technical Decisions (ADR Index)

### ADR-001: TaskDB Storage Technology
**Decision:** PostgreSQL with JSONB columns for TaskObject payloads
**Date:** Oct 15, 2025
**Status:** Accepted (Pilot-Validated)
**Context:** Need ACID guarantees for task/artifact lineage; flexible schema for evolving TaskObject.
**Rationale:**
- Postgres JSONB provides schema flexibility + rich querying (GIN indexes)
- ACID transactions critical for artifact immutability guarantees
- Team expertise; existing infra support
**Consequences:**
- (+) Strong consistency; reliable audit trail
- (+) JSON Schema validation via CHECK constraints
- (-) More complex ops than document DB (mitigated by managed RDS)
**Alternatives Considered:** MongoDB (rejected: weaker consistency), DynamoDB (rejected: query limitations)

---

### ADR-002: Context Bundle Determinism Strategy
**Decision:** Hash-based content addressing + canonical JSON serialization
**Date:** Oct 22, 2025
**Status:** Accepted (Pilot-Validated)
**Context:** Model outputs non-deterministic; need stable artifact references for replay.
**Rationale:**
- SHA-256 hash of bundle contents = immutable content ID
- Canonical JSON (sorted keys, no whitespace variance) ensures repeatability
- Bundle references model outputs but doesn't rehash model responses (preserves provenance)
**Implementation:**
- `ContextBuilder` uses `json.dumps(sort_keys=True, separators=(',', ':'))` before hashing
- Artifact registry validates hash on write; returns 409 Conflict if hash mismatch
**Consequences:**
- (+) Immutability guaranteed; tamper detection
- (+) Replay flows by referencing stable bundle IDs
- (-) Storage overhead (bundles not deduplicated; mitigated by S3 lifecycle policies)

---

### ADR-003: 4th Model (Test Specialist) Sandboxing
**Decision:** Reuse GPT-4 Turbo for pilot; defer dedicated test model to Phase 7
**Date:** Nov 1, 2025
**Status:** Accepted (Pilot Decision)
**Context:** Budget constraints + vendor contract negotiations ongoing.
**Rationale:**
- GPT-4 Turbo adequate for contract test generation (pilot evidence: 100% schema validation)
- Dedicated test model (e.g., Codex, Gemini Pro for code) deferred until ROI proven at scale
- Cost guardrails enforced via per-flow token caps (test generation ≤15K tokens/run)
**Consequences:**
- (+) Simplified pilot; reduced vendor surface
- (-) Suboptimal for complex property-based test generation (acceptable for pilot scope)
- (!) Revisit Q1 2026 once Anthropic releases Claude for code specialization

---

### ADR-004: Verification Service Test Harness
**Decision:** Pytest + Hypothesis (property-based) + Mutmut (mutation testing)
**Date:** Oct 28, 2025
**Status:** Accepted (Pilot-Validated)
**Context:** Need automated verification pipeline for blocks.
**Rationale:**
- Pytest: industry-standard; team expertise
- Hypothesis: property-based testing for contract validation (e.g., "all outputs satisfy schema")
- Mutmut: mutation testing to ensure ≥60% kill-rate threshold (pilot achieved 68%)
**Implementation:**
- Harness at `src/verification/harness.py`
- CI integration: `pytest --hypothesis-profile=ci --cov=90`
- Mutation runs: `mutmut run --paths-to-mutate=src/blocks/`
**Consequences:**
- (+) High test confidence; pilot defect rate -25% vs baseline
- (-) Mutation runs slow (~12min/block; mitigated by parallel CI runners)

---

### ADR-005: Integration Service Architecture
**Decision:** Event-driven mapping layer using AWS EventBridge + Lambda
**Date:** Nov 3, 2025
**Status:** Accepted (Pilot-Validated)
**Context:** Need loose coupling between Orchestrator (A) and Blocks (B).
**Rationale:**
- TaskObject completion triggers event → Lambda transforms → invokes Block Catalog API
- Decouples Orchestrator/Block release cycles
- Supports async workflows (e.g., long-running verification jobs)
**Implementation:**
- EventBridge rule: `TaskObject.status == "completed"` → invoke `IntegrationMapper` Lambda
- Lambda reads context bundle, extracts blueprint, publishes to Block Catalog
**Consequences:**
- (+) Scalable; supports future multi-region deployments
- (+) Fault-tolerant; DLQ for failed transformations
- (-) Increased ops complexity (CloudWatch monitoring, Lambda cold starts; mitigated by provisioned concurrency)

---

### ADR-006: FlowEngine Retry & Fault Tolerance
**Decision:** Exponential backoff + circuit breaker pattern
**Date:** Oct 18, 2025
**Status:** Accepted (Pilot-Validated)
**Context:** LLM API rate limits; transient failures (network, timeouts).
**Rationale:**
- Retry policy: 3 attempts, exponential backoff (1s, 2s, 4s)
- Circuit breaker: open after 5 consecutive failures; half-open after 60s
- Fail fast on non-retryable errors (400 Bad Request, quota exceeded)
**Implementation:**
- `FlowEngine` uses `tenacity` library for retries
- Circuit breaker via `pybreaker` library
- Metrics emitted to CloudWatch (retry counts, circuit state)
**Consequences:**
- (+) 99.2% flow success rate (pilot target: ≥99%)
- (+) Graceful degradation under vendor outages
- (-) Latency variance during retries (P95 increased by ~8s; within SLO)

---

### ADR-007: Artifact Immutability via SHA-256 Hashing
**Decision:** Content-addressable storage with hash verification on read/write
**Date:** Oct 25, 2025
**Status:** Accepted (Pilot-Validated)
**Context:** Need tamper-proof audit trail for compliance.
**Rationale:**
- Every artifact (context bundle, review report, ADR) hashed on write
- Hash stored in metadata; verified on every read
- S3 Object Lock (WORM mode) prevents deletion for 7 years (Basel-I retention requirement)
**Implementation:**
- `ArtifactRegistry.store(content)` → computes SHA-256 → stores with `Content-Hash` metadata
- `ArtifactRegistry.get(uri)` → reads, recomputes hash, validates match
**Consequences:**
- (+) Immutability guaranteed; caught 2 pilot bugs (accidental overwrites)
- (+) Audit-ready; compliance-friendly
- (-) Storage costs (no deduplication; mitigated by lifecycle policies)

---

## 10. Implementation Notes

### FlowEngine Architecture
**Component:** `src/orchestrator/flow_engine.py`
**Purpose:** Execute plan/impl/review/docs pipelines using multi-model routing

**Key Classes:**
- `FlowEngine`: Orchestrates flow execution; delegates to ModelRouter
- `ModelRouter`: Routes tasks to Claude/GPT/Gemini based on `models.yaml` role assignments
- `ContextBuilder`: Assembles context bundles (repo state, blueprints, diffs)
- `ResponseMerger`: Aggregates multi-model outputs; preserves provenance

**Flow Execution Sequence:**
1. CLI invokes `flow exec plan --task-id abc123`
2. `FlowEngine` reads `models.yaml`, assigns planner role to GPT-4 Turbo
3. `ContextBuilder` compiles repo state → context bundle (hashed, stored)
4. `ModelRouter` sends prompt + context to GPT-4 Turbo
5. `ResponseMerger` validates response, extracts work packages, stores in TaskObject
6. TaskObject written to TaskDB; event emitted (triggers Integration Service)

**Pilot Logs:** See `planning/50_pilot/evidence/qa/flowengine_run_logs.md` for 4 end-to-end runs.

---

### Verification Service Architecture
**Component:** `src/verification/verification_service.py`
**Purpose:** Execute test suites, record mutation kill-rate, set verification status

**Key Classes:**
- `VerificationService`: Orchestrates test execution
- `TestHarness`: Runs unit/integration/property/mutation tests
- `MutationAnalyzer`: Computes kill-rate from Mutmut output
- `VerificationDecision`: Records status (`verified_exact`, `verified_equivalent`, `needs_revision`)

**Verification Flow:**
1. Engineer publishes block blueprint to catalog (status: `pending_verification`)
2. Catalog triggers `VerificationService` via EventBridge
3. Service clones repo, installs deps, runs `pytest` + `mutmut`
4. `MutationAnalyzer` parses Mutmut JSON report → computes kill-rate
5. If kill-rate ≥60% + all tests pass → status = `verified_exact` (or `verified_equivalent` if golden output fuzzy-matched)
6. Status + logs written to catalog; notification sent to author

**Pilot Results:** 4/4 blocks achieved `verified_exact`; avg mutation kill-rate 68%.

---

### Integration Service Architecture
**Component:** `src/integration/integration_service.py` (Lambda)
**Purpose:** Map TaskObject outputs → BlockBlueprint inputs via context bundles

**Key Functions:**
- `handle_task_completion(event)`: EventBridge trigger on TaskObject completion
- `extract_blueprint(context_bundle)`: Parse context bundle, extract blueprint artifacts
- `publish_to_catalog(block_id, blueprint, artifacts)`: Invoke Block Catalog API

**Integration Sequence:**
1. Orchestrator completes review flow → emits `TaskCompleted` event
2. EventBridge routes to `IntegrationMapper` Lambda
3. Lambda reads context bundle from S3
4. Extracts code patches, review reports, ADRs
5. Constructs BlockBlueprint (six faces populated from artifacts)
6. Publishes to Block Catalog with status `pending_verification`

**Pilot Validation:** 4/4 end-to-end runs completed successfully; average Lambda duration 1.2s.

---

## 11. Open Technical Questions (Resolved)
1. ~~Storage technology for TaskDB and Block Catalog?~~ → **Resolved:** PostgreSQL (ADR-001)
2. ~~Best approach for deterministic context bundles?~~ → **Resolved:** SHA-256 hashing + canonical JSON (ADR-002)
3. ~~Strategy for sandboxing 4th model?~~ → **Resolved:** Reuse GPT-4 Turbo for pilot; defer dedicated model (ADR-003)
