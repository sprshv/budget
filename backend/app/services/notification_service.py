from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime, timezone
import uuid


NOTIFICATION_TYPES = [
    "budget_alert",
    "bill_reminder",
    "low_balance",
    "large_purchase",
    "unusual_spending",
    "weekly_summary",
    "monthly_summary",
]

DEFAULT_THRESHOLDS = {
    "low_balance": 100.0,
    "large_purchase": 500.0,
}


async def list_notifications(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    from app.models.notification import Notification

    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    notifs = result.scalars().all()

    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
    )
    unread_count = unread_result.scalar() or 0

    return {
        "notifications": [_format(n) for n in notifs],
        "unread_count": unread_count,
        "total": len(notifs),
    }


async def mark_read(
    notification_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> dict:
    from app.models.notification import Notification

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        return None

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return _format(notif)


async def mark_all_read(user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.notification import Notification

    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"success": True}


async def get_unread_count(user_id: uuid.UUID, db: AsyncSession) -> int:
    from app.models.notification import Notification

    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
    )
    return result.scalar() or 0


async def create_notification(
    user_id: uuid.UUID,
    notif_type: str,
    title: str,
    body: str,
    db: AsyncSession,
    notif_metadata: dict = None,
    metadata: dict = None,  # alias accepted by webhook router
) -> object:
    from app.models.notification import Notification

    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        body=body,
        notif_metadata=notif_metadata or metadata,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def get_preferences(user_id: uuid.UUID, db: AsyncSession) -> list:
    from app.models.notification_preference import NotificationPreference

    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    existing = {p.notification_type: p for p in result.scalars().all()}

    prefs = []
    for ntype in NOTIFICATION_TYPES:
        pref = existing.get(ntype)
        prefs.append({
            "notif_type": ntype,
            "push_enabled": pref.push_enabled if pref else True,
            "email_enabled": pref.email_enabled if pref else False,
            "threshold_amount": (
                float(pref.threshold_amount)
                if pref and pref.threshold_amount is not None
                else DEFAULT_THRESHOLDS.get(ntype)
            ),
        })
    return prefs


async def update_preferences(user_id: uuid.UUID, updates: list, db: AsyncSession) -> list:
    from app.models.notification_preference import NotificationPreference

    for upd in updates:
        ntype = upd.get("notif_type")
        if ntype not in NOTIFICATION_TYPES:
            continue

        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == ntype,
            )
        )
        pref = result.scalar_one_or_none()

        if pref is None:
            pref = NotificationPreference(user_id=user_id, notification_type=ntype)
            db.add(pref)

        if "push_enabled" in upd:
            pref.push_enabled = upd["push_enabled"]
        if "email_enabled" in upd:
            pref.email_enabled = upd["email_enabled"]
        if "threshold_amount" in upd:
            pref.threshold_amount = upd["threshold_amount"]

    await db.commit()
    return await get_preferences(user_id, db)


def _format(n) -> dict:
    return {
        "id": str(n.id),
        "type": n.type,
        "title": n.title,
        "message": n.body,  # model uses `body`; expose as `message` in the API
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "read_at": n.read_at.isoformat() if n.read_at else None,
    }
