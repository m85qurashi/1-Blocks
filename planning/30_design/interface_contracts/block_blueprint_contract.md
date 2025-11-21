# BlockBlueprint Contract

```yaml
block_id: structure_trio_block
version: 1.0.0
faces:
  bottom_structure_spec:
    datastore: postgres
    tables:
      - name: basel_structures
        columns:
          - { name: structure_key, type: text, constraints: [primary_key] }
  front_ui_spec:
    type: wizard
    steps:
      - name: master
        fields: [...]
  back_integration_spec:
    sinks:
      - type: queue
        name: audit_events
  top_logic_spec:
    invariants:
      - "levels must align with allowed sets"
  left_input_contract:
    schema_ref: contracts/structure_trio/input.v1.json
  right_output_contract:
    schema_ref: contracts/structure_trio/output.v1.json
acceptance_criteria:
  - id: AC-001
    text: Duplicate structure_key rejected with S_409
traceability:
  - ac_id: AC-001
    tests:
      - tests/contracts/test_duplicate_structure.py
```

Additional example (`planning/30_design/schemas/examples/compliance_attestation_blueprint.yaml`) shows how a compliance block references `contracts/compliance_attestation/*.json` schemas for left/right faces.

Rules:
- All six faces required.
- `schema_ref` must point to versioned JSON schema stored under `planning/30_design/schemas/`.
- AC IDs must map to RTM entries in `planning/20_definition/acceptance_criteria.md`.
