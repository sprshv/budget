from pydantic import BaseModel, model_validator
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List


class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    category_id: Optional[UUID] = None
    plaid_transaction_id: Optional[str] = None
    amount: Decimal
    currency: str
    date: date
    description: str
    merchant_name: Optional[str] = None
    pending: bool
    category_confidence: Optional[Decimal] = None
    is_manual: bool
    is_recurring: bool
    is_duplicate: bool
    is_hidden: bool
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_tax_deductible: bool
    tax_category: Optional[str] = None
    merchant_city: Optional[str] = None
    merchant_state: Optional[str] = None
    receipt_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    limit: int
    offset: int


class TransactionCreate(BaseModel):
    account_id: UUID
    amount: Decimal
    date: date
    description: str
    merchant_name: Optional[str] = None
    category_id: Optional[UUID] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_tax_deductible: bool = False
    currency: str = "USD"


class TransactionCreateResponse(BaseModel):
    transaction: TransactionResponse
    duplicate_warning: Optional[dict] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[UUID] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_tax_deductible: Optional[bool] = None
    tax_category: Optional[str] = None
    merchant_name: Optional[str] = None
    is_hidden: Optional[bool] = None


class BulkUpdateBody(BaseModel):
    transaction_ids: List[UUID]
    updates: TransactionUpdate

    @model_validator(mode="after")
    def at_least_one_id(self):
        if not self.transaction_ids:
            raise ValueError("transaction_ids must not be empty")
        return self
