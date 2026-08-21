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
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4


def _make_bill(days_until=2, remind_days_before=3):
    today = date.today()
    bill = MagicMock()
    bill.id = uuid4()
    bill.user_id = uuid4()
    bill.merchant_name = "Electric Company"
    bill.description = "Electric bill"
    bill.average_amount = Decimal("-120.00")
    bill.next_expected_date = today + timedelta(days=days_until)
    bill.remind_days_before = remind_days_before
    bill.is_bill = True
    bill.is_active = True
    bill.alert_enabled = True
    return bill


@pytest.mark.anyio
async def test_bill_reminder_creates_notification_when_due_soon():
    """Bill due in 2 days with remind_days_before=3 — notification should be created."""
    from app.jobs.bill_reminder_job import check_bill_reminders

    bill = _make_bill(days_until=2, remind_days_before=3)

    # First execute: bills query
    bills_result = MagicMock()
    bills_result.scalars.return_value.all.return_value = [bill]

    # Second execute: dedup check — no prior notification found
    dedup_result = MagicMock()
    dedup_result.scalar_one_or_none.return_value = None

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return bills_result
        return dedup_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.jobs.bill_reminder_job.create_notification", new_callable=AsyncMock) as mock_create:
        result = await check_bill_reminders(mock_db)
        assert mock_create.called
        assert result == 1
        # Verify correct arguments passed
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["notif_type"] == "bill_reminder"
        assert "Electric Company" in call_kwargs["title"]


@pytest.mark.anyio
async def test_bill_reminder_skips_when_not_due_soon():
    """Bill due in 20 days with remind_days_before=3 — no notification should be created."""
    from app.jobs.bill_reminder_job import check_bill_reminders

    bill = _make_bill(days_until=20, remind_days_before=3)

    bills_result = MagicMock()
    bills_result.scalars.return_value.all.return_value = [bill]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=bills_result)

    with patch("app.jobs.bill_reminder_job.create_notification", new_callable=AsyncMock) as mock_create:
        result = await check_bill_reminders(mock_db)
        assert not mock_create.called
        assert result == 0
