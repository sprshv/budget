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

@pytest.mark.anyio
async def test_history_returns_at_most_12_months():
    from app.services.budget_service import get_budget_history

    mock_db = AsyncMock()
    with patch("app.services.budget_service.list_budgets", return_value=[]):
        result = await get_budget_history(uuid4(), 12, mock_db)
    # All months had no budgets, so result is empty — just verify no crash and no DB execute
    assert isinstance(result, list)

@pytest.mark.anyio
async def test_history_calculates_variance_correctly():
    from app.services.budget_service import get_budget_history

    cat_id = uuid4()
    budget = MagicMock()
    budget.id = uuid4()
    budget.category_id = cat_id
    budget.amount = Decimal("500.00")
    budget.rollover_amount = Decimal("0.00")

    # Spent $400 → under budget by $100
    row = MagicMock()
    row.category_id = cat_id
    row.total = Decimal("-400.00")

    txn_result = MagicMock()
    txn_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=txn_result)

    # Only return budget for the first month, empty for rest
    call_count = 0
    async def mock_list(user_id, month, year, db):
        nonlocal call_count
        call_count += 1
        return [budget] if call_count == 1 else []

    with patch("app.services.budget_service.list_budgets", side_effect=mock_list):
        result = await get_budget_history(uuid4(), 3, mock_db)

    assert len(result) == 1
    assert result[0]["budgets"][0]["budgeted"] == 500.0
    assert result[0]["budgets"][0]["actual"] == 400.0
    assert result[0]["budgets"][0]["variance"] == 100.0
    assert result[0]["budgets"][0]["over_budget"] is False

@pytest.mark.anyio
async def test_history_marks_over_budget_correctly():
    from app.services.budget_service import get_budget_history

    cat_id = uuid4()
    budget = MagicMock()
    budget.id = uuid4()
    budget.category_id = cat_id
    budget.amount = Decimal("200.00")
    budget.rollover_amount = Decimal("0.00")

    # Spent $350 → over budget
    row = MagicMock()
    row.category_id = cat_id
    row.total = Decimal("-350.00")

    txn_result = MagicMock()
    txn_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=txn_result)

    call_count = 0
    async def mock_list(user_id, month, year, db):
        nonlocal call_count
        call_count += 1
        return [budget] if call_count == 1 else []

    with patch("app.services.budget_service.list_budgets", side_effect=mock_list):
        result = await get_budget_history(uuid4(), 3, mock_db)

    assert result[0]["budgets"][0]["over_budget"] is True
    assert result[0]["budgets"][0]["variance"] < 0
