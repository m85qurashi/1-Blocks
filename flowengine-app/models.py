from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)

from database import Base
from domain_types import ReadinessStatus, Wave, WorkflowFamily


class SerializableMixin:
    """Helper mixin to convert SQLAlchemy models to dictionaries."""

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                payload[column.name] = value.isoformat()
            else:
                payload[column.name] = value
        return payload


class Idea(Base, SerializableMixin):
    __tablename__ = "ideas"

    id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    sponsoring_team = Column(String(255), nullable=False)
    workflow_family = Column(Enum(WorkflowFamily, native_enum=False), nullable=False)
    desired_outcomes = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False, server_default="active")


class RepoReadiness(Base, SerializableMixin):
    __tablename__ = "repo_readiness"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_name = Column(String(500), nullable=False, unique=True, index=True)
    owner = Column(String(255), nullable=True)
    training_completed = Column(Boolean, nullable=False, server_default="0")
    cli_installed = Column(Boolean, nullable=False, server_default="0")
    test_coverage_80 = Column(Boolean, nullable=False, server_default="0")
    runbook_acknowledged = Column(Boolean, nullable=False, server_default="0")
    notes = Column(Text, nullable=True)
    readiness_status = Column(Enum(ReadinessStatus, native_enum=False), nullable=False, server_default=ReadinessStatus.NOT_STARTED.value)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class WaveAssignment(Base, SerializableMixin):
    __tablename__ = "wave_assignments"
    __table_args__ = (UniqueConstraint("repo_name", "wave", name="uq_repo_wave"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_name = Column(String(500), nullable=False)
    wave = Column(Enum(Wave, native_enum=False), nullable=False)
    scheduled_date = Column(Date, nullable=True)
    priority = Column(Integer, nullable=False, server_default="0")
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    assigned_by = Column(String(255), nullable=True)
