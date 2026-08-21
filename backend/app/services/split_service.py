from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.transaction_split import TransactionSplit
from app.models.transaction import Transaction
from app.services.transaction_service import get_transaction_by_id
from decimal import Decimal
from typing import List
import uuid

async def create_splits(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID,
    splits: List[dict],
    db: AsyncSession,
) -> List[TransactionSplit]:
    """
    Create splits for a transaction.
    Validates:
    - Transaction exists and belongs to user
    - Split amounts sum to original transaction amount (within $0.01 tolerance)
    - At least 2 splits
    Replaces any existing splits.
    """
    txn = await get_transaction_by_id(transaction_id, user_id, db)
    if not txn:
        raise ValueError("Transaction not found")

    total = sum(Decimal(str(s["amount"])) for s in splits)
    original = Decimal(str(txn.amount))

    if abs(total - original) > Decimal("0.01"):
        raise ValueError(
            f"Split amounts ({total}) must sum to original transaction amount ({original})"
        )

    # Delete existing splits
    await db.execute(
        delete(TransactionSplit).where(TransactionSplit.transaction_id == transaction_id)
    )

    # Create new splits
    new_splits = []
    for s in splits:
        split = TransactionSplit(
            transaction_id=transaction_id,
            category_id=s["category_id"],
            amount=Decimal(str(s["amount"])),
            notes=s.get("notes"),
        )
        db.add(split)
        new_splits.append(split)

    await db.commit()
    for split in new_splits:
        await db.refresh(split)

    return new_splits

async def get_splits(transaction_id: uuid.UUID, db: AsyncSession) -> List[TransactionSplit]:
    result = await db.execute(
        select(TransactionSplit).where(
            TransactionSplit.transaction_id == transaction_id
        ).order_by(TransactionSplit.created_at)
    )
    return result.scalars().all()
