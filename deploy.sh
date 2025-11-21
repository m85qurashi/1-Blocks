#!/bin/bash
set -e

echo "=========================================="
echo "Multi-LLM Orchestrator - MVP Deployment"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please configure kubectl."
    exit 1
fi

echo "✅ kubectl configured and cluster accessible"
echo ""

# Get API keys
echo "Please provide your API keys:"
echo ""
read -p "Anthropic API Key (sk-ant-...): " ANTHROPIC_KEY
read -p "OpenAI API Key (sk-proj-...): " OPENAI_KEY
read -p "Google API Key (AIzaSy...): " GOOGLE_KEY
echo ""

if [ -z "$ANTHROPIC_KEY" ] || [ -z "$OPENAI_KEY" ] || [ -z "$GOOGLE_KEY" ]; then
    echo "❌ All API keys are required"
    exit 1
fi

# Step 1: Create namespace
echo "Step 1/6: Creating production namespace..."
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace created"
echo ""

# Step 2: Create secrets
echo "Step 2/6: Creating model API keys secret..."
kubectl create secret generic model-api-keys \
  --namespace=production \
  --from-literal=anthropic=$ANTHROPIC_KEY \
  --from-literal=openai=$OPENAI_KEY \
  --from-literal=google=$GOOGLE_KEY \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Secrets created"
echo ""

# Step 3: Deploy PostgreSQL
echo "Step 3/6: Deploying PostgreSQL (TaskDB)..."
kubectl apply -f postgres.yaml
echo "⏳ Waiting for postgres to be ready (may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app=postgres -n production --timeout=300s
echo "✅ PostgreSQL deployed and ready"
echo ""

# Step 4: Deploy FlowEngine
echo "Step 4/6: Deploying FlowEngine..."
kubectl apply -f flowengine-deployment.yaml
echo "⏳ Waiting for flowengine pods to be ready (may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app=flowengine -n production --timeout=300s
echo "✅ FlowEngine deployed and ready"
echo ""

# Step 5: Verify deployment
echo "Step 5/6: Verifying deployment..."
echo ""
echo "Pods in production namespace:"
kubectl get pods -n production
echo ""

# Step 6: Check logs
echo "Step 6/6: Checking FlowEngine logs..."
echo ""
kubectl logs deployment/flowengine -n production --tail=20
echo ""

# Success message
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Install CLI: pip install blocks-orchestrator"
echo "2. Port-forward: kubectl port-forward -n production svc/flowengine 8080:8080"
echo "3. Run first flow: blocks generate --family compliance --block-type attestation"
echo ""
echo "Monitor flows: kubectl logs -f deployment/flowengine -n production"
echo "Check DB: kubectl exec -it statefulset/postgres -n production -- psql -U flowengine_user -d flowengine_db"
echo ""
echo "See MVP_QUICKSTART.md for detailed usage instructions."
echo ""
