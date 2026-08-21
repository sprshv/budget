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
from unittest.mock import AsyncMock
from decimal import Decimal
from uuid import uuid4


@pytest.mark.anyio
async def test_income_summary_returns_correct_structure():
    from app.services.budget_service import get_income_summary

    # First call: budgets join (returns empty list)
    budget_result = MagicMock()
    budget_result.scalars.return_value.all.return_value = []

    # Second call: transaction sum ($2000 actual income)
    txn_scalar_result = MagicMock()
    txn_scalar_result.scalar.return_value = Decimal("2000.00")

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return budget_result
        return txn_scalar_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_income_summary(uuid4(), 8, 2026, mock_db)

    assert "planned_income" in result
    assert "actual_income" in result
    assert "variance" in result
    assert "period_month" in result
    assert result["period_month"] == 8
    assert result["actual_income"] == 2000.0


@pytest.mark.anyio
async def test_income_summary_variance_positive_when_ahead():
    from app.services.budget_service import get_income_summary

    # planned = 0 (no income budgets), actual = $3000 → variance = +3000
    budget_result = MagicMock()
    budget_result.scalars.return_value.all.return_value = []

    txn_scalar_result = MagicMock()
    txn_scalar_result.scalar.return_value = Decimal("3000.00")

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return budget_result
        return txn_scalar_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_income_summary(uuid4(), 8, 2026, mock_db)

    assert result["actual_income"] == 3000.0
    assert result["planned_income"] == 0.0
    assert result["variance"] >= 0


@pytest.mark.anyio
async def test_income_summary_handles_no_transactions():
    from app.services.budget_service import get_income_summary

    budget_result = MagicMock()
    budget_result.scalars.return_value.all.return_value = []

    txn_scalar_result = MagicMock()
    txn_scalar_result.scalar.return_value = None  # no income transactions

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return budget_result
        return txn_scalar_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_income_summary(uuid4(), 8, 2026, mock_db)

    assert result["actual_income"] == 0.0
    assert result["planned_income"] == 0.0
    assert result["variance"] == 0.0
