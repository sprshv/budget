from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.notification_service import (
    list_notifications,
    mark_read,
    mark_all_read,
    get_unread_count,
    get_preferences,
    update_preferences,
)
from typing import List
import uuid

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_notifications(uuid.UUID(current_user["id"]), db, limit, offset)


@router.get("/unread-count")
async def unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await get_unread_count(uuid.UUID(current_user["id"]), db)
    return {"unread_count": count}


# IMPORTANT: /preferences and /read-all must be registered BEFORE /{notification_id}/read
# so FastAPI does not interpret these static segments as UUID path parameters.
@router.get("/preferences")
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_preferences(uuid.UUID(current_user["id"]), db)


@router.patch("/preferences")
async def update_notification_preferences(
    updates: List[dict] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_preferences(uuid.UUID(current_user["id"]), updates, db)


@router.patch("/read-all")
async def read_all(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mark_all_read(uuid.UUID(current_user["id"]), db)


@router.patch("/{notification_id}/read")
async def read_one(
    notification_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await mark_read(notification_id, uuid.UUID(current_user["id"]), db)
    if result is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result
