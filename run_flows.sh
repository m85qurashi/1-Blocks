#!/bin/bash
# Evidence collection script - run multiple flows through gates

echo "=== Starting Evidence Collection ==="
echo "Running 15 flows across different repo types"
echo ""

# Flow configurations: family, block_type, repo
flows=(
    "compliance:attestation:compliance-repo-1"
    "compliance:validation:compliance-repo-2"
    "compliance:audit:compliance-repo-3"
    "security:scan:security-repo-1"
    "security:encrypt:security-repo-2"
    "security:auth:security-repo-3"
    "testing:unit:test-repo-1"
    "testing:integration:test-repo-2"
    "testing:e2e:test-repo-3"
    "deployment:cicd:deploy-repo-1"
    "deployment:container:deploy-repo-2"
    "deployment:orchestration:deploy-repo-3"
    "monitoring:metrics:monitor-repo-1"
    "monitoring:logging:monitor-repo-2"
    "monitoring:alerting:monitor-repo-3"
)

count=0
for flow_config in "${flows[@]}"; do
    IFS=':' read -r family block_type repo <<< "$flow_config"
    count=$((count + 1))

    echo "[$count/15] Running: $family/$block_type -> $repo"

    result=$(curl -s -X POST http://localhost:8080/api/flows/generate \
        -H "Content-Type: application/json" \
        -d "{\"family\": \"$family\", \"block_type\": \"$block_type\", \"repo\": \"$repo\"}")

    flow_id=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin).get('flow_id', 'error'))")
    status=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))")
    gates=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin).get('quality_gates', 'error'))")

    echo "   → $flow_id: $status ($gates)"
    sleep 0.5
done

echo ""
echo "=== Evidence Collection Complete ==="
echo "Total flows executed: $count"
