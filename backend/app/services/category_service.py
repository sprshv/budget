from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.category import Category
import uuid


async def list_categories(user_id: uuid.UUID, db: AsyncSession) -> list:
    """Return system categories + user's own custom categories."""
    result = await db.execute(
        select(Category).where(
            or_(
                Category.is_system == True,
                Category.user_id == user_id,
            )
        ).order_by(Category.is_system.desc(), Category.name)
    )
    return result.scalars().all()


async def create_category(user_id: uuid.UUID, data: dict, db: AsyncSession) -> Category:
    category = Category(user_id=user_id, is_system=False, **data)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_category(
    category_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
    db: AsyncSession,
) -> Category:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_system == False,  # cannot edit system categories
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise ValueError("Category not found or cannot be modified")
    for field, value in data.items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(
    category_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_system == False,  # cannot delete system categories
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise ValueError("Category not found or cannot be deleted")
    await db.delete(category)
    await db.commit()
