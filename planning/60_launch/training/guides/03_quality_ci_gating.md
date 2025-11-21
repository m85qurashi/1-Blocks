# Quality & CI Gating Guide

**Module 3:** Integrating Quality Gates into CI/CD Pipelines
**Duration:** 60 minutes (hands-on lab)
**Owner:** QA
**Last Updated:** November 16, 2025

---

## Overview

Quality gates ensure AI-generated blocks meet production standards before merge. This hands-on lab teaches you to integrate 5 quality gates into your CI/CD pipeline.

### What You'll Learn
- Configure 5 quality gates (contract, coverage, mutation, security, review)
- Integrate `blocks verify` into GitHub Actions / GitLab CI
- Interpret mutation testing results (Mutmut)
- Handle BLOCKER-level review findings
- Set up automated triage runbooks

### Prerequisites
- Completed Module 2 (Block Authoring)
- CI/CD system (GitHub Actions, GitLab CI, or Jenkins)
- Existing test suite (pytest, Jest, or equivalent)

---

## The 5 Quality Gates

| Gate | Tool | Threshold | Blocker? | Purpose |
| --- | --- | --- | --- | --- |
| **1. Contract Validation** | JSON Schema | 100% pass | ✅ Yes | Ensure input/output match schemas |
| **2. Unit Test Coverage** | pytest-cov | ≥90% | ⚠️ Warn | Verify logic exercised |
| **3. Mutation Kill-Rate** | Mutmut | ≥60% | ⚠️ Warn | Detect weak tests |
| **4. Security Scan** | Bandit / Semgrep | 0 HIGH/CRIT | ✅ Yes | No vulnerabilities |
| **5. Logic Review** | Claude Sonnet 4.5 | 0 BLOCKERs | ✅ Yes | AI validates correctness |

---

## Lab Setup

### Step 1: Install Quality Tools

```bash
# Install quality gate dependencies
pip install blocks-orchestrator[quality]

# This installs:
# - jsonschema (contract validation)
# - pytest-cov (coverage)
# - mutmut (mutation testing)
# - bandit (security scanning for Python)
# - semgrep (multi-language security)

# Verify installation
blocks verify --version
# Expected: blocks-verify v1.0.0
```

### Step 2: Initialize Quality Config

```bash
# Create quality configuration
blocks quality init

# This creates .blocks/quality.yml:
cat .blocks/quality.yml
```

**`.blocks/quality.yml`:**
```yaml
quality_gates:
  contract_validation:
    enabled: true
    threshold: 100  # Percent schemas passing

  unit_test_coverage:
    enabled: true
    threshold: 90   # Percent lines covered
    exclude_patterns:
      - "*/tests/*"
      - "*/migrations/*"

  mutation_testing:
    enabled: true
    threshold: 60   # Percent mutants killed
    timeout_per_mutant: 10  # Seconds

  security_scan:
    enabled: true
    severity_threshold: HIGH  # Block on HIGH or CRITICAL
    tools:
      - bandit
      - semgrep

  logic_review:
    enabled: true
    model: claude-sonnet-4-5
    blocker_keywords:
      - "BLOCKER:"
      - "Security Risk:"
      - "Data Loss Risk:"

ci_integration:
  fail_on_blocker: true
  fail_on_threshold_miss: warn  # warn or fail
  generate_report: true
  report_path: .blocks/quality_report.md
```

---

## Gate 1: Contract Validation

Validates all blocks against their input/output JSON Schemas.

### Manual Execution

```bash
# Validate a single block
blocks verify contract blocks/compliance/compliance_attestation.py

# Output:
# ┌───────────────────────────────────────────────────┐
# │ Contract Validation: compliance_attestation        │
# ├───────────────────────────────────────────────────┤
# │ Status: ✅ PASS                                    │
# │                                                   │
# │ Input Schema:  ✅ compliance_input.schema.json   │
# │   - Valid: 100% (0 errors)                        │
# │   - Examples tested: 2/2 passed                   │
# │                                                   │
# │ Output Schema: ✅ compliance_output.schema.json  │
# │   - Valid: 100% (0 errors)                        │
# │   - Examples tested: 1/1 passed                   │
# └───────────────────────────────────────────────────┘
```

### CI Integration (GitHub Actions)

**`.github/workflows/quality_gates.yml`:**
```yaml
name: Quality Gates

on:
  pull_request:
    branches: [main]

jobs:
  contract_validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install blocks-orchestrator[quality]

      - name: Validate Contracts
        run: |
          blocks verify contract blocks/ --output-format json > contract_results.json

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: contract-validation-results
          path: contract_results.json

      - name: Fail on Errors
        run: |
          if grep -q '"status": "FAIL"' contract_results.json; then
            echo "❌ Contract validation failed"
            exit 1
          fi
```

---

## Gate 2: Unit Test Coverage

Ensures ≥90% of block logic is exercised by tests.

### Manual Execution

```bash
# Run tests with coverage
pytest blocks/compliance/tests/ --cov=blocks/compliance --cov-report=term-missing

# Output:
# ---------- coverage: platform linux, python 3.9.7 -----------
# Name                                 Stmts   Miss  Cover   Missing
# ------------------------------------------------------------------
# blocks/compliance/__init__.py            3      0   100%
# blocks/compliance/logic.py              45      3    93%   78-80
# blocks/compliance/validators.py         28      1    96%   42
# blocks/compliance/formatters.py         22      0   100%
# ------------------------------------------------------------------
# TOTAL                                   98      4    96%

# ✅ Coverage: 96% (exceeds 90% threshold)
```

### CI Integration (GitHub Actions)

Add to `.github/workflows/quality_gates.yml`:
```yaml
  unit_test_coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run Tests with Coverage
        run: |
          pytest blocks/ --cov=blocks --cov-report=json --cov-report=term

      - name: Check Coverage Threshold
        run: |
          python -c "
          import json
          with open('coverage.json') as f:
              coverage = json.load(f)['totals']['percent_covered']
          print(f'Coverage: {coverage:.1f}%')
          if coverage < 90:
              print('❌ Coverage below 90% threshold')
              exit(1)
          "
```

---

## Gate 3: Mutation Testing

Mutation testing validates that your tests actually catch bugs by introducing intentional defects.

### How Mutation Testing Works

1. **Mutmut** mutates your code (e.g., changes `>` to `>=`, `+` to `-`)
2. Tests run against each mutant
3. If tests **pass** with mutant present → **mutant survived** (weak test)
4. If tests **fail** with mutant present → **mutant killed** (strong test)

**Goal:** ≥60% mutation kill-rate (60% of mutants killed by tests)

### Manual Execution

```bash
# Run mutation testing on a specific file
mutmut run --paths-to-mutate blocks/compliance/logic.py

# Output:
# 1. Running tests without mutations
# ⠙ Running... Done
#
# 2. Checking mutants
# ⠙ 1/32  🎉 KILLED
# ⠙ 2/32  🎉 KILLED
# ⠙ 3/32  😱 SURVIVED
# ...
# ⠙ 32/32 🎉 KILLED
#
# Results:
# - Killed: 28 (87.5%)
# - Survived: 3 (9.4%)
# - Timeout: 1 (3.1%)

# View surviving mutants (need attention)
mutmut results

# Show specific surviving mutant
mutmut show 3
# --- blocks/compliance/logic.py
# +++ blocks/compliance/logic.py
# @@ -45,7 +45,7 @@
#      def _verify_sha256(artifact_uri: str, expected_hash: str) -> bool:
# -        return artifact_hash == expected_hash
# +        return True  # 😱 SURVIVED: Test doesn't verify hash comparison
```

### Fixing Weak Tests

**Before (weak test):**
```python
def test_verify_sha256():
    """Test hash verification."""
    result = AttestationEngine._verify_sha256("s3://bucket/file", "abc123")
    assert isinstance(result, bool)  # ❌ Doesn't verify correctness
```

**After (strong test):**
```python
def test_verify_sha256_with_valid_hash():
    """Test hash verification passes for correct hash."""
    result = AttestationEngine._verify_sha256("s3://bucket/file", "abc123")
    assert result is True  # ✅ Verifies True path

def test_verify_sha256_with_invalid_hash():
    """Test hash verification fails for incorrect hash."""
    result = AttestationEngine._verify_sha256("s3://bucket/file", "wrong_hash")
    assert result is False  # ✅ Verifies False path (kills "return True" mutant)
```

### CI Integration

Add to `.github/workflows/quality_gates.yml`:
```yaml
  mutation_testing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mutmut

      - name: Run Mutation Tests
        run: |
          mutmut run --paths-to-mutate blocks/ --CI
          mutmut results > mutation_results.txt

      - name: Check Mutation Kill-Rate
        run: |
          kill_rate=$(grep -oP 'Killed: \K\d+\.\d+' mutation_results.txt)
          echo "Mutation kill-rate: ${kill_rate}%"
          if (( $(echo "$kill_rate < 60" | bc -l) )); then
            echo "⚠️  Mutation kill-rate below 60% threshold"
            exit 1
          fi
```

---

## Gate 4: Security Scan

Scans for vulnerabilities using Bandit (Python) and Semgrep (multi-language).

### Manual Execution

```bash
# Scan with Bandit (Python)
bandit -r blocks/ -f json -o bandit_results.json

# Output:
# Run started:2025-11-16 10:30:00
#
# Test results:
# >> Issue: [B605:start_process_with_shell]
#    Severity: High   Confidence: High
#    Location: blocks/compliance/integrations.py:42
#    More Info: https://bandit.readthedocs.io/en/latest/plugins/b605_start_process_with_shell.html
# 42    os.system(f"aws s3 cp {file} {s3_uri}")  # ❌ Shell injection risk
#
# Code scanned: 450 lines
# Issues found: 1 (High: 1, Medium: 0, Low: 0)

# Scan with Semgrep
semgrep --config=auto blocks/ --json > semgrep_results.json
```

### Fixing Security Issues

**Before (vulnerable):**
```python
def upload_to_s3(file_path: str, s3_uri: str):
    os.system(f"aws s3 cp {file_path} {s3_uri}")  # ❌ Shell injection
```

**After (secure):**
```python
import boto3

def upload_to_s3(file_path: str, s3_uri: str):
    s3 = boto3.client('s3')
    bucket, key = parse_s3_uri(s3_uri)
    with open(file_path, 'rb') as f:
        s3.upload_fileobj(f, bucket, key)  # ✅ No shell injection
```

### CI Integration

Add to `.github/workflows/quality_gates.yml`:
```yaml
  security_scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r blocks/ -f json -o bandit.json || true

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: auto

      - name: Check for HIGH/CRITICAL Issues
        run: |
          high_count=$(jq '[.results[] | select(.issue_severity=="HIGH" or .issue_severity=="CRITICAL")] | length' bandit.json)
          if [ "$high_count" -gt 0 ]; then
            echo "❌ Found $high_count HIGH/CRITICAL security issues"
            exit 1
          fi
```

---

## Gate 5: Logic Review (AI-Powered)

Claude Sonnet 4.5 reviews block logic for correctness, security, and adherence to patterns.

### Manual Execution

```bash
# Submit block for AI review
blocks review submit blocks/compliance/compliance_attestation.py

# Output:
# 🔄 Submitting to Claude Sonnet 4.5 for review...
# ⏱️  Review duration: 22.1s | Cost: $0.42
#
# Review Report:
# ┌─────────────────────────────────────────────────────┐
# │ Logic Review: compliance_attestation.py              │
# ├─────────────────────────────────────────────────────┤
# │ Overall: ✅ APPROVED (1 suggestion, 0 blockers)     │
# │                                                     │
# │ ✅ Correctness                                       │
# │    - Logic follows 6-face architecture              │
# │    - Input validation comprehensive                 │
# │    - Error handling present                         │
# │                                                     │
# │ ✅ Security                                          │
# │    - No injection vulnerabilities                   │
# │    - Secrets properly isolated                      │
# │    - Audit trail complete                           │
# │                                                     │
# │ 💡 Suggestion (line 78)                             │
# │    Consider adding pagination for large block lists │
# │    Severity: INFO                                   │
# └─────────────────────────────────────────────────────┘
```

### Handling BLOCKERs

If review finds a BLOCKER, the CI pipeline fails:

```bash
# Example BLOCKER output:
# ❌ BLOCKER (line 45): Data Loss Risk
#    The attestation overwrites existing reports without backup.
#    Recommendation: Add versioning or archive old reports before overwrite.
```

**Fix and re-submit:**
```python
def save_attestation(report_id: str, attestation: Dict[str, Any]):
    # Before: overwrites without backup
    # with open(f"{report_id}.json", "w") as f:
    #     json.dump(attestation, f)

    # After: version control
    version = get_next_version(report_id)
    versioned_path = f"{report_id}_v{version}.json"
    with open(versioned_path, "w") as f:
        json.dump(attestation, f)  # ✅ No data loss
```

### CI Integration

Add to `.github/workflows/quality_gates.yml`:
```yaml
  logic_review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Submit for AI Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          blocks review submit blocks/ --output-format json > review_results.json

      - name: Check for BLOCKERs
        run: |
          blocker_count=$(jq '[.reviews[] | select(.findings[] | .severity=="BLOCKER")] | length' review_results.json)
          if [ "$blocker_count" -gt 0 ]; then
            echo "❌ Found $blocker_count BLOCKER-level issues"
            cat review_results.json | jq '.reviews[].findings[] | select(.severity=="BLOCKER")'
            exit 1
          fi
```

---

## Complete CI Pipeline

**Full `.github/workflows/quality_gates.yml`:**
```yaml
name: Quality Gates

on:
  pull_request:
    branches: [main]

jobs:
  quality_gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Dependencies
        run: |
          pip install blocks-orchestrator[quality]
          pip install -r requirements.txt

      - name: Run All Quality Gates
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          blocks verify all blocks/ --output-format json > quality_report.json

      - name: Generate Quality Report
        run: |
          blocks verify report quality_report.json --format markdown > quality_report.md

      - name: Upload Quality Report
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: quality_report.md

      - name: Post Report to PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('quality_report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });

      - name: Fail on Blocker Issues
        run: |
          if jq -e '.blockers > 0' quality_report.json > /dev/null; then
            echo "❌ Quality gates failed (blockers detected)"
            exit 1
          fi
```

---

## Automated Triage Runbook

When quality gates fail, use this runbook:

### 1. Contract Validation Failure
**Symptom:** Input/output doesn't match schema

**Triage:**
```bash
blocks verify contract blocks/X --verbose
# Shows: exact schema validation errors
```

**Fix:**
- Update schema if requirements changed
- Fix block implementation if schema is correct

### 2. Coverage Below 90%
**Symptom:** `pytest-cov` reports <90%

**Triage:**
```bash
pytest blocks/X --cov=blocks/X --cov-report=html
# Open htmlcov/index.html to see uncovered lines
```

**Fix:** Add tests for uncovered edge cases

### 3. Mutation Kill-Rate <60%
**Symptom:** Too many mutants survive

**Triage:**
```bash
mutmut show <mutant_id>
# Shows exact mutant that survived
```

**Fix:** Strengthen assertions in tests

### 4. Security Scan Failures
**Symptom:** Bandit/Semgrep reports HIGH/CRITICAL

**Triage:**
```bash
bandit -r blocks/X -ll  # Show only HIGH issues
```

**Fix:** Apply secure coding patterns (see examples above)

### 5. BLOCKER in Logic Review
**Symptom:** Claude flags critical issue

**Triage:** Read BLOCKER rationale carefully

**Fix:** Address root cause (data loss, security, correctness)

---

## Best Practices

1. **Run Locally Before Push:**
   ```bash
   blocks verify all blocks/ --fast
   ```

2. **Monitor Quality Metrics:**
   - Track mutation kill-rate trend (aim for ≥60%)
   - Track BLOCKER rate (aim for <1% of PRs)

3. **Educate Team:**
   - Share mutation testing examples in team meetings
   - Create a "Quality Hall of Fame" for high-quality blocks

4. **Iterate on Thresholds:**
   - Start with lenient thresholds (e.g., 80% coverage)
   - Gradually increase as team matures

---

## Next Steps

1. **Integrate into Your CI:** Add `.github/workflows/quality_gates.yml` to your repo
2. **Run First Quality Check:** Submit a PR and verify all gates pass
3. **Review Dashboards:** Access Quality Dashboard (Module 5) to track trends
4. **Learn Runbooks:** Proceed to Module 4 for incident response procedures

---

**Module 3 Complete!** Proceed to Module 4: Runbooks & Rollback
