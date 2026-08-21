from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
import uuid


async def get_category_spending(
    user_id: uuid.UUID,
    db: AsyncSession,
    start_date: date = None,
    end_date: date = None,
) -> dict:
    from app.models.transaction import Transaction
    from app.models.category import Category
    import calendar

    today = date.today()
    if start_date is None:
        start_date = date(today.year, today.month, 1)
    if end_date is None:
        end_date = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Transaction.amount < 0,       # expenses only
            Category.is_income == False,
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount))  # most negative = highest spend first
        .limit(20)
    )
    rows = result.all()

    categories = []
    for row in rows:
        amount = abs(float(row.total or 0))
        categories.append({
            "category_id": str(row.id),
            "name": row.name,
            "color": row.color,
            "amount": amount,
            "transaction_count": row.count,
        })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "categories": categories,
    }


async def get_merchant_spending(
    user_id: uuid.UUID,
    db: AsyncSession,
    start_date: date = None,
    end_date: date = None,
    limit: int = 15,
) -> dict:
    from app.models.transaction import Transaction
    import calendar

    today = date.today()
    if start_date is None:
        start_date = date(today.year, today.month, 1)
    if end_date is None:
        end_date = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    result = await db.execute(
        select(
            Transaction.merchant_name,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Transaction.amount < 0,
            Transaction.merchant_name.isnot(None),
        )
        .group_by(Transaction.merchant_name)
        .order_by(func.sum(Transaction.amount))  # most negative = highest spend
        .limit(limit)
    )
    rows = result.all()

    merchants = [
        {
            "merchant_name": row.merchant_name,
            "total_spent": abs(float(row.total or 0)),
            "transaction_count": row.count,
        }
        for row in rows
    ]

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "merchants": merchants,
    }


async def get_income_vs_expenses(
    user_id: uuid.UUID,
    db: AsyncSession,
    months: int = 12,
) -> list[dict]:
    from app.models.transaction import Transaction
    import calendar

    today = date.today()
    result = []

    for months_ago in range(months - 1, -1, -1):
        m = today.month - months_ago
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        start = date(y, m, 1)
        end = date(y, m, calendar.monthrange(y, m)[1])

        inc_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.amount > 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
                Transaction.is_duplicate == False,
            )
        )
        income = float(inc_result.scalar() or 0)

        exp_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.amount < 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
                Transaction.is_duplicate == False,
            )
        )
        expenses = abs(float(exp_result.scalar() or 0))

        result.append({
            "month": f"{y}-{m:02d}",
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "net": round(income - expenses, 2),
        })

    return result


async def get_year_over_year(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    from app.models.transaction import Transaction
    import calendar

    today = date.today()
    current_year = today.year
    prior_year = today.year - 1

    async def get_monthly_expenses(year: int) -> list[dict]:
        months = []
        for m in range(1, 13):
            start = date(year, m, 1)
            end = date(year, m, calendar.monthrange(year, m)[1])

            result = await db.execute(
                select(func.sum(Transaction.amount)).where(
                    Transaction.user_id == user_id,
                    Transaction.amount < 0,
                    Transaction.date >= start,
                    Transaction.date <= end,
                    Transaction.pending == False,
                    Transaction.is_hidden == False,
                    Transaction.is_duplicate == False,
                )
            )
            expenses = abs(float(result.scalar() or 0))
            months.append({"month": m, "expenses": round(expenses, 2)})
        return months

    current = await get_monthly_expenses(current_year)
    prior = await get_monthly_expenses(prior_year)

    MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    series = []
    for i in range(12):
        series.append({
            "month": MONTH_NAMES[i],
            "current_year": current[i]["expenses"],
            "prior_year": prior[i]["expenses"],
        })

    return {
        "current_year": current_year,
        "prior_year": prior_year,
        "series": series,
    }


async def get_tax_summary(
    user_id: uuid.UUID,
    db: AsyncSession,
    year: int = None,
) -> dict:
    from app.models.transaction import Transaction
    from app.models.category import Category
    import calendar

    if year is None:
        year = date.today().year

    start = date(year, 1, 1)
    end = date(year, 12, 31)

    # Total deductible spending
    total_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.is_tax_deductible == True,
            Transaction.amount < 0,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
    )
    total_deductible = abs(float(total_result.scalar() or 0))

    # Breakdown by tax_category
    cat_result = await db.execute(
        select(
            Transaction.tax_category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.is_tax_deductible == True,
            Transaction.amount < 0,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
        .group_by(Transaction.tax_category)
        .order_by(func.sum(Transaction.amount))  # most negative = highest deductible first
    )
    cat_rows = cat_result.all()

    by_category = [
        {
            "tax_category": row.tax_category or "Uncategorized",
            "total": abs(float(row.total or 0)),
            "transaction_count": row.count,
        }
        for row in cat_rows
    ]

    # All deductible transactions for the year (for the export list)
    tx_result = await db.execute(
        select(
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.merchant_name,
            Transaction.amount,
            Transaction.tax_category,
            Category.name.label("category_name"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_tax_deductible == True,
            Transaction.amount < 0,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
        .order_by(Transaction.date.desc())
        .limit(500)
    )
    tx_rows = tx_result.all()

    transactions = [
        {
            "id": str(row.id),
            "date": row.date.isoformat(),
            "description": row.description,
            "merchant_name": row.merchant_name,
            "amount": abs(float(row.amount)),
            "tax_category": row.tax_category or "Uncategorized",
            "category_name": row.category_name,
        }
        for row in tx_rows
    ]

    return {
        "year": year,
        "total_deductible": round(total_deductible, 2),
        "by_tax_category": by_category,
        "transactions": transactions,
    }
