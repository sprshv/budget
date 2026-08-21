from pydantic import BaseModel
from uuid import UUID
from typing import Literal


class BudgetProgressItem(BaseModel):
    budget_id: UUID
    category_id: UUID
    amount: float
    rollover_amount: float
    effective_limit: float
    spent: float
    remaining: float
    percentage: float
    status: Literal["ok", "warning", "over"]
    period_month: int
    period_year: int
