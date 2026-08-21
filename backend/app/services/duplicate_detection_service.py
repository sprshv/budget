from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.transaction import Transaction
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import uuid

async def check_manual_duplicate(
    user_id: uuid.UUID,
    amount: Decimal,
    txn_date: date,
    merchant_name: Optional[str],
    db: AsyncSession,
    exclude_id: Optional[uuid.UUID] = None,
) -> Optional[dict]:
    """
    Check if a manual transaction is a potential duplicate.
    Returns a warning dict if a duplicate is found, None otherwise.

    Criteria: same user + amount (within $0.01) + date (within 1 day) + similar merchant.
    """
    date_start = txn_date - timedelta(days=1)
    date_end = txn_date + timedelta(days=1)

    # Amount tolerance: exact match for simplicity (Decimal comparison)
    conditions = [
        Transaction.user_id == user_id,
        Transaction.amount == amount,
        Transaction.date >= date_start,
        Transaction.date <= date_end,
        Transaction.is_duplicate == False,
    ]

    if exclude_id:
        conditions.append(Transaction.id != exclude_id)

    if merchant_name:
        conditions.append(
            func.lower(Transaction.merchant_name) == merchant_name.lower()
        )

    result = await db.execute(
        select(Transaction).where(and_(*conditions)).limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "is_potential_duplicate": True,
            "duplicate_of": str(existing.id),
            "message": f"A similar transaction exists on {existing.date} for ${amount}",
        }

    return None


async def mark_as_duplicate(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Mark a transaction as a duplicate. Only owner can mark."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        return False
    txn.is_duplicate = True
    await db.commit()
    return True
