from pydantic import BaseModel, model_validator
from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from datetime import datetime

class SplitItem(BaseModel):
    category_id: UUID
    amount: Decimal
    notes: Optional[str] = None

class SplitRequest(BaseModel):
    splits: List[SplitItem]

    @model_validator(mode="after")
    def at_least_two_splits(self):
        if len(self.splits) < 2:
            raise ValueError("Must provide at least 2 splits")
        return self

class SplitResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    category_id: UUID
    amount: Decimal
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class SplitListResponse(BaseModel):
    splits: List[SplitResponse]
    transaction_id: UUID
    original_amount: Decimal
