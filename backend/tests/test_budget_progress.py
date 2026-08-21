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


def _make_budget(amount="500.00", rollover="0.00", threshold="0.80"):
    b = MagicMock()
    b.id = uuid4()
    b.category_id = uuid4()
    b.amount = Decimal(amount)
    b.rollover_amount = Decimal(rollover)
    b.alert_threshold = Decimal(threshold)
    return b


@pytest.mark.anyio
async def test_progress_status_ok():
    from app.services.budget_service import get_budget_progress

    budget = _make_budget(amount="500.00", threshold="0.80")
    # spent = 200 → 40% → ok
    row = MagicMock()
    row.category_id = budget.category_id
    row.total = Decimal("-200.00")

    spent_result = MagicMock()
    spent_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=spent_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        result = await get_budget_progress(uuid4(), 8, 2026, mock_db)

    assert len(result) == 1
    assert result[0]["status"] == "ok"
    assert result[0]["spent"] == 200.0
    assert result[0]["percentage"] == 40.0


@pytest.mark.anyio
async def test_progress_status_warning():
    from app.services.budget_service import get_budget_progress

    budget = _make_budget(amount="500.00", threshold="0.80")
    # spent = 450 → 90% → warning (>= 80%)
    row = MagicMock()
    row.category_id = budget.category_id
    row.total = Decimal("-450.00")

    spent_result = MagicMock()
    spent_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=spent_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        result = await get_budget_progress(uuid4(), 8, 2026, mock_db)

    assert result[0]["status"] == "warning"


@pytest.mark.anyio
async def test_progress_status_over():
    from app.services.budget_service import get_budget_progress

    budget = _make_budget(amount="500.00", threshold="0.80")
    # spent = 600 → 120% → over
    row = MagicMock()
    row.category_id = budget.category_id
    row.total = Decimal("-600.00")

    spent_result = MagicMock()
    spent_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=spent_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        result = await get_budget_progress(uuid4(), 8, 2026, mock_db)

    assert result[0]["status"] == "over"
    assert result[0]["remaining"] < 0


@pytest.mark.anyio
async def test_progress_with_rollover():
    from app.services.budget_service import get_budget_progress

    # Budget $400 + $100 rollover = $500 effective limit
    budget = _make_budget(amount="400.00", rollover="100.00", threshold="0.80")
    # spent = 420 → 420/500 = 84% → warning
    row = MagicMock()
    row.category_id = budget.category_id
    row.total = Decimal("-420.00")

    spent_result = MagicMock()
    spent_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=spent_result)

    with patch("app.services.budget_service.list_budgets", return_value=[budget]):
        result = await get_budget_progress(uuid4(), 8, 2026, mock_db)

    assert result[0]["effective_limit"] == 500.0
    assert result[0]["status"] == "warning"


@pytest.mark.anyio
async def test_progress_returns_empty_for_no_budgets():
    from app.services.budget_service import get_budget_progress

    mock_db = AsyncMock()
    with patch("app.services.budget_service.list_budgets", return_value=[]):
        result = await get_budget_progress(uuid4(), 8, 2026, mock_db)

    assert result == []
    mock_db.execute.assert_not_called()
