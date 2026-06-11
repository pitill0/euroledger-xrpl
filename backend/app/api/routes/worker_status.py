from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.worker_status import WorkerStatusRead
from app.services.worker_status import get_xrpl_worker_status

router = APIRouter(tags=["worker"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/worker-status",
    response_model=WorkerStatusRead,
)
def get_worker_status_endpoint(
    db: DbSession,
) -> WorkerStatusRead:
    settings = get_settings()

    return get_xrpl_worker_status(
        db=db,
        stale_after_seconds=settings.xrpl_worker_stale_after_seconds,
    )
