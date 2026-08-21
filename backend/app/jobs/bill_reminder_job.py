import logging
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)


async def check_bill_reminders(db: AsyncSession) -> int:
    """
    Check all active bills with alert_enabled=True.
    For each bill where next_expected_date is within remind_days_before days,
    create a notification if one hasn't been sent in the current cycle.
    Returns count of notifications created.
    """
    from app.models.recurring_transaction import RecurringTransaction
    from app.models.notification import Notification

    today = date.today()
    created = 0

    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.is_bill == True,
            RecurringTransaction.is_active == True,
            RecurringTransaction.alert_enabled == True,
            RecurringTransaction.next_expected_date.isnot(None),
        ).limit(200)
    )
    bills = result.scalars().all()

    for bill in bills:
        try:
            days_until = (bill.next_expected_date - today).days
            remind_days = bill.remind_days_before or 3
            if days_until < 0 or days_until > remind_days:
                continue

            # Dedup: check if we already have a notification for this bill in this cycle
            # "This cycle" = a notification created within the last remind_days+1 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=remind_days + 1)

            existing_result = await db.execute(
                select(Notification.id).where(
                    Notification.user_id == bill.user_id,
                    Notification.type == "bill_reminder",
                    Notification.notif_metadata["recurring_id"].astext == str(bill.id),
                    Notification.created_at >= cutoff,
                )
            )
            if existing_result.scalar_one_or_none() is not None:
                continue  # already sent for this cycle

            name = bill.merchant_name or bill.description or "Bill"
            amount = abs(float(bill.average_amount or 0))
            due_str = bill.next_expected_date.strftime("%b %d")

            title = f"{name} due {due_str}"
            body = f"${amount:.2f} payment due in {days_until} day{'s' if days_until != 1 else ''}."

            await create_notification(
                db=db,
                user_id=bill.user_id,
                notif_type="bill_reminder",
                title=title,
                body=body,
                notif_metadata={"recurring_id": str(bill.id), "due_date": bill.next_expected_date.isoformat()},
            )
            created += 1
        except Exception as e:
            logger.error(f"Bill reminder job: failed to process bill {bill.id}: {e}")

    logger.info(f"Bill reminder job: {created} notifications created")
    return created


async def run_bill_reminders() -> None:
    """Entry point called by APScheduler."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await check_bill_reminders(db)
        except Exception as e:
            logger.error(f"Bill reminder job failed: {e}")
