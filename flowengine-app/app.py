from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import os
import uuid
import json
import time
from datetime import datetime
from typing import Optional

# Import quality gates (with real LLM integration)
from gates_llm import QualityGateRunner

app = FastAPI(title="FlowEngine", version="1.3.0")


class FlowRequest(BaseModel):
    family: str
    block_type: str
    repo: str
    context: Optional[dict] = None


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres.production.svc.cluster.local"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "flowengine_db"),
        user=os.getenv("DB_USER", "flowengine_user"),
        password=os.getenv("DB_PASSWORD", "changeme")
    )


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "flowengine", "version": "1.0.0"}


@app.get("/ready")
def ready():
    """Readiness check with database connectivity test"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {
            "status": "ready",
            "database": "connected",
            "api_keys": {
                "anthropic": "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing",
                "openai": "configured" if os.getenv("OPENAI_API_KEY") else "missing",
                "google": "configured" if os.getenv("GOOGLE_API_KEY") else "missing"
            }
        }
    except Exception as e:
        return {"status": "not ready", "error": str(e)}, 503


@app.post("/api/flows/generate")
def generate_flow(request: FlowRequest):
    """
    Generate a flow with quality gates

    Flow:
    1. Generate code (simulated for MVP)
    2. Run 5 quality gates (Contract, Coverage, Mutation, Security, LLM Review with Claude)
    3. Store results
    """
    flow_id = f"flow-{uuid.uuid4().hex[:12]}"
    flow_start = time.time()

    try:
        # Step 1: Generate code (simulated - would call LLMs in production)
        generated_code = f"""
def {request.block_type}(data: dict) -> dict:
    '''
    {request.family} {request.block_type} for {request.repo}
    '''
    if not data:
        raise ValueError("Data cannot be empty")

    try:
        result = {{"processed": True, "data": data}}
        assert result is not None
        if not result:
            raise ValueError("Result validation failed")
        return result
    except Exception as e:
        raise Exception(f"Processing failed: {{e}}")
"""

        # Step 2: Run quality gates
        gate_runner = QualityGateRunner()
        gate_results = gate_runner.run_all(generated_code, request.context or {})

        # Calculate totals
        duration = int(time.time() - flow_start)
        cost = 0.05  # Simulated cost for MVP
        quality_gates_passed = gate_results["passed_gates"]
        quality_gates_total = gate_results["total_gates"]
        status = "success" if gate_results["all_passed"] else "failed"

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO flows (
                id, repo, status, created_at, duration_seconds,
                cost_dollars, quality_gates_passed, quality_gates_total,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            flow_id,
            request.repo,
            status,
            datetime.utcnow(),
            duration,
            cost,
            quality_gates_passed,
            quality_gates_total,
            psycopg2.extras.Json({
                "family": request.family,
                "block_type": request.block_type,
                "context": request.context,
                "gate_results": gate_results["gates"],
                "code_length": len(generated_code)
            })
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "flow_id": flow_id,
            "status": status,
            "repo": request.repo,
            "duration_seconds": duration,
            "cost_dollars": cost,
            "quality_gates": f"{quality_gates_passed}/{quality_gates_total}",
            "gates": {
                "passed": quality_gates_passed,
                "failed": gate_results["failed_gates"],
                "success_rate": round(gate_results["success_rate"] * 100, 1),
                "details": [
                    {
                        "name": g["name"],
                        "passed": g["passed"],
                        "score": round(g["score"], 2)
                    }
                    for g in gate_results["gates"]
                ]
            },
            "message": f"Flow {status} - {quality_gates_passed}/{quality_gates_total} gates passed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flow generation failed: {str(e)}")


@app.get("/api/flows")
def list_flows(limit: int = 10):
    """List recent flows"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, repo, status, created_at, duration_seconds,
                   cost_dollars, quality_gates_passed, quality_gates_total
            FROM flows
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        flows = []
        for row in rows:
            flows.append({
                "id": row[0],
                "repo": row[1],
                "status": row[2],
                "created_at": row[3].isoformat(),
                "duration_seconds": row[4],
                "cost_dollars": float(row[5]) if row[5] else 0,
                "quality_gates": f"{row[6]}/{row[7]}"
            })

        return {"flows": flows, "count": len(flows)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list flows: {str(e)}")


@app.get("/api/metrics/summary")
def metrics_summary():
    """Get summary metrics for all flows"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_flows,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                ROUND(AVG(duration_seconds), 0) as avg_duration,
                ROUND(SUM(cost_dollars), 2) as total_cost,
                ROUND(AVG(cost_dollars), 2) as avg_cost
            FROM flows
        """)

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return {
            "total_flows": row[0],
            "successful_flows": row[1],
            "success_rate": round((row[1] / row[0] * 100), 2) if row[0] > 0 else 0,
            "avg_duration_seconds": int(row[2]) if row[2] else 0,
            "total_cost_dollars": float(row[3]) if row[3] else 0,
            "avg_cost_dollars": float(row[4]) if row[4] else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
