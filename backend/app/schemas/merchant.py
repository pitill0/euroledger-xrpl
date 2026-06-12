from datetime import datetime

from pydantic import BaseModel


class MerchantRead(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class MerchantAuthenticationRead(BaseModel):
    merchant: MerchantRead
    authentication_method: str = "api_key"
