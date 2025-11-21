from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from domain_types import ReadinessStatus, Wave, WorkflowFamily


class IdeaCreate(BaseModel):
    name: str
    sponsoring_team: str
    workflow_family: WorkflowFamily
    desired_outcomes: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class RepoReadinessPayload(BaseModel):
    repo_name: str
    owner: str
    training_completed: bool = False
    cli_installed: bool = False
    test_coverage_80: bool = False
    runbook_acknowledged: bool = False
    notes: Optional[str] = None


class WaveAssignmentPayload(BaseModel):
    repo_name: str
    wave: Wave
    scheduled_date: Optional[str] = None
    priority: int = 0


class ReadinessSummary(BaseModel):
    repo_name: str
    readiness_status: ReadinessStatus
    checks_passed: str
    message: str
