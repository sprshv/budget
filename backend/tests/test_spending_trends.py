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


@pytest.mark.anyio
async def test_spending_trends_returns_6_months():
    from app.services.dashboard_service import get_spending_trends

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        # Alternate: odd calls = income query, even = expense query
        if call_count % 2 == 1:
            result.scalar.return_value = Decimal("2000.00")
        else:
            result.scalar.return_value = Decimal("-800.00")
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_spending_trends(uuid4(), mock_db)

    assert len(result) == 6
    months = [r["month"] for r in result]
    assert months == sorted(months)
    # All months have income and expenses keys
    for m in result:
        assert "month" in m
        assert "income" in m
        assert "expenses" in m


@pytest.mark.anyio
async def test_spending_trends_expenses_are_positive():
    from app.services.dashboard_service import get_spending_trends

    async def mock_execute(query):
        result = MagicMock()
        result.scalar.return_value = Decimal("-500.00")  # negative in DB
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_spending_trends(uuid4(), mock_db)

    # Expenses must always be returned as positive values
    for m in result:
        assert m["expenses"] >= 0
