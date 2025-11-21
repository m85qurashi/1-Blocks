"""
Repository Readiness & Selection API
Manages idea intake, readiness tracking, and wave assignments
"""
import json
import os
import uuid
from datetime import datetime, date
from typing import Any, Dict, Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import SessionLocal, init_db
from domain_types import ReadinessStatus, Wave
from models import Idea, RepoReadiness, WaveAssignment
from schemas import IdeaCreate, RepoReadinessPayload, WaveAssignmentPayload

app = FastAPI(title="Repo Readiness API", version="2.0.0")

# Configure CORS to allow requests from team_site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PLANNING_ROOT = os.getenv("PLANNING_ROOT", "/tmp/planning")
API_KEY = os.getenv("READINESS_API_KEY")
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: Optional[str] = Security(api_key_scheme)) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def ensure_planning_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def readiness_status_from_payload(payload: RepoReadinessPayload) -> ReadinessStatus:
    checks_passed = sum(
        [
            payload.training_completed,
            payload.cli_installed,
            payload.test_coverage_80,
            payload.runbook_acknowledged,
        ]
    )
    if checks_passed == 4:
        return ReadinessStatus.READY
    if checks_passed > 0:
        return ReadinessStatus.IN_PROGRESS
    return ReadinessStatus.NOT_STARTED


def parse_scheduled_date(raw_date: Optional[str]) -> Optional[date]:
    if not raw_date:
        return None
    try:
        return datetime.fromisoformat(raw_date).date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="scheduled_date must be ISO format (YYYY-MM-DD)") from exc


def serialize_idea(idea: Idea) -> Dict[str, Any]:
    payload = idea.to_dict()
    payload["created_at"] = payload["created_at"]
    payload["desired_outcomes"] = payload.get("desired_outcomes") or {}
    wf = payload.get("workflow_family")
    if hasattr(wf, "value"):
        payload["workflow_family"] = wf.value
    return payload


def serialize_readiness(record: RepoReadiness) -> Dict[str, Any]:
    payload = record.to_dict()
    payload["created_at"] = payload["created_at"]
    payload["updated_at"] = payload["updated_at"]
    status = payload.get("readiness_status")
    if hasattr(status, "value"):
        payload["readiness_status"] = status.value
    return payload


def serialize_wave_assignment(record: WaveAssignment) -> Dict[str, Any]:
    payload = record.to_dict()
    wave = payload.get("wave")
    if hasattr(wave, "value"):
        payload["wave"] = wave.value
    payload["scheduled_date"] = payload["scheduled_date"].isoformat() if payload["scheduled_date"] else None
    payload["assigned_at"] = payload["assigned_at"]
    return payload


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy", "service": "repo-readiness-api"}


@app.post("/api/ideas", dependencies=[Depends(require_api_key)])
def create_idea(idea: IdeaCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    idea_id = f"idea-{uuid.uuid4().hex[:12]}"
    new_idea = Idea(
        id=idea_id,
        name=idea.name,
        sponsoring_team=idea.sponsoring_team,
        workflow_family=idea.workflow_family,
        desired_outcomes=idea.desired_outcomes,
        description=idea.description,
    )

    db.add(new_idea)
    db.commit()

    planning_content = f"""# Idea: {idea.name}

**ID**: {idea_id}
**Sponsoring Team**: {idea.sponsoring_team}
**Workflow Family**: {idea.workflow_family}
**Created**: {datetime.utcnow().isoformat()}

## Desired Outcomes
{json.dumps(idea.desired_outcomes, indent=2)}

## Description
{idea.description or "No description provided"}

## Next Steps
1. Identify candidate repositories
2. Complete readiness checklist
3. Assign to wave
4. Execute pilot
"""

    planning_dir = os.path.join(PLANNING_ROOT, "00_idea")
    ensure_planning_directory(planning_dir)
    planning_path = os.path.join(planning_dir, f"{idea_id}.md")
    with open(planning_path, "w", encoding="utf-8") as handle:
        handle.write(planning_content)

    return {
        "idea_id": idea_id,
        "status": "created",
        "message": f"Idea '{idea.name}' created successfully",
        "planning_file": planning_path.replace(PLANNING_ROOT, "planning"),
    }


@app.get("/api/ideas")
def list_ideas(status: Optional[str] = "active", db: Session = Depends(get_db)) -> Dict[str, Any]:
    query = db.query(Idea)
    if status:
        query = query.filter(Idea.status == status)
    ideas = query.order_by(Idea.created_at.desc()).all()
    return {"ideas": [serialize_idea(idea) for idea in ideas], "count": len(ideas)}


@app.post("/api/readiness", dependencies=[Depends(require_api_key)])
def create_repo_readiness(readiness: RepoReadinessPayload, db: Session = Depends(get_db)) -> Dict[str, Any]:
    status = readiness_status_from_payload(readiness)
    existing = db.query(RepoReadiness).filter(RepoReadiness.repo_name == readiness.repo_name).first()

    if existing:
        existing.owner = readiness.owner
        existing.training_completed = readiness.training_completed
        existing.cli_installed = readiness.cli_installed
        existing.test_coverage_80 = readiness.test_coverage_80
        existing.runbook_acknowledged = readiness.runbook_acknowledged
        existing.notes = readiness.notes
        existing.readiness_status = status
    else:
        db.add(
            RepoReadiness(
                repo_name=readiness.repo_name,
                owner=readiness.owner,
                training_completed=readiness.training_completed,
                cli_installed=readiness.cli_installed,
                test_coverage_80=readiness.test_coverage_80,
                runbook_acknowledged=readiness.runbook_acknowledged,
                notes=readiness.notes,
                readiness_status=status,
            )
        )

    db.commit()

    checks_passed = sum(
        [
            readiness.training_completed,
            readiness.cli_installed,
            readiness.test_coverage_80,
            readiness.runbook_acknowledged,
        ]
    )

    return {
        "repo_name": readiness.repo_name,
        "readiness_status": status,
        "checks_passed": f"{checks_passed}/4",
        "message": "Readiness updated successfully",
    }


@app.get("/api/readiness")
def list_repo_readiness(status: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    query = db.query(RepoReadiness)
    if status:
        query = query.filter(RepoReadiness.readiness_status == status)
    repos = query.order_by(RepoReadiness.readiness_status.desc(), RepoReadiness.updated_at.desc()).all()
    return {"repositories": [serialize_readiness(repo) for repo in repos], "count": len(repos)}


@app.get("/api/readiness/{repo_name}")
def get_repo_readiness(repo_name: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = db.query(RepoReadiness).filter(RepoReadiness.repo_name == repo_name).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return serialize_readiness(repo)


@app.post("/api/waves/assign", dependencies=[Depends(require_api_key)])
def assign_to_wave(assignment: WaveAssignmentPayload, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = db.query(RepoReadiness).filter(RepoReadiness.repo_name == assignment.repo_name).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found in readiness tracking")

    if assignment.wave != Wave.FUTURE and repo.readiness_status != ReadinessStatus.READY:
        raise HTTPException(status_code=400, detail=f"Repository not ready for assignment (status: {repo.readiness_status})")

    scheduled_date = parse_scheduled_date(assignment.scheduled_date)

    existing = (
        db.query(WaveAssignment)
        .filter(WaveAssignment.repo_name == assignment.repo_name, WaveAssignment.wave == assignment.wave)
        .first()
    )

    if existing:
        existing.scheduled_date = scheduled_date
        existing.priority = assignment.priority
    else:
        db.add(
            WaveAssignment(
                repo_name=assignment.repo_name,
                wave=assignment.wave,
                scheduled_date=scheduled_date,
                priority=assignment.priority,
            )
        )

    db.commit()

    return {
        "repo_name": assignment.repo_name,
        "wave": assignment.wave,
        "scheduled_date": scheduled_date.isoformat() if scheduled_date else None,
        "message": "Wave assignment successful",
    }


@app.get("/api/waves")
def list_wave_assignments(wave: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    query = db.query(WaveAssignment)
    if wave:
        query = query.filter(WaveAssignment.wave == wave)
    assignments = query.order_by(WaveAssignment.wave, WaveAssignment.priority.desc(), WaveAssignment.scheduled_date.asc()).all()
    return {"assignments": [serialize_wave_assignment(a) for a in assignments], "count": len(assignments)}


@app.get("/api/waves/summary")
def wave_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    summary: Dict[str, Dict[str, Any]] = {}
    assignments = db.query(WaveAssignment).all()
    for record in assignments:
        key = record.wave.value
        bucket = summary.setdefault(key, {"wave": record.wave.value, "repo_count": 0, "earliest_date": None, "latest_date": None})
        bucket["repo_count"] += 1
        if record.scheduled_date:
            iso_date = record.scheduled_date.isoformat()
            if not bucket["earliest_date"] or iso_date < bucket["earliest_date"]:
                bucket["earliest_date"] = iso_date
            if not bucket["latest_date"] or iso_date > bucket["latest_date"]:
                bucket["latest_date"] = iso_date

    ordered_waves = [Wave.SOAK.value, Wave.WAVE_1.value, Wave.WAVE_2.value, Wave.FUTURE.value]
    return {"summary": [summary[wave] for wave in ordered_waves if wave in summary]}


@app.post("/api/waves/export", dependencies=[Depends(require_api_key)])
def export_wave_assignments(db: Session = Depends(get_db)) -> Dict[str, Any]:
    assignments = db.query(WaveAssignment).order_by(WaveAssignment.wave, WaveAssignment.priority.desc()).all()

    md_lines: List[str] = [
        "# Repository Wave Assignments",
        "",
        f"**Generated**: {datetime.utcnow().isoformat()}",
        f"**Total Repositories**: {len(assignments)}",
        "",
        "---",
        "",
        "## Phase 6: Soak Period",
    ]

    for wave in [Wave.SOAK.value, Wave.WAVE_1.value, Wave.WAVE_2.value, Wave.FUTURE.value]:
        wave_records = [a for a in assignments if a.wave.value == wave]
        if wave == Wave.WAVE_1.value:
            md_lines.append("")
            md_lines.append("## Phase 7: Wave 1")
        elif wave == Wave.WAVE_2.value:
            md_lines.append("")
            md_lines.append("## Phase 7: Wave 2")
        elif wave == Wave.FUTURE.value:
            md_lines.append("")
            md_lines.append("## Future Waves")

        md_lines.extend(
            [
                "",
                "| Repository | Wave | Readiness | Scheduled Date | Priority |",
                "|------------|------|-----------|----------------|----------|",
            ]
        )

        for record in wave_records:
            repo = db.query(RepoReadiness).filter(RepoReadiness.repo_name == record.repo_name).first()
            readiness = repo.readiness_status if repo else ReadinessStatus.NOT_STARTED
            scheduled = record.scheduled_date.isoformat() if record.scheduled_date else "TBD"
            md_lines.append(
                f"| {record.repo_name} | {record.wave.value} | {readiness} | {scheduled} | {record.priority} |"
            )

        md_lines.append(f"\n**Total**: {len(wave_records)} repositories\n")

    launch_dir = os.path.join(PLANNING_ROOT, "60_launch")
    ensure_planning_directory(launch_dir)
    output_path = os.path.join(launch_dir, f"repo_assignments_{datetime.utcnow().strftime('%Y%m%d')}.md")
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(md_lines))

    return {
        "status": "exported",
        "file_path": output_path.replace(PLANNING_ROOT, "planning"),
        "repository_count": len(assignments),
        "message": "Wave assignments exported successfully",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
