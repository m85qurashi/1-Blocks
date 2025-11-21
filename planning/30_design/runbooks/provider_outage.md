# Runbook: Provider Outage Response

**Runbook ID:** RB-CORE-004
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona
**Severity:** HIGH (Service Degradation)

---

## Purpose

This runbook provides procedures for detecting and responding to model provider (Anthropic, OpenAI, Google) outages or degradations affecting the Multi-LLM Orchestrator.

**Provider Outage Definition:**
- Provider API completely unreachable (HTTP 5xx, connection timeout)
- Provider API degraded (latency >60s, error rate >10%)
- Provider planned maintenance window

**Target Audience:** SRE on-call

---

## Supported Providers

### Provider Details

| Provider | Models Used | Role in Orchestrator | Impact if Down |
| --- | --- | --- | --- |
| **Anthropic** | Claude Sonnet 4.5 | Architecture, Logic Review | HIGH (45% of workflow) |
| **OpenAI** | GPT-4 Turbo | Implementation, Code Generation | HIGH (38% of workflow) |
| **Google** | Gemini Pro | Context Retrieval | MEDIUM (17% of workflow) |

**Failure Tolerance:**
- **1 provider down:** Orchestrator operational (automatic failover)
- **2 providers down:** Orchestrator degraded (limited capacity)
- **3 providers down:** Orchestrator offline (rollback to pilot or manual)

---

## Detection

### Automated Alerts

**Alert: Provider API Unreachable**

```yaml
alert: ProviderAPIUnreachable
expr: |
  probe_success{job="model_provider_health"} == 0
for: 5m
labels:
  severity: critical
  runbook: RB-CORE-004
annotations:
  summary: "Model provider {{ $labels.provider }} unreachable"
  description: "Health check failed for >5 minutes"
```

**Alert: Provider API Degraded**

```yaml
alert: ProviderAPIDegraded
expr: |
  histogram_quantile(0.95,
    rate(flowengine_model_api_latency_seconds_bucket[10m])
  ) > 60
for: 10m
labels:
  severity: warning
  provider: "{{ $labels.provider }}"
annotations:
  summary: "Provider {{ $labels.provider }} API latency >60s"
  description: "P95 latency: {{ $value }}s (normal: <30s)"
```

**Alert: Provider Error Rate High**

```yaml
alert: ProviderErrorRateHigh
expr: |
  rate(flowengine_model_api_errors_total{provider=~".*"}[10m]) /
  rate(flowengine_model_api_requests_total{provider=~".*"}[10m]) > 0.1
for: 10m
labels:
  severity: warning
  provider: "{{ $labels.provider }}"
annotations:
  summary: "Provider {{ $labels.provider }} error rate >10%"
  description: "Error rate: {{ $value | humanizePercentage }}"
```

---

### Manual Detection

```bash
# Check provider health (all 3 providers)
blocks health check --providers all

# Expected output:
# | Provider | Status | Latency | Error Rate | Last Checked |
# |----------|--------|---------|------------|--------------|
# | Anthropic | ✅ Healthy | 28s | 0.0% | 1 min ago |
# | OpenAI | ✅ Healthy | 24s | 0.2% | 1 min ago |
# | Google | ✅ Healthy | 19s | 0.1% | 1 min ago |

# If any provider shows ❌ Down or ⚠️ Degraded, investigate

# Check provider status pages
for provider in anthropic openai google; do
  echo "=== $provider ==="
  curl -s https://status.$provider.com/api/v2/status.json | \
    jq '{status: .status.indicator, description: .status.description}'
done

# Expected: indicator: "none" (no incidents)
# If "minor", "major", "critical" → confirmed outage
```

---

## Root Cause Verification

### Step 1: Confirm Outage Scope (3 minutes)

```bash
# Test direct API connectivity from FlowEngine pod
for provider in anthropic openai google; do
  echo "Testing $provider..."

  case $provider in
    anthropic)
      API_URL="https://api.anthropic.com/v1/messages"
      API_KEY=$ANTHROPIC_API_KEY
      ;;
    openai)
      API_URL="https://api.openai.com/v1/chat/completions"
      API_KEY=$OPENAI_API_KEY
      ;;
    google)
      API_URL="https://generativelanguage.googleapis.com/v1beta/models"
      API_KEY=$GOOGLE_API_KEY
      ;;
  esac

  kubectl exec -n production deployment/flowengine -- \
    curl -o /dev/null -s -w "Provider: $provider, HTTP: %{http_code}, Time: %{time_total}s\n" \
    -H "Authorization: Bearer $API_KEY" \
    "$API_URL"
done

# Expected: HTTP 200 or 401 (auth method varies), Time <1s
# If HTTP 5xx or 000 (no response), provider down
# If Time >10s, provider degraded
```

---

### Step 2: Check Provider Status Page (2 minutes)

**Anthropic:**

```bash
# Status page: https://status.anthropic.com
curl -s https://status.anthropic.com/api/v2/summary.json | \
  jq '{
    status: .status.indicator,
    incidents: .incidents | length,
    scheduled_maintenance: .scheduled_maintenances | length
  }'

# Expected: status: "none", incidents: 0
# If status: "major" or "critical", confirmed outage
```

**OpenAI:**

```bash
# Status page: https://status.openai.com
curl -s https://status.openai.com/api/v2/summary.json | jq .status
```

**Google (GCP):**

```bash
# Status page: https://status.cloud.google.com
# Note: Google Gemini is part of GCP, check "AI Platform" service
curl -s https://status.cloud.google.com/incidents.json | \
  jq '.[] | select(.service_name == "Google Cloud AI Platform")'
```

---

### Step 3: Determine Impact on Orchestrator (5 minutes)

```bash
# Check recent flow failures attributed to provider outage
blocks metrics query \
  --metric flow_failures_total \
  --last 30m \
  --filter error_type=provider_unavailable \
  --group-by provider

# Example output:
# | Provider | Failures (last 30m) |
# |----------|---------------------|
# | Anthropic | 12 |
# | OpenAI | 0 |
# | Google | 0 |

# If Anthropic down → 12 flows failed (or routed to fallback)

# Check if automatic failover occurred
kubectl logs deployment/flowengine -n production --tail=50 | grep "Failover"

# Expected log (if failover working):
# "Provider anthropic unreachable, failing over to gpt-4-turbo"
```

---

## Response Actions

### Scenario 1: Single Provider Down (Automatic Failover)

**Default behavior: Orchestrator automatically routes to healthy providers**

```bash
# Verify failover configuration enabled
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="ENABLE_PROVIDER_FAILOVER")].value}'

# Expected: "true"

# Verify failover logic in logs
kubectl logs deployment/flowengine -n production --tail=100 | grep -A 5 "Provider.*unreachable"

# Expected log:
# [2025-11-16 14:32:10] Provider anthropic unreachable (HTTP 503)
# [2025-11-16 14:32:10] Failover enabled: true
# [2025-11-16 14:32:10] Selecting alternate model for role: architect
# [2025-11-16 14:32:10] Alternate model: gpt-4-turbo (provider: openai)
# [2025-11-16 14:32:11] Flow continuing with fallback model

# Monitor alternate provider quota
blocks quota show --provider openai

# If alternate provider quota low (<30% headroom), may hit rate limits
# Consider: Reduce flow volume temporarily or enable circuit breaker
```

**Notify Stakeholders (Informational):**

```bash
# Post to #ops-alerts Slack
slack-cli post --channel ops-alerts --message "
ℹ️ **Provider Outage: Anthropic (Claude)**

**Status:** Automatic failover to OpenAI (GPT-4 Turbo)
**Impact:** Minimal (flows continuing normally)
**Root Cause:** Anthropic API outage (confirmed via status page)
**Provider ETA:** <ETA from status page, e.g., \"Investigating\">

**Action Taken:**
- Failover: ✅ Automatic
- Flows affected: 12 (re-routed successfully)
- Monitoring: Alternate provider quota usage

**No user action required.** We'll notify when Anthropic is restored.

SRE On-Call: @sre-oncall"
```

**Monitor Until Provider Restored:**

```bash
# Poll provider status every 15 min
while true; do
  STATUS=$(curl -s https://status.anthropic.com/api/v2/status.json | jq -r '.status.indicator')
  echo "$(date): Anthropic status: $STATUS"

  if [ "$STATUS" == "none" ]; then
    echo "✅ Anthropic restored!"
    break
  fi

  sleep 900  # 15 minutes
done

# When provider restored, verify health
blocks health check --provider anthropic

# Re-enable provider (automatic, but verify)
kubectl logs deployment/flowengine -n production --tail=20 | grep "Provider.*restored"
# Expected: "Provider anthropic restored, re-enabling"
```

---

### Scenario 2: Two Providers Down (Degraded Service)

**Orchestrator operational but limited capacity**

```bash
# Example: Anthropic + Google down, only OpenAI available

# Check remaining provider capacity
blocks quota show --provider openai

# Expected Phase 6: 1.5M tokens/day quota
# Current usage: 1.1M tokens (73%)
# Remaining headroom: 400K tokens (~11 flows)

# If headroom insufficient for current load:
# Option 1: Enable circuit breaker (pause at 85% quota)
kubectl set env deployment/flowengine -n production \
  ENABLE_CIRCUIT_BREAKER=true \
  CIRCUIT_BREAKER_THRESHOLD=85

# Option 2: Throttle flow execution (reduce concurrency)
kubectl set env deployment/flowengine -n production \
  MAX_CONCURRENT_FLOWS=5  # Reduce from 10-20

# Option 3: Rollback to pilot scope (if cannot sustain 10-repo load)
# Reference: RB-LAUNCH-002 (rollback_to_pilot.md)
```

**Notify Stakeholders (Warning):**

```bash
slack-cli post --channel ops-alerts --message "
⚠️ **DEGRADED: Multiple Provider Outage**

**Providers Down:**
- Anthropic (Claude): ❌ Down
- Google (Gemini): ❌ Down

**Providers Available:**
- OpenAI (GPT-4): ✅ Available (headroom: 27%)

**Impact:**
- Service: Degraded (operating on 1/3 providers)
- Capacity: Reduced to ~50% normal load
- Action: Circuit breaker enabled at 85% OpenAI quota

**Mitigation:**
- Flows routed to OpenAI only
- Non-critical flows may be delayed
- Monitoring: OpenAI quota consumption closely

**ETA for Full Restoration:** <ETA based on provider status pages>

SRE On-Call: @sre-oncall
Product Lead: @product-lead (FYI)"

# Escalate to Incident Commander if >2 hours
```

---

### Scenario 3: All Providers Down (Service Offline)

**CRITICAL: Complete orchestrator outage**

```bash
# Verify all 3 providers unreachable
blocks health check --providers all

# Expected (worst case):
# | Provider | Status |
# |----------|--------|
# | Anthropic | ❌ Down |
# | OpenAI | ❌ Down |
# | Google | ❌ Down |

# Trigger P1 incident
pagerduty trigger \
  --severity critical \
  --title "Multi-LLM Orchestrator: All Providers Down" \
  --details "Anthropic, OpenAI, and Google APIs all unreachable. Complete service outage."

# Post to #incidents Slack
slack-cli post --channel incidents --message "
🚨 **P1 INCIDENT: All Model Providers Down**

**Status:** Complete orchestrator outage
**Providers:** Anthropic ❌, OpenAI ❌, Google ❌
**Impact:** All flows failing, service offline

**Incident Commander:** @incident-commander
**SRE On-Call:** @sre-oncall
**Engineering TL:** @eng-tl

**Next Steps:**
1. Verify provider status pages (all show major outage?)
2. If provider-side outage: Wait for restoration, communicate to users
3. If infrastructure issue: Investigate network, DNS, API keys

**ETA for Update:** +15 minutes"
```

**Options:**

#### Option A: Wait for Provider Restoration (If Provider-Side Outage)

```bash
# Confirm outage is provider-side (not infrastructure issue)
# - All 3 provider status pages show "major" or "critical" incidents
# - Unlikely all 3 have simultaneous outages unless widespread internet issue

# Communication to users
echo "Subject: Multi-LLM Orchestrator Outage

All model providers (Anthropic, OpenAI, Google) are currently experiencing
outages confirmed via their status pages:
- Anthropic: https://status.anthropic.com
- OpenAI: https://status.openai.com
- Google: https://status.cloud.google.com

Multi-LLM Orchestrator is offline until at least one provider is restored.

**Expected Resolution:** <ETA based on provider status pages>

We will notify you immediately when service is restored.

SRE Team" | mail -s "🚨 Orchestrator Outage - Provider Issue" \
  all-users@company.com
```

#### Option B: Rollback to Manual Workflow (If Extended Outage)

```bash
# If provider outage >4 hours, revert to manual development workflow
# (Pre-orchestrator process)

# Disable orchestrator in CI/CD
for repo in $(cat planning/60_launch/evidence/onboarded_repos.txt); do
  blocks repo disable $repo --reason "Provider outage, manual workflow fallback"
done

# Notify users
echo "Due to extended provider outage (>4 hours), we are temporarily
reverting to manual development workflow.

**Action Required:**
- DO NOT use 'blocks generate' command
- Use standard development process (manual coding, testing)

**Estimated Duration:** Until providers restored + 1 hour (validation)

We apologize for the disruption.

SRE Team" | mail -s "Orchestrator Disabled - Manual Fallback" \
  all-users@company.com
```

---

## Provider-Specific Escalation

### Anthropic Support Contact

```bash
# Emergency contact (enterprise customers)
# Email: support@anthropic.com
# Phone: <enterprise support phone, if available>

# Email template
cat > /tmp/anthropic_outage.txt <<EOF
Subject: Production Outage - API Unreachable

To: support@anthropic.com

Hello Anthropic Support,

We are experiencing a production outage with the Claude API.

**Issue:**
- API Endpoint: https://api.anthropic.com/v1/messages
- Error: HTTP 503 Service Unavailable (or connection timeout)
- Duration: <X> minutes (started at <time> UTC)

**Impact:**
- Service: Multi-LLM Orchestrator (10-50 flows/day)
- Users Affected: <count> engineering teams

**Request:**
- ETA for restoration
- Status updates every 30 minutes

**Contact:**
- Primary: <sre_phone>
- Email: sre-oncall@company.com

Account ID: <account_id>

Thank you,
<Your Name>
SRE Team
EOF

mail -s "Production Outage - API Unreachable" support@anthropic.com < /tmp/anthropic_outage.txt
```

---

### OpenAI Support Contact

```bash
# Support portal: https://help.openai.com
# Enterprise customers: Account rep (direct contact)
```

---

### Google Support Contact

```bash
# GCP Console: Support → Create Case
# Priority: P1 (production outage)
# Issue: "Gemini API unreachable"
```

---

## Provider Restoration Verification

**After provider reports "resolved":**

```bash
# Step 1: Test API connectivity
blocks health check --provider anthropic

# Expected: Status: ✅ Healthy, Latency: <30s

# Step 2: Execute test flow
blocks generate \
  --repo compliance-service \
  --family compliance \
  --block-type attestation \
  --config test.json \
  --output /tmp/test/ \
  --verbose

# Expected: Flow completes successfully, uses restored provider

# Step 3: Re-enable provider (if manually disabled)
kubectl set env deployment/flowengine -n production \
  DISABLE_PROVIDERS=""  # Clear disabled list

# Step 4: Monitor for 30 minutes
watch -n 300 'blocks health check --providers all; blocks metrics query --metric flow_failures_total --last 30m'

# Expected: All providers healthy, zero failures

# Step 5: Notify stakeholders
slack-cli post --channel ops-alerts --message "
✅ **Provider Restored: Anthropic (Claude)**

**Status:** Fully operational
**Verification:** Test flows successful, health checks passing
**Duration:** <total outage duration>

All orchestrator flows resuming normally.

Incident closed.

SRE Team"
```

---

## Prevention & Monitoring

### Provider Health Monitoring

**Proactive health checks every 5 minutes:**

```yaml
# File: provider-health-checks.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: blackbox-exporter-config
  namespace: monitoring
data:
  blackbox.yml: |
    modules:
      http_2xx:
        prober: http
        timeout: 10s
        http:
          valid_status_codes: [200, 401]  # 401 = auth required, but API reachable
          method: GET
          headers:
            Authorization: "Bearer ${API_KEY}"

      http_post_2xx:
        prober: http
        timeout: 30s
        http:
          method: POST
          headers:
            Authorization: "Bearer ${API_KEY}"
            Content-Type: "application/json"
          body: '{"model": "claude-sonnet-4-5", "max_tokens": 10, "messages": [{"role": "user", "content": "ping"}]}'
          valid_status_codes: [200]
```

```yaml
# Prometheus scrape config
scrape_configs:
  - job_name: 'model_provider_health'
    metrics_path: /probe
    params:
      module: [http_post_2xx]
    static_configs:
      - targets:
          - https://api.anthropic.com/v1/messages
          - https://api.openai.com/v1/chat/completions
          - https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
        labels:
          provider: "anthropic"  # Override per target
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

---

### Provider Redundancy Strategy

**Ensure no single provider is critical:**

| Workflow Stage | Primary Model | Fallback Model | Fallback 2 |
| --- | --- | --- | --- |
| **Architecture** | Claude Sonnet 4.5 | GPT-4 Turbo | Gemini Pro |
| **Context Retrieval** | Gemini Pro | Claude Sonnet 4.5 | GPT-4 Turbo |
| **Implementation** | GPT-4 Turbo | Claude Sonnet 4.5 | Gemini Pro |
| **Review** | Claude Sonnet 4.5 | GPT-4 Turbo | — |

**Configuration:**

```yaml
env:
  - name: ENABLE_PROVIDER_FAILOVER
    value: "true"
  - name: FAILOVER_STRATEGY
    value: "round_robin"  # Cycle through available providers
  - name: PROVIDER_HEALTH_CHECK_INTERVAL
    value: "300"  # 5 minutes
```

---

### Scheduled Maintenance Tracking

**Subscribe to provider status pages:**

```bash
# Anthropic
# Subscribe: https://status.anthropic.com (email notifications)

# OpenAI
# Subscribe: https://status.openai.com

# Google GCP
# Subscribe: https://status.cloud.google.com (filter: AI Platform)

# When maintenance scheduled:
# 1. Add to ops calendar: ops-calendar@company.com
# 2. Notify stakeholders: #ops-alerts Slack (1 week before)
# 3. Plan mitigation: Enable failover, reduce load, or schedule downtime
```

---

## Metrics & SLOs

**Provider Availability SLO:**
- Target: ≥99.9% uptime per provider per month
- Acceptable: ≥99.0% (degraded service tolerable with failover)
- Critical: <99.0% (indicates chronic reliability issue)

**Failover Effectiveness:**
- Failover success rate: ≥95% (flows continue after provider failure)
- Failover latency: <10s (time to detect failure + reroute)

**Pilot Performance:**
- Provider uptime: 100% (all 3 providers, Nov 4-12)
- Failover tested: 1 simulation (success)

---

## Escalation

### L1: Automatic Failover
- **Trigger:** Provider health check fails
- **Action:** Route to alternate provider
- **SLA:** <10 seconds (automated)

### L2: SRE On-Call
- **Trigger:** Failover ineffective OR 2+ providers down
- **Action:** Manual intervention, stakeholder notification
- **SLA:** <30 minutes

### L3: Incident Commander + Provider Support
- **Trigger:** All providers down OR extended outage (>2 hours)
- **Action:** Coordinate with provider support, consider rollback
- **SLA:** <2 hours (resolution or workaround)

---

## Related Runbooks

- **RB-CORE-001:** Flow Failure Response (`planning/30_design/runbooks/flow_failure_response.md`)
- **RB-CORE-003:** Rate Limit Exhaustion (`planning/30_design/runbooks/rate_limit_exhaustion.md`)
- **RB-LAUNCH-002:** Rollback to Pilot (`planning/60_launch/runbooks/rollback_to_pilot.md`)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE Persona | Initial version for Phase 6/7 provider reliability |

---

**Status:** ✅ Ready for Phase 6 (failover logic validated)
**Next Review:** Post-Phase 6 retrospective (Dec 1, 2025)
**Maintained By:** SRE Persona

---

**Key Principle:** No single provider should be a single point of failure. Automatic failover is critical.
