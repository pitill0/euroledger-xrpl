from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.exceptions import (
    InvalidPaymentIntentCursorError,
    InvalidPaymentIntentListFilterError,
    InvalidPaymentIntentStatusTransitionError,
    PaymentIntentCancellationConflictError,
    PaymentValidationError,
)
from app.domain.idempotency import (
    IdempotencyConflictError,
)
from app.models.payment_intent import (
    PaymentIntentStatus,
)
from app.schemas.payment_intent import (
    PaymentIntentCancel,
    PaymentIntentConfirm,
    PaymentIntentCreate,
    PaymentIntentDetectedPayment,
    PaymentIntentListResponse,
    PaymentIntentRead,
)
from app.services.payment_intent_api_metrics import (
    record_payment_intent_creation,
)
from app.services.payment_intent_listing import (
    list_payment_intents,
)
from app.services.payment_intents import (
    cancel_payment_intent,
    confirm_payment_intent,
    create_payment_intent,
    get_payment_intent,
    get_payment_intent_by_payment_reference,
    validate_and_confirm_detected_payment,
)

router = APIRouter(
    prefix="/payment-intents",
    tags=["payment-intents"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]

IdempotencyKey = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
]

StatusFilter = Annotated[
    PaymentIntentStatus | None,
    Query(),
]

ReferenceFilter = Annotated[
    str | None,
    Query(
        min_length=4,
        max_length=64,
    ),
]

CreatedFromFilter = Annotated[
    datetime | None,
    Query(),
]

CreatedToFilter = Annotated[
    datetime | None,
    Query(),
]

CursorFilter = Annotated[
    str | None,
    Query(
        min_length=1,
    ),
]

LimitFilter = Annotated[
    int,
    Query(
        ge=1,
        le=100,
    ),
]


@router.post(
    "",
    response_model=PaymentIntentRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "description": ("Existing payment intent returned after idempotent replay."),
        },
        status.HTTP_409_CONFLICT: {
            "description": ("Idempotency-Key was reused with a different payload."),
        },
    },
)
def create_payment_intent_endpoint(
    payload: PaymentIntentCreate,
    db: DbSession,
    response: Response,
    idempotency_key: IdempotencyKey = None,
) -> PaymentIntentRead:
    is_idempotent = idempotency_key is not None

    try:
        result = create_payment_intent(
            db=db,
            payload=payload,
            idempotency_key=idempotency_key,
        )
    except IdempotencyConflictError as exc:
        record_payment_intent_creation(
            result="conflict",
            status_code=status.HTTP_409_CONFLICT,
            idempotent=is_idempotent,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if result.created:
        record_payment_intent_creation(
            result="created",
            status_code=status.HTTP_201_CREATED,
            idempotent=is_idempotent,
        )
    else:
        response.status_code = status.HTTP_200_OK

        record_payment_intent_creation(
            result="replayed",
            status_code=status.HTTP_200_OK,
            idempotent=True,
        )

    return result.payment_intent


@router.get(
    "",
    response_model=PaymentIntentListResponse,
)
def list_payment_intents_endpoint(
    db: DbSession,
    status_filter: StatusFilter = None,
    reference: ReferenceFilter = None,
    created_from: CreatedFromFilter = None,
    created_to: CreatedToFilter = None,
    cursor: CursorFilter = None,
    limit: LimitFilter = 20,
) -> PaymentIntentListResponse:
    try:
        result = list_payment_intents(
            db=db,
            status=status_filter,
            reference=reference,
            created_from=created_from,
            created_to=created_to,
            cursor=cursor,
            limit=limit,
        )
    except (
        InvalidPaymentIntentCursorError,
        InvalidPaymentIntentListFilterError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return PaymentIntentListResponse(
        items=[PaymentIntentRead.model_validate(item) for item in result.items],
        next_cursor=result.next_cursor,
    )


@router.post(
    "/detected-payments",
    response_model=PaymentIntentRead,
)
def validate_detected_payment_endpoint(
    payload: PaymentIntentDetectedPayment,
    db: DbSession,
) -> PaymentIntentRead:
    try:
        return validate_and_confirm_detected_payment(
            db=db,
            detected_payment=payload,
        )
    except PaymentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except InvalidPaymentIntentStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/by-reference/{reference}",
    response_model=PaymentIntentRead,
)
def get_payment_intent_by_reference_endpoint(
    reference: str,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent_by_payment_reference(
        db,
        reference,
    )

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    return payment_intent


@router.get(
    "/{payment_intent_id}",
    response_model=PaymentIntentRead,
)
def get_payment_intent_endpoint(
    payment_intent_id: str,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent(
        db,
        payment_intent_id,
    )

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    return payment_intent


@router.post(
    "/{payment_intent_id}/confirm",
    response_model=PaymentIntentRead,
)
def confirm_payment_intent_endpoint(
    payment_intent_id: str,
    payload: PaymentIntentConfirm,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent(
        db,
        payment_intent_id,
    )

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    try:
        return confirm_payment_intent(
            db=db,
            payment_intent=payment_intent,
            xrpl_transaction_hash=(payload.xrpl_transaction_hash),
        )
    except InvalidPaymentIntentStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{payment_intent_id}/cancel",
    response_model=PaymentIntentRead,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": (
                "Payment intent cannot be cancelled or was already cancelled with another reason."
            ),
        },
    },
)
def cancel_payment_intent_endpoint(
    payment_intent_id: str,
    payload: PaymentIntentCancel,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent(
        db,
        payment_intent_id,
    )

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    try:
        result = cancel_payment_intent(
            db=db,
            payment_intent=payment_intent,
            reason=payload.reason,
        )
    except (
        InvalidPaymentIntentStatusTransitionError,
        PaymentIntentCancellationConflictError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return result.payment_intent
