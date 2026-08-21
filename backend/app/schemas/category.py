from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class CategoryCreate(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_income: bool = False


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None


class CategoryResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_income: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
