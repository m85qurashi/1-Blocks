from enum import Enum


class WorkflowFamily(str, Enum):
    COMPLIANCE = "compliance"
    SECURITY = "security"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class ReadinessStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    BLOCKED = "blocked"


class Wave(str, Enum):
    SOAK = "soak"
    WAVE_1 = "wave_1"
    WAVE_2 = "wave_2"
    FUTURE = "future"
