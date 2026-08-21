from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


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
    is_manual: bool
    sync_status: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
