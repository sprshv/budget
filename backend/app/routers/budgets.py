from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.schemas.budget_progress import BudgetProgressItem
from app.services.budget_service import (
    list_budgets,
    create_budget,
    update_budget,
    delete_budget,
    auto_create_from_previous,
    get_budget_progress,
    get_income_summary,
    get_spending_forecast,
)
from typing import List
from datetime import date
import uuid

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=List[BudgetResponse])
async def get_budgets(
    period_month: int = Query(default=None, ge=1, le=12),
    period_year: int = Query(default=None, ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    month = period_month or today.month
    year = period_year or today.year
    user_id = uuid.UUID(current_user["id"])

    budgets = await list_budgets(user_id, month, year, db)
    if not budgets:
        budgets = await auto_create_from_previous(user_id, month, year, db)
    return budgets


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_new_budget(
    body: BudgetCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_budget(uuid.UUID(current_user["id"]), body.model_dump(), db)


@router.get("/progress", response_model=List[BudgetProgressItem])
async def get_progress(
    period_month: int = Query(default=None, ge=1, le=12),
    period_year: int = Query(default=None, ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    month = period_month or today.month
    year = period_year or today.year
    return await get_budget_progress(uuid.UUID(current_user["id"]), month, year, db)


@router.get("/income-summary")
async def get_income_summary_endpoint(
    period_month: int = Query(default=None, ge=1, le=12),
    period_year: int = Query(default=None, ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    month = period_month or today.month
    year = period_year or today.year
    return await get_income_summary(uuid.UUID(current_user["id"]), month, year, db)


@router.get("/forecast")
async def get_forecast(
    period_month: int = Query(default=None, ge=1, le=12),
    period_year: int = Query(default=None, ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    month = period_month or today.month
    year = period_year or today.year
    return await get_spending_forecast(uuid.UUID(current_user["id"]), month, year, db)


@router.get("/history")
async def get_history(
    months: int = Query(default=6, ge=1, le=12),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.budget_service import get_budget_history
    return await get_budget_history(uuid.UUID(current_user["id"]), months, db)


@router.get("/zero-based")
async def get_zero_based(
    period_month: int = Query(default=None, ge=1, le=12),
    period_year: int = Query(default=None, ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.budget_service import get_zero_based_summary
    today = date.today()
    month = period_month or today.month
    year = period_year or today.year
    return await get_zero_based_summary(uuid.UUID(current_user["id"]), month, year, db)


@router.patch("/{budget_id}", response_model=BudgetResponse)
async def update_existing_budget(
    budget_id: uuid.UUID,
    body: BudgetUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_budget(
            budget_id,
            uuid.UUID(current_user["id"]),
            body.model_dump(exclude_unset=True),
            db,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_budget(
    budget_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_budget(budget_id, uuid.UUID(current_user["id"]), db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
