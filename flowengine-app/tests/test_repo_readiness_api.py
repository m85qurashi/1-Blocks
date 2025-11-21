import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import database  # noqa: E402
import models  # noqa: E402
import repo_readiness_api  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "readiness.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("READINESS_API_KEY", "test-key")

    importlib.reload(database)
    importlib.reload(models)
    importlib.reload(repo_readiness_api)

    with TestClient(repo_readiness_api.app) as test_client:
        yield test_client


def auth_headers():
    return {"X-API-Key": "test-key"}


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_idea_creation_requires_api_key(client):
    payload = {
        "name": "Telemetry Flow",
        "sponsoring_team": "SRE",
        "workflow_family": "monitoring",
        "desired_outcomes": {"latency": "p99 < 150ms"},
        "description": "New telemetry ingestion workflow",
    }

    resp = client.post("/api/ideas", json=payload)
    assert resp.status_code == 401

    resp = client.post("/api/ideas", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"

    ideas = client.get("/api/ideas").json()
    assert ideas["count"] == 1
    assert ideas["ideas"][0]["workflow_family"] == "monitoring"


def test_readiness_flow_and_wave_assignment(client):
    # Seed readiness record (not ready yet)
    readiness_payload = {
        "repo_name": "monitor-repo-1",
        "owner": "devrel",
        "training_completed": True,
        "cli_installed": False,
        "test_coverage_80": False,
        "runbook_acknowledged": False,
        "notes": "CLI install scheduled",
    }

    resp = client.post("/api/readiness", json=readiness_payload, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["readiness_status"] == "in_progress"

    # Attempt to assign to wave_1 before ready -> fail
    resp = client.post(
        "/api/waves/assign",
        json={"repo_name": "monitor-repo-1", "wave": "wave_1", "priority": 1},
        headers=auth_headers(),
    )
    assert resp.status_code == 400

    # Mark repo as fully ready
    readiness_payload.update({"cli_installed": True, "test_coverage_80": True, "runbook_acknowledged": True})
    resp = client.post("/api/readiness", json=readiness_payload, headers=auth_headers())
    assert resp.json()["readiness_status"] == "ready"

    # Assign to wave_1
    resp = client.post(
        "/api/waves/assign",
        json={"repo_name": "monitor-repo-1", "wave": "wave_1", "priority": 2, "scheduled_date": "2025-11-20"},
        headers=auth_headers(),
    )
    body = resp.json()
    assert resp.status_code == 200
    assert body["wave"] == "wave_1"
    assert body["scheduled_date"] == "2025-11-20"

    # Validate listing and summary
    wave_list = client.get("/api/waves").json()
    assert wave_list["count"] == 1
    assert wave_list["assignments"][0]["repo_name"] == "monitor-repo-1"

    summary = client.get("/api/waves/summary").json()
    assert summary["summary"][0]["repo_count"] == 1


def test_future_wave_assignment_allows_incomplete_repo(client):
    readiness_payload = {
        "repo_name": "beta-repo",
        "owner": "qa",
        "training_completed": False,
        "cli_installed": False,
        "test_coverage_80": False,
        "runbook_acknowledged": False,
    }
    client.post("/api/readiness", json=readiness_payload, headers=auth_headers())

    resp = client.post(
        "/api/waves/assign",
        json={"repo_name": "beta-repo", "wave": "future", "priority": 0},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["wave"] == "future"
