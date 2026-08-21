import logging
from datetime import date, datetime, timezone
from sqlalchemy import select
from app.models.financial_account import FinancialAccount
from app.services.transaction_sync_service import sync_account_transactions
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

_last_seen_month: int = None
_last_seen_year: int = None


async def _alert_large_purchases(user_id, db, since_time) -> None:
    """Check for newly synced large transactions and fire notifications with dedup."""
    from app.models.transaction import Transaction
    from app.models.notification import Notification
    from app.services.large_purchase_service import check_large_purchase

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.amount < -500,
            Transaction.created_at >= since_time,
            Transaction.is_hidden == False,
            Transaction.is_duplicate == False,
            Transaction.pending == False,
        ).limit(20)
    )
    new_txs = result.scalars().all()
    for tx in new_txs:
        dedup = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.type == "large_purchase",
                Notification.notif_metadata["transaction_id"].astext == str(tx.id),
            ).limit(1)
        )
        if dedup.scalars().first():
            continue
        await check_large_purchase(
            user_id, tx.id, float(tx.amount), tx.description, tx.merchant_name, db
        )


async def run_transaction_sync():
    """
    APScheduler job: pull new transactions for all active accounts.
    Runs every 4 hours.
    """
    global _last_seen_month, _last_seen_year
    today = date.today()
    current_month = today.month
    current_year = today.year

    if _last_seen_month is not None and (
        current_month != _last_seen_month or current_year != _last_seen_year
    ):
        # New month detected — apply rollover before syncing transactions
        logger.info(
            f"New month detected ({current_month}/{current_year}), running rollover"
        )
        from app.services.rollover_service import apply_rollover_all_users

        async with AsyncSessionLocal() as rollover_db:
            try:
                await apply_rollover_all_users(current_month, current_year, rollover_db)
            except Exception as e:
                logger.error(f"Rollover job error: {e}")
                # Rollover errors must not abort the sync job

    _last_seen_month = current_month
    _last_seen_year = current_year

    logger.info("Starting scheduled transaction sync")
    sync_start = datetime.now(timezone.utc)
    total_synced = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(FinancialAccount).where(
                    FinancialAccount.is_active == True,
                    FinancialAccount.sync_status != "reauth_required",
                    FinancialAccount.plaid_access_token.isnot(None),
                )
            )
            accounts = result.scalars().all()
            logger.info(f"Syncing {len(accounts)} accounts")

            for account in accounts:
                try:
                    count = await sync_account_transactions(
                        account, db, account.user_id
                    )
                    total_synced += count
                except Exception as e:
                    logger.error(f"Sync failed for account {account.id}: {e}")
                    errors += 1

        except Exception as e:
            logger.error(f"Sync job DB error: {e}")
            return

    logger.info(f"Sync complete: {total_synced} new transactions, {errors} errors")

    # Run recurring detection for each user whose accounts were synced
    synced_user_ids = list({account.user_id for account in accounts})
    async with AsyncSessionLocal() as detect_db:
        from app.services.recurring_service import detect_recurring_for_user
        for user_id in synced_user_ids:
            try:
                patterns = await detect_recurring_for_user(user_id, detect_db)
                logger.info(f"Recurring detection for user {user_id}: {patterns} patterns found")
            except Exception as e:
                logger.error(f"Recurring detection failed for user {user_id}: {e}")

    # Check budget alerts for each synced user
    async with AsyncSessionLocal() as alert_db:
        from app.services.budget_alert_service import check_budget_alerts
        for user_id in synced_user_ids:
            try:
                await check_budget_alerts(user_id, alert_db)
            except Exception as e:
                logger.error(f"Budget alert check failed for user {user_id}: {e}")

    # Check low balance alerts for each synced user
    async with AsyncSessionLocal() as low_balance_db:
        from app.services.low_balance_service import check_low_balances
        for user_id in synced_user_ids:
            try:
                await check_low_balances(user_id, low_balance_db)
            except Exception as e:
                logger.error(f"Low balance check failed for user {user_id}: {e}")

    # Check large purchase alerts for newly synced transactions
    async with AsyncSessionLocal() as large_purchase_db:
        for user_id in synced_user_ids:
            try:
                await _alert_large_purchases(user_id, large_purchase_db, sync_start)
            except Exception as e:
                logger.error(f"Large purchase alert check failed for user {user_id}: {e}")

    # Check unusual spending alerts for each synced user
    async with AsyncSessionLocal() as unusual_db:
        from app.services.unusual_spending_service import check_unusual_spending
        for user_id in synced_user_ids:
            try:
                await check_unusual_spending(user_id, unusual_db)
            except Exception as e:
                logger.error(f"Unusual spending check failed for user {user_id}: {e}")
