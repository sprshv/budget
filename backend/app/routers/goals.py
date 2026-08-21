from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.goal import GoalCreate, GoalUpdate, ContributionCreate
from app.services.goal_service import (
    list_goals,
    create_goal,
    get_goal,
    update_goal,
    delete_goal,
    add_contribution,
    get_goal_progress,
    get_goal_forecast,
    list_contributions,
)
import uuid

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("")
async def get_goals(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_goals(uuid.UUID(current_user["id"]), db)


@router.post("", status_code=201)
async def create_goal_endpoint(
    data: GoalCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_goal(uuid.UUID(current_user["id"]), data, db)


@router.get("/{goal_id}")
async def get_goal_endpoint(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_goal(goal_id, uuid.UUID(current_user["id"]), db)


@router.patch("/{goal_id}")
async def update_goal_endpoint(
    goal_id: uuid.UUID,
    data: GoalUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_goal(goal_id, uuid.UUID(current_user["id"]), data, db)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal_endpoint(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_goal(goal_id, uuid.UUID(current_user["id"]), db)


@router.post("/{goal_id}/contribute", status_code=201)
async def contribute_to_goal(
    goal_id: uuid.UUID,
    data: ContributionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await add_contribution(goal_id, uuid.UUID(current_user["id"]), data, db)


@router.get("/{goal_id}/progress")
async def goal_progress(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_goal_progress(goal_id, uuid.UUID(current_user["id"]), db)


@router.get("/{goal_id}/forecast")
async def goal_forecast(
    goal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_goal_forecast(goal_id, uuid.UUID(current_user["id"]), db)


@router.get("/{goal_id}/contributions")
async def get_contributions(
    goal_id: uuid.UUID,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_contributions(goal_id, uuid.UUID(current_user["id"]), db, limit, offset)
