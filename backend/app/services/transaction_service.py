from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.transaction import Transaction
from datetime import date
from decimal import Decimal
from typing import Optional, List
import uuid


async def get_transactions(
    user_id: uuid.UUID,
    db: AsyncSession,
    account_id: Optional[uuid.UUID] = None,
    category_id: Optional[uuid.UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    amount_min: Optional[Decimal] = None,
    amount_max: Optional[Decimal] = None,
    search: Optional[str] = None,
    pending: Optional[bool] = None,
    tax_deductible: Optional[bool] = None,
    is_hidden: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[Transaction], int]:
    conditions = [
        Transaction.user_id == user_id,
        Transaction.is_hidden == is_hidden,
        Transaction.is_duplicate == False,
    ]

    if account_id:
        conditions.append(Transaction.account_id == account_id)
    if category_id:
        conditions.append(Transaction.category_id == category_id)
    if date_from:
        conditions.append(Transaction.date >= date_from)
    if date_to:
        conditions.append(Transaction.date <= date_to)
    if amount_min is not None:
        conditions.append(Transaction.amount >= amount_min)
    if amount_max is not None:
        conditions.append(Transaction.amount <= amount_max)
    if pending is not None:
        conditions.append(Transaction.pending == pending)
    if tax_deductible is not None:
        conditions.append(Transaction.is_tax_deductible == tax_deductible)
    if search:
        search_term = f"%{search}%"
        conditions.append(
            or_(
                Transaction.merchant_name.ilike(search_term),
                Transaction.description.ilike(search_term),
            )
        )

    base_query = select(Transaction).where(and_(*conditions))

    # Count total matching rows
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    # Paginated results
    result = await db.execute(
        base_query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()

    return transactions, total


async def get_transaction_by_id(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_transaction(
    user_id: uuid.UUID,
    data: dict,
    db: AsyncSession,
) -> tuple:
    """Create a manual transaction. Returns (transaction, duplicate_warning_or_None)."""
    from app.models.financial_account import FinancialAccount
    from app.services.categorization_service import categorize_with_rules
    from app.services.duplicate_detection_service import check_manual_duplicate

    # Verify account belongs to user
    acct_result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.id == data["account_id"],
            FinancialAccount.user_id == user_id,
        )
    )
    if not acct_result.scalar_one_or_none():
        raise ValueError("Account not found or does not belong to user")

    # Duplicate check
    duplicate_warning = await check_manual_duplicate(
        user_id=user_id,
        amount=data["amount"],
        txn_date=data["date"],
        merchant_name=data.get("merchant_name") or data.get("description"),
        db=db,
    )

    # Auto-categorize if no category provided
    category_id = data.get("category_id")
    confidence = None
    if not category_id:
        category_id, confidence = await categorize_with_rules(
            user_id=user_id,
            merchant_name=data.get("merchant_name", ""),
            description=data.get("description", ""),
            amount=data["amount"],
            plaid_category_primary=None,
            db=db,
        )

    txn = Transaction(
        user_id=user_id,
        account_id=data["account_id"],
        category_id=category_id,
        amount=data["amount"],
        currency=data.get("currency", "USD"),
        date=data["date"],
        description=data["description"],
        merchant_name=data.get("merchant_name"),
        notes=data.get("notes"),
        tags=data.get("tags"),
        is_tax_deductible=data.get("is_tax_deductible", False),
        is_manual=True,
        category_confidence=confidence,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    # Large purchase alert (fire and forget — errors are isolated in check_large_purchase)
    from app.services.large_purchase_service import check_large_purchase
    await check_large_purchase(
        user_id=user_id,
        transaction_id=txn.id,
        amount=float(txn.amount),
        description=txn.description,
        merchant_name=txn.merchant_name,
        db=db,
    )

    return txn, duplicate_warning


async def update_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
    db: AsyncSession,
) -> Optional[Transaction]:
    txn = await get_transaction_by_id(transaction_id, user_id, db)
    if not txn:
        return None
    for field, value in data.items():
        if value is not None:
            setattr(txn, field, value)
    await db.commit()
    await db.refresh(txn)
    return txn


def _sanitize_csv_field(value: str) -> str:
    """Prevent CSV formula injection by neutralizing leading formula trigger characters."""
    if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return '\t' + value
    return value


async def export_transactions_csv(
    user_id: uuid.UUID,
    db: AsyncSession,
    start_date: date = None,
    end_date: date = None,
) -> str:
    from app.models.transaction import Transaction
    from app.models.category import Category
    from app.models.financial_account import FinancialAccount
    import csv
    import io

    query = (
        select(
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.merchant_name,
            Transaction.amount,
            Transaction.notes,
            Transaction.is_tax_deductible,
            Transaction.tax_category,
            Transaction.pending,
            Category.name.label("category_name"),
            FinancialAccount.name.label("account_name"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .outerjoin(FinancialAccount, Transaction.account_id == FinancialAccount.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
    )

    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    query = query.order_by(Transaction.date.desc()).limit(10000)

    result = await db.execute(query)
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Description", "Merchant", "Amount", "Category",
        "Account", "Notes", "Tax Deductible", "Tax Category", "Pending", "ID",
    ])
    for row in rows:
        writer.writerow([
            row.date.isoformat() if row.date else "",
            _sanitize_csv_field(row.description or ""),
            _sanitize_csv_field(row.merchant_name or ""),
            float(row.amount) if row.amount is not None else "",
            _sanitize_csv_field(row.category_name or ""),
            _sanitize_csv_field(row.account_name or ""),
            _sanitize_csv_field(row.notes or ""),
            "Yes" if row.is_tax_deductible else "No",
            _sanitize_csv_field(row.tax_category or ""),
            "Yes" if row.pending else "No",
            str(row.id),
        ])

    return output.getvalue()


async def bulk_update_transactions(
    transaction_ids: list,
    updates: dict,
    user_id,
    db: AsyncSession,
) -> list:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id.in_(transaction_ids)
        )
    )
    found = result.scalars().all()

    if len(found) != len(transaction_ids):
        raise ValueError("One or more transaction IDs not found")

    for txn in found:
        if str(txn.user_id) != str(user_id):
            raise PermissionError("One or more transactions do not belong to current user")

    update_data = {k: v for k, v in updates.items() if v is not None}
    updated = []
    for txn in found:
        for field, value in update_data.items():
            setattr(txn, field, value)
        updated.append(txn)

    await db.commit()
    for txn in updated:
        await db.refresh(txn)

    return updated
