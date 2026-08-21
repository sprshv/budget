from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
import uuid

from app.services.budget_service import get_budget_progress, list_budgets


async def apply_rollover_for_user(
    user_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> int:
    """
    For each rollover-enabled budget in the previous month:
    1. Calculate unused = max(0, effective_limit - spent)
    2. Find the matching budget in the current period
    3. Add unused to that budget's rollover_amount

    Returns count of budgets updated.
    """

    # Determine previous month
    if period_month == 1:
        prev_month, prev_year = 12, period_year - 1
    else:
        prev_month, prev_year = period_month - 1, period_year

    prev_progress = await get_budget_progress(user_id, prev_month, prev_year, db)
    if not prev_progress:
        return 0

    # Build rollover_enabled map from previous month budgets
    prev_budgets = await list_budgets(user_id, prev_month, prev_year, db)
    rollover_map = {str(b.category_id): b.rollover_enabled for b in prev_budgets}

    # Get current month budgets indexed by category_id
    curr_budgets = await list_budgets(user_id, period_month, period_year, db)
    curr_map = {str(b.category_id): b for b in curr_budgets}

    updated = 0
    for prog in prev_progress:
        cat_id_str = str(prog["category_id"])

        # Skip budgets with rollover disabled
        if not rollover_map.get(cat_id_str, False):
            continue

        # Unused = effective_limit - spent, floored at 0 (never carry negative)
        unused = max(
            Decimal("0.00"),
            Decimal(str(prog["effective_limit"])) - Decimal(str(prog["spent"])),
        )
        if unused <= 0:
            continue

        # Apply to current-month budget if it exists
        if cat_id_str in curr_map:
            curr_budget = curr_map[cat_id_str]
            curr_budget.rollover_amount = (
                Decimal(str(curr_budget.rollover_amount)) + unused
            )
            updated += 1
        # If no current-month budget for this category, skip silently

    if updated > 0:
        await db.commit()

    return updated


async def apply_rollover_all_users(
    period_month: int,
    period_year: int,
    db: AsyncSession,
) -> None:
    """Called by the sync job when a new month is detected."""
    import logging
    from app.models.user import User

    logger = logging.getLogger(__name__)

    result = await db.execute(select(User.id))
    user_ids = result.scalars().all()

    for user_id in user_ids:
        try:
            count = await apply_rollover_for_user(user_id, period_month, period_year, db)
            if count:
                logger.info(
                    f"Rollover: applied {count} budget(s) for user {user_id} "
                    f"({period_month}/{period_year})"
                )
        except Exception as e:
            # Per-user errors must not abort the job
            logger.error(f"Rollover failed for user {user_id}: {e}")
