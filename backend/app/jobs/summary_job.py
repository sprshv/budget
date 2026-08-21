import logging
import calendar
from datetime import date, timedelta
from sqlalchemy import select, func

from app.models.financial_account import FinancialAccount
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)


async def send_weekly_summary() -> None:
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user_ids = await _get_all_user_ids(db)
        for user_id in user_ids:
            try:
                await _weekly_summary_for_user(user_id, db)
            except Exception as e:
                logger.error(f"Weekly summary failed for user {user_id}: {e}")


async def send_monthly_summary() -> None:
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user_ids = await _get_all_user_ids(db)
        for user_id in user_ids:
            try:
                await _monthly_summary_for_user(user_id, db)
            except Exception as e:
                logger.error(f"Monthly summary failed for user {user_id}: {e}")


async def _get_all_user_ids(db) -> list:
    """Get all distinct user_ids from financial_accounts (active users who have linked accounts)."""
    result = await db.execute(
        select(FinancialAccount.user_id).distinct().limit(1000)
    )
    return [row.user_id for row in result.all()]


async def _weekly_summary_for_user(user_id, db) -> None:
    today = date.today()
    this_week_start = today - timedelta(days=7)
    prior_week_start = today - timedelta(days=14)
    prior_week_end = today - timedelta(days=8)

    # This week spending
    curr_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= this_week_start,
            Transaction.date <= today,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
    )
    curr_spent = abs(float(curr_result.scalar() or 0))

    # Prior week spending
    prior_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= prior_week_start,
            Transaction.date <= prior_week_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
    )
    prior_spent = abs(float(prior_result.scalar() or 0))

    # Top category this week
    top_cat_result = await db.execute(
        select(
            Category.name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= this_week_start,
            Transaction.date <= today,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Category.is_income == False,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount))
        .limit(1)
    )
    top_cat_row = top_cat_result.first()
    top_cat = top_cat_row.name if top_cat_row else "various categories"

    if curr_spent == 0:
        return  # No activity this week — skip

    change = curr_spent - prior_spent
    change_str = f"${abs(change):.0f} {'more' if change > 0 else 'less'} than last week"

    body = f"You spent ${curr_spent:.2f} this week — {change_str}. Top category: {top_cat}."

    await create_notification(
        user_id=user_id,
        notif_type="weekly_summary",
        title=f"Weekly spending: ${curr_spent:.0f}",
        body=body,
        db=db,
        notif_metadata={"week_start": this_week_start.isoformat(), "total": curr_spent},
    )


async def _monthly_summary_for_user(user_id, db) -> None:
    today = date.today()
    # Prior month
    if today.month == 1:
        pm, py = 12, today.year - 1
    else:
        pm, py = today.month - 1, today.year

    start = date(py, pm, 1)
    end = date(py, pm, calendar.monthrange(py, pm)[1])
    month_label = start.strftime("%B %Y")

    # Income
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

    # Expenses
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

    if income == 0 and expenses == 0:
        return

    net = income - expenses
    net_str = f"saved ${net:.0f}" if net > 0 else f"deficit of ${abs(net):.0f}"

    # Top merchant
    merchant_result = await db.execute(
        select(
            Transaction.merchant_name,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Transaction.merchant_name.isnot(None),
        )
        .group_by(Transaction.merchant_name)
        .order_by(func.sum(Transaction.amount))
        .limit(1)
    )
    top_merchant_row = merchant_result.first()
    top_merchant = top_merchant_row.merchant_name if top_merchant_row else None

    body = f"In {month_label}: income ${income:.0f}, spent ${expenses:.0f}, {net_str}."
    if top_merchant:
        body += f" Top merchant: {top_merchant}."

    await create_notification(
        user_id=user_id,
        notif_type="monthly_summary",
        title=f"{month_label} summary",
        body=body,
        db=db,
        notif_metadata={"month": pm, "year": py, "income": income, "expenses": expenses, "net": net},
    )
