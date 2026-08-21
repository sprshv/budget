from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
import uuid

# Account type classifications
ASSET_TYPES = {"checking", "savings", "investment", "brokerage", "cd", "money_market", "other_asset"}
LIABILITY_TYPES = {"credit", "loan", "mortgage", "student_loan", "auto", "line_of_credit", "other_liability"}


async def get_net_worth(user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.financial_account import FinancialAccount

    result = await db.execute(
        select(
            FinancialAccount.account_type,
            func.sum(FinancialAccount.balance_current).label("total"),
        ).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.is_active == True,
        ).group_by(FinancialAccount.account_type)
    )
    rows = result.all()

    liquid = Decimal("0.00")
    investments = Decimal("0.00")
    total_debt = Decimal("0.00")

    for row in rows:
        acct_type = (row.account_type or "").lower()
        balance = Decimal(str(row.total or 0))

        if acct_type in LIABILITY_TYPES:
            total_debt += abs(balance)
        elif acct_type in {"investment", "brokerage"}:
            investments += balance
        else:
            liquid += balance

    net_total = liquid + investments - total_debt

    return {
        "liquid_assets": float(liquid),
        "investments": float(investments),
        "total_debt": float(total_debt),
        "net_total": float(net_total),
    }


async def get_cash_flow(user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.transaction import Transaction
    import calendar
    from datetime import date

    today = date.today()

    # Current month range
    curr_start = date(today.year, today.month, 1)
    curr_end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    # Previous month range
    if today.month == 1:
        prev_month, prev_year = 12, today.year - 1
    else:
        prev_month, prev_year = today.month - 1, today.year
    prev_start = date(prev_year, prev_month, 1)
    prev_end = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])

    async def get_period_totals(start, end):
        result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
            )
        )
        total = Decimal(str(result.scalar() or 0))

        # Income = positive amounts, expenses = negative amounts (abs)
        inc_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.amount > 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
            )
        )
        income = Decimal(str(inc_result.scalar() or 0))
        expenses = abs(total - income)
        return income, expenses

    curr_income, curr_expenses = await get_period_totals(curr_start, curr_end)
    prev_income, prev_expenses = await get_period_totals(prev_start, prev_end)

    curr_net = curr_income - curr_expenses
    prev_net = prev_income - prev_expenses

    def pct_change(curr, prev):
        if prev == 0:
            return None
        return round(float((curr - prev) / abs(prev) * 100), 1)

    return {
        "current_month": {
            "income": float(curr_income),
            "expenses": float(curr_expenses),
            "net": float(curr_net),
        },
        "previous_month": {
            "income": float(prev_income),
            "expenses": float(prev_expenses),
            "net": float(prev_net),
        },
        "income_change_pct": pct_change(curr_income, prev_income),
        "expense_change_pct": pct_change(curr_expenses, prev_expenses),
        "net_change_pct": pct_change(curr_net, prev_net),
    }


async def get_account_sparkline(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.financial_account import FinancialAccount
    from app.models.transaction import Transaction
    from datetime import date, timedelta

    # Verify ownership
    acct_result = await db.execute(
        select(FinancialAccount.id).where(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id,
            FinancialAccount.is_active == True,
        )
    )
    if acct_result.scalar() is None:
        return []

    # Last 30 days of daily net transaction flow
    today = date.today()
    start = today - timedelta(days=29)

    result = await db.execute(
        select(
            Transaction.date,
            func.sum(Transaction.amount).label("daily_total"),
        ).where(
            Transaction.account_id == account_id,
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= today,
            Transaction.pending == False,
            Transaction.is_hidden == False,
        ).group_by(Transaction.date)
        .order_by(Transaction.date)
    )
    rows = result.all()

    # Build 30-point series (fill missing days with 0)
    daily_map = {row.date: float(row.daily_total or 0) for row in rows}
    series = []
    for i in range(30):
        d = start + timedelta(days=i)
        series.append({"date": d.isoformat(), "amount": daily_map.get(d, 0.0)})

    return series


async def get_spending_breakdown(user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.transaction import Transaction
    from app.models.category import Category
    from datetime import date
    import calendar

    today = date.today()
    start = date(today.year, today.month, 1)
    end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.amount < 0,   # expenses only (negative amounts)
            Category.is_income == False,
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount))  # most negative first
    )
    rows = result.all()

    total_spent = sum(abs(float(row.total or 0)) for row in rows)

    categories = []
    for row in rows:
        amount = abs(float(row.total or 0))
        categories.append({
            "category_id": str(row.id),
            "name": row.name,
            "color": row.color,
            "amount": amount,
            "percentage": round(amount / total_spent * 100, 1) if total_spent > 0 else 0.0,
        })

    return {"total_spent": total_spent, "categories": categories}


async def get_net_worth_history(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.financial_account import FinancialAccount
    from app.models.transaction import Transaction
    from datetime import date
    import calendar

    today = date.today()

    # Get current account balances classified as assets vs liabilities
    acct_result = await db.execute(
        select(
            FinancialAccount.account_type,
            func.sum(FinancialAccount.balance_current).label("total"),
        ).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.is_active == True,
        ).group_by(FinancialAccount.account_type)
    )
    acct_rows = acct_result.all()

    liquid = Decimal("0.00")
    investments = Decimal("0.00")
    total_debt = Decimal("0.00")
    for row in acct_rows:
        acct_type = (row.account_type or "").lower()
        balance = Decimal(str(row.total or 0))
        if acct_type in LIABILITY_TYPES:
            total_debt += abs(balance)
        elif acct_type in {"investment", "brokerage"}:
            investments += balance
        else:
            liquid += balance

    current_net = liquid + investments - total_debt

    # Reconstruct monthly snapshots by working backwards from current net worth.
    # For each past month end, subtract the sum of transactions that occurred
    # after that month's end up to today — that gives the net worth at that point.
    snapshots = []
    for months_ago in range(11, -1, -1):
        m = today.month - months_ago
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        month_end = date(y, m, calendar.monthrange(y, m)[1])

        tx_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.date > month_end,
                Transaction.date <= today,
                Transaction.pending == False,
                Transaction.is_hidden == False,
            )
        )
        delta = Decimal(str(tx_result.scalar() or 0))
        net_at_month = float(current_net - delta)

        snapshots.append({
            "month": f"{y}-{m:02d}",
            "net_worth": round(net_at_month, 2),
        })

    return snapshots


async def get_spending_trends(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.transaction import Transaction
    from datetime import date
    import calendar

    today = date.today()
    months = []

    for months_ago in range(5, -1, -1):  # 6 months: 5 ago → current
        m = today.month - months_ago
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        start = date(y, m, 1)
        end = date(y, m, calendar.monthrange(y, m)[1])

        # Income (positive amounts)
        inc_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.amount > 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
            )
        )
        income = float(inc_result.scalar() or 0)

        # Expenses (negative amounts — return as positive number)
        exp_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.amount < 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
            )
        )
        expenses = abs(float(exp_result.scalar() or 0))

        months.append({
            "month": f"{y}-{m:02d}",
            "income": round(income, 2),
            "expenses": round(expenses, 2),
        })

    return months


async def get_recent_transactions(user_id: uuid.UUID, db: AsyncSession, limit: int = 10) -> list[dict]:
    from app.models.transaction import Transaction
    from app.models.category import Category

    result = await db.execute(
        select(
            Transaction.id,
            Transaction.amount,
            Transaction.date,
            Transaction.description,
            Transaction.merchant_name,
            Transaction.pending,
            Transaction.is_hidden,
            Transaction.is_duplicate,
            Category.name.label("category_name"),
            Category.color.label("category_color"),
            Category.icon.label("category_icon"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "id": str(row.id),
            "amount": float(row.amount),
            "date": row.date.isoformat(),
            "description": row.description,
            "merchant_name": row.merchant_name,
            "pending": row.pending,
            "category_name": row.category_name,
            "category_color": row.category_color,
            "category_icon": row.category_icon,
        }
        for row in rows
    ]
