import logging
import uuid

from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)

LARGE_PURCHASE_THRESHOLD = 500.0


async def check_large_purchase(
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    amount: float,
    description: str,
    merchant_name: str,
    db,
) -> None:
    """Called after transaction insert. Creates notification if amount exceeds threshold."""
    if abs(amount) < LARGE_PURCHASE_THRESHOLD:
        return

    merchant = merchant_name or description or "Unknown merchant"
    amt_str = f"${abs(amount):,.2f}"

    try:
        await create_notification(
            db=db,
            user_id=user_id,
            notif_type="large_purchase",
            title=f"Large purchase: {amt_str}",
            body=f"{merchant} — {amt_str} was charged. Let us know if this wasn't you.",
            notif_metadata={"transaction_id": str(transaction_id), "amount": abs(amount)},
        )
    except Exception as e:
        logger.error(f"Large purchase notification failed for tx {transaction_id}: {e}")
