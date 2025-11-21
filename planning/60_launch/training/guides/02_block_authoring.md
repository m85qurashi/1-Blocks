# Block Blueprint Authoring Guide

**Module 2:** Creating 6-Face Blocks with Contract-First Design
**Duration:** 45 minutes (workshop format)
**Owner:** Engineering + QA
**Last Updated:** November 16, 2025

---

## Overview

Blocks are modular, contract-validated components following a 6-face architecture. This guide teaches you to author production-ready blocks that integrate seamlessly with the orchestrator.

### What You'll Learn
- 6-face block architecture (Structure, UI, Integration, Logic, Input, Output)
- JSON Schema contract design
- Property-based testing with Hypothesis
- Immutability patterns for artifact storage

### Prerequisites
- Completed Module 1 (CLI Quick-Start)
- Familiarity with JSON Schema
- Python 3.9+ or TypeScript 4.5+

---

## 6-Face Block Architecture

Every block has 6 faces defining its interface and behavior:

```
        ┌─────────────────┐
        │   [Structure]   │  Schema + validation logic
        │   Face #1       │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐   ┌───▼────┐   ┌──▼─────┐
│  [UI]  │   │ [Logic]│   │[Integ.]│
│ Face#2 │   │ Face#4 │   │ Face#3 │
└───┬────┘   └───┬────┘   └──┬─────┘
    │            │            │
    └────────────┼────────────┘
                 │
        ┌────────▼────────┐
        │   [Input Face]  │  Left face: data ingress
        │   Face #5       │
        └─────────────────┘
                 │
        ┌────────▼────────┐
        │  [Output Face]  │  Right face: data egress
        │   Face #6       │
        └─────────────────┘
```

### Face Responsibilities

| Face | Purpose | Artifacts | Owner |
| --- | --- | --- | --- |
| **1. Structure** | Define data contracts (JSON Schema) | `*_input.schema.json`, `*_output.schema.json` | Architect |
| **2. UI** | CLI/API interaction patterns | `cli.py`, `api_handlers.py` | Product + Eng |
| **3. Integration** | External system connectors (EventBridge, webhooks) | `integrations/`, `event_handlers.py` | SRE + Eng |
| **4. Logic** | Core business logic (pure functions preferred) | `logic.py`, `transformations.py` | Engineering |
| **5. Input** | Ingress validation + deserialization | `validators.py`, `parsers.py` | Engineering |
| **6. Output** | Egress serialization + formatting | `formatters.py`, `serializers.py` | Engineering |

---

## Workshop: Building a Compliance Attestation Block

We'll build a Basel-I compliant attestation block step-by-step.

### Step 1: Define Structure Face (Contracts)

Create JSON Schema for input/output:

```bash
mkdir -p blocks/compliance/schemas
cd blocks/compliance/schemas
```

**Input Schema (`compliance_input.schema.json`):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://blocks-orchestrator.com/schemas/compliance_input.v1.json",
  "title": "Compliance Attestation Input",
  "description": "Input for generating Basel-I compliant attestation reports",
  "type": "object",
  "required": ["task_id", "blocks", "retention_years"],
  "properties": {
    "task_id": {
      "type": "string",
      "pattern": "^task_[a-z0-9]{6}$",
      "description": "TaskObject identifier"
    },
    "blocks": {
      "type": "array",
      "description": "List of verified blocks to attest",
      "items": {
        "type": "object",
        "required": ["block_id", "artifact_uri", "sha256"],
        "properties": {
          "block_id": {"type": "string"},
          "artifact_uri": {"type": "string", "format": "uri"},
          "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
        }
      },
      "minItems": 1
    },
    "retention_years": {
      "type": "integer",
      "minimum": 7,
      "description": "Retention period (Basel-I requires ≥7 years)"
    }
  },
  "examples": [{
    "task_id": "task_abc123",
    "blocks": [
      {
        "block_id": "compliance_attestation",
        "artifact_uri": "s3://blocks-prod/compliance_attestation.py",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ],
    "retention_years": 7
  }]
}
```

**Output Schema (`compliance_output.schema.json`):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://blocks-orchestrator.com/schemas/compliance_output.v1.json",
  "title": "Compliance Attestation Output",
  "description": "Generated attestation report with audit trail",
  "type": "object",
  "required": ["report_id", "attestation", "audit_trail"],
  "properties": {
    "report_id": {
      "type": "string",
      "description": "Unique report identifier"
    },
    "attestation": {
      "type": "object",
      "required": ["status", "blocks_verified", "retention_metadata"],
      "properties": {
        "status": {"type": "string", "enum": ["PASS", "FAIL"]},
        "blocks_verified": {"type": "integer"},
        "retention_metadata": {
          "type": "object",
          "properties": {
            "retention_years": {"type": "integer"},
            "expiry_date": {"type": "string", "format": "date"}
          }
        }
      }
    },
    "audit_trail": {
      "type": "array",
      "description": "Chronological audit log",
      "items": {
        "type": "object",
        "required": ["timestamp", "action", "actor"],
        "properties": {
          "timestamp": {"type": "string", "format": "date-time"},
          "action": {"type": "string"},
          "actor": {"type": "string"}
        }
      }
    }
  }
}
```

### Step 2: Implement Input Face (Validation)

**File:** `blocks/compliance/validators.py`

```python
import jsonschema
from pathlib import Path
from typing import Dict, Any

class ComplianceInputValidator:
    """Input face: validates incoming data against schema."""

    def __init__(self):
        schema_path = Path(__file__).parent / "schemas" / "compliance_input.schema.json"
        with open(schema_path) as f:
            self.schema = json.load(f)

    def validate(self, input_data: Dict[str, Any]) -> None:
        """Raises jsonschema.ValidationError if invalid."""
        jsonschema.validate(instance=input_data, schema=self.schema)

    def parse(self, input_data: Dict[str, Any]) -> "ComplianceInput":
        """Parse and return typed input object."""
        self.validate(input_data)
        return ComplianceInput(
            task_id=input_data["task_id"],
            blocks=input_data["blocks"],
            retention_years=input_data["retention_years"]
        )

@dataclass
class ComplianceInput:
    task_id: str
    blocks: List[Dict[str, str]]
    retention_years: int
```

### Step 3: Implement Logic Face (Business Logic)

**File:** `blocks/compliance/logic.py`

```python
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib

class AttestationEngine:
    """Logic face: pure functions for attestation generation."""

    @staticmethod
    def generate_attestation(
        task_id: str,
        blocks: List[Dict[str, str]],
        retention_years: int
    ) -> Dict[str, Any]:
        """Generate attestation report (pure function)."""

        # Verify all block artifacts
        verified_blocks = []
        for block in blocks:
            # Check artifact integrity
            if AttestationEngine._verify_sha256(block["artifact_uri"], block["sha256"]):
                verified_blocks.append(block)

        # Calculate retention metadata
        expiry_date = datetime.now() + timedelta(days=365 * retention_years)

        # Generate audit trail
        audit_trail = [
            {
                "timestamp": datetime.now().isoformat(),
                "action": "attestation_generated",
                "actor": "orchestrator"
            }
        ]

        return {
            "report_id": f"report_{task_id}",
            "attestation": {
                "status": "PASS" if len(verified_blocks) == len(blocks) else "FAIL",
                "blocks_verified": len(verified_blocks),
                "retention_metadata": {
                    "retention_years": retention_years,
                    "expiry_date": expiry_date.date().isoformat()
                }
            },
            "audit_trail": audit_trail
        }

    @staticmethod
    def _verify_sha256(artifact_uri: str, expected_hash: str) -> bool:
        """Verify artifact integrity via SHA-256."""
        # Implementation: download artifact, compute hash, compare
        # (Simplified for example)
        return True
```

### Step 4: Implement Output Face (Serialization)

**File:** `blocks/compliance/formatters.py`

```python
import json
from typing import Dict, Any

class ComplianceOutputFormatter:
    """Output face: serialize attestation to JSON."""

    def __init__(self):
        schema_path = Path(__file__).parent / "schemas" / "compliance_output.schema.json"
        with open(schema_path) as f:
            self.schema = json.load(f)

    def format(self, attestation: Dict[str, Any]) -> str:
        """Serialize attestation, validate against output schema."""
        jsonschema.validate(instance=attestation, schema=self.schema)
        return json.dumps(attestation, indent=2)

    def write_to_s3(self, attestation: Dict[str, Any], s3_uri: str) -> None:
        """Write attestation to S3 with immutability (WORM mode)."""
        formatted = self.format(attestation)
        # Upload to S3 with Object Lock enabled
        # (See SRE runbooks for S3 configuration)
```

### Step 5: Wire Integration Face (EventBridge)

**File:** `blocks/compliance/event_handlers.py`

```python
import boto3

class ComplianceEventHandler:
    """Integration face: publish attestation events to EventBridge."""

    def __init__(self):
        self.eventbridge = boto3.client('events')

    def publish_attestation_complete(self, report_id: str, status: str) -> None:
        """Emit event when attestation completes."""
        event = {
            'Source': 'blocks.compliance',
            'DetailType': 'AttestationComplete',
            'Detail': json.dumps({
                'report_id': report_id,
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
        }
        self.eventbridge.put_events(Entries=[event])
```

### Step 6: Add UI Face (CLI Command)

**File:** `blocks/compliance/cli.py`

```python
import click
from .validators import ComplianceInputValidator
from .logic import AttestationEngine
from .formatters import ComplianceOutputFormatter

@click.command()
@click.option('--task-id', required=True, help='TaskObject ID')
@click.option('--blocks', required=True, type=click.File('r'), help='JSON file with blocks list')
@click.option('--retention-years', default=7, help='Retention period (default: 7)')
def generate_attestation(task_id, blocks, retention_years):
    """Generate Basel-I compliance attestation report."""

    # Parse input
    validator = ComplianceInputValidator()
    input_data = json.load(blocks)
    compliance_input = validator.parse({
        "task_id": task_id,
        "blocks": input_data["blocks"],
        "retention_years": retention_years
    })

    # Generate attestation
    attestation = AttestationEngine.generate_attestation(
        task_id=compliance_input.task_id,
        blocks=compliance_input.blocks,
        retention_years=compliance_input.retention_years
    )

    # Format and output
    formatter = ComplianceOutputFormatter()
    output = formatter.format(attestation)
    click.echo(output)

if __name__ == '__main__':
    generate_attestation()
```

---

## Property-Based Testing

Use Hypothesis to generate test cases automatically:

**File:** `blocks/compliance/tests/test_logic.py`

```python
import pytest
from hypothesis import given, strategies as st
from ..logic import AttestationEngine

class TestAttestationEngine:

    @given(
        task_id=st.text(min_size=11, max_size=11).filter(lambda x: x.startswith("task_")),
        retention_years=st.integers(min_value=7, max_value=20),
        num_blocks=st.integers(min_value=1, max_value=10)
    )
    def test_generate_attestation_always_returns_valid_structure(
        self, task_id, retention_years, num_blocks
    ):
        """Property: attestation always has required fields."""
        blocks = [
            {
                "block_id": f"block_{i}",
                "artifact_uri": f"s3://bucket/block_{i}.py",
                "sha256": "a" * 64
            }
            for i in range(num_blocks)
        ]

        attestation = AttestationEngine.generate_attestation(
            task_id=task_id,
            blocks=blocks,
            retention_years=retention_years
        )

        # Invariants
        assert "report_id" in attestation
        assert attestation["attestation"]["blocks_verified"] == num_blocks
        assert attestation["attestation"]["retention_metadata"]["retention_years"] == retention_years

    def test_attestation_immutability(self):
        """Ensure attestation output is deterministic given same inputs."""
        blocks = [{"block_id": "test", "artifact_uri": "s3://bucket/test.py", "sha256": "a" * 64}]

        result1 = AttestationEngine.generate_attestation("task_abc123", blocks, 7)
        result2 = AttestationEngine.generate_attestation("task_abc123", blocks, 7)

        # Timestamps will differ, so exclude them
        assert result1["report_id"] == result2["report_id"]
        assert result1["attestation"]["blocks_verified"] == result2["attestation"]["blocks_verified"]
```

---

## Immutability Patterns

### Artifact Storage (S3 Object Lock)

```python
import boto3

def store_immutable_artifact(artifact_data: bytes, s3_uri: str) -> str:
    """Store artifact with WORM (Write Once Read Many) guarantee."""
    s3 = boto3.client('s3')
    bucket, key = parse_s3_uri(s3_uri)

    # Upload with Object Lock enabled (7-year retention)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=artifact_data,
        ObjectLockMode='COMPLIANCE',
        ObjectLockRetainUntilDate=datetime.now() + timedelta(days=365*7),
        Metadata={
            'sha256': hashlib.sha256(artifact_data).hexdigest(),
            'created_at': datetime.now().isoformat()
        }
    )

    return s3_uri
```

### Context Bundle Hashing

```python
def generate_context_bundle_hash(context: Dict[str, Any]) -> str:
    """Generate deterministic SHA-256 hash of context bundle."""
    # Sort keys to ensure deterministic serialization
    canonical_json = json.dumps(context, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode()).hexdigest()
```

---

## Block Catalog Registration

After authoring your block, register it in the catalog:

```bash
blocks catalog add \
  --block-path blocks/compliance/compliance_attestation.py \
  --family compliance \
  --tags "basel-i,audit,retention" \
  --input-schema blocks/compliance/schemas/compliance_input.schema.json \
  --output-schema blocks/compliance/schemas/compliance_output.schema.json \
  --owner engineering@company.com
```

Catalog entry created at `.blocks/catalog/compliance_attestation.yml`:
```yaml
block_id: compliance_attestation
family: compliance
version: 1.0.0
tags: [basel-i, audit, retention]
schemas:
  input: blocks/compliance/schemas/compliance_input.schema.json
  output: blocks/compliance/schemas/compliance_output.schema.json
owner: engineering@company.com
created_at: 2025-11-16T10:30:00Z
```

---

## Best Practices Checklist

- [ ] All 6 faces implemented (Structure, UI, Integration, Logic, Input, Output)
- [ ] JSON Schemas validated with examples
- [ ] Property-based tests cover edge cases (Hypothesis)
- [ ] Immutability enforced for artifacts (S3 Object Lock)
- [ ] Pure functions preferred for Logic face (no side effects)
- [ ] Integration face publishes events to EventBridge
- [ ] CLI commands include `--help` documentation
- [ ] Block registered in catalog with metadata
- [ ] README.md documents usage + examples
- [ ] Runbook created for incident response (see Module 4)

---

## Next Steps

1. **Practice:** Author a second block for your domain (e.g., observability, financial reporting)
2. **Review:** Submit your block for peer review via `blocks review submit`
3. **CI Integration:** Add contract validation to CI (Module 3)
4. **Monitoring:** Add telemetry to your block (Module 5)

---

**Module 2 Complete!** Proceed to Module 3: Quality & CI Gating
