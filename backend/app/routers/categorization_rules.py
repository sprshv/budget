from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleUpdate,
    CategorizationRuleResponse,
)
from app.services.rule_service import list_rules, create_rule, update_rule, delete_rule
from typing import List
import uuid

router = APIRouter(prefix="/categorization-rules", tags=["categorization-rules"])


@router.get("", response_model=List[CategorizationRuleResponse])
async def get_rules(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_rules(uuid.UUID(current_user["id"]), db)


@router.post("", response_model=CategorizationRuleResponse, status_code=201)
async def create_categorization_rule(
    body: CategorizationRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_rule(uuid.UUID(current_user["id"]), body.model_dump(), db)


@router.patch("/{rule_id}", response_model=CategorizationRuleResponse)
async def update_categorization_rule(
    rule_id: uuid.UUID,
    body: CategorizationRuleUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_rule(
            rule_id,
            uuid.UUID(current_user["id"]),
            body.model_dump(exclude_unset=True),
            db,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": str(e), "code": "RULE_NOT_FOUND"},
        )


@router.delete("/{rule_id}", status_code=204)
async def delete_categorization_rule(
    rule_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_rule(rule_id, uuid.UUID(current_user["id"]), db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": str(e), "code": "RULE_NOT_FOUND"},
        )
