from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from app.models.transaction import Transaction
from app.models.financial_account import FinancialAccount
from app.services.plaid_service import sync_transactions
from app.services.encryption_service import decrypt
from app.services.categorization_service import categorize_with_rules
from app.services.normalization_service import normalize_merchant
from datetime import date
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)


def _normalize_merchant(raw_name: str, merchant_name: str) -> str:
    """Return cleaned merchant name: prefer Plaid's merchant_name if present."""
    if merchant_name:
        return merchant_name.strip()
    if raw_name:
        return raw_name.strip().title()
    return "Unknown"


async def sync_account_transactions(
    account: FinancialAccount,
    db: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """Sync all transactions for a single account. Returns count of new transactions stored."""
    try:
        access_token = decrypt(account.plaid_access_token)
    except Exception:
        logger.error(f"Failed to decrypt access token for account {account.id}")
        return 0

    cursor = account.plaid_cursor

    try:
        sync_data = await sync_transactions(access_token, cursor)
    except Exception as e:
        logger.error(f"Plaid sync failed for account {account.id}: {e}")
        account.sync_status = "error"
        await db.commit()
        return 0

    added = sync_data["added"]
    new_cursor = sync_data["next_cursor"]

    inserted = 0
    for txn in added:
        plaid_txn_id = txn.get("transaction_id")
        if not plaid_txn_id:
            continue

        # Deduplication check
        existing = await db.execute(
            select(Transaction).where(Transaction.plaid_transaction_id == plaid_txn_id)
        )
        if existing.scalar_one_or_none():
            continue

        # Categorize
        pfc = txn.get("personal_finance_category", {}) or {}
        primary = pfc.get("primary") if isinstance(pfc, dict) else None

        # Amount: Plaid positive = expense for checking/savings, negative = credit
        raw_amount = Decimal(str(txn.get("amount", 0)))

        category_id, confidence = await categorize_with_rules(
            user_id=user_id,
            merchant_name=txn.get("merchant_name", ""),
            description=txn.get("name", ""),
            amount=raw_amount,
            plaid_category_primary=primary,
            db=db,
        )

        location = txn.get("location", {}) or {}

        new_txn = Transaction(
            user_id=user_id,
            account_id=account.id,
            category_id=category_id,
            plaid_transaction_id=plaid_txn_id,
            amount=raw_amount,
            currency=txn.get("iso_currency_code", "USD") or "USD",
            date=txn.get("date", date.today()),
            description=txn.get("name", "Unknown"),
            merchant_name=normalize_merchant(txn.get("name", ""), txn.get("merchant_name")),
            pending=txn.get("pending", False),
            category_confidence=Decimal(str(confidence)),
            merchant_city=location.get("city"),
            merchant_state=location.get("region"),
            merchant_country=location.get("country"),
        )
        db.add(new_txn)
        inserted += 1

    # Update cursor and last_synced_at
    account.plaid_cursor = new_cursor
    account.sync_status = "ok"
    account.last_synced_at = func.now()

    await db.commit()
    return inserted


async def initial_sync(
    account_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> dict:
    """Run initial sync for a list of newly linked accounts (background task)."""
    from app.database import AsyncSessionLocal

    total = 0
    async with AsyncSessionLocal() as db:
        for account_id in account_ids:
            result = await db.execute(
                select(FinancialAccount).where(
                    FinancialAccount.id == account_id,
                    FinancialAccount.user_id == user_id,
                )
            )
            account = result.scalar_one_or_none()
            if not account:
                continue
            try:
                count = await sync_account_transactions(account, db, user_id)
                total += count
            except Exception:
                logger.exception("initial_sync failed for account %s", account_id)
    return {"transactions_synced": total}
