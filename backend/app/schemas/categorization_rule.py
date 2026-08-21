from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime

VALID_OPERATORS = {"contains", "equals", "starts_with", "greater_than"}
VALID_MATCH_FIELDS = {"description", "merchant_name", "amount"}


class CategorizationRuleCreate(BaseModel):
    category_id: UUID
    match_field: str
    operator: str
    match_value: str
    priority: int = 0

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v):
        if v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("match_field")
    @classmethod
    def validate_match_field(cls, v):
        if v not in VALID_MATCH_FIELDS:
            raise ValueError(f"match_field must be one of {VALID_MATCH_FIELDS}")
        return v


class CategorizationRuleUpdate(BaseModel):
    category_id: Optional[UUID] = None
    match_field: Optional[str] = None
    operator: Optional[str] = None
    match_value: Optional[str] = None
    priority: Optional[int] = None

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v):
        if v is not None and v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("match_field")
    @classmethod
    def validate_match_field(cls, v):
        if v is not None and v not in VALID_MATCH_FIELDS:
            raise ValueError(f"match_field must be one of {VALID_MATCH_FIELDS}")
        return v


class CategorizationRuleResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    match_field: str
    # The model stores this as match_operator; expose it as operator in the API
    operator: str = Field(alias="match_operator")
    match_value: str
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
