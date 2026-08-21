from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.recurring_service import list_subscriptions, get_subscriptions_summary, get_annual_summary
import uuid

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/summary")
async def subscriptions_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_subscriptions_summary(uuid.UUID(current_user["id"]), db)


@router.get("/annual-summary")
async def annual_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_annual_summary(uuid.UUID(current_user["id"]), db)


@router.get("")
async def get_subscriptions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_subscriptions(uuid.UUID(current_user["id"]), db)
