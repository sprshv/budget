from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from app.models.user import User


async def get_or_create_user(
    user_id: str,
    email: str,
    db: AsyncSession,
) -> User:
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid.UUID(user_id),
            email=email,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_user_by_id(user_id: str, db: AsyncSession) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    return result.scalar_one_or_none()
