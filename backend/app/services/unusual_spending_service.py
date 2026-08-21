import logging
import uuid

from sqlalchemy import select
from app.models.notification import Notification
from app.services.insights_service import get_anomalies
from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)


async def check_unusual_spending(user_id: uuid.UUID, db) -> None:
    """Run anomaly detection and notify for any newly-flagged transactions."""
    try:
        anomalies = await get_anomalies(user_id, db)
    except Exception as e:
        logger.error(f"Anomaly detection failed for user {user_id}: {e}")
        return

    for anomaly in anomalies:
        try:
            tx_id = anomaly["transaction_id"]

            # Dedup: already notified for this transaction?
            dedup = await db.execute(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.type == "unusual_spending",
                    Notification.notif_metadata["transaction_id"].astext == tx_id,
                ).limit(1)
            )
            if dedup.scalars().first():
                continue

            merchant = anomaly.get("merchant_name") or anomaly.get("description") or "Unknown"
            amount = abs(anomaly.get("amount", 0))
            category = anomaly.get("category_name", "Unknown")
            expected = anomaly.get("expected_max", 0)

            await create_notification(
                db=db,
                user_id=user_id,
                notif_type="unusual_spending",
                title=f"Unusual purchase: {merchant}",
                body=f"${amount:.2f} in {category} — your typical max is ${expected:.2f}.",
                notif_metadata={"transaction_id": tx_id, "overage": anomaly.get("overage", 0)},
            )
        except Exception as e:
            logger.error(
                f"Unusual spending notification failed for tx {anomaly.get('transaction_id')}: {e}"
            )
