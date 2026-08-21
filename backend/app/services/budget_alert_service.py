from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
import uuid

from app.services.notification_service import create_notification


async def check_budget_alerts(user_id: uuid.UUID, db: AsyncSession) -> None:
    from app.models.budget import Budget
    from app.models.transaction import Transaction
    from app.models.category import Category

    today = date.today()
    month = today.month
    year = today.year

    # Get all budgets for current month
    budget_result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.period_month == month,
            Budget.period_year == year,
        )
    )
    budgets = budget_result.scalars().all()

    if not budgets:
        return

    # Get spending per category this month (amount < 0 = expense)
    curr_start = date(year, month, 1)
    spend_result = await db.execute(
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= curr_start,
            Transaction.date <= today,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        ).group_by(Transaction.category_id)
    )
    spend_map = {str(r.category_id): abs(float(r.total or 0)) for r in spend_result.all()}

    # Get category names
    cat_ids = [b.category_id for b in budgets]
    cat_result = await db.execute(
        select(Category.id, Category.name).where(Category.id.in_(cat_ids))
    )
    cat_map = {str(r.id): r.name for r in cat_result.all()}

    for budget in budgets:
        cat_id = str(budget.category_id)
        spent = spend_map.get(cat_id, 0.0)
        limit = float(budget.amount)

        if limit <= 0:
            continue

        pct = (spent / limit) * 100
        # alert_threshold stored as fraction (0.80 = 80%) — convert to percentage for comparison
        threshold_pct = float(budget.alert_threshold or 0.80) * 100

        if pct < threshold_pct:
            continue

        if budget.alert_sent:
            # Threshold alert already sent — only re-notify if budget is now exceeded
            if pct < 100:
                continue

        cat_name = cat_map.get(cat_id, "Unknown")

        if pct >= 100:
            title = f"{cat_name} budget exceeded"
            body = f"You've spent ${spent:.2f} of your ${limit:.2f} {cat_name} budget ({pct:.0f}%)."
        else:
            title = f"{cat_name} budget at {pct:.0f}%"
            body = f"You've used {pct:.0f}% of your ${limit:.2f} {cat_name} budget this month."

        await create_notification(
            user_id=user_id,
            notif_type="budget_alert",
            title=title,
            body=body,
            db=db,
            notif_metadata={"budget_id": str(budget.id), "category_id": cat_id, "pct": round(pct, 1)},
        )

        if not budget.alert_sent:
            budget.alert_sent = True
            await db.commit()
