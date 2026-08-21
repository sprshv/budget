from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    onboarding_complete: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    currency: str
    timezone: str
    onboarding_complete: bool
    financial_health_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
