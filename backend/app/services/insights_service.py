from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date
import uuid
import calendar


async def get_spending_changes(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.transaction import Transaction
    from app.models.category import Category

    today = date.today()

    # Current month
    curr_start = date(today.year, today.month, 1)
    curr_end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    # Prior month
    if today.month == 1:
        pm, py = 12, today.year - 1
    else:
        pm, py = today.month - 1, today.year
    prev_start = date(py, pm, 1)
    prev_end = date(py, pm, calendar.monthrange(py, pm)[1])

    # 3-month window (90 days back from start of current month)
    # Go back 3 months
    m3 = today.month - 3
    y3 = today.year
    while m3 <= 0:
        m3 += 12
        y3 -= 1
    three_month_window_start = date(y3, m3, 1)
    three_month_window_end = prev_end  # up to end of prior month (exclude current)

    async def spend_by_category(start, end):
        result = await db.execute(
            select(
                Transaction.category_id,
                Category.name,
                Category.color,
                func.sum(Transaction.amount).label("total"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.amount < 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
                Transaction.is_duplicate == False,
                Category.is_income == False,
            )
            .group_by(Transaction.category_id, Category.name, Category.color)
        )
        return {str(row.category_id): row for row in result.all()}

    curr_data = await spend_by_category(curr_start, curr_end)

    # 3-month average: sum over 3 months / 3
    three_month_result = await db.execute(
        select(
            Transaction.category_id,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= three_month_window_start,
            Transaction.date <= three_month_window_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Category.is_income == False,
        )
        .group_by(Transaction.category_id, Category.name, Category.color)
    )
    three_month_data = {str(row.category_id): row for row in three_month_result.all()}

    prev_data = await spend_by_category(prev_start, prev_end)

    changes = []
    # Union of all category_ids seen
    all_cats = set(curr_data.keys()) | set(prev_data.keys())

    for cat_id in all_cats:
        curr_row = curr_data.get(cat_id)
        prev_row = prev_data.get(cat_id)
        three_row = three_month_data.get(cat_id)

        curr_amt = abs(float(curr_row.total or 0)) if curr_row else 0.0
        prev_amt = abs(float(prev_row.total or 0)) if prev_row else 0.0
        three_month_avg = abs(float(three_row.total or 0)) / 3 if three_row else 0.0

        name = (curr_row or prev_row).name
        color = (curr_row or prev_row).color

        # vs prior month
        if prev_amt > 0:
            pct_vs_prev = round((curr_amt - prev_amt) / prev_amt * 100, 1)
        else:
            pct_vs_prev = None

        # vs 3-month average
        if three_month_avg > 0:
            pct_vs_avg = round((curr_amt - three_month_avg) / three_month_avg * 100, 1)
        else:
            pct_vs_avg = None

        direction = "up" if (pct_vs_prev or 0) > 0 else "down"
        significant = abs(pct_vs_prev or 0) > 15

        changes.append({
            "category_id": cat_id,
            "category_name": name,
            "category_color": color,
            "current_month_spend": round(curr_amt, 2),
            "prior_month_spend": round(prev_amt, 2),
            "three_month_avg": round(three_month_avg, 2),
            "pct_vs_prior_month": pct_vs_prev,
            "pct_vs_three_month_avg": pct_vs_avg,
            "direction": direction,
            "significant": significant,
        })

    # Sort by significance and magnitude
    changes.sort(key=lambda x: (not x["significant"], -abs(x["pct_vs_prior_month"] or 0)))
    return changes


async def get_savings_opportunities(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.transaction import Transaction
    from app.models.category import Category

    today = date.today()

    # Current month
    curr_start = date(today.year, today.month, 1)
    curr_end = today

    # 3-month window: 3 full months prior to current month
    m3 = today.month - 3
    y3 = today.year
    while m3 <= 0:
        m3 += 12
        y3 -= 1
    three_month_start = date(y3, m3, 1)

    if today.month == 1:
        pm, py = 12, today.year - 1
    else:
        pm, py = today.month - 1, today.year
    three_month_end = date(py, pm, calendar.monthrange(py, pm)[1])

    async def category_spend(start, end):
        result = await db.execute(
            select(
                Transaction.category_id,
                Category.name,
                Category.color,
                func.sum(Transaction.amount).label("total"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.amount < 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
                Transaction.is_duplicate == False,
                Category.is_income == False,
            )
            .group_by(Transaction.category_id, Category.name, Category.color)
        )
        return result.all()

    curr_rows = await category_spend(curr_start, curr_end)
    three_rows = await category_spend(three_month_start, three_month_end)

    three_map = {str(r.category_id): abs(float(r.total or 0)) / 3 for r in three_rows}

    opportunities = []
    for row in curr_rows:
        cat_id = str(row.category_id) if row.category_id else None
        curr_amt = abs(float(row.total or 0))
        avg = three_map.get(cat_id, 0.0) if cat_id else 0.0

        if avg > 0 and curr_amt > avg * 1.10:
            overage = curr_amt - avg
            pct_over = round((curr_amt - avg) / avg * 100, 1)
            opportunities.append({
                "category_id": cat_id,
                "category_name": row.name,
                "category_color": row.color,
                "current_month_spend": round(curr_amt, 2),
                "three_month_avg": round(avg, 2),
                "overage": round(overage, 2),
                "pct_over_average": pct_over,
                "potential_savings": round(overage, 2),
            })

    opportunities.sort(key=lambda x: -x["overage"])
    return opportunities


async def get_anomalies(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.transaction import Transaction
    from app.models.category import Category
    import math
    from datetime import timedelta

    today = date.today()
    window_start = today - timedelta(days=90)

    # Fetch all expense transactions in 90-day window
    result = await db.execute(
        select(
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.merchant_name,
            Transaction.amount,
            Transaction.category_id,
            Category.name.label("category_name"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= window_start,
            Transaction.date <= today,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
        )
        .order_by(Transaction.date.desc())
        .limit(2000)
    )
    rows = result.all()

    # Group by category_id
    by_cat: dict[str, list] = {}
    for row in rows:
        cat_key = str(row.category_id) if row.category_id else "uncategorized"
        by_cat.setdefault(cat_key, []).append(row)

    anomalies = []
    for cat_key, txs in by_cat.items():
        amounts = [abs(float(tx.amount)) for tx in txs]
        if len(amounts) < 3:
            # Need at least 3 data points for meaningful std_dev
            continue

        mean = sum(amounts) / len(amounts)
        variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        threshold = mean + 2 * std_dev

        for tx, amt in zip(txs, amounts):
            if amt > threshold and threshold > 0:
                anomalies.append({
                    "transaction_id": str(tx.id),
                    "date": tx.date.isoformat(),
                    "description": tx.description,
                    "merchant_name": tx.merchant_name,
                    "amount": -amt,  # negative (expense)
                    "category_name": tx.category_name or "Uncategorized",
                    "category_id": str(tx.category_id) if tx.category_id else None,
                    "expected_max": round(threshold, 2),
                    "mean": round(mean, 2),
                    "std_dev": round(std_dev, 2),
                    "overage": round(amt - threshold, 2),
                })

    # Sort by overage descending (biggest anomaly first)
    anomalies.sort(key=lambda x: -x["overage"])
    return anomalies


async def get_budget_recommendations(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    from app.models.transaction import Transaction
    from app.models.category import Category
    from app.models.budget import Budget

    today = date.today()

    # Last 3 full months
    month_windows = []
    for months_ago in range(1, 4):
        m = today.month - months_ago
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        start = date(y, m, 1)
        end = date(y, m, calendar.monthrange(y, m)[1])
        month_windows.append((m, y, start, end))

    # Per-month spending by category
    monthly_spend: dict = {}  # cat_id -> {"name": ..., "color": ..., "months": {(m,y): amount}}
    for (m, y, start, end) in month_windows:
        result = await db.execute(
            select(
                Transaction.category_id,
                Category.name,
                Category.color,
                func.sum(Transaction.amount).label("total"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.amount < 0,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.pending == False,
                Transaction.is_hidden == False,
                Transaction.is_duplicate == False,
                Category.is_income == False,
            )
            .group_by(Transaction.category_id, Category.name, Category.color)
        )
        for row in result.all():
            cat_id = str(row.category_id)
            if cat_id not in monthly_spend:
                monthly_spend[cat_id] = {"name": row.name, "color": row.color, "months": {}}
            monthly_spend[cat_id]["months"][(m, y)] = abs(float(row.total or 0))

    # Fetch current budgets (current month)
    budget_result = await db.execute(
        select(Budget.category_id, Budget.amount).where(
            Budget.user_id == user_id,
            Budget.period_month == today.month,
            Budget.period_year == today.year,
        ).limit(500)
    )
    budgets = {str(row.category_id): float(row.amount) for row in budget_result.all()}

    recommendations = []

    for cat_id, info in monthly_spend.items():
        months_data = list(info["months"].values())
        if not months_data:
            continue

        avg = sum(months_data) / len(months_data)

        if cat_id not in budgets:
            # No budget → suggest creating one
            recommendations.append({
                "category_id": cat_id,
                "category_name": info["name"],
                "category_color": info["color"],
                "type": "create",
                "message": f"No budget set. Suggest ${avg:.0f}/mo based on 3-month average.",
                "suggested_amount": round(avg, 2),
                "current_budget": None,
            })
        else:
            limit = budgets[cat_id]
            # Check utilization each month
            utilizations = [spend / limit for spend in months_data if limit > 0]

            if all(u < 0.70 for u in utilizations) and len(utilizations) == 3:
                # Consistently under 70% → suggest lowering
                recommendations.append({
                    "category_id": cat_id,
                    "category_name": info["name"],
                    "category_color": info["color"],
                    "type": "lower",
                    "message": f"Budget of ${limit:.0f} is consistently over-allocated. Suggest ${avg:.0f}/mo.",
                    "suggested_amount": round(avg, 2),
                    "current_budget": limit,
                })
            elif all(u > 1.0 for u in utilizations) and len(utilizations) == 3:
                # Consistently exceeded → suggest raising
                recommendations.append({
                    "category_id": cat_id,
                    "category_name": info["name"],
                    "category_color": info["color"],
                    "type": "raise",
                    "message": f"Budget of ${limit:.0f} is consistently exceeded. Suggest ${avg:.0f}/mo.",
                    "suggested_amount": round(avg, 2),
                    "current_budget": limit,
                })

    # Sort: create first, then raise, then lower; by suggested_amount desc
    type_order = {"create": 0, "raise": 1, "lower": 2}
    recommendations.sort(key=lambda x: (type_order.get(x["type"], 3), -x["suggested_amount"]))
    return recommendations


async def get_health_score(user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.transaction import Transaction
    from app.models.category import Category
    from app.models.budget import Budget
    from app.models.financial_account import FinancialAccount
    from app.models.recurring_transaction import RecurringTransaction

    today = date.today()

    # Helper: 3 prior months ranges
    def prior_months(n=3):
        windows = []
        for months_ago in range(1, n + 1):
            m = today.month - months_ago
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            start = date(y, m, 1)
            end = date(y, m, calendar.monthrange(y, m)[1])
            windows.append((m, y, start, end))
        return windows

    windows = prior_months(3)
    earliest_start = windows[-1][2]
    latest_end = windows[0][3]

    # --- Budget adherence ---
    # For each (category, month), check if spend <= budget
    adherent_count = 0
    total_count = 0
    for (m, y, start, end) in windows:
        budget_result = await db.execute(
            select(Budget.category_id, Budget.amount).where(
                Budget.user_id == user_id,
                Budget.period_month == m,
                Budget.period_year == y,
            ).limit(500)
        )
        budgets_for_month = {str(r.category_id): float(r.amount) for r in budget_result.all()}

        if not budgets_for_month:
            continue

        spend_result = await db.execute(
            select(
                Transaction.category_id,
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
            )
            .group_by(Transaction.category_id)
        )
        spend_map = {str(r.category_id): abs(float(r.total or 0)) for r in spend_result.all()}

        for cat_id, limit in budgets_for_month.items():
            total_count += 1
            spent = spend_map.get(cat_id, 0.0)
            if spent <= limit:
                adherent_count += 1

    adherence_score = (adherent_count / total_count * 100) if total_count > 0 else 50.0

    # --- Savings rate ---
    inc_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.amount > 0,
            Transaction.date >= earliest_start,
            Transaction.date <= latest_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
        )
    )
    total_income = float(inc_result.scalar() or 0)

    exp_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= earliest_start,
            Transaction.date <= latest_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
        )
    )
    total_expenses = abs(float(exp_result.scalar() or 0))

    savings_rate = (total_income - total_expenses) / total_income if total_income > 0 else 0
    savings_score = min(savings_rate / 0.20, 1.0) * 100  # 20% savings = full score

    # --- Debt-to-income ---
    LIABILITY_TYPES = {"credit", "loan", "mortgage", "student_loan", "auto", "line_of_credit", "other_liability"}
    acct_result = await db.execute(
        select(FinancialAccount.account_type, func.sum(FinancialAccount.balance_current).label("total"))
        .where(FinancialAccount.user_id == user_id, FinancialAccount.is_active == True)
        .group_by(FinancialAccount.account_type)
    )
    acct_rows = acct_result.all()

    total_debt = sum(abs(float(r.total or 0)) for r in acct_rows if r.account_type in LIABILITY_TYPES)
    liquid = sum(float(r.total or 0) for r in acct_rows if r.account_type not in LIABILITY_TYPES)

    monthly_income = total_income / 3 if total_income > 0 else 1.0
    dti = total_debt / (monthly_income * 12) if monthly_income > 0 else 0
    dti_score = max(0, (1 - dti / 2.0)) * 100  # 0 debt = 100, 2x annual income = 0

    # --- Emergency fund ---
    monthly_expenses = total_expenses / 3 if total_expenses > 0 else 1.0
    emergency_months = liquid / monthly_expenses if monthly_expenses > 0 else 0
    emergency_score = min(emergency_months / 6.0, 1.0) * 100  # 6 months = full score

    # --- Subscription ratio ---
    sub_result = await db.execute(
        select(RecurringTransaction.average_amount, RecurringTransaction.frequency).where(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_subscription == True,
            RecurringTransaction.is_active == True,
        ).limit(500)
    )
    sub_rows = sub_result.all()

    FREQ_MONTHLY = {"monthly": 1, "weekly": 4.33, "biweekly": 2.17, "quarterly": 1/3, "annual": 1/12}
    total_monthly_subs = sum(
        abs(float(r.average_amount or 0)) * FREQ_MONTHLY.get(r.frequency, 1)
        for r in sub_rows
    )
    sub_ratio = total_monthly_subs / monthly_income if monthly_income > 0 else 0
    sub_score = max(0, (1 - sub_ratio / 0.20)) * 100  # 0% = 100, 20% = 0

    # --- Composite score ---
    composite = (
        adherence_score * 0.30 +
        savings_score * 0.25 +
        dti_score * 0.20 +
        emergency_score * 0.15 +
        sub_score * 0.10
    )

    return {
        "overall_score": round(composite, 1),
        "components": {
            "budget_adherence": {
                "score": round(adherence_score, 1),
                "weight": 30,
                "label": "Budget Adherence",
                "detail": f"{adherent_count}/{total_count} categories within budget (last 3 months)",
            },
            "savings_rate": {
                "score": round(savings_score, 1),
                "weight": 25,
                "label": "Savings Rate",
                "detail": f"{savings_rate*100:.1f}% savings rate (target: 20%)",
            },
            "debt_to_income": {
                "score": round(dti_score, 1),
                "weight": 20,
                "label": "Debt-to-Income",
                "detail": f"${total_debt:,.0f} debt vs ${monthly_income * 12:,.0f} annual income",
            },
            "emergency_fund": {
                "score": round(emergency_score, 1),
                "weight": 15,
                "label": "Emergency Fund",
                "detail": f"{emergency_months:.1f} months of expenses covered (target: 6)",
            },
            "subscription_ratio": {
                "score": round(sub_score, 1),
                "weight": 10,
                "label": "Subscription Ratio",
                "detail": f"${total_monthly_subs:.0f}/mo in subscriptions ({sub_ratio*100:.1f}% of income)",
            },
        },
    }


async def get_insights_summary(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Aggregate top insights from all engines, sorted by impact."""
    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    async def safe(coro, default):
        try:
            return await coro
        except Exception as exc:
            logger.exception("Insight sub-function failed: %s", exc)
            return default

    # Run sequentially — SQLAlchemy async sessions don't support concurrent access
    spending_changes = await safe(get_spending_changes(user_id, db), [])
    anomalies = await safe(get_anomalies(user_id, db), [])
    forecast = await safe(get_forecast(user_id, db), {"categories": []})
    savings_opps = await safe(get_savings_opportunities(user_id, db), [])
    health = await safe(get_health_score(user_id, db), {"overall_score": 50, "components": {}})

    insights = []

    # Health score insight (always shown)
    score = health["overall_score"]
    score_label = "Excellent" if score >= 80 else "Good" if score >= 65 else "Fair" if score >= 50 else "Needs attention"
    insights.append({
        "type": "health_score",
        "priority": 1 if score < 50 else 3,
        "icon": "heart",
        "title": f"Financial Health: {score_label} ({score:.0f}/100)",
        "description": f"Your overall financial health score is {score:.0f} out of 100.",
        "action_url": "/dashboard",
        "data": {"score": score},
    })

    # Largest significant spending increase
    significant_increases = [c for c in spending_changes if c["significant"] and c["direction"] == "up"]
    if significant_increases:
        top = significant_increases[0]
        insights.append({
            "type": "spending_increase",
            "priority": 2,
            "icon": "trending-up",
            "title": f"{top['category_name']} spending up {top['pct_vs_prior_month']:.0f}%",
            "description": f"You spent ${top['current_month_spend']:.0f} this month vs ${top['prior_month_spend']:.0f} last month.",
            "action_url": "/transactions",
            "data": top,
        })

    # Anomalies (up to 1 alert)
    if anomalies:
        a = anomalies[0]
        insights.append({
            "type": "anomaly",
            "priority": 2,
            "icon": "alert-triangle",
            "title": f"Unusual purchase at {a['merchant_name'] or a['description']}",
            "description": f"${abs(a['amount']):.2f} — ${a['overage']:.2f} above your typical spend in {a['category_name']}.",
            "action_url": "/transactions",
            "data": a,
        })

    # Top savings opportunity
    if savings_opps:
        s = savings_opps[0]
        insights.append({
            "type": "savings_opportunity",
            "priority": 2,
            "icon": "piggy-bank",
            "title": f"Save up to ${s['potential_savings']:.0f} on {s['category_name']}",
            "description": f"You're {s['pct_over_average']:.0f}% over your 3-month average in {s['category_name']}.",
            "action_url": "/budgets",
            "data": s,
        })

    # Forecast warning
    over_budget_cats = [c for c in forecast.get("categories", []) if c["status"] == "over_budget"]
    if over_budget_cats:
        cat = over_budget_cats[0]
        insights.append({
            "type": "forecast_warning",
            "priority": 2,
            "icon": "calendar",
            "title": f"{cat['category_name']} projected to exceed budget",
            "description": f"At your current pace, you'll spend ${cat['projected_month_total']:.0f} vs ${cat['budget_limit']:.0f} budget.",
            "action_url": "/budgets",
            "data": cat,
        })

    # Sort by priority (lower = more urgent), limit to 5
    insights.sort(key=lambda x: x["priority"])
    return insights[:5]


async def get_forecast(user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.transaction import Transaction
    from app.models.category import Category
    from app.models.budget import Budget

    today = date.today()
    days_elapsed = today.day  # days since start of month (including today)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_remaining = days_in_month - days_elapsed

    curr_start = date(today.year, today.month, 1)
    curr_end = today

    # Current month spending by category
    spend_result = await db.execute(
        select(
            Transaction.category_id,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.date >= curr_start,
            Transaction.date <= curr_end,
            Transaction.pending == False,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Category.is_income == False,
        )
        .group_by(Transaction.category_id, Category.name, Category.color)
    )
    spend_rows = spend_result.all()

    # Budget amounts for current month
    budget_result = await db.execute(
        select(Budget.category_id, Budget.amount).where(
            Budget.user_id == user_id,
            Budget.period_month == today.month,
            Budget.period_year == today.year,
        )
    )
    budgets = {str(row.category_id): float(row.amount) for row in budget_result.all()}

    categories = []
    total_spent = 0.0
    total_projected = 0.0

    for row in spend_rows:
        spent = abs(float(row.total or 0))
        daily_rate = spent / days_elapsed if days_elapsed > 0 else 0
        projected = round(daily_rate * days_in_month, 2)
        cat_id = str(row.category_id) if row.category_id else None
        budget_limit = budgets.get(cat_id) if cat_id else None

        status = "on_track"
        if budget_limit and projected > budget_limit:
            status = "over_budget"
        elif budget_limit and projected > budget_limit * 0.9:
            status = "near_limit"

        categories.append({
            "category_id": cat_id,
            "category_name": row.name,
            "category_color": row.color,
            "spent_so_far": round(spent, 2),
            "daily_rate": round(daily_rate, 2),
            "projected_month_total": projected,
            "budget_limit": budget_limit,
            "status": status,
        })

        total_spent += spent
        total_projected += projected

    overall_daily_rate = total_spent / days_elapsed if days_elapsed > 0 else 0

    return {
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "days_in_month": days_in_month,
        "total_spent_so_far": round(total_spent, 2),
        "total_projected": round(total_projected, 2),
        "overall_daily_rate": round(overall_daily_rate, 2),
        "categories": categories,
    }
