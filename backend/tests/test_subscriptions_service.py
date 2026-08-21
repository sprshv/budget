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


def test_monthly_cost_monthly_frequency():
    from app.services.recurring_service import _monthly_cost
    assert _monthly_cost(15.99, "monthly") == 15.99


def test_monthly_cost_annual_frequency():
    from app.services.recurring_service import _monthly_cost
    # $120/year = $10/month
    assert _monthly_cost(120.0, "annual") == 10.0


def test_monthly_cost_weekly_frequency():
    from app.services.recurring_service import _monthly_cost
    # $10/week * 52 / 12 = $43.33
    result = _monthly_cost(10.0, "weekly")
    assert abs(result - 43.33) < 0.01


def test_annual_cost_monthly_frequency():
    from app.services.recurring_service import _annual_cost
    assert _annual_cost(9.99, "monthly") == 119.88


def test_annual_cost_annual_frequency():
    from app.services.recurring_service import _annual_cost
    assert _annual_cost(99.0, "annual") == 99.0


@pytest.mark.anyio
async def test_get_subscriptions_summary_totals():
    from app.services.recurring_service import get_subscriptions_summary

    # Two monthly subscriptions: $10 and $20
    def _make_sub(amount):
        s = MagicMock()
        s.id = uuid4()
        s.user_id = uuid4()
        s.merchant_name = "Service"
        s.description = None
        s.average_amount = Decimal(str(amount))
        s.currency = "USD"
        s.frequency = "monthly"
        s.last_date = date(2025, 7, 1)
        s.next_expected_date = date(2025, 8, 1)
        s.is_subscription = True
        s.is_bill = False
        s.is_active = True
        s.remind_days_before = 3
        s.alert_enabled = True
        s.category_id = None
        return s

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [_make_sub(10.0), _make_sub(20.0)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_subscriptions_summary(uuid4(), mock_db)

    assert result["total_monthly"] == 30.0
    assert result["total_annual"] == 360.0
    assert result["count"] == 2
    assert len(result["subscriptions"]) == 2
