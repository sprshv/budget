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
from datetime import date


def _make_bill(days_until=5):
    today = date.today()
    from datetime import timedelta
    bill = MagicMock()
    bill.id = uuid4()
    bill.user_id = uuid4()
    bill.merchant_name = "Electric Company"
    bill.description = "Monthly electricity"
    bill.average_amount = Decimal("95.00")
    bill.currency = "USD"
    bill.frequency = "monthly"
    bill.last_date = today - timedelta(days=25)
    bill.next_expected_date = today + timedelta(days=days_until)
    bill.is_subscription = False
    bill.is_bill = True
    bill.is_active = True
    bill.remind_days_before = 3
    bill.alert_enabled = True
    bill.category_id = None
    return bill


@pytest.mark.anyio
async def test_list_bills_returns_sorted_list():
    from app.services.recurring_service import list_bills

    bill1 = _make_bill(days_until=2)
    bill2 = _make_bill(days_until=10)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [bill1, bill2]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await list_bills(uuid4(), mock_db)

    assert len(result) == 2
    assert result[0]["days_until_due"] == 2
    assert result[1]["days_until_due"] == 10
    assert result[0]["is_bill"] is True


@pytest.mark.anyio
async def test_mark_bill_paid_advances_next_date():
    from app.services.recurring_service import mark_bill_paid

    bill = _make_bill(days_until=2)
    original_next = bill.next_expected_date

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = bill

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    async def mock_refresh(obj):
        pass  # bill is already updated in-place

    mock_db.refresh = mock_refresh

    result = await mark_bill_paid(bill.id, bill.user_id, mock_db)

    # next_expected_date should be advanced by ~30 days from today
    today = date.today()
    assert bill.last_date == today
    assert bill.next_expected_date > today
    assert bill.next_expected_date > original_next


@pytest.mark.anyio
async def test_mark_bill_paid_not_found_raises_404():
    from app.services.recurring_service import mark_bill_paid
    from fastapi import HTTPException

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await mark_bill_paid(uuid4(), uuid4(), mock_db)

    assert exc_info.value.status_code == 404
