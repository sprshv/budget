from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.category import Category
from decimal import Decimal
import uuid
import calendar
from datetime import date


async def list_budgets(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> list:
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.period_month == period_month,
            Budget.period_year == period_year,
        ).order_by(Budget.created_at)
    )
    return result.scalars().all()


async def create_budget(user_id: uuid.UUID, data: dict, db: AsyncSession) -> Budget:
    budget = Budget(user_id=user_id, rollover_amount=Decimal("0.00"), **data)
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


async def get_budget(budget_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_budget(
    budget_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
    db: AsyncSession,
) -> Budget:
    budget = await get_budget(budget_id, user_id, db)
    if not budget:
        raise ValueError("Budget not found")
    for field, value in data.items():
        setattr(budget, field, value)
    await db.commit()
    await db.refresh(budget)
    return budget


async def delete_budget(
    budget_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    budget = await get_budget(budget_id, user_id, db)
    if not budget:
        raise ValueError("Budget not found")
    await db.delete(budget)
    await db.commit()


async def auto_create_from_previous(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> list:
    """Copy budgets from previous month if none exist for the requested period."""
    existing = await list_budgets(user_id, period_month, period_year, db)
    if existing:
        return existing

    # Calculate previous month
    if period_month == 1:
        prev_month, prev_year = 12, period_year - 1
    else:
        prev_month, prev_year = period_month - 1, period_year

    prev_budgets = await list_budgets(user_id, prev_month, prev_year, db)
    if not prev_budgets:
        return []

    created = []
    for prev in prev_budgets:
        new_budget = Budget(
            user_id=user_id,
            category_id=prev.category_id,
            amount=prev.amount,
            period_month=period_month,
            period_year=period_year,
            rollover_enabled=prev.rollover_enabled,
            rollover_amount=Decimal("0.00"),
            alert_threshold=prev.alert_threshold,
            alert_sent=False,
        )
        db.add(new_budget)
        created.append(new_budget)

    await db.commit()
    for b in created:
        await db.refresh(b)
    return created


async def get_budget_progress(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> list:
    budgets = await list_budgets(user_id, period_month, period_year, db)
    if not budgets:
        return []

    # Date range for the period
    last_day = calendar.monthrange(period_year, period_month)[1]
    period_start = date(period_year, period_month, 1)
    period_end = date(period_year, period_month, last_day)

    # Build category_id -> spent map with one query
    category_ids = [b.category_id for b in budgets]
    result = await db.execute(
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.category_id.in_(category_ids),
            Transaction.date >= period_start,
            Transaction.date <= period_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
        ).group_by(Transaction.category_id)
    )
    spent_map = {row.category_id: abs(row.total) for row in result.all()}

    progress = []
    for budget in budgets:
        amount = Decimal(str(budget.amount))
        rollover = Decimal(str(budget.rollover_amount))
        effective_limit = amount + rollover
        spent = Decimal(str(spent_map.get(budget.category_id, 0)))
        remaining = effective_limit - spent
        percentage = float(spent / effective_limit * 100) if effective_limit > 0 else 0.0

        # alert_threshold is stored as Decimal 0.01–1.00
        threshold = Decimal(str(budget.alert_threshold))
        if spent >= effective_limit:
            status = "over"
        elif threshold > 0 and spent >= effective_limit * threshold:
            status = "warning"
        else:
            status = "ok"

        progress.append({
            "budget_id": budget.id,
            "category_id": budget.category_id,
            "amount": float(amount),
            "rollover_amount": float(rollover),
            "effective_limit": float(effective_limit),
            "spent": float(spent),
            "remaining": float(remaining),
            "percentage": round(percentage, 1),
            "status": status,
            "period_month": period_month,
            "period_year": period_year,
        })

    return progress


async def get_income_summary(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> dict:
    """Return planned vs actual income for the given period.

    Planned income comes from budgets whose linked category has is_income=True.
    Actual income is the sum of transactions with a negative amount (income sign
    convention: positive = expense, negative = income).
    """
    # Fetch income budgets by joining with categories
    budget_result = await db.execute(
        select(Budget).join(
            Category, Budget.category_id == Category.id
        ).where(
            Budget.user_id == user_id,
            Budget.period_month == period_month,
            Budget.period_year == period_year,
            Category.is_income == True,
        )
    )
    income_budgets = budget_result.scalars().all()
    planned = sum((Decimal(str(b.amount)) for b in income_budgets), Decimal("0"))

    # Fetch actual income: negative transactions (income) for the period
    last_day = calendar.monthrange(period_year, period_month)[1]
    period_start = date(period_year, period_month, 1)
    period_end = date(period_year, period_month, last_day)

    txn_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,  # negative = income per schema convention
            Transaction.date >= period_start,
            Transaction.date <= period_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
        )
    )
    raw = txn_result.scalar()
    actual = abs(Decimal(str(raw))) if raw is not None else Decimal("0")

    return {
        "planned_income": float(planned),
        "actual_income": float(actual),
        "variance": float(actual - planned),
        "income_budgets": [
            {
                "budget_id": str(b.id),
                "category_id": str(b.category_id),
                "amount": float(b.amount),
            }
            for b in income_budgets
        ],
        "period_month": period_month,
        "period_year": period_year,
    }


async def get_spending_forecast(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> list:
    import calendar as cal

    budgets = await list_budgets(user_id, period_month, period_year, db)
    if not budgets:
        return []

    today = date.today()
    days_in_month = cal.monthrange(period_year, period_month)[1]
    period_start = date(period_year, period_month, 1)
    period_end = date(period_year, period_month, days_in_month)

    # days_elapsed: how many days into the period we are (minimum 1 to avoid divide-by-zero)
    if today.month == period_month and today.year == period_year:
        days_elapsed = max(today.day, 1)
    else:
        # For past months, elapsed = full month
        days_elapsed = days_in_month

    category_ids = [b.category_id for b in budgets]
    result = await db.execute(
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.category_id.in_(category_ids),
            Transaction.date >= period_start,
            Transaction.date <= period_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
        ).group_by(Transaction.category_id)
    )
    spent_map = {row.category_id: abs(row.total) for row in result.all()}

    forecasts = []
    for budget in budgets:
        amount = Decimal(str(budget.amount))
        rollover = Decimal(str(budget.rollover_amount))
        effective_limit = amount + rollover
        spent = Decimal(str(spent_map.get(budget.category_id, 0)))

        daily_rate = spent / Decimal(str(days_elapsed))
        projected = daily_rate * Decimal(str(days_in_month))
        will_exceed = projected > effective_limit

        forecasts.append({
            "budget_id": str(budget.id),
            "category_id": str(budget.category_id),
            "effective_limit": float(effective_limit),
            "spent_so_far": float(spent),
            "projected_total": round(float(projected), 2),
            "will_exceed": will_exceed,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
            "period_month": period_month,
            "period_year": period_year,
        })

    return forecasts


async def get_zero_based_summary(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> dict:
    """
    Zero-based budgeting: every dollar of income is assigned to a category.
    Returns total income budgeted, total expenses budgeted, and the unallocated remainder.

    Budget model has no is_income column — is_income lives on Category.
    We use get_income_summary for planned income (budgets in income categories)
    and derive expense total as all budgets minus income budgets.
    """
    budgets = await list_budgets(user_id, period_month, period_year, db)

    # is_income is on Category, not Budget, so getattr fallback will always be 0
    income_total = sum(
        Decimal(str(b.amount)) for b in budgets if getattr(b, "is_income", False)
    )
    expense_total = sum(
        Decimal(str(b.amount)) for b in budgets if not getattr(b, "is_income", False)
    )

    # Since is_income doesn't exist on Budget, income_total is always 0 here.
    # Fall back to get_income_summary for actual income and treat all budgets as expenses.
    if income_total == 0:
        income_summary = await get_income_summary(user_id, period_month, period_year, db)
        income_total = Decimal(str(income_summary["actual_income"]))
        expense_total = sum(Decimal(str(b.amount)) for b in budgets)

    unallocated = income_total - expense_total

    return {
        "total_income": float(income_total),
        "total_budgeted": float(expense_total),
        "unallocated": float(unallocated),
        "is_fully_allocated": unallocated == 0,
        "period_month": period_month,
        "period_year": period_year,
    }


async def get_budget_history(
    user_id: uuid.UUID,
    months: int,
    db: AsyncSession,
) -> list:
    """Returns budget performance for the last N months (max 12)."""
    import calendar as cal
    from app.models.transaction import Transaction

    months = min(months, 12)
    today = date.today()
    history = []

    for i in range(months):
        # Calculate month offset
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        budgets = await list_budgets(user_id, month, year, db)
        if not budgets:
            continue

        last_day = cal.monthrange(year, month)[1]
        period_start = date(year, month, 1)
        period_end = date(year, month, last_day)

        category_ids = [b.category_id for b in budgets]
        txn_result = await db.execute(
            select(
                Transaction.category_id,
                func.sum(Transaction.amount).label("total"),
            ).where(
                Transaction.user_id == user_id,
                Transaction.category_id.in_(category_ids),
                Transaction.date >= period_start,
                Transaction.date <= period_end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
            ).group_by(Transaction.category_id)
        )
        spent_map = {row.category_id: abs(row.total) for row in txn_result.all()}

        month_data = {
            "period_month": month,
            "period_year": year,
            "budgets": [],
        }
        for budget in budgets:
            amount = Decimal(str(budget.amount))
            rollover = Decimal(str(budget.rollover_amount))
            effective_limit = amount + rollover
            spent = Decimal(str(spent_map.get(budget.category_id, 0)))
            month_data["budgets"].append({
                "budget_id": str(budget.id),
                "category_id": str(budget.category_id),
                "budgeted": float(effective_limit),
                "actual": float(spent),
                "variance": float(effective_limit - spent),
                "over_budget": spent > effective_limit,
            })
        history.append(month_data)

    return history
