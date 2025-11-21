# Getting Started — Multi-LLM Orchestrator MVP

**Current Status:** ✅ Infrastructure deployed and ready
**Next Step:** Deploy real FlowEngine application or test with current setup

---

## What's Already Running

```bash
# Check your deployment:
kubectl get pods -n production

# Expected output:
# NAME                         READY   STATUS    RESTARTS   AGE
# flowengine-xxx               1/1     Running   0          5m
# postgres-0                   1/1     Running   0          15m
```

✅ **Kubernetes Cluster:** Minikube running
✅ **PostgreSQL (TaskDB):** Operational with schema
✅ **FlowEngine:** Deployed (nginx placeholder)
✅ **Secrets:** Created (needs real API keys)

---

## Quick Start Options

### Option A: Test Database & Monitoring (5 minutes)

**Validate PostgreSQL is working:**

```bash
# Connect to database
kubectl exec -it statefulset/postgres -n production -- \
  psql -U flowengine_user -d flowengine_db

# Inside psql, check tables:
\dt

# Expected output:
#              List of relations
#  Schema |     Name      | Type  |      Owner
# --------+---------------+-------+------------------
#  public | flow_metrics  | table | flowengine_user
#  public | flows         | table | flowengine_user

# Insert test data:
INSERT INTO flows (id, repo, status, created_at, duration_seconds, cost_dollars, quality_gates_passed, quality_gates_total)
VALUES ('test-flow-001', 'test-repo', 'success', NOW(), 95, 1.65, 5, 5);

# Query it:
SELECT id, repo, status, duration_seconds, cost_dollars FROM flows;

# Exit:
\q
```

**Run monitoring queries from MVP_QUICKSTART.md:**

```bash
# Daily flow summary
kubectl exec -it statefulset/postgres -n production -- \
  psql -U flowengine_user -d flowengine_db -c "
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_flows,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
  ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate,
  ROUND(SUM(cost_dollars), 2) as total_cost
FROM flows
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;"
```

**Log test result in MVP_METRICS_LOG.md**

---

### Option B: Deploy Real FlowEngine Application (2-4 hours)

**Step 1: Create FlowEngine Application**

Create a simple Python FastAPI application:

```bash
# Create app directory
mkdir -p flowengine-app
cd flowengine-app
```

**File: `app.py`**
```python
from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    # Check database connection
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        conn.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}

@app.post("/api/flows/generate")
def generate_flow(request: dict):
    # TODO: Implement actual flow generation
    # This would call Claude, GPT-4, Gemini
    # Run quality gates
    # Store results in TaskDB
    return {
        "flow_id": "flow-123",
        "status": "success",
        "duration": 95,
        "cost": 1.65,
        "quality_gates": "5/5"
    }
```

**File: `requirements.txt`**
```
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
anthropic==0.7.0
openai==1.3.0
google-generativeai==0.3.0
```

**File: `Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Step 2: Build and Load Image into Minikube**

```bash
# Build Docker image
docker build -t flowengine:v1.0 .

# Load into minikube
minikube image load flowengine:v1.0

# Verify
minikube image ls | grep flowengine
```

**Step 3: Deploy to Kubernetes**

```bash
cd "/Users/mohammadmacbookpro/1- Blocks"

# Update deployment to use real image
kubectl set image deployment/flowengine flowengine=flowengine:v1.0 -n production

# Add back health checks (now that endpoints exist)
kubectl patch deployment flowengine -n production --type=json -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/livenessProbe",
    "value": {
      "httpGet": {
        "path": "/health",
        "port": 8080
      },
      "initialDelaySeconds": 30,
      "periodSeconds": 10
    }
  },
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/readinessProbe",
    "value": {
      "httpGet": {
        "path": "/ready",
        "port": 8080
      },
      "initialDelaySeconds": 10,
      "periodSeconds": 5
    }
  }
]'

# Wait for rollout
kubectl rollout status deployment/flowengine -n production

# Verify
kubectl get pods -n production
kubectl logs -f deployment/flowengine -n production
```

**Step 4: Update API Keys (Real Keys)**

```bash
# Get your real API keys from:
# - Anthropic: https://console.anthropic.com/settings/keys
# - OpenAI: https://platform.openai.com/api-keys
# - Google: https://console.cloud.google.com/apis/credentials

# Delete placeholder secret
kubectl delete secret model-api-keys -n production

# Create with real keys
kubectl create secret generic model-api-keys \
  --namespace=production \
  --from-literal=anthropic=YOUR_ANTHROPIC_KEY \
  --from-literal=openai=YOUR_OPENAI_KEY \
  --from-literal=google=YOUR_GOOGLE_KEY

# Restart to pick up new keys
kubectl rollout restart deployment/flowengine -n production
```

**Step 5: Test First Flow**

```bash
# Port-forward to access FlowEngine
kubectl port-forward -n production svc/flowengine 8080:8080 &

# Test health endpoint
curl http://localhost:8080/health
# Expected: {"status":"healthy"}

# Test ready endpoint
curl http://localhost:8080/ready
# Expected: {"status":"ready","database":"connected"}

# Generate first flow
curl -X POST http://localhost:8080/api/flows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "family": "compliance",
    "block_type": "attestation",
    "repo": "test-repo"
  }'

# Expected: {"flow_id":"flow-123","status":"success",...}
```

---

### Option C: Use Existing FlowEngine Image (If Available)

If you already have a FlowEngine Docker image:

```bash
# If in a registry:
kubectl set image deployment/flowengine flowengine=your-registry.com/flowengine:latest -n production

# Or if local image:
docker save flowengine:latest | (eval $(minikube docker-env) && docker load)
kubectl set image deployment/flowengine flowengine=flowengine:latest -n production
```

---

## Daily Operations

### Check System Health

```bash
# Pods status
kubectl get pods -n production

# Recent logs
kubectl logs -f deployment/flowengine -n production --tail=50

# Database queries (from MVP_QUICKSTART.md)
kubectl exec -it statefulset/postgres -n production -- \
  psql -U flowengine_user -d flowengine_db
```

### Monitor Costs & Flows

```sql
-- Daily summary
SELECT
  DATE(created_at) as date,
  COUNT(*) as flows,
  ROUND(AVG(duration_seconds), 0) as avg_duration,
  ROUND(SUM(cost_dollars), 2) as total_cost,
  ROUND(AVG(cost_dollars), 2) as avg_cost
FROM flows
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Update MVP_METRICS_LOG.md Daily

```bash
# Run SQL query, copy results to:
# /Users/mohammadmacbookpro/1- Blocks/MVP_METRICS_LOG.md
```

---

## Common Commands

### Restart Services

```bash
# Restart FlowEngine
kubectl rollout restart deployment/flowengine -n production

# Restart PostgreSQL
kubectl rollout restart statefulset/postgres -n production
```

### View Logs

```bash
# FlowEngine logs (real-time)
kubectl logs -f deployment/flowengine -n production

# PostgreSQL logs
kubectl logs statefulset/postgres -n production --tail=50
```

### Access Services Locally

```bash
# Port-forward FlowEngine
kubectl port-forward -n production svc/flowengine 8080:8080

# Access: http://localhost:8080/health

# Port-forward PostgreSQL
kubectl port-forward -n production svc/postgres 5432:5432

# Connect: psql -h localhost -U flowengine_user -d flowengine_db
```

### Update Secrets

```bash
# Update API keys
kubectl delete secret model-api-keys -n production
kubectl create secret generic model-api-keys \
  --namespace=production \
  --from-literal=anthropic=NEW_KEY \
  --from-literal=openai=NEW_KEY \
  --from-literal=google=NEW_KEY

kubectl rollout restart deployment/flowengine -n production
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -l app=flowengine -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'

# Check logs
kubectl logs -l app=flowengine -n production
```

### Database Connection Issues

```bash
# Test connection from FlowEngine pod
kubectl exec -it deployment/flowengine -n production -- \
  curl -v telnet://postgres.production.svc.cluster.local:5432

# Check PostgreSQL is accepting connections
kubectl exec -it statefulset/postgres -n production -- \
  psql -U flowengine_user -d flowengine_db -c "SELECT 1;"
```

### API Key Issues

```bash
# Verify secrets exist
kubectl get secret model-api-keys -n production

# Check secret contents (base64 encoded)
kubectl get secret model-api-keys -n production -o yaml

# Test with real keys (from FlowEngine pod)
kubectl exec -it deployment/flowengine -n production -- env | grep API_KEY
```

---

## Next Steps After MVP

Once you've validated the MVP works:

1. **Formal Process:** Migrate to full gate approvals (see `planning/approvals/`)
2. **Monitoring:** Deploy Grafana dashboards (see `planning/60_launch/training/guides/05_metrics_dashboards.md`)
3. **Runbooks:** Implement operational procedures (see `planning/60_launch/runbooks/`)
4. **Scale:** Expand from 1 repo to 10-50 repos (Phase 6/7)
5. **Training:** Deliver formal training (see `planning/60_launch/training/`)

---

## Key Files Reference

| File | Purpose |
| --- | --- |
| `MVP_QUICKSTART.md` | 1-page deployment & operations guide |
| `MVP_METRICS_LOG.md` | Daily flow tracking table |
| `flowengine-deployment.yaml` | Kubernetes FlowEngine manifest |
| `postgres.yaml` | Kubernetes PostgreSQL manifest |
| `deploy.sh` | Automated deployment script |

---

## Support

- **Infrastructure Issues:** Check this guide's Troubleshooting section
- **Application Development:** See Option B above
- **Formal Process:** See `planning/approvals/gate_schedule.md`

---

**Last Updated:** November 14, 2025
**Status:** Infrastructure ready, awaiting FlowEngine application
**Next Milestone:** First real flow execution
