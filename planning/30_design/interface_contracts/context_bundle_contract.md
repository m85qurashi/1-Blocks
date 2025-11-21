# Context Bundle Contract

```
{
  "bundle_id": "uuid",
  "task_id": "T-2025-0001",
  "blueprint_slice": {
    "block_id": "structure_trio_block",
    "version": "1.0.0"
  },
  "repo_state": {
    "files": [
      {"path": "src/service.py", "content_hash": "sha256-..."}
    ],
    "diff": "patch"
  },
  "tests": {
    "unit": ["tests/unit/test_structure.py"],
    "integration": ["tests/integration/test_structure_flow.py"],
    "property": [],
    "mutation": {
      "plan": "nightly",
      "baseline_kill_rate": 0.6
    }
  },
  "constraints": ["budget:tokens<20000"],
  "metadata": {
    "generated_at": "2025-01-05T12:00:00Z",
    "generator_version": "cbuilder-0.1.0"
  }
}
```

Validation rules:
- `bundle_id`, `task_id` required; combination must be unique.
- `blueprint_slice` must align with BlockBlueprint contract version.
- `repo_state.files[].content_hash` uses SHA256 for immutability.
- `tests.mutation.baseline_kill_rate` captured for QA gating.
