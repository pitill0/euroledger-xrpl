from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def validate_webhook_url(value: str) -> str:
    if not value.startswith(("https://", "http://")):
        raise ValueError("Webhook URL must use http or https.")

    return value


class WebhookEndpointCreate(BaseModel):
    url: str = Field(
        ...,
        min_length=8,
        max_length=2048,
    )
    secret: str = Field(
        ...,
        min_length=16,
        max_length=255,
    )
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_webhook_url(value)


class WebhookEndpointUpdate(BaseModel):
    url: str | None = Field(
        default=None,
        min_length=8,
        max_length=2048,
    )
    secret: str | None = Field(
        default=None,
        min_length=16,
        max_length=255,
    )
    enabled: bool | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return validate_webhook_url(value)


class WebhookEndpointRead(BaseModel):
    id: str
    merchant_id: str
    url: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class WebhookEndpointListResponse(BaseModel):
    items: list[WebhookEndpointRead]
