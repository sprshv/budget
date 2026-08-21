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
async def test_net_worth_history_returns_12_months():
    from app.services.dashboard_service import get_net_worth_history

    # First execute: account balances
    acct_result = MagicMock()
    row = MagicMock()
    row.account_type = "checking"
    row.total = Decimal("10000.00")
    acct_result.all.return_value = [row]

    # Subsequent 12 executes: monthly tx deltas (all 0)
    delta_result = MagicMock()
    delta_result.scalar.return_value = Decimal("0.00")

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return acct_result
        return delta_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_net_worth_history(uuid4(), mock_db)

    assert len(result) == 12
    # All snapshots should have the same net worth since delta=0
    assert all(s["net_worth"] == 10000.0 for s in result)
    # Months are in ascending order
    months = [s["month"] for s in result]
    assert months == sorted(months)


@pytest.mark.anyio
async def test_net_worth_history_applies_delta():
    from app.services.dashboard_service import get_net_worth_history

    # Current net worth = 10000
    acct_result = MagicMock()
    row = MagicMock()
    row.account_type = "checking"
    row.total = Decimal("10000.00")
    acct_result.all.return_value = [row]

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return acct_result
        # For months in the past, delta = 1000 (meaning 1000 was earned after that month)
        # So net worth at that past month = 10000 - 1000 = 9000
        result = MagicMock()
        result.scalar.return_value = Decimal("1000.00")
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_net_worth_history(uuid4(), mock_db)

    assert len(result) == 12
    # All months should show 9000 (current 10000 - delta 1000)
    assert all(s["net_worth"] == 9000.0 for s in result)
