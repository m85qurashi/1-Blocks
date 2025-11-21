"""
Utility script to seed the Repo Readiness database with starter data.
"""
from datetime import date

from database import SessionLocal, init_db
from domain_types import ReadinessStatus, Wave, WorkflowFamily
from models import Idea, RepoReadiness, WaveAssignment


def seed_ideas(session):
    if session.query(Idea).count() > 0:
        return

    ideas = [
        Idea(
            id="idea-seed-monitoring",
            name="Monitoring Blueprint Expansion",
            sponsoring_team="SRE",
            workflow_family=WorkflowFamily.MONITORING,
            desired_outcomes={"latency": "p99 < 150ms", "coverage": "5 workflows"},
            description="Extend monitoring blueprint to cover availability alerts.",
        ),
        Idea(
            id="idea-seed-security",
            name="Security Regression Harness",
            sponsoring_team="Security",
            workflow_family=WorkflowFamily.SECURITY,
            desired_outcomes={"semgrep": "Critical findings auto triaged"},
            description="Automate triage of Semgrep critical findings via FlowEngine.",
        ),
    ]
    session.add_all(ideas)


def seed_readiness(session):
    repos = [
        RepoReadiness(
            repo_name="compliance-repo-5",
            owner="compliance-team",
            training_completed=True,
            cli_installed=True,
            test_coverage_80=True,
            runbook_acknowledged=True,
            readiness_status=ReadinessStatus.READY,
        ),
        RepoReadiness(
            repo_name="security-repo-6",
            owner="appsec",
            training_completed=True,
            cli_installed=True,
            test_coverage_80=False,
            runbook_acknowledged=False,
            notes="Waiting on mutation run fixes",
            readiness_status=ReadinessStatus.IN_PROGRESS,
        ),
        RepoReadiness(
            repo_name="monitor-repo-2",
            owner="sre",
            training_completed=False,
            cli_installed=False,
            test_coverage_80=False,
            runbook_acknowledged=False,
            readiness_status=ReadinessStatus.NOT_STARTED,
        ),
    ]
    for repo in repos:
        existing = session.query(RepoReadiness).filter(RepoReadiness.repo_name == repo.repo_name).first()
        if existing:
            continue
        session.add(repo)


def seed_wave_assignments(session):
    ready_repo = session.query(RepoReadiness).filter(RepoReadiness.readiness_status == ReadinessStatus.READY).first()
    if not ready_repo:
        return

    existing = (
        session.query(WaveAssignment)
        .filter(WaveAssignment.repo_name == ready_repo.repo_name, WaveAssignment.wave == Wave.WAVE_1)
        .first()
    )
    if existing:
        return

    session.add(
        WaveAssignment(
            repo_name=ready_repo.repo_name,
            wave=Wave.WAVE_1,
            scheduled_date=date(2025, 11, 18),
            priority=2,
        )
    )


def main():
    init_db()
    session = SessionLocal()
    try:
        seed_ideas(session)
        seed_readiness(session)
        seed_wave_assignments(session)
        session.commit()
        print("✅ Seed data inserted successfully.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
