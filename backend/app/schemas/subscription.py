from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str
