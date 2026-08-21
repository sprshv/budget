from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.dashboard_service import get_net_worth, get_cash_flow, get_account_sparkline, get_spending_breakdown, get_net_worth_history, get_spending_trends, get_recent_transactions
import uuid

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/net-worth")
async def net_worth(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_net_worth(uuid.UUID(current_user["id"]), db)


@router.get("/cash-flow")
async def cash_flow(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_cash_flow(uuid.UUID(current_user["id"]), db)


@router.get("/spending-breakdown")
async def spending_breakdown(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_spending_breakdown(uuid.UUID(current_user["id"]), db)


@router.get("/net-worth-history")
async def net_worth_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_net_worth_history(uuid.UUID(current_user["id"]), db)


@router.get("/spending-trends")
async def spending_trends(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_spending_trends(uuid.UUID(current_user["id"]), db)


@router.get("/recent-transactions")
async def recent_transactions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_recent_transactions(uuid.UUID(current_user["id"]), db)


@router.get("/accounts/sparkline/{account_id}")
async def account_sparkline(
    account_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_account_sparkline(account_id, uuid.UUID(current_user["id"]), db)
