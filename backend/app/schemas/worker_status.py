from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class WorkerHealthStatus(StrEnum):
    NOT_STARTED = "not_started"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALE = "stale"


class WorkerStatusRead(BaseModel):
    worker_name: str
    status: WorkerHealthStatus
    last_ledger_index: int | None
    last_cycle_started_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None
