# Orchestrator CLI Quick-Start Guide

**Module 1:** Getting Started with Multi-LLM Orchestrator
**Duration:** 30 minutes
**Owner:** Product + Engineering
**Last Updated:** November 16, 2025

---

## Overview

The Multi-LLM Orchestrator enables contract-first AI-assisted development using verified blocks. This guide walks you through your first flow execution in 30 minutes.

### What You'll Learn
- Install and configure the CLI
- Execute your first plan→impl→review→docs flow
- Understand context bundles and TaskObjects
- Interpret quality gates and verification reports

### Prerequisites
- Git repository with existing codebase
- Python 3.9+ or Node.js 16+
- API keys for Claude, GPT-4, and/or Gemini (at least one required)

---

## Installation

### Step 1: Install CLI

```bash
# Via pip (Python)
pip install blocks-orchestrator

# Via npm (Node.js)
npm install -g @blocks/orchestrator

# Verify installation
blocks --version
# Expected: blocks-orchestrator v1.0.0
```

### Step 2: Configure API Keys

```bash
# Set API keys (choose providers based on your budget)
export ANTHROPIC_API_KEY="sk-ant-..."      # Required for architect/review
export OPENAI_API_KEY="sk-..."             # Required for implementation
export GOOGLE_API_KEY="..."                # Optional for context augmentation

# Verify configuration
blocks config verify
# Expected: ✅ Claude Sonnet 4.5 available
#           ✅ GPT-4 Turbo available
#           ⚠️  Gemini Pro not configured (optional)
```

### Step 3: Initialize Repository

```bash
# Navigate to your repository
cd /path/to/your/repo

# Initialize blocks workspace
blocks init

# This creates:
# - .blocks/config.yml (orchestrator settings)
# - .blocks/catalog/ (verified block catalog)
# - .blocks/schemas/ (JSON Schema definitions)
```

---

## Your First Flow

### Scenario: Generate a Basel-I Compliant Attestation Report

We'll use the orchestrator to generate a compliance attestation block following the 6-face architecture.

### Step 1: Create Feature Request

```bash
# Create a new feature request file
cat > feature_request.md <<EOF
# Feature: Basel-I Compliance Attestation

## User Story
As a compliance officer, I need to generate attestation reports that prove
our AI-generated code meets Basel-I retention and audit requirements.

## Acceptance Criteria
1. Report includes all verified blocks used in the flow
2. Artifact hashes (SHA-256) for tamper detection
3. 7-year retention metadata
4. Audit trail of review decisions
EOF
```

### Step 2: Run Orchestrator Flow

```bash
# Execute complete flow: plan → impl → review → docs
blocks flow run \
  --input feature_request.md \
  --block-family compliance \
  --output-dir ./blocks/compliance/ \
  --quality-gate strict

# Expected output:
# 🔄 [PLAN] Generating block blueprint... (Claude Sonnet 4.5, 18.2s)
# 🔄 [IMPL] Implementing 6-face block... (GPT-4 Turbo, 28.4s)
# 🔄 [REVIEW] Validating contracts + logic... (Claude Sonnet 4.5, 22.1s)
# 🔄 [DOCS] Generating README + runbook... (Gemini Pro, 12.3s)
# ✅ Flow completed in 94s | Cost: $1.42 | Blocks: 1 | Quality: PASS
```

### Step 3: Inspect Generated Artifacts

```bash
# View TaskObject (orchestrator state)
cat .blocks/tasks/task_abc123.json

# Key fields:
{
  "task_id": "task_abc123",
  "flow_type": "plan_impl_review_docs",
  "status": "completed",
  "blocks_generated": 1,
  "quality_gate": "PASS",
  "cost_usd": 1.42,
  "duration_seconds": 94,
  "artifacts": {
    "plan": "s3://context-bundles/plan_abc123.json",
    "impl": "blocks/compliance/compliance_attestation.py",
    "review": ".blocks/reviews/review_abc123.md",
    "docs": "blocks/compliance/README.md"
  }
}
```

### Step 4: Review Quality Report

```bash
# View verification report
blocks verify show task_abc123

# Sample output:
# ┌─────────────────────────────────────────────────────┐
# │ Verification Report: task_abc123                    │
# ├─────────────────────────────────────────────────────┤
# │ Status: ✅ PASS (3/3 checks)                        │
# │                                                     │
# │ ✅ Contract Validation                              │
# │    - Input schema: compliance_input.schema.json    │
# │    - Output schema: compliance_output.schema.json  │
# │    - Validation: 100% (0 errors)                   │
# │                                                     │
# │ ✅ Logic Review                                     │
# │    - Complexity: LOW (cyclomatic 3)                │
# │    - Security: PASS (0 vulnerabilities)            │
# │    - Correctness: PASS (0 logical errors)          │
# │                                                     │
# │ ✅ Test Coverage                                    │
# │    - Unit tests: 8 generated                       │
# │    - Coverage: 94.2% (exceeds 90% threshold)       │
# │    - Mutation kill-rate: 72.5% (exceeds 60%)       │
# └─────────────────────────────────────────────────────┘
```

### Step 5: Integrate into Codebase

```bash
# Add block to catalog
blocks catalog add \
  --block-path blocks/compliance/compliance_attestation.py \
  --family compliance \
  --tags "basel-i,audit,retention"

# Run tests
pytest blocks/compliance/tests/

# Commit to repository
git add blocks/compliance/ .blocks/catalog/
git commit -m "feat: add Basel-I compliance attestation block

- Generated via orchestrator (task_abc123)
- Contract-validated against compliance_input/output schemas
- Test coverage: 94.2% | Mutation kill-rate: 72.5%
- Cost: $1.42 | Duration: 94s

🤖 Generated with Multi-LLM Orchestrator"
```

---

## Understanding Context Bundles

Context bundles are immutable snapshots of the feature request, codebase context, and dependencies. They enable:
- **Deterministic regeneration** (same inputs → same outputs)
- **Tamper detection** (SHA-256 hashing)
- **7-year retention** (Basel-I compliance)

### Context Bundle Structure

```json
{
  "context_id": "ctx_abc123",
  "created_at": "2025-11-06T14:32:18Z",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "components": {
    "feature_request": "...",
    "codebase_snapshot": ["file1.py", "file2.js"],
    "dependencies": ["package.json", "requirements.txt"],
    "schemas": ["compliance_input.schema.json"]
  },
  "size_kb": 180,
  "retention_years": 7
}
```

### Accessing Context Bundles

```bash
# Download context bundle for a task
blocks context download task_abc123 --output ctx_abc123.json

# Verify integrity
sha256sum ctx_abc123.json
# Compare with TaskObject.context.sha256

# Regenerate block from context (deterministic)
blocks flow replay --context ctx_abc123.json
```

---

## Quality Gates

The orchestrator enforces 5 quality gates. Any failures trigger automatic retry or manual review.

| Gate | Threshold | Purpose | Action on Failure |
| --- | --- | --- | --- |
| **Contract Validation** | 100% pass | Ensure input/output schemas match | BLOCK (no merge) |
| **Unit Test Coverage** | ≥90% | Verify block logic exercised | WARN (review required) |
| **Mutation Kill-Rate** | ≥60% | Detect weak tests | WARN (review required) |
| **Security Scan** | 0 HIGH/CRITICAL | No vulnerabilities | BLOCK (no merge) |
| **Logic Review** | 0 BLOCKERs | Claude validates correctness | BLOCK (no merge) |

### Overriding Quality Gates (Caution!)

```bash
# Lower quality gate for prototyping (NOT recommended for production)
blocks flow run --quality-gate permissive feature_request.md

# Skip specific gate (requires justification)
blocks flow run --skip-gate mutation feature_request.md \
  --justification "Legacy code has low mutation baseline"
```

---

## Troubleshooting

### Error: "Context bundle exceeds 500KB"

**Cause:** Large dependencies or codebase snapshot included in context.

**Solution:**
```bash
# Enable context pruning
blocks config set context.max_size_kb 180
blocks config set context.pruning.enabled true

# Exclude large files
echo "node_modules/" >> .blocks/contextignore
echo "*.log" >> .blocks/contextignore
```

### Error: "Model API rate limit exceeded"

**Cause:** Too many concurrent flows or quota exhaustion.

**Solution:**
```bash
# Check quota usage
blocks quota show

# Enable circuit breaker
blocks config set circuit_breaker.enabled true
blocks config set circuit_breaker.threshold 80  # Pause at 80% quota

# Use fallback model
blocks config set fallback.model gpt-4-turbo
```

### Error: "Quality gate BLOCKER: contract validation failed"

**Cause:** Generated block doesn't match input/output schema.

**Solution:**
```bash
# View detailed validation errors
blocks verify show task_abc123 --verbose

# Common fixes:
# 1. Update schema to match expected behavior
# 2. Add examples to feature request
# 3. Retry with stricter planning prompt
blocks flow retry task_abc123 --planning-mode strict
```

---

## Best Practices

### 1. Write Clear Feature Requests
```markdown
# Good Example
## User Story
As a [role], I need [capability] so that [outcome].

## Acceptance Criteria
1. [Specific measurable criterion]
2. [Include edge cases]
3. [Define error handling]

## Technical Constraints
- Must integrate with existing auth service
- Response time <200ms
- Budget: <$2/block
```

### 2. Use Block Families for Consistency
```bash
# Organize blocks by domain
blocks catalog families
# Output:
# - structure (schema, validation, transformation)
# - compliance (basel-i, audit, retention)
# - observability (metrics, logging, tracing)
# - financial (reporting, reconciliation)
```

### 3. Monitor Costs
```bash
# Set budget alerts
blocks config set budget.daily_max_usd 50
blocks config set budget.alert_threshold 80  # Alert at 80% of daily budget

# View cost breakdown
blocks cost report --last-30-days
```

### 4. Version Control Everything
```bash
# Commit orchestrator config
git add .blocks/config.yml .blocks/catalog/

# Include TaskObject references in commit messages
git commit -m "feat: add feature X (task_abc123)"
```

---

## Next Steps

1. **Explore Block Families:** Review `.blocks/catalog/` for reusable blocks
2. **Customize Prompts:** Edit `.blocks/prompts/` to align with your team's style
3. **Integrate CI/CD:** Add `blocks verify` to your CI pipeline (see Module 3)
4. **Monitor Dashboards:** Access ROI/Quality/Reliability dashboards (see Module 5)

---

## Getting Help

- **Documentation:** `blocks docs` or https://docs.blocks-orchestrator.com
- **Community:** Slack #blocks-help or https://community.blocks-orchestrator.com
- **Support:** support@blocks-orchestrator.com
- **Office Hours:** Thursdays 2-3 PM (see training calendar)

---

**Module 1 Complete!** Proceed to Module 2: Block Blueprint Authoring
