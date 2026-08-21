from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from decimal import Decimal
from datetime import datetime


class BudgetCreate(BaseModel):
    category_id: UUID
    amount: Decimal
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2020, le=2100)
    rollover_enabled: bool = False
    # alert_threshold stored as 0.0–1.0 (e.g. 0.80 means 80%)
    alert_threshold: Decimal = Field(Decimal("0.80"), ge=Decimal("0.01"), le=Decimal("1.00"))


class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = None
    rollover_enabled: Optional[bool] = None
    alert_threshold: Optional[Decimal] = Field(None, ge=Decimal("0.01"), le=Decimal("1.00"))


class BudgetResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    amount: Decimal
    period_month: int
    period_year: int
    rollover_enabled: bool
    rollover_amount: Decimal
    alert_threshold: Decimal
    alert_sent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
