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

def _make_budget(amount="600.00", rollover="0.00"):
    b = MagicMock()
    b.id = uuid4()
    b.category_id = uuid4()
    b.amount = Decimal(amount)
    b.rollover_amount = Decimal(rollover)
    return b

@pytest.mark.anyio
async def test_forecast_will_exceed_when_on_pace_to_overspend():
    from app.services.budget_service import get_spending_forecast

    budget = _make_budget(amount="300.00")
    # 10 days elapsed, spent $200 → daily rate $20 → projected $620 for 31-day month → exceeds $300
    row = MagicMock()
    row.category_id = budget.category_id
    row.total = Decimal("-200.00")

    txn_result = MagicMock()
    txn_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=txn_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        with patch("app.services.budget_service.date") as mock_date:
            mock_date.today.return_value = MagicMock(day=10, month=8, year=2026)
            result = await get_spending_forecast(uuid4(), 8, 2026, mock_db)

    assert len(result) == 1
    assert result[0]["will_exceed"] is True
    assert result[0]["spent_so_far"] == 200.0

@pytest.mark.anyio
async def test_forecast_will_not_exceed_when_under_pace():
    from app.services.budget_service import get_spending_forecast

    budget = _make_budget(amount="600.00")
    # 15 days elapsed, spent $100 → daily rate ~$6.67 → projected ~$206 for 31 days → under $600
    row = MagicMock()
    row.category_id = budget.category_id
    row.total = Decimal("-100.00")

    txn_result = MagicMock()
    txn_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=txn_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        with patch("app.services.budget_service.date") as mock_date:
            mock_date.today.return_value = MagicMock(day=15, month=8, year=2026)
            result = await get_spending_forecast(uuid4(), 8, 2026, mock_db)

    assert result[0]["will_exceed"] is False

@pytest.mark.anyio
async def test_forecast_returns_empty_for_no_budgets():
    from app.services.budget_service import get_spending_forecast

    mock_db = AsyncMock()
    with patch("app.services.budget_service.list_budgets", return_value=[]):
        result = await get_spending_forecast(uuid4(), 8, 2026, mock_db)

    assert result == []
    mock_db.execute.assert_not_called()

@pytest.mark.anyio
async def test_forecast_zero_spend_produces_zero_projected():
    from app.services.budget_service import get_spending_forecast

    budget = _make_budget(amount="500.00")
    txn_result = MagicMock()
    txn_result.all.return_value = []  # no spending yet

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=txn_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        with patch("app.services.budget_service.date") as mock_date:
            mock_date.today.return_value = MagicMock(day=10, month=8, year=2026)
            result = await get_spending_forecast(uuid4(), 8, 2026, mock_db)

    assert result[0]["projected_total"] == 0.0
    assert result[0]["will_exceed"] is False
