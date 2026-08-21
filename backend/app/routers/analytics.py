from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.analytics_service import get_category_spending, get_merchant_spending, get_income_vs_expenses, get_year_over_year, get_tax_summary
from datetime import date
import uuid

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/category-spending")
async def category_spending(
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_category_spending(
        uuid.UUID(current_user["id"]), db, start_date, end_date
    )


@router.get("/merchants")
async def merchant_spending(
    start_date: date = Query(None),
    end_date: date = Query(None),
    limit: int = Query(15, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_merchant_spending(
        uuid.UUID(current_user["id"]), db, start_date, end_date, limit
    )


@router.get("/income-vs-expenses")
async def income_vs_expenses(
    months: int = Query(12, ge=1, le=24),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_income_vs_expenses(uuid.UUID(current_user["id"]), db, months)


@router.get("/year-over-year")
async def year_over_year(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_year_over_year(uuid.UUID(current_user["id"]), db)


@router.get("/tax-summary")
async def tax_summary(
    year: int = Query(None, ge=2000, le=2100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_tax_summary(uuid.UUID(current_user["id"]), db, year)
