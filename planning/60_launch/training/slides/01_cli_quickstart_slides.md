# Module 1: Orchestrator CLI Quick-Start

**Presentation Slides**
**Duration:** 30 minutes
**Format:** Live demo + hands-on
**Owner:** Product + Engineering

---

## Slide 1: Title

# Multi-LLM Orchestrator
## CLI Quick-Start

**Module 1 of 5**

Generate production-ready blocks in minutes, not days

---

## Slide 2: Agenda

### What We'll Cover (30 min)

1. **Overview** (5 min) — What is the orchestrator?
2. **Installation** (5 min) — Get up and running
3. **First Flow** (10 min) — Generate a Basel-I block
4. **Quality Gates** (5 min) — Understand verification
5. **Best Practices** (5 min) — Tips for success

---

## Slide 3: The Problem

### Traditional AI-Assisted Development

```
Developer writes prompt
    ↓
Copilot suggests code
    ↓
Developer reviews (hit or miss)
    ↓
Manually write tests
    ↓
Hope it works in production
```

**Challenges:**
- No contracts (schema drift)
- Weak test coverage
- No audit trail
- Unpredictable quality

---

## Slide 4: The Solution

### Contract-First Multi-LLM Orchestration

```
Feature request (user story)
    ↓
[PLAN]  Claude Sonnet 4.5 → Blueprint + schemas
    ↓
[IMPL]  GPT-4 Turbo → 6-face block implementation
    ↓
[REVIEW] Claude Sonnet 4.5 → Contract validation + logic review
    ↓
[DOCS]  Gemini Pro → README + runbook
    ↓
✅ Production-ready block (verified)
```

**Benefits:**
- 100% schema compliance
- 92%+ test coverage
- Full audit trail
- Consistent quality

---

## Slide 5: Pilot Results

### 8-Day Pilot (Nov 4-12, 2025)

| Metric | Baseline | Pilot | Improvement |
| --- | --- | --- | --- |
| **Cycle Time** | 12.5 days | 8.2 days | -34% ⬇️ |
| **Cost/Feature** | $200 | $1.60 | -99% ⬇️ |
| **AI Code %** | 15% | 38% | +23 pts ⬆️ |
| **Quality Score** | 68% | 94% | +26 pts ⬆️ |

**ROI:** 3.6× first-year return

---

## Slide 6: Installation (Part 1)

### Step 1: Install CLI

```bash
# Via pip
pip install blocks-orchestrator

# Or via npm
npm install -g @blocks/orchestrator

# Verify
blocks --version
# Expected: v1.0.0
```

**Supported Platforms:** macOS, Linux, Windows (WSL)
**Requirements:** Python 3.9+ or Node.js 16+

---

## Slide 7: Installation (Part 2)

### Step 2: Configure API Keys

```bash
# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."  # Claude (required)
export OPENAI_API_KEY="sk-..."         # GPT-4 (required)
export GOOGLE_API_KEY="..."            # Gemini (optional)

# Verify connectivity
blocks config verify
```

**Cost Estimate:** ~$1.60 per block (Claude $0.87, GPT $0.58, Gemini $0.15)

---

## Slide 8: Installation (Part 3)

### Step 3: Initialize Repository

```bash
cd /path/to/your/repo
blocks init

# Creates:
# .blocks/config.yml       ← Orchestrator settings
# .blocks/catalog/         ← Verified block registry
# .blocks/schemas/         ← JSON Schema definitions
```

---

## Slide 9: Demo — First Flow

### Live Demo: Generate Basel-I Compliance Block

**Input:** Feature request (user story)

```markdown
# Feature: Basel-I Compliance Attestation

As a compliance officer, I need to generate attestation
reports proving AI-generated code meets Basel-I requirements.

## Acceptance Criteria
1. Report includes all verified blocks
2. Artifact hashes for tamper detection
3. 7-year retention metadata
4. Audit trail of review decisions
```

---

## Slide 10: Demo — Execute Flow

```bash
blocks flow run \
  --input feature_request.md \
  --block-family compliance \
  --output-dir ./blocks/compliance/ \
  --quality-gate strict
```

**Expected Duration:** ~90 seconds

---

## Slide 11: Demo — Flow Output (Live)

```
🔄 [PLAN] Generating block blueprint...
   Model: Claude Sonnet 4.5 | Duration: 18.2s | Cost: $0.31

🔄 [IMPL] Implementing 6-face block...
   Model: GPT-4 Turbo | Duration: 28.4s | Cost: $0.58

🔄 [REVIEW] Validating contracts + logic...
   Model: Claude Sonnet 4.5 | Duration: 22.1s | Cost: $0.42

🔄 [DOCS] Generating README + runbook...
   Model: Gemini Pro | Duration: 12.3s | Cost: $0.15

✅ Flow completed in 94s | Cost: $1.42 | Quality: PASS
```

---

## Slide 12: Generated Artifacts

### What the Orchestrator Created

```
blocks/compliance/
├── schemas/
│   ├── compliance_input.schema.json   ← Structure face
│   └── compliance_output.schema.json
├── compliance_attestation.py          ← Logic + integration
├── validators.py                      ← Input face
├── formatters.py                      ← Output face
├── cli.py                             ← UI face
├── tests/
│   └── test_attestation.py            ← 8 tests (94% coverage)
└── README.md                          ← Documentation
```

---

## Slide 13: Quality Report

### Automated Verification

```
┌─────────────────────────────────────────────────┐
│ Verification Report: task_abc123                │
├─────────────────────────────────────────────────┤
│ Status: ✅ PASS (3/3 checks)                    │
│                                                 │
│ ✅ Contract Validation                          │
│    Input/output schemas: 100% valid             │
│                                                 │
│ ✅ Logic Review                                 │
│    Security: PASS | Correctness: PASS           │
│    Blockers: 0                                  │
│                                                 │
│ ✅ Test Coverage                                │
│    Unit tests: 94.2% (exceeds 90% threshold)    │
│    Mutation kill-rate: 72.5% (exceeds 60%)      │
└─────────────────────────────────────────────────┘
```

---

## Slide 14: Context Bundles

### Immutability for Compliance

Every flow generates a **context bundle** (immutable snapshot):

```json
{
  "context_id": "ctx_abc123",
  "sha256": "e3b0c44...",
  "components": {
    "feature_request": "...",
    "codebase_snapshot": ["file1.py"],
    "schemas": ["compliance_input.schema.json"]
  },
  "retention_years": 7
}
```

**Purpose:**
- Deterministic regeneration (audit requirement)
- Tamper detection (SHA-256 hashing)
- 7-year retention (Basel-I compliance)

---

## Slide 15: The 5 Quality Gates

| Gate | Tool | Threshold | Blocker? |
| --- | --- | --- | --- |
| **1. Contract Validation** | JSON Schema | 100% | ✅ Yes |
| **2. Unit Coverage** | pytest-cov | ≥90% | ⚠️ Warn |
| **3. Mutation Kill-Rate** | Mutmut | ≥60% | ⚠️ Warn |
| **4. Security Scan** | Bandit/Semgrep | 0 HIGH | ✅ Yes |
| **5. Logic Review** | Claude | 0 BLOCKERs | ✅ Yes |

**Any BLOCKER = CI fails** (no merge allowed)

---

## Slide 16: Best Practice #1

### Write Clear Feature Requests

**Good Example:**
```markdown
## User Story
As a [role], I need [capability] so that [outcome].

## Acceptance Criteria
1. [Specific, measurable]
2. [Include edge cases]
3. [Define error handling]

## Technical Constraints
- Must integrate with auth service
- Response time <200ms
```

**Bad Example:**
```markdown
Add a compliance thing.
```

---

## Slide 17: Best Practice #2

### Use Block Families

Organize blocks by domain for consistency:

```bash
blocks catalog families

# Output:
# - structure       (schema, validation, transformation)
# - compliance      (basel-i, audit, retention)
# - observability   (metrics, logging, tracing)
# - financial       (reporting, reconciliation)
```

**Why?** Reuse schemas, patterns, and test strategies across similar blocks.

---

## Slide 18: Best Practice #3

### Monitor Costs

```bash
# Set daily budget
blocks config set budget.daily_max_usd 50

# Alert at 80% of budget
blocks config set budget.alert_threshold 80

# View cost breakdown
blocks cost report --last-7-days
```

**Pilot Average:** $1.60/block (well under $200 budget envelope)

---

## Slide 19: Troubleshooting — Timeouts

**Error:** "Context bundle exceeds 500KB"

**Solution:**
```bash
# Enable context pruning
blocks config set context.max_size_kb 180
blocks config set context.pruning.enabled true

# Exclude large files
echo "node_modules/" >> .blocks/contextignore

# Retry
blocks flow retry task_abc123 --enable-pruning
```

---

## Slide 20: Troubleshooting — Rate Limits

**Error:** "Model API rate limit exceeded"

**Solution:**
```bash
# Check quota
blocks quota show

# Enable circuit breaker
blocks config set circuit_breaker.enabled true

# Use fallback model
blocks config set fallback.model gpt-4-turbo
```

---

## Slide 21: Next Steps

### After This Session

1. **Practice:** Generate your first block (choose a simple use case)
2. **Explore Catalog:** `blocks catalog list` to see reusable blocks
3. **Integrate CI:** Add `blocks verify` to your pipeline (Module 3)
4. **Join Community:** #blocks-help Slack channel for support

**Office Hours:** Thursdays 2-3 PM for live Q&A

---

## Slide 22: Key Takeaways

### Summary

✅ **Installation:** 3 steps (CLI, API keys, init)
✅ **First Flow:** ~90 seconds to production-ready block
✅ **Quality Gates:** 5 gates ensure consistent quality
✅ **Cost:** $1.60/block (99% cheaper than manual)
✅ **Compliance:** Context bundles for audit trail

**Next Module:** Block Blueprint Authoring (6-face architecture)

---

## Slide 23: Q&A

# Questions?

**Contact:**
- Slack: #blocks-help
- Email: support@blocks-orchestrator.com
- Docs: https://docs.blocks-orchestrator.com

**Next Session:** Module 2 — Block Blueprint Authoring
**When:** [Date/Time TBD]

---

## Slide 24: Thank You

# Thank You!

**Module 1 Complete** ✅

**Homework:**
- Generate your first block
- Review the CLI quick-start guide
- Join #blocks-community

See you in Module 2! 🚀
