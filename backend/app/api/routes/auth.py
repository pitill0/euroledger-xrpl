from fastapi import APIRouter

from app.api.dependencies.auth import CurrentMerchant
from app.schemas.merchant import (
    MerchantAuthenticationRead,
    MerchantRead,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.get(
    "/me",
    response_model=MerchantAuthenticationRead,
)
def authenticated_merchant(
    merchant: CurrentMerchant,
) -> MerchantAuthenticationRead:
    return MerchantAuthenticationRead(
        merchant=MerchantRead.model_validate(
            merchant,
        ),
    )
