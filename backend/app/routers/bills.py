from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.recurring_service import list_bills, mark_bill_paid
import uuid

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("")
async def get_bills(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_bills(uuid.UUID(current_user["id"]), db)


@router.post("/{bill_id}/mark-paid")
async def bill_mark_paid(
    bill_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mark_bill_paid(bill_id, uuid.UUID(current_user["id"]), db)
