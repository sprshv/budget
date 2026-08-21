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
from decimal import Decimal
from uuid import uuid4
from datetime import date


@pytest.mark.anyio
async def test_annual_summary_sorts_by_annual_cost_descending():
    from app.services.recurring_service import get_annual_summary

    # Mock list_subscriptions to return two subs with different annual costs
    cheap_sub = {
        "id": str(uuid4()), "merchant_name": "Spotify", "average_amount": 9.99,
        "frequency": "monthly", "monthly_cost": 9.99, "annual_cost": 119.88,
        "is_subscription": True, "is_bill": False, "is_active": True,
        "next_expected_date": None, "days_until_due": None,
        "last_date": None, "description": None, "remind_days_before": 3,
        "alert_enabled": True, "category_id": None,
    }
    expensive_sub = {
        "id": str(uuid4()), "merchant_name": "Adobe CC", "average_amount": 54.99,
        "frequency": "monthly", "monthly_cost": 54.99, "annual_cost": 659.88,
        "is_subscription": True, "is_bill": False, "is_active": True,
        "next_expected_date": None, "days_until_due": None,
        "last_date": None, "description": None, "remind_days_before": 3,
        "alert_enabled": True, "category_id": None,
    }

    mock_db = AsyncMock()

    with patch("app.services.recurring_service.list_subscriptions", return_value=[cheap_sub, expensive_sub]):
        result = await get_annual_summary(uuid4(), mock_db)

    assert result["total_annual"] == round(119.88 + 659.88, 2)
    # Most expensive should be first
    assert result["subscriptions_by_cost"][0]["merchant_name"] == "Adobe CC"
    assert result["subscriptions_by_cost"][1]["merchant_name"] == "Spotify"
    assert result["count"] == 2


@pytest.mark.anyio
async def test_annual_summary_empty_returns_zeros():
    from app.services.recurring_service import get_annual_summary

    mock_db = AsyncMock()

    with patch("app.services.recurring_service.list_subscriptions", return_value=[]):
        result = await get_annual_summary(uuid4(), mock_db)

    assert result["total_annual"] == 0.0
    assert result["total_monthly"] == 0.0
    assert result["count"] == 0
    assert result["subscriptions_by_cost"] == []
    assert result["top3_annual_savings"] == 0.0
