from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.insights_service import get_spending_changes, get_anomalies, get_forecast, get_savings_opportunities, get_budget_recommendations, get_health_score, get_insights_summary
import uuid

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/summary")
async def insights_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_insights_summary(uuid.UUID(current_user["id"]), db)


@router.get("/spending-changes")
async def spending_changes(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_spending_changes(uuid.UUID(current_user["id"]), db)


@router.get("/anomalies")
async def anomalies(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_anomalies(uuid.UUID(current_user["id"]), db)


@router.get("/forecast")
async def forecast(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_forecast(uuid.UUID(current_user["id"]), db)


@router.get("/savings-opportunities")
async def savings_opportunities(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_savings_opportunities(uuid.UUID(current_user["id"]), db)


@router.get("/budget-recommendations")
async def budget_recommendations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_budget_recommendations(uuid.UUID(current_user["id"]), db)


@router.get("/health-score")
async def health_score(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_health_score(uuid.UUID(current_user["id"]), db)
