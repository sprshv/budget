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
from datetime import date


def test_detect_frequency_monthly():
    from app.services.recurring_service import _detect_frequency
    dates = [
        date(2025, 1, 1),
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 2),  # 1 day off — within tolerance
    ]
    assert _detect_frequency(dates) == "monthly"


def test_detect_frequency_weekly():
    from app.services.recurring_service import _detect_frequency
    dates = [
        date(2025, 1, 1),
        date(2025, 1, 8),
        date(2025, 1, 15),
        date(2025, 1, 22),
    ]
    assert _detect_frequency(dates) == "weekly"


def test_detect_frequency_too_few_dates_returns_none():
    from app.services.recurring_service import _detect_frequency
    assert _detect_frequency([date(2025, 1, 1)]) is None
    assert _detect_frequency([]) is None


def test_is_subscription_consistent_amounts():
    from app.services.recurring_service import _is_subscription
    # Netflix at $15.99 — very consistent
    assert _is_subscription([15.99, 15.99, 15.99, 15.99]) is True


def test_is_subscription_variable_amounts():
    from app.services.recurring_service import _is_subscription
    # Electricity bill — varies a lot
    assert _is_subscription([80.0, 120.0, 95.0, 150.0]) is False


def test_is_subscription_empty_returns_false():
    from app.services.recurring_service import _is_subscription
    assert _is_subscription([]) is False
