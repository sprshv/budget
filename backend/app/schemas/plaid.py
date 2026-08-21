from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class LinkTokenResponse(BaseModel):
    link_token: str


class ExchangeTokenRequest(BaseModel):
    public_token: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None


class ExchangeTokenResponse(BaseModel):
    accounts_linked: int
    message: str


class AccountResponse(BaseModel):
    id: UUID
    name: str
    official_name: Optional[str] = None
    nickname: Optional[str] = None
    institution_name: Optional[str] = None
    institution_logo: Optional[str] = None
    account_type: str
    account_subtype: Optional[str] = None
    balance_current: Optional[Decimal] = None
    balance_available: Optional[Decimal] = None
    balance_limit: Optional[Decimal] = None
    is_active: bool
    sync_status: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
