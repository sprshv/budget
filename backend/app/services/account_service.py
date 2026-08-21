from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.financial_account import FinancialAccount
from typing import List
import uuid


async def get_user_accounts(user_id: uuid.UUID, db: AsyncSession) -> List[FinancialAccount]:
    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.is_active == True,
        ).order_by(FinancialAccount.created_at.desc())
    )
    return result.scalars().all()


async def get_accounts_needing_reauth(user_id: uuid.UUID, db: AsyncSession) -> List[FinancialAccount]:
    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.sync_status == "reauth_required",
            FinancialAccount.is_active == True,
        )
    )
    return result.scalars().all()


async def get_account_by_id(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_account(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> bool:
    account = await get_account_by_id(account_id, user_id, db)
    if not account:
        return False
    await db.delete(account)
    await db.commit()
    return True
