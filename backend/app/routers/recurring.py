from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.recurring_service import list_recurring, detect_recurring_for_user
import uuid

router = APIRouter(prefix="/recurring", tags=["recurring"])


@router.get("")
async def get_recurring(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_recurring(uuid.UUID(current_user["id"]), db)


@router.post("/detect", status_code=200)
async def trigger_detection(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger recurring detection for the current user."""
    count = await detect_recurring_for_user(uuid.UUID(current_user["id"]), db)
    return {"patterns_found": count}
