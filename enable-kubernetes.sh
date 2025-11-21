#!/bin/bash
set -e

echo "=========================================="
echo "Docker Desktop Kubernetes Enabler"
echo "=========================================="
echo ""

# Check if Docker is running
echo "Checking Docker Desktop status..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker Desktop is not running"
    echo "Please start Docker Desktop first, then run this script again"
    exit 1
fi
echo "✅ Docker Desktop is running"
echo ""

# Docker Desktop settings file location
DOCKER_SETTINGS="$HOME/Library/Group Containers/group.com.docker/settings.json"

# Check if settings file exists
if [ ! -f "$DOCKER_SETTINGS" ]; then
    echo "❌ Docker Desktop settings file not found at:"
    echo "   $DOCKER_SETTINGS"
    echo ""
    echo "Please enable Kubernetes manually:"
    echo "1. Open Docker Desktop"
    echo "2. Settings → Kubernetes"
    echo "3. Check 'Enable Kubernetes'"
    echo "4. Click 'Apply & Restart'"
    exit 1
fi

echo "Found Docker Desktop settings file"
echo ""

# Backup current settings
BACKUP_FILE="$DOCKER_SETTINGS.backup-$(date +%Y%m%d-%H%M%S)"
echo "Creating backup: $BACKUP_FILE"
cp "$DOCKER_SETTINGS" "$BACKUP_FILE"
echo "✅ Backup created"
echo ""

# Check if Kubernetes is already enabled
if grep -q '"kubernetesEnabled":true' "$DOCKER_SETTINGS" 2>/dev/null; then
    echo "✅ Kubernetes is already enabled!"
    echo ""
    echo "Verifying cluster status..."
    sleep 2
    if kubectl cluster-info > /dev/null 2>&1; then
        echo "✅ Kubernetes cluster is running!"
        kubectl cluster-info
        echo ""
        echo "Ready to deploy. Run: ./deploy.sh"
        exit 0
    else
        echo "⚠️ Kubernetes enabled but cluster not ready yet"
        echo "Wait 1-2 minutes and run: kubectl cluster-info"
        exit 0
    fi
fi

# Enable Kubernetes by modifying settings
echo "Enabling Kubernetes in Docker Desktop settings..."

# Use Python to safely modify JSON (more reliable than sed/awk)
python3 - <<'PYTHON_SCRIPT'
import json
import sys

settings_file = "$DOCKER_SETTINGS"

try:
    with open(settings_file.replace('$DOCKER_SETTINGS', '$HOME/Library/Group Containers/group.com.docker/settings.json').replace('$HOME', '$HOME'), 'r') as f:
        settings = json.load(f)

    # Enable Kubernetes
    settings['kubernetesEnabled'] = True

    # Write back
    with open(settings_file.replace('$DOCKER_SETTINGS', '$HOME/Library/Group Containers/group.com.docker/settings.json').replace('$HOME', '$HOME'), 'w') as f:
        json.dump(settings, f, indent=2)

    print("✅ Settings updated")
    sys.exit(0)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYTHON_SCRIPT

# Better approach: use jq if available, otherwise manual edit
if command -v jq > /dev/null 2>&1; then
    echo "Using jq to modify settings..."
    jq '.kubernetesEnabled = true' "$DOCKER_SETTINGS" > "${DOCKER_SETTINGS}.tmp"
    mv "${DOCKER_SETTINGS}.tmp" "$DOCKER_SETTINGS"
    echo "✅ Kubernetes enabled in settings"
else
    # Fallback: use sed (less safe but works)
    echo "Using sed to modify settings..."
    sed -i '' 's/"kubernetesEnabled":\s*false/"kubernetesEnabled":true/' "$DOCKER_SETTINGS"
    echo "✅ Kubernetes enabled in settings"
fi

echo ""
echo "⏳ Restarting Docker Desktop to apply changes..."
echo "This may take 2-3 minutes..."
echo ""

# Restart Docker Desktop
osascript -e 'quit app "Docker"'
sleep 3
open -a Docker

echo "Waiting for Docker Desktop to restart..."
sleep 10

# Wait for Docker to be ready
for i in {1..30}; do
    if docker info > /dev/null 2>&1; then
        echo "✅ Docker Desktop restarted"
        break
    fi
    echo "Waiting for Docker... ($i/30)"
    sleep 2
done

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker Desktop did not restart properly"
    echo "Please manually restart Docker Desktop"
    exit 1
fi

echo ""
echo "⏳ Waiting for Kubernetes to start (this takes 1-2 minutes)..."
echo ""

# Wait for Kubernetes to be ready
for i in {1..60}; do
    if kubectl cluster-info > /dev/null 2>&1; then
        echo ""
        echo "=========================================="
        echo "✅ Kubernetes is Ready!"
        echo "=========================================="
        echo ""
        kubectl cluster-info
        echo ""
        echo "Next step: Run deployment"
        echo "./deploy.sh"
        echo ""
        exit 0
    fi
    echo "Waiting for Kubernetes... ($i/60)"
    sleep 2
done

echo ""
echo "⚠️ Kubernetes is taking longer than expected"
echo ""
echo "Please check Docker Desktop:"
echo "1. Look for green indicator in Docker Desktop → Kubernetes"
echo "2. Or run manually: kubectl cluster-info"
echo ""
echo "Once ready, run: ./deploy.sh"
echo ""
