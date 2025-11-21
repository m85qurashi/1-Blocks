# Runbook: Capacity Scaling

**Runbook ID:** RB-LAUNCH-003
**Version:** 1.0
**Last Updated:** November 16, 2025
**Owner:** SRE Persona + Engineering TL
**Severity:** MEDIUM (Proactive Scaling)

---

## Purpose

This runbook provides procedures for scaling Multi-LLM Orchestrator infrastructure capacity to support Phase 6 (10-repo soak) and Phase 7 (org-wide rollout).

**Use When:**
- Expanding from pilot (1 repo) → Phase 6 (10 repos) → Phase 7 (50+ repos)
- Concurrent flow load increases beyond current capacity
- Performance degradation detected (latency, queue depth)
- Proactive capacity planning for anticipated load

**Target Audience:** SRE on-call, Engineering TL, Infrastructure team

---

## Capacity Baseline & Targets

### Pilot Baseline (1 Repo: compliance-service)

**Observed Load (Nov 4-12, 2025):**
- Flows executed: 4 flows total, ~0.5 flows/day
- Peak concurrency: 1 concurrent flow
- FlowEngine replicas: 3
- Database connections: 50-70 (avg)
- CPU utilization: 35% (avg), 52% (peak)
- Memory utilization: 45% (avg), 61% (peak)

**Infrastructure:**
- FlowEngine: 3 replicas (2 vCPU, 4 GB RAM each)
- PostgreSQL: 1 instance (4 vCPU, 16 GB RAM, 100 GB SSD)
- Connection pool: 100 connections

---

### Phase 6 Targets (10 Repos, Nov 16-30)

**Projected Load:**
- Flows executed: 50+ flows total, ~3-5 flows/day
- Peak concurrency: 10 concurrent flows (stress test validated)
- Expected growth: 10× pilot load

**Scaled Infrastructure:**
- FlowEngine: 5 replicas (min 5, max 20 with HPA)
- PostgreSQL: Same instance (sufficient for 10× load)
- Connection pool: 200 connections
- CPU target: <70% (allow headroom for spikes)
- Memory target: <75%

---

### Phase 7 Targets (50+ Repos, Dec 9-20)

**Projected Load:**
- Flows executed: 500+ flows total, ~40-50 flows/day
- Peak concurrency: 50 concurrent flows
- Expected growth: 100× pilot load (50× Phase 6)

**Scaled Infrastructure:**
- FlowEngine: 10 replicas (min 10, max 50 with HPA)
- PostgreSQL: Upgrade to larger instance (8 vCPU, 32 GB RAM, 500 GB SSD)
- Connection pool: 500 connections
- CPU target: <70%
- Memory target: <75%
- Read replicas: 2 (for analytics/dashboards)

---

## Scaling Procedures

### Pre-Phase 6 Scaling (Execute Before Nov 16)

#### Step 1: Scale FlowEngine Replicas (10 minutes)

```bash
# Current replica count (pilot)
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.replicas}'
# Expected: 3

# Scale to Phase 6 target
kubectl scale deployment/flowengine -n production --replicas=5

# Wait for scale-up
kubectl rollout status deployment/flowengine -n production --timeout=300s

# Verify all pods running
kubectl get pods -n production -l app=flowengine
# Expected: 5/5 Running
```

---

#### Step 2: Configure Horizontal Pod Autoscaler (HPA) (5 minutes)

```yaml
# File: flowengine-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: flowengine-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: flowengine
  minReplicas: 5
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 75
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

```bash
# Apply HPA
kubectl apply -f flowengine-hpa.yaml

# Verify HPA configured
kubectl get hpa flowengine-hpa -n production

# Expected output:
# NAME              REFERENCE              TARGETS         MINPODS   MAXPODS   REPLICAS
# flowengine-hpa    Deployment/flowengine   35%/70% (CPU)   5         20        5
```

---

#### Step 3: Increase Database Connection Pool (5 minutes)

```bash
# Check current pool size
kubectl get deployment/flowengine -n production -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="DB_POOL_SIZE")].value}'
# Expected: 100 (pilot)

# Increase to Phase 6 target
kubectl set env deployment/flowengine -n production \
  DB_POOL_SIZE=200

# Restart deployment to apply
kubectl rollout restart deployment/flowengine -n production

# Verify pool size applied
kubectl logs deployment/flowengine -n production --tail=20 | grep "Database connection pool"
# Expected: "Database connection pool initialized: size=200"
```

---

#### Step 4: Validate Database Capacity (10 minutes)

```bash
# Check PostgreSQL resource limits
kubectl get statefulset/postgres -n production -o yaml | grep -A 5 "resources:"

# Expected (pilot baseline):
# resources:
#   requests:
#     cpu: 4
#     memory: 16Gi
#   limits:
#     cpu: 4
#     memory: 16Gi

# Check current database load
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT
      count(*) as active_connections,
      max_conn.setting::int as max_connections,
      round(100.0 * count(*) / max_conn.setting::int, 2) as pct_used
    FROM pg_stat_activity
    CROSS JOIN pg_settings max_conn
    WHERE max_conn.name = 'max_connections'
    GROUP BY max_conn.setting;"

# Expected output (pilot):
# active_connections | max_connections | pct_used
# -------------------+-----------------+----------
#                 65 |             300 |    21.67

# Phase 6 target: <200 connections (<67% of max)
# If projected >200 connections, increase max_connections:
kubectl exec -n production statefulset/postgres -- \
  psql -U postgres -c "ALTER SYSTEM SET max_connections = 400;"

kubectl rollout restart statefulset/postgres -n production
```

---

#### Step 5: Load Test Phase 6 Capacity (20 minutes)

**Simulate 10 concurrent flows:**

```bash
# Execute load test
blocks test load \
  --env production \
  --concurrency 10 \
  --duration 10m \
  --repos compliance-service,financial-reporting,customer-analytics

# Monitor during test
watch -n 5 'kubectl top pods -n production -l app=flowengine'

# Expected results:
# - All 10 flows complete successfully
# - CPU utilization: 50-70% (within target)
# - Memory utilization: 60-75% (within target)
# - P95 latency: <120s (pilot baseline: 118s)
# - Zero pod restarts
# - Zero database connection errors

# If load test fails:
# - CPU >85%: Increase HPA minReplicas or pod CPU limits
# - Memory >90%: Increase pod memory limits
# - Latency >150s: Enable context pruning, optimize model routing
# - Database errors: Increase connection pool or database resources
```

---

### Pre-Phase 7 Scaling (Execute Before Dec 9)

#### Step 1: Scale FlowEngine to Phase 7 Targets (10 minutes)

```bash
# Update HPA for Phase 7
kubectl patch hpa flowengine-hpa -n production --type='json' -p='[
  {"op": "replace", "path": "/spec/minReplicas", "value": 10},
  {"op": "replace", "path": "/spec/maxReplicas", "value": 50}
]'

# Scale to new minimum
kubectl scale deployment/flowengine -n production --replicas=10

# Verify scale-up
kubectl get pods -n production -l app=flowengine
# Expected: 10/10 Running
```

---

#### Step 2: Upgrade PostgreSQL Instance (30 minutes)

**⚠️ Requires coordination with DBA + planned maintenance window**

```bash
# Backup database before upgrade
kubectl exec -n production statefulset/postgres -- \
  pg_dump -U flowengine_user flowengine_db | \
  gzip > /tmp/taskdb_pre_phase7_$(date +%Y%m%d).sql.gz

# Upload backup to S3 (disaster recovery)
aws s3 cp /tmp/taskdb_pre_phase7_$(date +%Y%m%d).sql.gz \
  s3://blocks-backups/postgres/

# Option A: Vertical scaling (resize existing instance)
# - Stop FlowEngine (maintenance mode)
# - Resize PostgreSQL: 4 vCPU → 8 vCPU, 16 GB → 32 GB RAM
# - Restart FlowEngine
# - Downtime: ~10 minutes

# Option B: Migrate to new instance (zero downtime)
# - Provision new PostgreSQL instance (8 vCPU, 32 GB RAM)
# - Set up streaming replication from old → new
# - Cutover when lag <1s (update FlowEngine DB_HOST)
# - Downtime: ~30 seconds (connection re-establishment)

# Verify upgrade
kubectl exec -n production statefulset/postgres -- \
  psql -U postgres -c "
    SELECT version();
    SELECT pg_size_pretty(pg_database_size('flowengine_db')) as db_size;
    SHOW max_connections;
  "

# Expected:
# version: PostgreSQL 15.x
# db_size: ~2 GB (Phase 6 data)
# max_connections: 500 (Phase 7 target)
```

---

#### Step 3: Deploy Read Replicas (Analytics/Dashboards) (20 minutes)

```yaml
# File: postgres-read-replica.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-read-replica
  namespace: production
spec:
  serviceName: postgres-read-replica
  replicas: 2
  selector:
    matchLabels:
      app: postgres-read-replica
  template:
    metadata:
      labels:
        app: postgres-read-replica
    spec:
      containers:
        - name: postgres
          image: postgres:15
          env:
            - name: POSTGRES_USER
              value: flowengine_user
            - name: POSTGRES_DB
              value: flowengine_db
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
            - name: PRIMARY_HOST
              value: postgres-primary.production.svc.cluster.local
          resources:
            requests:
              cpu: 2
              memory: 8Gi
            limits:
              cpu: 4
              memory: 16Gi
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 250Gi
```

```bash
# Deploy read replicas
kubectl apply -f postgres-read-replica.yaml

# Configure Grafana to use read replicas (reduce load on primary)
kubectl set env deployment/grafana -n monitoring \
  DB_HOST=postgres-read-replica.production.svc.cluster.local

# Verify replication lag
kubectl exec -n production statefulset/postgres-read-replica-0 -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT
      pg_last_wal_receive_lsn(),
      pg_last_wal_replay_lsn(),
      pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) as lag_bytes;
  "

# Expected: lag_bytes <1 MB (acceptable)
```

---

#### Step 4: Increase Model API Quotas (Vendor Coordination)

**Request quota increases from model providers:**

**Anthropic (Claude):**

```bash
# Current quota (Phase 6): 2M tokens/day
# Phase 7 target: 10M tokens/day

# Contact: support@anthropic.com
# Subject: "Quota Increase Request - Production Deployment"
# Message:
# "Hello,
#
# We are scaling our Multi-LLM Orchestrator from 10 repositories to 50+
# repositories starting December 9, 2025. We request a quota increase:
#
# - Current: 2M tokens/day
# - Requested: 10M tokens/day
# - Justification: 5× load increase (50 repos vs 10 repos)
# - Expected daily usage: 6-8M tokens/day
# - Account ID: <account_id>
#
# Please confirm by December 5, 2025.
#
# Thank you!"

# Expected response time: 2-3 business days
```

**OpenAI (GPT-4 Turbo):**

```bash
# Current quota: 1.5M tokens/day
# Phase 7 target: 7.5M tokens/day

# Request via: https://help.openai.com (or account rep if enterprise)
```

**Google (Gemini Pro):**

```bash
# Current quota: 1M tokens/day
# Phase 7 target: 5M tokens/day

# Request via: https://cloud.google.com/support (Console → Support → Quota increase)
```

---

#### Step 5: Load Test Phase 7 Capacity (30 minutes)

**Simulate 50 concurrent flows:**

```bash
# Execute load test (staging environment first!)
blocks test load \
  --env staging \
  --concurrency 50 \
  --duration 15m \
  --repos $(cat repos_phase7.txt | tr '\n' ',')

# Monitor:
# - FlowEngine CPU/memory (should trigger HPA scale-up)
# - Database connections (should stay <400)
# - Model API rate limits (should not hit quota)
# - P95 latency (<120s target)

# Expected behavior:
# - HPA scales FlowEngine: 10 → 25 replicas (50% increase per policy)
# - All 50 flows complete successfully
# - P95 latency: <130s (+10s acceptable under heavy load)
# - Zero failures

# If load test passes in staging, repeat in production (dry run):
blocks test load \
  --env production \
  --concurrency 50 \
  --duration 10m \
  --dry-run  # Does not execute actual flows, simulates load only

# If load test fails:
# - Scale issue: Increase HPA maxReplicas or pod resources
# - Database issue: Increase connection pool or PostgreSQL resources
# - Model API issue: Request higher quotas or enable circuit breaker earlier
```

---

## Monitoring During Scaling

### Key Metrics to Monitor

#### FlowEngine Metrics

```bash
# CPU utilization (target: <70%)
kubectl top pods -n production -l app=flowengine --no-headers | \
  awk '{sum+=$2} END {print "Avg CPU:", sum/NR "%"}'

# Memory utilization (target: <75%)
kubectl top pods -n production -l app=flowengine --no-headers | \
  awk '{sum+=$3} END {print "Avg Memory:", sum/NR "%"}'

# Replica count (should match HPA target)
kubectl get hpa flowengine-hpa -n production -o jsonpath='{.status.currentReplicas}'

# Pod restarts (target: 0 recent restarts)
kubectl get pods -n production -l app=flowengine --no-headers | \
  awk '{sum+=$4} END {print "Total Restarts:", sum}'
```

---

#### Database Metrics

```bash
# Active connections (Phase 6: <200, Phase 7: <400)
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT count(*) as active_connections
    FROM pg_stat_activity
    WHERE datname='flowengine_db';"

# Database size (track growth)
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT pg_size_pretty(pg_database_size('flowengine_db')) as db_size;"

# Long-running queries (should be <10s avg)
kubectl exec -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db -c "
    SELECT
      pid,
      now() - query_start as duration,
      query
    FROM pg_stat_activity
    WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
    ORDER BY duration DESC
    LIMIT 5;"
```

---

#### Model API Metrics

```bash
# Quota usage (target: <85% to avoid circuit breaker)
blocks quota show --all-providers

# Expected Phase 6:
# Anthropic: 1.5M / 2M (75%)
# OpenAI: 1.1M / 1.5M (73%)
# Google: 700K / 1M (70%)

# Expected Phase 7:
# Anthropic: 7M / 10M (70%)
# OpenAI: 5.5M / 7.5M (73%)
# Google: 3.5M / 5M (70%)

# Rate limit errors (target: 0)
blocks metrics query \
  --metric model_api_errors_total \
  --filter error_type=rate_limit \
  --last 1h
```

---

### Grafana Dashboards

**Dashboard URLs:**
- **Capacity Overview:** https://grafana.company.com/d/flowengine-capacity
- **Database Metrics:** https://grafana.company.com/d/postgres-metrics
- **HPA Autoscaling:** https://grafana.company.com/d/kubernetes-hpa

**Key Panels:**
- FlowEngine replica count over time (should track with load)
- CPU/memory utilization by pod
- Database connection pool usage
- Queue depth (flows waiting to execute)
- P95 latency by phase

---

## Scaling Alerts

### Alert: FlowEngine CPU High

```yaml
alert: FlowEngineCPUHigh
expr: |
  avg(rate(container_cpu_usage_seconds_total{pod=~"flowengine-.*"}[5m])) > 0.85
for: 10m
labels:
  severity: warning
  runbook: RB-LAUNCH-003
annotations:
  summary: "FlowEngine CPU usage >85%"
  description: "Avg CPU: {{ $value | humanizePercentage }}. Consider scaling or optimizing."
```

**Response:**
- Check if HPA is scaling (may need time to catch up)
- If HPA at maxReplicas, increase maxReplicas or pod CPU limits
- Review flow complexity (large code generation may need optimization)

---

### Alert: Database Connection Pool Exhaustion

```yaml
alert: DatabaseConnectionPoolExhausted
expr: |
  sum(pg_stat_activity{datname="flowengine_db"}) /
  max(pg_settings{name="max_connections"}) > 0.9
for: 5m
labels:
  severity: critical
  runbook: RB-LAUNCH-003
annotations:
  summary: "Database connection pool >90% used"
  description: "{{ $value | humanizePercentage }} connections in use. Risk of exhaustion."
```

**Response:**
- Immediate: Increase connection pool size (`DB_POOL_SIZE`)
- Short-term: Scale up PostgreSQL instance (more resources)
- Long-term: Optimize query patterns, add connection pooling (PgBouncer)

---

### Alert: HPA Unable to Scale

```yaml
alert: HPAUnableToScale
expr: |
  kube_horizontalpodautoscaler_status_desired_replicas{horizontalpodautoscaler="flowengine-hpa"} >
  kube_horizontalpodautoscaler_status_current_replicas{horizontalpodautoscaler="flowengine-hpa"}
for: 10m
labels:
  severity: warning
  runbook: RB-LAUNCH-003
annotations:
  summary: "HPA unable to scale FlowEngine"
  description: "Desired: {{ $labels.desired }}, Current: {{ $labels.current }}. Check cluster capacity."
```

**Response:**
- Check cluster node capacity (`kubectl describe nodes`)
- If insufficient resources, add cluster nodes or increase node size
- Review resource requests (may be too high, preventing scheduling)

---

## Capacity Planning

### Quarterly Capacity Review

**Schedule:** Last Friday of each quarter (March, June, September, December)

**Review Checklist:**

- [ ] **Load Trends:** Analyze flow volume growth over past quarter
- [ ] **Resource Utilization:** Review CPU/memory trends (FlowEngine, database)
- [ ] **Cost Efficiency:** Cost per flow trending down (learning curve)?
- [ ] **Performance:** P95 latency stable or improving?
- [ ] **Incidents:** Any capacity-related incidents (scale-up too slow, resource exhaustion)?
- [ ] **Next Quarter Projection:** Estimate load growth, plan infrastructure changes

**Report Template:** `planning/60_launch/capacity_review_<YYYY-QN>.md`

---

### Capacity Headroom

**Maintain 30% headroom at all times:**

- **FlowEngine:** HPA target CPU 70% (30% headroom for spikes)
- **Database:** Connection pool 70% used (30% headroom)
- **Model API:** Quota usage <85% (15% headroom before circuit breaker)

**If headroom <20% sustained for >1 week:**
- Scale proactively (don't wait for incidents)
- Update capacity plan and budget

---

## Rollback Procedure

**If scaling causes instability:**

### Rollback FlowEngine Scaling

```bash
# Revert to previous replica count
kubectl scale deployment/flowengine -n production --replicas=<previous_count>

# Revert HPA settings
kubectl patch hpa flowengine-hpa -n production --type='json' -p='[
  {"op": "replace", "path": "/spec/minReplicas", "value": <previous_min>},
  {"op": "replace", "path": "/spec/maxReplicas", "value": <previous_max>}
]'

# Revert connection pool size
kubectl set env deployment/flowengine -n production \
  DB_POOL_SIZE=<previous_pool_size>

kubectl rollout restart deployment/flowengine -n production
```

### Rollback Database Upgrade

```bash
# Restore from backup (taken in Step 2)
kubectl exec -n production statefulset/postgres -- \
  psql -U postgres -c "DROP DATABASE flowengine_db;"

kubectl exec -n production statefulset/postgres -- \
  psql -U postgres -c "CREATE DATABASE flowengine_db OWNER flowengine_user;"

gunzip -c /tmp/taskdb_pre_phase7_<timestamp>.sql.gz | \
kubectl exec -i -n production statefulset/postgres -- \
  psql -U flowengine_user -d flowengine_db

# Downtime: ~15 minutes (database restore)
```

---

## Related Runbooks

- **RB-LAUNCH-001:** Repository Onboarding (`planning/60_launch/runbooks/repo_onboarding.md`)
- **RB-LAUNCH-002:** Rollback to Pilot (`planning/60_launch/runbooks/rollback_to_pilot.md`)
- **RB-LAUNCH-005:** Mass Failure Response (`planning/60_launch/runbooks/mass_failure.md`)

---

## Change Log

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | Nov 16, 2025 | SRE + Engineering TL | Initial version for Phase 6/7 scaling |

---

**Status:** ✅ Ready for Phase 6 (load test validated 10× capacity)
**Next Review:** Pre-Phase 7 (Dec 8, 2025)
**Maintained By:** SRE Persona + Engineering TL

---

**Scaling Philosophy:** Scale proactively, not reactively. Maintain 30% headroom.
