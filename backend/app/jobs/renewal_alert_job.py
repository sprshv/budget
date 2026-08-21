import logging
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_renewal_alerts(db: AsyncSession) -> int:
    """
    Check all active subscriptions with alert_enabled=True.
    For each subscription where next_expected_date is within remind_days_before days,
    create a notification if one hasn't been sent in the current cycle.
    Returns count of notifications created.
    """
    from app.models.recurring_transaction import RecurringTransaction
    from app.models.notification import Notification

    today = date.today()
    created = 0

    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.is_subscription == True,
            RecurringTransaction.is_active == True,
            RecurringTransaction.alert_enabled == True,
            RecurringTransaction.next_expected_date.isnot(None),
        )
    )
    subscriptions = result.scalars().all()

    from datetime import datetime, timezone, timedelta

    for sub in subscriptions:
        try:
            days_until = (sub.next_expected_date - today).days
            if days_until < 0 or days_until > sub.remind_days_before:
                continue

            # Check if we already have a notification for this subscription in this cycle
            # "This cycle" = a notification created within the last remind_days_before+1 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=(sub.remind_days_before or 3) + 1)

            existing_result = await db.execute(
                select(Notification.id).where(
                    Notification.user_id == sub.user_id,
                    Notification.type == "bill_reminder",
                    Notification.notif_metadata["recurring_id"].astext == str(sub.id),
                    Notification.created_at >= cutoff,
                )
            )
            if existing_result.scalar() is not None:
                continue  # already sent for this cycle

            # Create notification
            notif = Notification(
                user_id=sub.user_id,
                type="bill_reminder",
                title=f"{sub.merchant_name} renews in {days_until} day{'s' if days_until != 1 else ''}",
                body=f"Your {sub.merchant_name} subscription of ${float(sub.average_amount):.2f} is due on {sub.next_expected_date.strftime('%b %d')}.",
                notif_metadata={"recurring_id": str(sub.id), "amount": float(sub.average_amount)},
            )
            db.add(notif)
            created += 1
        except Exception as e:
            logger.error(f"Renewal alert job: failed to process subscription {sub.id}: {e}")

    if created > 0:
        await db.commit()

    logger.info(f"Renewal alert job: {created} notifications created")
    return created


async def run_renewal_alerts():
    """Entry point called by APScheduler."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await check_renewal_alerts(db)
        except Exception as e:
            logger.error(f"Renewal alert job failed: {e}")
