from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
import uuid


FREQUENCY_DAYS = {
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "quarterly": 91,
    "annual": 365,
}
TOLERANCE_DAYS = 3
SUBSCRIPTION_AMOUNT_TOLERANCE = 0.10  # ±10%


def _detect_frequency(dates: list) -> str | None:
    """Given a sorted list of dates, detect repeating frequency."""
    if len(dates) < 2:
        return None
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    avg_gap = sum(gaps) / len(gaps)
    for freq, days in FREQUENCY_DAYS.items():
        if abs(avg_gap - days) <= TOLERANCE_DAYS:
            return freq
    return None


def _is_subscription(amounts: list) -> bool:
    """Returns True if amounts are consistent within ±10%."""
    if not amounts:
        return False
    avg = sum(amounts) / len(amounts)
    if avg == 0:
        return False
    return all(abs(a - avg) / avg <= SUBSCRIPTION_AMOUNT_TOLERANCE for a in amounts)


async def detect_recurring_for_user(user_id: uuid.UUID, db: AsyncSession) -> int:
    """
    Analyze transaction history for user and upsert recurring_transactions rows.
    Returns count of recurring patterns found.
    """
    from app.models.transaction import Transaction
    from app.models.recurring_transaction import RecurringTransaction

    # Get all non-hidden, non-pending, non-duplicate transactions with a merchant name
    result = await db.execute(
        select(
            Transaction.merchant_name,
            Transaction.amount,
            Transaction.date,
            Transaction.category_id,
        ).where(
            Transaction.user_id == user_id,
            Transaction.is_hidden == False,
            Transaction.pending == False,
            Transaction.is_duplicate == False,
            Transaction.merchant_name.isnot(None),
        ).order_by(Transaction.merchant_name, Transaction.date)
    )
    rows = result.all()

    # Group by merchant_name
    by_merchant = defaultdict(list)
    for row in rows:
        by_merchant[row.merchant_name].append(row)

    patterns_found = 0

    for merchant_name, txns in by_merchant.items():
        if len(txns) < 2:
            continue

        dates = sorted([t.date for t in txns])
        amounts = [abs(float(t.amount)) for t in txns]
        frequency = _detect_frequency(dates)
        if not frequency:
            continue

        avg_amount = sum(amounts) / len(amounts)
        is_sub = _is_subscription(amounts)
        last_date = dates[-1]
        freq_days = FREQUENCY_DAYS[frequency]
        next_expected = last_date + timedelta(days=freq_days)
        category_id = txns[-1].category_id  # use most recent category

        # Check if a recurring row already exists for this merchant+user
        existing_result = await db.execute(
            select(RecurringTransaction).where(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.merchant_name == merchant_name,
                RecurringTransaction.is_active == True,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.average_amount = Decimal(str(round(avg_amount, 2)))
            existing.frequency = frequency
            existing.last_date = last_date
            existing.next_expected_date = next_expected
            existing.is_subscription = is_sub
            existing.is_bill = not is_sub
            existing.category_id = category_id
        else:
            rec = RecurringTransaction(
                user_id=user_id,
                merchant_name=merchant_name,
                description=txns[0].description if txns else None,
                average_amount=Decimal(str(round(avg_amount, 2))),
                frequency=frequency,
                last_date=last_date,
                next_expected_date=next_expected,
                is_subscription=is_sub,
                is_bill=not is_sub,
                category_id=category_id,
            )
            db.add(rec)

        patterns_found += 1

    await db.commit()
    return patterns_found


async def list_recurring(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.recurring_transaction import RecurringTransaction

    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_active == True,
        ).order_by(RecurringTransaction.next_expected_date).limit(200)
    )
    rows = result.scalars().all()
    return [_format_recurring(r) for r in rows]


async def list_bills(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.recurring_transaction import RecurringTransaction

    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_bill == True,
            RecurringTransaction.is_active == True,
        ).order_by(RecurringTransaction.next_expected_date).limit(200)
    )
    rows = result.scalars().all()
    return [_format_recurring(r) for r in rows]


async def mark_bill_paid(bill_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.recurring_transaction import RecurringTransaction
    from fastapi import HTTPException

    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.id == bill_id,
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_bill == True,
        )
    )
    bill = result.scalar_one_or_none()
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found", headers={"X-Error-Code": "BILL_NOT_FOUND"})

    # Advance last_date to today and compute next expected
    today = date.today()
    bill.last_date = today
    freq_days = FREQUENCY_DAYS.get(bill.frequency, 30)
    bill.next_expected_date = today + timedelta(days=freq_days)

    await db.commit()
    await db.refresh(bill)
    return _format_recurring(bill)


def _monthly_cost(amount: float, frequency: str) -> float:
    multipliers = {
        "weekly": 52 / 12,
        "biweekly": 26 / 12,
        "monthly": 1.0,
        "quarterly": 1 / 3,
        "annual": 1 / 12,
    }
    return round(amount * multipliers.get(frequency, 1.0), 2)


def _annual_cost(amount: float, frequency: str) -> float:
    multipliers = {
        "weekly": 52,
        "biweekly": 26,
        "monthly": 12,
        "quarterly": 4,
        "annual": 1,
    }
    return round(amount * multipliers.get(frequency, 12.0), 2)


async def list_subscriptions(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.recurring_transaction import RecurringTransaction

    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_subscription == True,
            RecurringTransaction.is_active == True,
        ).order_by(RecurringTransaction.average_amount.desc()).limit(200)
    )
    rows = result.scalars().all()

    subscriptions = []
    for r in rows:
        base = _format_recurring(r)
        amount = float(r.average_amount)
        base["monthly_cost"] = _monthly_cost(amount, r.frequency)
        base["annual_cost"] = _annual_cost(amount, r.frequency)
        subscriptions.append(base)
    return subscriptions


async def get_subscriptions_summary(user_id: uuid.UUID, db: AsyncSession) -> dict:
    subs = await list_subscriptions(user_id, db)
    total_monthly = round(sum(s["monthly_cost"] for s in subs), 2)
    total_annual = round(sum(s["annual_cost"] for s in subs), 2)
    return {
        "total_monthly": total_monthly,
        "total_annual": total_annual,
        "count": len(subs),
        "subscriptions": subs,
    }


async def get_annual_summary(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """
    Returns total annual subscription cost broken down by subscription,
    sorted by annual cost descending. Includes savings opportunity:
    if user cancelled the top 3 most expensive subscriptions, how much would they save.
    """
    subs = await list_subscriptions(user_id, db)

    # Sort by annual cost descending
    ranked = sorted(subs, key=lambda s: s["annual_cost"], reverse=True)

    total_annual = round(sum(s["annual_cost"] for s in ranked), 2)
    total_monthly = round(sum(s["monthly_cost"] for s in ranked), 2)

    # Top 3 savings opportunity
    top3_annual = round(sum(s["annual_cost"] for s in ranked[:3]), 2)

    return {
        "total_annual": total_annual,
        "total_monthly": total_monthly,
        "count": len(ranked),
        "subscriptions_by_cost": ranked,  # sorted highest annual cost first
        "top3_annual_savings": top3_annual,
    }


def _format_recurring(r) -> dict:
    today = date.today()
    days_until = None
    if r.next_expected_date:
        days_until = (r.next_expected_date - today).days

    return {
        "id": str(r.id),
        "merchant_name": r.merchant_name,
        "description": r.description,
        "average_amount": float(r.average_amount),
        "frequency": r.frequency,
        "last_date": r.last_date.isoformat() if r.last_date else None,
        "next_expected_date": r.next_expected_date.isoformat() if r.next_expected_date else None,
        "days_until_due": days_until,
        "is_subscription": r.is_subscription,
        "is_bill": r.is_bill,
        "is_active": r.is_active,
        "remind_days_before": r.remind_days_before,
        "alert_enabled": r.alert_enabled,
        "category_id": str(r.category_id) if r.category_id else None,
    }
