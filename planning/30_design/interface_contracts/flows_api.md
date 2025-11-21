# Flow API Contract

## Endpoint
`POST /flows/{type}` where `{type} ∈ {plan, impl, review, docs}`

### Request Schema (JSON)
```
{
  "task_id": "string",
  "flow_type": "plan",
  "context_bundle_ref": "uri",
  "inputs": {
    "repo": "git@...",
    "branch": "feature/...",
    "blueprint_ref": "blueprints/...",
    "goals": ["..."],
    "constraints": ["..."]
  },
  "budgets": {
    "tokens": 20000,
    "latency_ms": 90000
  },
  "metadata": {
    "request_id": "uuid",
    "caller": "cli|ci"
  }
}
```

### Response Schema
```
{
  "task_id": "string",
  "flow_type": "plan",
  "status": "succeeded|failed",
  "outputs": {
    "work_packages": [
      {"id": "WP-001", "description": "...", "owner_model": "chatgpt"}
    ],
    "artifacts": ["s3://.../plan.md"]
  },
  "metrics": {
    "tokens_used": 5234,
    "latency_ms": 45000,
    "models": [
      {"name": "chatgpt", "role": "planner", "tokens": 4000}
    ]
  },
  "annotations": {
    "blockers": [],
    "warnings": []
  }
}
```

### Error Codes
- `400` validation failure (missing context bundle).
- `402` budget exceeded.
- `409` task already in progress.
- `500` orchestration error.
