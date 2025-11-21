# Scrappy MVP Quick-Start — Multi-LLM Orchestrator

## 1. Deploy Core Services (Day 0)
```bash
kubectl apply -f flowengine-deployment.yaml   # FlowEngine API
kubectl create secret generic model-api-keys \
  --from-literal=anthropic=$ANTHROPIC_KEY \
  --from-literal=openai=$OPENAI_KEY \
  --from-literal=google=$GOOGLE_KEY
kubectl apply -f postgres.yaml                 # TaskDB
```
Confirm pods:
```bash
kubectl get pods -l app=flowengine
kubectl logs deploy/flowengine | tail -n 20
```

## 2. Run First Flow (Day 1)
```bash
pip install blocks-orchestrator
blocks auth login
blocks generate --family compliance --block-type attestation --repo <repo>
```
Quality gates auto-run (schema, unit, mutation, Semgrep, LLM review). Check status via FlowEngine logs or CLI output.

## 3. Minimal Monitoring
```bash
# Flow success / failure counts
echo "select date(created_at) d, status, count(*) from task_runs group by 1,2;" | psql $TASKDB_URL
# Daily cost
echo "select sum(cost_usd) from task_runs where created_at::date = current_date;" | psql $TASKDB_URL
```
Set Slack reminders to run these twice daily.

## 4. Onboard 1–2 Teams (Day 2)
- Pair install CLI (`pip install ...`), run `blocks generate`, watch gates.
- Capture issues manually in shared doc / Slack thread.

## 5. Share Value (Day 5)
- Capture cycle time delta, % AI code, cost/feature from SQL outputs.
- Summarize in 5 bullets for leadership.

> This skips gates, dashboards, and runbooks. You own the risk; reintroduce formal process before scaling past 2–3 repos.
