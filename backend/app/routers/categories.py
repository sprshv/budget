from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import (
    list_categories,
    create_category,
    update_category,
    delete_category,
)
from typing import List
import uuid

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_categories(uuid.UUID(current_user["id"]), db)


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_new_category(
    body: CategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_category(uuid.UUID(current_user["id"]), body.model_dump(), db)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_existing_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_category(
            category_id,
            uuid.UUID(current_user["id"]),
            body.model_dump(exclude_unset=True),
            db,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{category_id}", status_code=204)
async def delete_existing_category(
    category_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_category(category_id, uuid.UUID(current_user["id"]), db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
