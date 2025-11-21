# Runbook: Security Incident Response

**Runbook ID:** RB-CORE-005
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona + InfoSec
**Severity:** CRITICAL (Security Event)

---

## Purpose

This runbook provides procedures for detecting and responding to security incidents involving the Multi-LLM Orchestrator, including credential leaks, unauthorized access, and data breaches.

**Security Incident Definition:**
- API key exposure or leak (in code, logs, or public repos)
- Unauthorized access to orchestrator infrastructure
- Data breach (context bundles, generated code, PII)
- Malicious code generation or injection
- Compliance violation (data retention, audit trail tampering)

**Target Audience:** SRE on-call, InfoSec team, Incident Commander

---

## Threat Model

### Assets to Protect

| Asset | Sensitivity | Impact if Compromised | Mitigation |
| --- | --- | --- | --- |
| **Model API Keys** | CRITICAL | Unauthorized API usage, cost runaway, service suspension | Secrets management, rotation, monitoring |
| **Context Bundles** | HIGH | Source code exposure, IP theft | S3 encryption, access control, immutability |
| **Generated Code** | MEDIUM | Business logic exposure | Output validation, access control |
| **TaskDB** | MEDIUM | Flow metadata exposure, PII leak | Database encryption, connection security |
| **User Credentials** | HIGH | Unauthorized orchestrator access | SSO, MFA, least privilege |

---

### Threat Scenarios (By Likelihood)

#### Scenario 1: API Key Leak (Most Common — 50%)

**Example:**
- API key committed to public GitHub repo
- API key exposed in application logs
- API key in CI/CD pipeline environment variable (visible to all users)

**Indicators:**
- Unexpected API usage spike (unauthorized flows)
- Model provider notifies of key exposure
- Security scan detects key in code

---

#### Scenario 2: Unauthorized Infrastructure Access (20%)

**Example:**
- Compromised Kubernetes credentials
- SQL injection in TaskDB queries
- Exposed FlowEngine admin endpoint

**Indicators:**
- Unauthorized kubectl commands in audit logs
- Database queries from unknown IP addresses
- Admin API calls without valid authentication

---

#### Scenario 3: Generated Code Injection (15%)

**Example:**
- Attacker manipulates prompt to generate malicious code
- Orchestrator generates code with backdoors, SQL injection, XSS

**Indicators:**
- Security scan detects HIGH/CRITICAL vulnerabilities in generated code
- Quality gate BLOCKERs (BLOCKER-SEC-001: hardcoded credentials, etc.)

---

#### Scenario 4: Data Breach (10%)

**Example:**
- Unauthorized access to S3 context bundles
- Stolen generated code from output directories
- TaskDB dump exposed

**Indicators:**
- S3 access logs show unauthorized GetObject requests
- Database export activity from unknown source
- Data exfiltration detected by DLP tools

---

#### Scenario 5: Compliance Violation (5%)

**Example:**
- Context bundle deleted before 7-year retention requirement (Basel-I)
- Audit trail tampered with
- PII included in context without consent

**Indicators:**
- S3 Object Lock bypass detected
- Audit log gaps or modifications
- PII detection in context bundles (e.g., SSN, credit card numbers)

---

## Detection

### Automated Alerts

**Alert: API Key Exposed in Code**

```yaml
alert: APIKeyExposedInCode
expr: |
  security_scan_findings_total{severity="CRITICAL", finding_type="hardcoded_secret"} > 0
for: 1m
labels:
  severity: critical
  runbook: RB-CORE-005
annotations:
  summary: "API key detected in code repository"
  description: "{{ $value }} hardcoded secrets found in recent commits"
```

**Alert: Unauthorized API Usage**

```yaml
alert: UnauthorizedAPIUsage
expr: |
  rate(flowengine_flow_executions_total[1h]) > 10 AND hour() < 6 OR hour() > 22
for: 30m
labels:
  severity: warning
  runbook: RB-CORE-005
annotations:
  summary: "Unexpected flow execution during off-hours"
  description: "{{ $value }} flows/hour during 10 PM - 6 AM (normal: 0)"
```

**Alert: High-Severity Security Finding**

```yaml
alert: HighSeveritySecurityFinding
expr: |
  increase(flowengine_quality_gate_failures_total{gate="security_scan", severity="HIGH"}[1h]) > 0
for: 5m
labels:
  severity: warning
  runbook: RB-CORE-005
annotations:
  summary: "HIGH severity security finding in generated code"
  description: "{{ $value }} findings in last hour"
```

---

### Manual Detection

```bash
# Check for exposed secrets in recent commits
git log --all --full-history --source --remotes --pretty=format:"%h %an %ad %s" \
  --since="1 week ago" -- "*.env" "*.key" "*secret*" "*credential*"

# Scan codebase for hardcoded API keys
grep -r "sk-ant-" . # Anthropic key pattern
grep -r "sk-proj-" . # OpenAI key pattern
grep -r "AIzaSy" . # Google API key pattern

# Check S3 access logs for unauthorized access
aws s3api get-bucket-logging --bucket blocks-context-bundles | jq

# Review recent database access
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT DISTINCT client_addr, usename, query
    FROM pg_stat_statements
    WHERE query NOT LIKE '%pg_stat%'
    LIMIT 20;"
```

---

## Immediate Response (0-15 Minutes)

### Step 1: Assess Incident Severity (5 minutes)

**Severity Classification:**

| Level | Definition | Examples | Response Time |
| --- | --- | --- | --- |
| **P1 (Critical)** | Active breach, widespread impact | API key actively used by attacker, live data exfiltration | <15 min |
| **P2 (High)** | Potential breach, limited scope | API key exposed but no unauthorized usage yet, single user compromised | <1 hour |
| **P3 (Medium)** | Security vulnerability discovered | Code vulnerability (not exploited), misconfiguration | <4 hours |
| **P4 (Low)** | Security finding (informational) | Low-severity scan finding, audit log anomaly | <24 hours |

---

### Step 2: Contain the Incident (10 minutes)

#### For API Key Leak (P1/P2):

```bash
# IMMEDIATE: Rotate all API keys (assume all compromised)

# Step 1: Generate new API keys from provider portals
# - Anthropic: https://console.anthropic.com → API Keys → Create Key
# - OpenAI: https://platform.openai.com/api-keys → Create New Secret Key
# - Google: https://console.cloud.google.com → APIs & Services → Credentials

# Step 2: Update Kubernetes secrets
kubectl create secret generic model-api-keys-new \
  --from-literal=anthropic=$NEW_ANTHROPIC_KEY \
  --from-literal=openai=$NEW_OPENAI_KEY \
  --from-literal=google=$NEW_GOOGLE_KEY \
  -n production --dry-run=client -o yaml | kubectl apply -f -

# Step 3: Update FlowEngine deployment
kubectl set env deployment/flowengine -n production \
  --from=secret/model-api-keys-new

# Step 4: Restart FlowEngine (graceful, zero downtime)
kubectl rollout restart deployment/flowengine -n production

# Step 5: Revoke old API keys from provider portals
# - Anthropic: Delete old key
# - OpenAI: Revoke old key
# - Google: Disable old key

# Step 6: Delete old Kubernetes secret
kubectl delete secret model-api-keys -n production

# Step 7: Rename new secret
kubectl get secret model-api-keys-new -n production -o yaml | \
  sed 's/model-api-keys-new/model-api-keys/' | kubectl apply -f -
kubectl delete secret model-api-keys-new -n production

# Estimated time: 10-15 minutes
```

---

#### For Unauthorized Infrastructure Access (P1):

```bash
# Step 1: Revoke compromised credentials
# If Kubernetes credentials compromised:
kubectl config delete-context <compromised-context>
kubectl delete serviceaccount <compromised-sa> -n production

# If database credentials compromised:
kubectl exec -n production statefulset/postgres -- \
  psql -U postgres -c "
    ALTER USER flowengine_user WITH PASSWORD '<new-password>';
    REVOKE ALL ON DATABASE flowengine_db FROM <compromised-user>;
  "

# Step 2: Enable network firewall (restrict access to known IPs only)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flowengine-lockdown
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: flowengine
  policyTypes:
    - Ingress
  ingress:
    - from:
        - ipBlock:
            cidr: <trusted-ip-range>/24  # e.g., corporate VPN
EOF

# Step 3: Audit recent activity
kubectl logs deployment/flowengine -n production --since=1h | grep -i "error\|unauthorized\|denied"

# Step 4: Escalate to InfoSec immediately
```

---

#### For Generated Code Injection (P2):

```bash
# Step 1: Quarantine affected flow output
FLOW_ID="<suspicious_flow_id>"

# Move generated code to quarantine directory
mkdir -p /tmp/quarantine/
blocks flow export $FLOW_ID --output /tmp/quarantine/$FLOW_ID/

# Remove from production
rm -rf $(blocks flow show $FLOW_ID --format json | jq -r '.output_path')

# Step 2: Mark flow as BLOCKED
blocks flow update $FLOW_ID --status blocked --reason "Security finding: potential code injection"

# Step 3: Scan quarantined code
cd /tmp/quarantine/$FLOW_ID/
semgrep --config=auto --severity=HIGH --severity=CRITICAL .

# Step 4: Notify repo owner
REPO_OWNER=$(blocks flow show $FLOW_ID --format json | jq -r '.repo_owner')
slack-cli dm --user $REPO_OWNER --message "
⚠️ **Security Alert: Flow $FLOW_ID Quarantined**

Your recent flow generated code with potential security issues.

**Finding:** <brief description from scan>
**Severity:** HIGH/CRITICAL
**Action Taken:** Generated code quarantined, not deployed

**Next Steps:**
1. Review security scan report: /tmp/quarantine/$FLOW_ID/scan_report.json
2. If false positive, contact InfoSec for review
3. If legitimate issue, regenerate with secure config

Contact: @infosec, @sre-oncall"
```

---

### Step 3: Notify Stakeholders (Immediate)

```bash
# Post to #security-incidents Slack (private channel)
slack-cli post --channel security-incidents --message "
🚨 **P1 SECURITY INCIDENT**

**Type:** <API Key Leak / Unauthorized Access / Data Breach>
**Detected:** $(date)
**Severity:** P1 (Critical) / P2 (High)

**Containment Actions Taken:**
- <Action 1>
- <Action 2>
- <Action 3>

**Incident Commander:** @incident-commander
**InfoSec Lead:** @infosec-lead
**SRE On-Call:** @sre-oncall

**Next Steps:**
- Full incident response (this runbook)
- Forensic analysis (InfoSec)
- Stakeholder communication plan

**War Room:** Zoom link (or conference room)"

# Page InfoSec team
pagerduty trigger \
  --severity critical \
  --title "Security Incident: Multi-LLM Orchestrator" \
  --details "<brief description>"

# Email executive leadership (if P1)
if [ "$SEVERITY" == "P1" ]; then
  echo "Subject: URGENT: Security Incident - Multi-LLM Orchestrator

A critical security incident has been detected involving the Multi-LLM Orchestrator.

**Incident Type:** <type>
**Containment:** In progress (ETA: <X> minutes)
**Impact:** <brief impact assessment>

**Response Team:**
- Incident Commander: <name>
- InfoSec Lead: <name>
- SRE On-Call: <name>

**Next Update:** +30 minutes

This incident is being actively managed. We will provide updates every 30 minutes until resolved.

SRE Team" | mail -s "🚨 P1 Security Incident" \
    vp-engineering@company.com,ciso@company.com
fi
```

---

## Investigation & Forensics (15-60 Minutes)

### Step 1: Preserve Evidence

```bash
# Capture logs (all components, last 24h)
kubectl logs deployment/flowengine -n production --since=24h > /tmp/evidence/flowengine_$(date +%Y%m%d_%H%M%S).log

kubectl logs statefulset/postgres -n production --since=24h > /tmp/evidence/postgres_$(date +%Y%m%d_%H%M%S).log

# Capture Kubernetes audit logs
kubectl get events -n production --sort-by='.lastTimestamp' > /tmp/evidence/k8s_events_$(date +%Y%m%d_%H%M%S).log

# Export database snapshot (for forensics, DO NOT modify production DB)
kubectl exec -n production statefulset/postgres -- \
  pg_dump -U flowengine_user flowengine_db | \
  gzip > /tmp/evidence/taskdb_snapshot_$(date +%Y%m%d_%H%M%S).sql.gz

# Capture S3 access logs (context bundles)
aws s3 sync s3://blocks-context-bundles-logs/ /tmp/evidence/s3_access_logs/

# Upload evidence to secure forensics bucket
aws s3 sync /tmp/evidence/ s3://security-forensics-$(date +%Y%m%d)/ --sse AES256
```

---

### Step 2: Determine Attack Timeline

```bash
# Analyze logs to reconstruct timeline

# Example: API key leak detection
grep "API_KEY" /tmp/evidence/flowengine_*.log | head -50

# Identify first unauthorized usage
grep "401\|403\|unauthorized" /tmp/evidence/flowengine_*.log | \
  awk '{print $1, $2}' | sort | head -1

# Example output:
# 2025-11-16 03:42:15 Unauthorized API request from IP 203.0.113.42

# Geo-locate attacker IP
curl -s https://ipinfo.io/203.0.113.42 | jq

# Identify affected flows (if unauthorized usage occurred)
grep "flow_id" /tmp/evidence/flowengine_*.log | \
  awk '{print $5}' | sort | uniq > /tmp/affected_flows.txt

wc -l /tmp/affected_flows.txt
# Example: 37 affected flows
```

---

### Step 3: Assess Impact

```bash
# Quantify impact

# 1. Cost Impact (unauthorized API usage)
blocks metrics query \
  --metric flow_cost \
  --start <incident_start_time> \
  --end <incident_end_time> \
  --aggregation sum

# Example: $127 unauthorized spend

# 2. Data Exposure (context bundles accessed)
aws s3api list-objects-v2 --bucket blocks-context-bundles \
  --query "Contents[?LastModified>=\`<incident_start_time>\`].Key" | \
  jq 'length'

# Example: 42 context bundles potentially exposed

# 3. Code Generation (flows executed)
wc -l /tmp/affected_flows.txt
# Example: 37 flows executed by attacker

# 4. Infrastructure Compromise
kubectl get pods -n production --field-selector=status.phase=Failed
# Check for abnormal pod crashes during incident window
```

---

## Remediation & Recovery

### Step 1: Patch Vulnerabilities

**If API Key Leak:**

```bash
# Ensure keys rotated (already done in containment)

# Add secret scanning to pre-commit hooks (prevent future leaks)
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Secret scanning pre-commit hook

if git diff --cached | grep -qE "sk-ant-|sk-proj-|AIzaSy"; then
  echo "❌ ERROR: Potential API key detected in commit"
  echo "Remove hardcoded secrets before committing."
  exit 1
fi

echo "✅ Secret scan passed"
exit 0
EOF

chmod +x .git/hooks/pre-commit

# Add secret scanning to CI/CD pipeline
cat >> .github/workflows/security-scan.yml <<EOF
- name: Secret Scanning
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: main
    head: HEAD
EOF

# Configure automated secret rotation (every 90 days)
# - Calendar reminder: ops-calendar@company.com
# - Or use AWS Secrets Manager automatic rotation
```

---

**If Generated Code Injection:**

```bash
# Enhance prompt injection detection

kubectl set env deployment/flowengine -n production \
  ENABLE_PROMPT_INJECTION_DETECTION=true \
  PROMPT_INJECTION_THRESHOLD=0.8  # Block if confidence >80%

# Add post-generation security scan (mandatory)
kubectl set env deployment/flowengine -n production \
  ENABLE_POST_GENERATION_SCAN=true \
  BLOCK_ON_HIGH_SEVERITY=true  # Do not return output if HIGH/CRITICAL findings

# Update quality gate configuration
blocks config set --global security-scan-severity-threshold HIGH
```

---

**If Unauthorized Infrastructure Access:**

```bash
# Enforce MFA for Kubernetes access
# (Coordinate with Infrastructure team)

# Enable audit logging for all kubectl commands
kubectl create -f - <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: Metadata
    omitStages:
      - RequestReceived
EOF

# Restrict database access to FlowEngine pods only
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-access-control
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: flowengine
      ports:
        - protocol: TCP
          port: 5432
EOF
```

---

### Step 2: Notify Affected Users

**If data breach occurred:**

```bash
# Identify affected users (repo owners whose context was exposed)
cat /tmp/affected_flows.txt | xargs -I {} blocks flow show {} --format json | \
  jq -r '.repo_owner' | sort | uniq > /tmp/affected_users.txt

# Send breach notification
while read user; do
  echo "Subject: Security Incident Notification - Data Exposure

Dear $user,

We are writing to inform you of a security incident involving the Multi-LLM Orchestrator.

**Incident:** <brief description>
**Your Data:** Your repository's context bundle(s) may have been accessed by an unauthorized party.
**Date Range:** <incident start> to <incident end>

**Actions Taken:**
- Incident contained within <X> minutes of detection
- All API keys rotated
- Additional security measures implemented

**Recommended Actions:**
1. Review your repository for any sensitive data that may have been exposed
2. If PII or credentials were in context, follow your organization's breach procedures
3. Contact InfoSec if you have questions: infosec@company.com

We apologize for this incident and have implemented additional safeguards to prevent recurrence.

SRE Team + InfoSec" | mail -s "Security Incident Notification" $user
done < /tmp/affected_users.txt
```

---

### Step 3: Compliance Reporting (If Applicable)

**If PII exposed (GDPR, CCPA, etc.):**

```bash
# Notify Data Protection Officer (DPO)
# Required within 72 hours of detection for GDPR

echo "Subject: URGENT: Data Breach Notification (Regulatory Reporting)

To: dpo@company.com
CC: legal@company.com, ciso@company.com

A data breach has been detected that may require regulatory reporting.

**Incident Summary:**
- Date Detected: $(date)
- Type: <Unauthorized access to context bundles containing potential PII>
- Affected Records: <count> context bundles, <count> users
- Data Types: Source code, configuration files, potential PII

**Regulatory Requirements:**
- GDPR: Report to supervisory authority within 72 hours (Deadline: <date>)
- CCPA: Notify affected California residents without unreasonable delay

**Evidence Package:** s3://security-forensics-$(date +%Y%m%d)/

**Next Steps:**
1. DPO assessment of PII exposure (ASAP)
2. Legal review of notification requirements
3. Prepare regulatory reports (templates: legal/data_breach/)

Contact: infosec-lead@company.com

SRE Team" | mail -s "Data Breach - Regulatory Reporting Required" dpo@company.com
```

---

## Post-Incident Actions

### Step 1: Root Cause Analysis (Within 48 Hours)

**RCA Template:** `planning/60_launch/incidents/rca_security_<incident_id>.md`

```markdown
# Security Incident RCA: <Incident Title>

**Incident ID:** SEC-<date>-<number>
**Date:** <incident date>
**Severity:** P1/P2/P3
**Duration:** <detection to resolution>

## Executive Summary
<2-3 sentences: what happened, root cause, resolution>

## Attack Timeline
- <time>: Vulnerability introduced (e.g., API key committed to repo)
- <time>: Attacker discovered vulnerability
- <time>: First unauthorized access
- <time>: Detection (automated alert / manual discovery)
- <time>: Containment (keys rotated, access revoked)
- <time>: Incident resolved

## Root Cause
<Detailed analysis of how the incident occurred>

**Contributing Factors:**
1. Lack of secret scanning in pre-commit hooks
2. No alerting for off-hours API usage
3. Insufficient training on secret management best practices

## Impact Assessment
- **Cost:** $<amount> unauthorized API usage
- **Data:** <count> context bundles exposed, <count> flows executed
- **Users:** <count> repo owners affected
- **Compliance:** <any regulatory reporting required>

## Remediation
- <Action 1: Rotated all API keys>
- <Action 2: Implemented secret scanning>
- <Action 3: Enhanced monitoring>

## Prevention (Action Items)
- [ ] <Owner>: Implement automated secret rotation (Due: <date>)
- [ ] <Owner>: Mandatory security training for all engineers (Due: <date>)
- [ ] <Owner>: Quarterly security audit of orchestrator (Due: <date>)

## Lessons Learned
<Key takeaways>
```

---

### Step 2: Security Hardening Roadmap

**Implement following enhancements (Q1 2026):**

```markdown
## Security Hardening Roadmap

### Phase 1: Immediate (Within 1 Week)
- [ ] Automated secret scanning (pre-commit + CI/CD)
- [ ] Off-hours usage alerts
- [ ] Network policies (least privilege access)

### Phase 2: Short-Term (Within 1 Month)
- [ ] Automated secret rotation (90-day cycle)
- [ ] Security training for all orchestrator users
- [ ] Enhanced audit logging (Kubernetes, database, S3)

### Phase 3: Long-Term (Within 3 Months)
- [ ] Implement HashiCorp Vault for secret management
- [ ] SIEM integration (Splunk/ELK) for threat detection
- [ ] Penetration testing (external security firm)
- [ ] Bug bounty program

### Phase 4: Continuous
- [ ] Quarterly security audits
- [ ] Annual penetration testing
- [ ] Security champions program (embedded in each team)
```

---

## Prevention Best Practices

### Secure Secret Management

```bash
# Use Kubernetes secrets (encrypted at rest)
kubectl create secret generic model-api-keys \
  --from-literal=anthropic=$ANTHROPIC_KEY \
  --from-literal=openai=$OPENAI_KEY \
  --from-literal=google=$GOOGLE_KEY \
  -n production

# Enable encryption at rest (if not already enabled)
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>

# Rotate secrets every 90 days
# Add to ops calendar: "Rotate orchestrator API keys" (quarterly)
```

---

### Least Privilege Access

```bash
# Create service account with minimal permissions
kubectl create serviceaccount flowengine-sa -n production

kubectl create role flowengine-role -n production \
  --verb=get,list,watch \
  --resource=secrets,configmaps

kubectl create rolebinding flowengine-rb -n production \
  --role=flowengine-role \
  --serviceaccount=production:flowengine-sa

# Update deployment to use service account
kubectl patch deployment/flowengine -n production \
  -p '{"spec":{"template":{"spec":{"serviceAccountName":"flowengine-sa"}}}}'
```

---

### Audit Logging

```bash
# Enable S3 access logging (context bundles)
aws s3api put-bucket-logging \
  --bucket blocks-context-bundles \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "blocks-context-bundles-logs",
      "TargetPrefix": "access-logs/"
    }
  }'

# Enable database query logging
kubectl exec -n production statefulset/postgres -- \
  psql -U postgres -c "ALTER SYSTEM SET log_statement = 'all';"

kubectl rollout restart statefulset/postgres -n production
```

---

## Metrics & SLOs

**Security Incident Response:**
- Time to detection: <15 minutes (automated alerts)
- Time to containment: <30 minutes (key rotation, access revocation)
- Time to resolution: <4 hours (full remediation)

**Security Posture:**
- Critical vulnerabilities: 0 (continuous)
- Secret rotation frequency: Every 90 days
- Security training completion: 100% of orchestrator users

**Pilot Performance:**
- Security incidents: 0
- Vulnerabilities detected: 0 (5/5 quality gates met)

---

## Escalation

### L1: SRE On-Call (Initial Response)
- **Action:** Containment, evidence preservation
- **SLA:** <15 minutes

### L2: InfoSec Team
- **Action:** Forensic analysis, remediation guidance
- **SLA:** <1 hour

### L3: Incident Commander + CISO
- **Action:** Executive communication, regulatory reporting
- **SLA:** <4 hours (for P1 incidents)

---

## Emergency Contacts

| Role | Primary | Backup | Contact |
| --- | --- | --- | --- |
| **InfoSec Lead** | <name> | <name> | @infosec-lead, <phone> |
| **CISO** | <name> | — | @ciso, <phone> |
| **DPO (Data Protection)** | <name> | <name> | dpo@company.com |
| **Legal** | <name> | <name> | legal@company.com |
| **PR/Comms** | <name> | <name> | pr@company.com |

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-LAUNCH-002:** Rollback to Pilot (`planning/60_launch/runbooks/rollback_to_pilot.md`)
- **RB-LAUNCH-005:** Mass Failure Response (`planning/60_launch/runbooks/mass_failure.md`)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE + InfoSec | Initial version for Phase 6/7 security incident response |

---

**Status:** ✅ Ready for Phase 6 (security controls validated)
**Next Review:** Quarterly (March 2026)
**Maintained By:** SRE Persona + InfoSec Team

---

**CRITICAL:** Security incidents require immediate InfoSec involvement. Do not delay escalation.
