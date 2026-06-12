from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.merchant import Merchant
from app.services.merchant_auth import (
    authenticate_merchant_api_key,
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]

ApiKeyHeader = Annotated[
    str | None,
    Header(
        alias="X-API-Key",
    ),
]


def get_current_merchant(
    db: DbSession,
    api_key: ApiKeyHeader = None,
) -> Merchant:
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
            headers={
                "WWW-Authenticate": "ApiKey",
            },
        )

    settings = get_settings()

    merchant = authenticate_merchant_api_key(
        db=db,
        value=api_key,
        pepper=settings.merchant_api_key_pepper,
    )

    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={
                "WWW-Authenticate": "ApiKey",
            },
        )

    return merchant


CurrentMerchant = Annotated[
    Merchant,
    Depends(get_current_merchant),
]
