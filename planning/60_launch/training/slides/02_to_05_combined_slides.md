# Modules 2-5: Combined Slide Deck

**Presentation Slides for Modules 2-5**
**Total Duration:** 180 minutes
**Format:** Workshop + Labs + Demos
**Owners:** Engineering, QA, SRE, Data

---

# Module 2: Block Blueprint Authoring
## (45 minutes — Workshop)

---

## M2: The 6-Face Architecture

```
        ┌─────────────────┐
        │   [Structure]   │  JSON Schemas
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐   ┌───▼────┐   ┌──▼─────┐
│  [UI]  │   │ [Logic]│   │[Integ.]│
│  CLI   │   │  Pure  │   │EventBus│
└───┬────┘   └───┬────┘   └──┬─────┘
    │            │            │
    └────────────┼────────────┘
                 │
        ┌────────▼────────┐
        │   [Input Face]  │  Validation
        └─────────────────┘
                 │
        ┌────────▼────────┐
        │  [Output Face]  │  Serialization
        └─────────────────┘
```

**Key Principle:** Each face has a single responsibility

---

## M2: Face Responsibilities

| Face | Artifacts | Owner |
| --- | --- | --- |
| **Structure** | `*.schema.json` | Architect |
| **UI** | `cli.py`, `api_handlers.py` | Product + Eng |
| **Integration** | `event_handlers.py` | SRE + Eng |
| **Logic** | `logic.py` (pure functions) | Engineering |
| **Input** | `validators.py` | Engineering |
| **Output** | `formatters.py` | Engineering |

---

## M2: Workshop Exercise

### Build a Compliance Block (30 min hands-on)

**Steps:**
1. Define input/output schemas (Structure face)
2. Implement validation logic (Input face)
3. Write core business logic (Logic face)
4. Add output formatting (Output face)
5. Create CLI command (UI face)
6. Wire EventBridge integration (Integration face)

**Result:** Production-ready 6-face block

---

## M2: Property-Based Testing

### Why Property-Based Tests?

```python
# Traditional unit test (3 cases)
def test_attestation_basic():
    assert generate_attestation("task_123", [], 7)

def test_attestation_with_blocks():
    assert generate_attestation("task_456", [block1], 7)

def test_attestation_long_retention():
    assert generate_attestation("task_789", [], 10)
```

**Problem:** Only tests 3 specific inputs

---

## M2: Property-Based Tests (Hypothesis)

```python
from hypothesis import given, strategies as st

@given(
    task_id=st.text(min_size=11, max_size=11),
    retention_years=st.integers(min_value=7, max_value=20),
    num_blocks=st.integers(min_value=1, max_value=10)
)
def test_attestation_always_valid(task_id, retention_years, num_blocks):
    """Property: attestation always has required fields."""
    blocks = generate_test_blocks(num_blocks)
    result = generate_attestation(task_id, blocks, retention_years)

    # Invariants (true for ALL inputs)
    assert "report_id" in result
    assert result["attestation"]["blocks_verified"] == num_blocks
    assert result["attestation"]["retention_metadata"]["retention_years"] == retention_years
```

**Result:** Hypothesis generates 100+ random test cases automatically

---

## M2: Immutability Patterns

### S3 Object Lock (WORM)

```python
def store_immutable_artifact(artifact_data: bytes, s3_uri: str) -> str:
    """Store with Write Once Read Many guarantee."""
    s3 = boto3.client('s3')
    bucket, key = parse_s3_uri(s3_uri)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=artifact_data,
        ObjectLockMode='COMPLIANCE',           # ← Cannot be deleted
        ObjectLockRetainUntilDate=datetime.now() + timedelta(days=365*7),
        Metadata={
            'sha256': hashlib.sha256(artifact_data).hexdigest()
        }
    )
```

**Basel-I Requirement:** 7-year retention with tamper protection ✅

---

## M2: Catalog Registration

```bash
# Add block to catalog
blocks catalog add \
  --block-path blocks/compliance/compliance_attestation.py \
  --family compliance \
  --tags "basel-i,audit,retention" \
  --input-schema blocks/compliance/schemas/compliance_input.schema.json \
  --output-schema blocks/compliance/schemas/compliance_output.schema.json \
  --owner engineering@company.com
```

**Result:** Block discoverable in `.blocks/catalog/compliance_attestation.yml`

---

## M2: Checklist for Production-Ready Blocks

- [ ] All 6 faces implemented
- [ ] JSON Schemas with examples
- [ ] Property-based tests (Hypothesis)
- [ ] Immutability enforced (S3 Object Lock)
- [ ] Pure functions for Logic face
- [ ] EventBridge integration
- [ ] CLI commands with `--help`
- [ ] Catalog registration
- [ ] README.md with usage examples
- [ ] Runbook for incident response

---

# Module 3: Quality & CI Gating
## (60 minutes — Hands-On Lab)

---

## M3: The 5 Quality Gates

| Gate | Tool | Threshold | Blocker? | Purpose |
| --- | --- | --- | --- | --- |
| **1. Contract** | JSON Schema | 100% | ✅ | Schema match |
| **2. Coverage** | pytest-cov | ≥90% | ⚠️ | Logic exercised |
| **3. Mutation** | Mutmut | ≥60% | ⚠️ | Strong tests |
| **4. Security** | Bandit | 0 HIGH | ✅ | No vulnerabilities |
| **5. Review** | Claude | 0 BLOCKERs | ✅ | AI validates logic |

---

## M3: Mutation Testing Explained

### How It Works

1. **Mutmut** mutates your code:
   ```python
   # Original
   if balance > 0:
       return True

   # Mutant #1: Change > to >=
   if balance >= 0:
       return True

   # Mutant #2: Change > to <
   if balance < 0:
       return True
   ```

2. Run tests against each mutant
3. If tests **PASS** with mutant → **SURVIVED** (weak test ❌)
4. If tests **FAIL** with mutant → **KILLED** (strong test ✅)

**Goal:** ≥60% mutation kill-rate

---

## M3: Weak vs Strong Tests

**Weak Test (mutant survives):**
```python
def test_balance_check():
    result = check_balance(100)
    assert isinstance(result, bool)  # ❌ Doesn't verify True/False
```

**Strong Test (mutant killed):**
```python
def test_balance_positive():
    assert check_balance(100) is True  # ✅ Verifies True case

def test_balance_zero():
    assert check_balance(0) is False  # ✅ Kills "balance >= 0" mutant
```

---

## M3: Lab Exercise — Fix Weak Tests

```bash
# Run mutation testing
mutmut run --paths-to-mutate blocks/compliance/logic.py

# View survivors
mutmut results

# Show specific mutant
mutmut show 3

# Fix: Add stronger assertions
# Re-run: Verify kill-rate ≥60%
```

---

## M3: GitHub Actions Integration

```yaml
name: Quality Gates
on: [pull_request]

jobs:
  quality_gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Dependencies
        run: pip install blocks-orchestrator[quality]

      - name: Run All Quality Gates
        run: blocks verify all blocks/ --output quality_report.json

      - name: Fail on Blockers
        run: |
          if jq -e '.blockers > 0' quality_report.json; then
            exit 1
          fi
```

---

## M3: BLOCKER Example (AI Review)

```
File: blocks/compliance/logic.py:78
Severity: BLOCKER
Finding: "Data Loss Risk — Overwrites reports without backup"
Recommendation: Add versioning before overwrite

Action Required: Fix and re-submit for review
```

**Fix:**
```python
# Before: overwrites without backup
with open(f"{report_id}.json", "w") as f:
    json.dump(attestation, f)

# After: version control
version = get_next_version(report_id)
with open(f"{report_id}_v{version}.json", "w") as f:
    json.dump(attestation, f)  # ✅ No data loss
```

---

# Module 4: Runbooks & Rollback
## (45 minutes — Presentation + Demo)

---

## M4: Runbook Index

| Runbook | Trigger | MTTR | Validated? |
| --- | --- | --- | --- |
| **1. Flow Failure** | >1% failure rate | 15 min | ✅ Yes |
| **2. Timeout** | Flow >120s | 10 min | ✅ Yes |
| **3. Rate Limit** | Quota >80% | 20 min | 🧪 Tested |
| **4. Provider Outage** | API 5xx | 30 min | 🧪 Tested |
| **5. Security** | PII leak | 5 min | 🧪 Tested |

**Location:** `planning/30_design/runbooks/`

---

## M4: Runbook 1 — Flow Failure

### Quick Triage (5 min)

```bash
# Step 1: Identify failures
aws logs filter-pattern 'ERROR' --log-group /aws/lambda/flowengine --start-time -1h

# Step 2: Check TaskDB
psql -c "SELECT task_id, error_message FROM tasks WHERE status='failed' LIMIT 10;"

# Step 3: Categorize
# - Timeout → Apply context pruning
# - Rate Limit → Enable circuit breaker
# - Validation → Check schema version
# - API 5xx → Check vendor status
```

---

## M4: Timeout Recovery

**Problem:** Context bundle >500KB

**Solution:**
```bash
# Enable context pruning
blocks flow retry task_abc123 --enable-pruning --max-context-size 180KB

# Or configure globally
kubectl set env deployment/flowengine \
  CONTEXT_PRUNING_ENABLED=true \
  CONTEXT_MAX_SIZE_KB=180
```

**Pilot Validation:** 1 timeout in Run #2 → resolved in 12.3 min ✅

---

## M4: Rate Limit Mitigation

**Problem:** Claude quota at 82%

**Solution:**
```bash
# Step 1: Enable circuit breaker
kubectl set env deployment/flowengine \
  ENABLE_CIRCUIT_BREAKER=true \
  CIRCUIT_BREAKER_THRESHOLD=85

# Step 2: Route to fallback model
kubectl set env deployment/flowengine \
  ARCHITECT_FALLBACK_MODEL=gpt-4-turbo

# Step 3: Notify stakeholders
blocks notify slack --channel ops-alerts \
  --message "Claude quota 82%. Circuit breaker enabled."
```

---

## M4: Zero-Downtime Rollback

```bash
# Step 1: Rollback to previous version
kubectl rollout undo deployment/flowengine

# Step 2: Monitor rollback (45s)
kubectl rollout status deployment/flowengine

# Step 3: Verify
blocks test-flow --input test_case.md
```

**Pilot Validation (Nov 9):**
- Rollback completed in 45 seconds
- Zero downtime
- Previous version handled traffic successfully ✅

---

## M4: Post-Incident Review Template

```markdown
# PIR: [Incident Title]

## Timeline
- [HH:MM] Detection
- [HH:MM] Mitigation
- [HH:MM] Resolution

## Root Cause
[1-2 paragraphs]

## Action Items
1. [Action] — Owner — Due Date
2. [Action] — Owner — Due Date

## Lessons Learned
[Key takeaways]
```

---

# Module 5: Metrics & Dashboards
## (45 minutes — Screenshot Tour + Hands-On)

---

## M5: The 3 Core Dashboards

1. **ROI Dashboard** — Cycle time, cost, AI code %
   - **URL:** https://grafana.company.com/d/flowengine-roi

2. **Quality Dashboard** — Success rate, mutation, coverage
   - **URL:** https://grafana.company.com/d/flowengine-quality

3. **Reliability Dashboard** — Latency, uptime, incidents
   - **URL:** https://grafana.company.com/d/flowengine-slo

---

## M5: ROI Metrics

### Key Metrics from Pilot

| Metric | Baseline | Pilot | Improvement |
| --- | --- | --- | --- |
| **Cycle Time** | 12.5d | 8.2d | -34% ⬇️ |
| **Cost/Feature** | $200 | $1.60 | -99% ⬇️ |
| **AI Code %** | 15% | 38% | +23 pts ⬆️ |
| **ROI** | — | 3.6× | Target: ≥2× ✅ |

**Annual Benefit:** $47K
**Annual Cost:** $13K
**Net Benefit:** +$34K

---

## M5: Quality Metrics

### Pilot Results

| Metric | Target | Actual | Status |
| --- | --- | --- | --- |
| **Flow Success** | ≥99% | 100% | ✅ |
| **Mutation Kill-Rate** | ≥60% | 68.75% | ✅ |
| **Test Coverage** | ≥90% | 92.5% | ✅ |
| **BLOCKER Detection** | — | 94% | ✅ |

**Composite Quality Score:** 94.2%

---

## M5: Reliability Metrics (SLO Compliance)

| Metric | Target | Actual | Compliance |
| --- | --- | --- | --- |
| **P95 Latency** | <120s | 118s | 98.3% ✅ |
| **API Uptime** | ≥99.9% | 100% | 100% ✅ |
| **Cost Variance** | ≤20% | ±18% | 90% ✅ |
| **Critical Incidents** | 0 | 0 | 100% ✅ |

**Overall SLO Compliance:** 97.7%

---

## M5: Custom Alerts

### Budget Burn Rate Alert

```bash
blocks alerts create \
  --name "Budget Burn Rate High" \
  --query "sum(rate(flow_cost_usd[1h])) * 24" \
  --condition "> 50" \
  --severity P3 \
  --notification slack:#ops-alerts
```

**Alert fires if daily spend projected >$50**

---

## M5: Quality Degradation Alert

```bash
blocks alerts create \
  --name "Mutation Kill-Rate Low" \
  --query "avg_over_time(mutation_kill_rate[1h])" \
  --condition "< 60" \
  --severity P2 \
  --notification pagerduty:sre-oncall
```

**Alert fires if any flow <60% kill-rate**

---

## M5: Executive Reporting

### Monthly ROI Report

```bash
blocks metrics export \
  --report-type executive \
  --period monthly \
  --format pdf \
  --output monthly_roi_report.pdf
```

**Includes:**
- Cycle time trends
- Cost savings vs baseline
- ROI calculation
- Quality gate compliance
- Incident summary

---

## M5: Custom Instrumentation

### Adding Custom Metrics

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Create custom metric
compliance_score = meter.create_gauge(
    name="block.compliance_score",
    description="Basel-I compliance (0-100)",
    unit="score"
)

# Emit metric
score = calculate_compliance_score(block)
compliance_score.set(score, {"block_id": block_id})
```

**Query in Grafana:**
```promql
avg(block_compliance_score{block_family="compliance"})
```

---

# Modules 2-5: Summary

---

## Key Takeaways (All Modules)

**Module 2:** 6-face architecture + property-based testing
**Module 3:** 5 quality gates (contract, coverage, mutation, security, review)
**Module 4:** 5 runbooks + zero-downtime rollback
**Module 5:** 3 dashboards (ROI, quality, reliability)

---

## Certification Quiz

### To earn your certificate, complete the quiz:

**URL:** https://training.blocks-orchestrator.com/quiz

**Topics Covered:**
- CLI basics (Module 1)
- 6-face architecture (Module 2)
- Quality gates (Module 3)
- Runbook procedures (Module 4)
- Dashboard interpretation (Module 5)

**Pass Rate:** 80% (8/10 questions)

---

## Next Steps

1. **Apply Learnings:** Generate your first production block
2. **Join Community:** #blocks-community Slack
3. **Attend Showcase:** Monthly showcase (share your success)
4. **Office Hours:** Thursdays 2-3 PM for ongoing support

---

## Getting Help

**Slack:** #blocks-help
**Email:** support@blocks-orchestrator.com
**Docs:** https://docs.blocks-orchestrator.com
**Office Hours:** Thursdays 2-3 PM

---

# Congratulations! 🎉

You've completed all 5 training modules.

**You are now certified to use the Multi-LLM Orchestrator in production.**

---

# Thank You!

Questions? Join #blocks-community or attend office hours.

**See you in the field!** 🚀
