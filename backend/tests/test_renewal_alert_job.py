import sys
from unittest.mock import MagicMock
sys.modules.setdefault("plaid", MagicMock())
sys.modules.setdefault("plaid.api", MagicMock())
sys.modules.setdefault("plaid.api.plaid_api", MagicMock())
sys.modules.setdefault("plaid.model", MagicMock())
sys.modules.setdefault("plaid.model.link_token_create_request", MagicMock())
sys.modules.setdefault("plaid.configuration", MagicMock())
sys.modules.setdefault("plaid.api_client", MagicMock())

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4
from datetime import date, timedelta


def _make_sub(days_until=2, remind_days_before=3):
    today = date.today()
    sub = MagicMock()
    sub.id = uuid4()
    sub.user_id = uuid4()
    sub.merchant_name = "Netflix"
    sub.average_amount = Decimal("15.99")
    sub.next_expected_date = today + timedelta(days=days_until)
    sub.is_subscription = True
    sub.is_active = True
    sub.alert_enabled = True
    sub.remind_days_before = remind_days_before
    return sub


@pytest.mark.anyio
async def test_check_renewal_alerts_creates_notification_when_due_soon():
    from app.jobs.renewal_alert_job import check_renewal_alerts

    sub = _make_sub(days_until=2, remind_days_before=3)

    # First execute: subscriptions query
    sub_result = MagicMock()
    sub_result.scalars.return_value.all.return_value = [sub]

    # Second execute: existing notification check → none found
    existing_result = MagicMock()
    existing_result.scalar.return_value = None

    call_count = 0
    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sub_result
        return existing_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    result = await check_renewal_alerts(mock_db)

    assert result == 1
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_check_renewal_alerts_skips_when_not_due_soon():
    from app.jobs.renewal_alert_job import check_renewal_alerts

    sub = _make_sub(days_until=10, remind_days_before=3)  # 10 days away, remind only 3 days before

    sub_result = MagicMock()
    sub_result.scalars.return_value.all.return_value = [sub]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=sub_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    result = await check_renewal_alerts(mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_check_renewal_alerts_skips_when_already_notified():
    from app.jobs.renewal_alert_job import check_renewal_alerts

    sub = _make_sub(days_until=1, remind_days_before=3)

    sub_result = MagicMock()
    sub_result.scalars.return_value.all.return_value = [sub]

    # Existing notification already exists
    existing_result = MagicMock()
    existing_result.scalar.return_value = uuid4()  # found existing

    call_count = 0
    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sub_result
        return existing_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    result = await check_renewal_alerts(mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
