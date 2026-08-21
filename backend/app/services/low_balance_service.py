import logging
from datetime import datetime, timezone, timedelta
import uuid
from sqlalchemy import select
from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)

LOW_BALANCE_TYPES = {"checking", "savings"}
DEFAULT_THRESHOLD = 100.0


async def check_low_balances(user_id: uuid.UUID, db) -> None:
    from app.models.financial_account import FinancialAccount
    from app.models.notification import Notification

    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.user_id == user_id,
            FinancialAccount.is_active == True,
            FinancialAccount.account_type.in_(LOW_BALANCE_TYPES),
        ).limit(50)
    )
    accounts = result.scalars().all()

    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    for account in accounts:
        try:
            balance = float(account.balance_available or account.balance_current or 0)
            if balance >= DEFAULT_THRESHOLD:
                continue

            # Dedup: already notified in the last 24 hours for this account?
            dedup_result = await db.execute(
                select(Notification.id).where(
                    Notification.user_id == user_id,
                    Notification.type == "low_balance",
                    Notification.created_at >= cutoff,
                    Notification.notif_metadata["account_id"].astext == str(account.id),
                ).limit(1)
            )
            existing = dedup_result.scalar_one_or_none()
            if existing is not None:
                continue

            account_name = account.name or account.account_type or "Account"
            await create_notification(
                db=db,
                user_id=user_id,
                notif_type="low_balance",
                title=f"Low balance: {account_name}",
                body=f"Your {account_name} balance is ${balance:.2f}, which is below your $100 threshold.",
                notif_metadata={"account_id": str(account.id), "balance": balance},
            )
        except Exception as e:
            logger.error(f"Low balance check failed for account {account.id}: {e}")
