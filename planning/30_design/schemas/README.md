# Schema Documentation — Final Release

**Version:** 1.0 (Pilot-Validated)
**Last Updated:** Nov 13, 2025
**Owner:** Engineering Persona (Platform + App Eng)

---

## Schema Registry

### Core Schemas

#### 1. TaskObject Schema (`task_object.schema.json`)
**Purpose:** Defines orchestrator payload structure for plan/impl/review/docs flows.

**Key Properties:**
- `task_id` (string, UUID): Unique identifier for orchestrator run
- `flow_type` (enum): `plan`, `impl`, `review`, `docs`
- `context_bundle_uri` (string, URI): Link to immutable context artifact
- `artifacts` (array): Ordered list of output artifacts (code patches, review reports, ADRs)
- `metadata` (object): Token usage, latency, model routing decisions, BLOCKER counts

**Validation Rules:**
- `task_id` must be UUIDv4
- `context_bundle_uri` must resolve and pass SHA-256 hash check
- All artifacts must reference valid storage URIs

**Example Use Cases:**
- CLI command `flow exec plan --task-id abc123` generates TaskObject
- CI pipeline reads TaskObject to determine review status (BLOCKERS present → fail build)

---

#### 2. BlockBlueprint Schema (`block_blueprint.schema.json`)
**Purpose:** Validates 6-face block definitions (structure, UI, integration, logic, input, output).

**Six Faces (Required):**
1. **Structure Face** (`structure`): Component/module organization, dependencies, ADR links
2. **UI Face** (`ui`): User touchpoints (CLI args, config files, error messages)
3. **Integration Face** (`integration`): External APIs, message formats, auth patterns
4. **Logic Face** (`logic`): Core algorithms, business rules, calculation specs
5. **Left Face** (`input_schema_uri`): JSON Schema URI for block inputs
6. **Right Face** (`output_schema_uri`): JSON Schema URI for block outputs

**Metadata Properties:**
- `block_id` (string): Unique block identifier (e.g., `basel-i-structure-trio`)
- `version` (string, semver): Block version (e.g., `1.0.0`)
- `verification_status` (enum): `verified_exact`, `verified_equivalent`, `needs_revision`
- `author`, `created_at`, `updated_at`

**Validation Rules:**
- All six faces must be non-empty
- Input/output schema URIs must resolve to valid JSON Schemas
- Verification status required before catalog publish

**Example Use Cases:**
- Block authoring: Engineer writes `basel-i-compliance.yaml` → schema validates → auto-generates contract tests
- Catalog publish: Verification service checks mutation kill-rate ≥60% → sets status → publishes to catalog

---

### Contract Schemas (Block-Specific)

#### 3. Structure Trio Contracts (`contracts/structure_trio/`)
**Block Family:** Basel-I compliance foundations
**Purpose:** Define input/output for structure extraction/validation block

**Files:**
- `input.v1.json`: Accepts source code + metadata → extracts structure
- `output.v1.json`: Returns structured JSON (modules, dependencies, ADR references)

**Example:**
```json
// input.v1.json excerpt
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["source_files", "extraction_rules"],
  "properties": {
    "source_files": {"type": "array", "items": {"type": "string"}},
    "extraction_rules": {"type": "object"}
  }
}
```

**Pilot Validation:** ✅ 4/4 runs passed schema validation; `verified_exact` status achieved.

---

#### 4. Compliance Attestation Contracts (`contracts/compliance_attestation/`)
**Block Family:** Basel-I regulatory reporting
**Purpose:** Validate compliance attestation inputs/outputs per Basel-I spec

**Files:**
- `input.v1.json`: Accepts attestation request (entity, period, control IDs)
- `output.v1.json`: Returns attestation report (status, evidence links, auditor notes)

**Key Requirements:**
- Input must include ISO-8601 date ranges
- Output includes digital signature field (reserved for future PKI integration)

**Example Blueprint:** `examples/compliance_attestation_blueprint.yaml`

**Pilot Validation:** ✅ Schema validation 100%; contract tests generated and passed.

---

#### 5. Observability Dashboard Contracts (`contracts/observability_dashboard/`)
**Block Family:** Monitoring & dashboards
**Purpose:** Generate Grafana-compatible dashboard JSON from metrics spec

**Files:**
- `input.v1.json`: Metrics list, panel layouts, alert thresholds
- `output.v1.json`: Grafana dashboard JSON (panels, queries, variables)

**Key Requirements:**
- Input metrics must reference valid Prometheus/InfluxDB queries
- Output must validate against Grafana v10+ schema

**Example Blueprint:** `examples/observability_dashboard_blueprint.yaml`

**Pilot Validation:** ✅ Output validated against Grafana schema; dashboards deployed and functional.

---

#### 6. Financial Reporting Contracts (`contracts/financial_reporting/`)
**Block Family:** Basel-I financial metrics
**Purpose:** Calculate regulatory financial metrics per Basel-I formulas

**Files:**
- `input.v1.json`: Balance sheet data, reporting period, regulatory framework version
- `output.v1.json`: Calculated metrics (capital ratios, risk weights, compliance flags)

**Key Requirements:**
- Input must include Basel-I framework version (e.g., `basel-i-v3.1`)
- Output includes calculation audit trail (formula references, intermediate values)

**Example Blueprint:** `examples/financial_reporting_blueprint.yaml`

**Pilot Validation:** ✅ Calculation accuracy verified against reference implementation; 100% match.

---

## Schema Versioning & Change Control

### Versioning Scheme
- **Major version** (v1 → v2): Breaking changes (remove required fields, change types)
- **Minor version** (v1.0 → v1.1): Additive changes (new optional fields)
- **Patch version** (v1.0.0 → v1.0.1): Documentation, examples, non-breaking fixes

### Change Control Process
1. Propose schema change via ADR (see `4-Engineering/artifacts/srs.md` ADR index)
2. Update schema + examples
3. Regenerate contract tests via harness
4. Validate with pilot data
5. Version bump + catalog publish

### Deprecation Policy
- Deprecated schemas supported for 2 major versions (e.g., v1 supported until v3 release)
- Breaking changes require 90-day notice to downstream consumers

---

## Integration with Orchestrator

### Context Bundle Schema (Orchestrator ↔ Blocks)
**File:** `context_bundle.schema.json` (referenced by TaskObject)

**Purpose:** Package repo state, blueprints, test results for model consumption

**Structure:**
```json
{
  "bundle_id": "uuid",
  "created_at": "ISO-8601 timestamp",
  "content_hash": "SHA-256 of bundle contents",
  "artifacts": [
    {"type": "blueprint", "uri": "s3://..."},
    {"type": "code_patch", "uri": "s3://..."},
    {"type": "review_report", "uri": "s3://..."}
  ]
}
```

**Immutability Guarantee:** Content hash verified on every read; tampering detection.

---

## Developer Experience

### Schema Tooling
- **Validation CLI:** `schema validate --input block.yaml --schema block_blueprint.schema.json`
- **Test Generation:** `schema gen-tests --contract contracts/compliance_attestation/` → auto-generates contract test suite
- **Documentation:** JSON Schemas auto-render docs via `schema docs --output html/`

### Quick Start (Block Authors)
1. Copy example blueprint: `cp examples/compliance_attestation_blueprint.yaml my_block.yaml`
2. Edit six faces + metadata
3. Validate: `schema validate --input my_block.yaml`
4. Generate tests: `schema gen-tests --blueprint my_block.yaml`
5. Run verification harness
6. Publish to catalog once `verified_exact` or `verified_equivalent`

---

## References & Governance

- **ADRs:** See `4-Engineering/artifacts/srs.md` § ADR Index for schema design decisions
- **RTM:** Contract schemas mapped to AC in `planning/20_definition/acceptance_criteria.md`
- **Pilot Evidence:** Schema validation logs in `planning/50_pilot/evidence/qa/flowengine_run_logs.md`
- **Governance:** Schema changes require TL approval (RACI: Eng R/A, PM C, QA C)

---

**Status:** ✅ Production-ready; all pilot schemas validated and in active use.
**Next Iterations:** Expand to additional block families (auth, data pipelines, ML inference) in Phase 7.
