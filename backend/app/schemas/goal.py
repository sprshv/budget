from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal
from datetime import date, datetime
import uuid

VALID_TYPES = {"savings", "debt_payoff", "emergency_fund", "custom"}
VALID_FREQUENCIES = {"weekly", "biweekly", "monthly"}


class GoalCreate(BaseModel):
    name: str
    goal_type: str
    target_amount: Decimal
    current_amount: Decimal = Decimal("0.00")
    target_date: Optional[date] = None
    linked_account_id: Optional[uuid.UUID] = None
    auto_contribute: bool = False
    auto_amount: Optional[Decimal] = None
    auto_frequency: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    @field_validator("goal_type")
    @classmethod
    def validate_goal_type(cls, v):
        if v not in VALID_TYPES:
            raise ValueError(f"goal_type must be one of {VALID_TYPES}")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError("target_amount must be positive")
        return v


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[Decimal] = None
    current_amount: Optional[Decimal] = None
    target_date: Optional[date] = None
    auto_contribute: Optional[bool] = None
    auto_amount: Optional[Decimal] = None
    auto_frequency: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_complete: Optional[bool] = None


class GoalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    linked_account_id: Optional[uuid.UUID]
    name: str
    goal_type: str
    target_amount: float
    current_amount: float
    target_date: Optional[date]
    auto_contribute: bool
    auto_amount: Optional[float]
    auto_frequency: Optional[str]
    is_complete: bool
    completed_at: Optional[datetime]
    icon: Optional[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime
    percentage: float  # current_amount / target_amount * 100

    class Config:
        from_attributes = True


class ContributionCreate(BaseModel):
    amount: Decimal
    note: Optional[str] = None
    contributed_at: Optional[date] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class ContributionResponse(BaseModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    amount: float
    note: Optional[str]
    contributed_at: date
    created_at: datetime

    class Config:
        from_attributes = True
