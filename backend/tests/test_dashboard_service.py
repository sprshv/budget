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


def _make_row(account_type, total):
    row = MagicMock()
    row.account_type = account_type
    row.total = Decimal(str(total))
    return row


@pytest.mark.anyio
async def test_net_worth_calculates_correctly():
    from app.services.dashboard_service import get_net_worth

    rows = [
        _make_row("checking", "5000.00"),     # liquid
        _make_row("savings", "10000.00"),     # liquid
        _make_row("investment", "25000.00"),  # investments
        _make_row("credit", "-3000.00"),      # debt (abs)
    ]

    mock_result = MagicMock()
    mock_result.all.return_value = rows

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_net_worth(uuid4(), mock_db)

    assert result["liquid_assets"] == 15000.0
    assert result["investments"] == 25000.0
    assert result["total_debt"] == 3000.0
    assert result["net_total"] == 37000.0  # 15000 + 25000 - 3000


@pytest.mark.anyio
async def test_net_worth_zero_when_no_accounts():
    from app.services.dashboard_service import get_net_worth

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_net_worth(uuid4(), mock_db)

    assert result["liquid_assets"] == 0.0
    assert result["investments"] == 0.0
    assert result["total_debt"] == 0.0
    assert result["net_total"] == 0.0


@pytest.mark.anyio
async def test_net_worth_negative_when_debt_exceeds_assets():
    from app.services.dashboard_service import get_net_worth

    rows = [
        _make_row("checking", "1000.00"),
        _make_row("loan", "50000.00"),   # large liability
    ]

    mock_result = MagicMock()
    mock_result.all.return_value = rows

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_net_worth(uuid4(), mock_db)

    assert result["total_debt"] == 50000.0
    assert result["net_total"] == -49000.0


@pytest.mark.anyio
async def test_cash_flow_calculates_income_and_expenses():
    from app.services.dashboard_service import get_cash_flow
    from decimal import Decimal

    # DB returns income and expense sums. We mock 4 execute calls:
    # curr total, curr income, prev total, prev income
    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:   # curr total
            result.scalar.return_value = Decimal("1500.00")  # net = 3000 income - 1500 expenses
        elif call_count == 2:  # curr income
            result.scalar.return_value = Decimal("3000.00")
        elif call_count == 3:  # prev total
            result.scalar.return_value = Decimal("800.00")
        elif call_count == 4:  # prev income
            result.scalar.return_value = Decimal("2500.00")
        else:
            result.scalar.return_value = Decimal("0.00")
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_cash_flow(uuid4(), mock_db)

    assert "current_month" in result
    assert "previous_month" in result
    assert result["current_month"]["income"] == 3000.0
    assert result["current_month"]["net"] > 0  # income > expenses


@pytest.mark.anyio
async def test_cash_flow_handles_zero_previous_month():
    from app.services.dashboard_service import get_cash_flow
    from decimal import Decimal

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        result.scalar.return_value = Decimal("0.00")
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_cash_flow(uuid4(), mock_db)

    # When prev = 0, pct_change returns None (not a div-by-zero error)
    assert result["income_change_pct"] is None
    assert result["expense_change_pct"] is None


@pytest.mark.anyio
async def test_sparkline_unknown_account_returns_empty():
    from app.services.dashboard_service import get_account_sparkline

    # Ownership check returns None -> empty list
    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_scalar_result)

    result = await get_account_sparkline(uuid4(), uuid4(), mock_db)
    assert result == []


@pytest.mark.anyio
async def test_sparkline_returns_30_points():
    from app.services.dashboard_service import get_account_sparkline
    from datetime import date, timedelta

    # First execute: ownership check -> account found
    ownership_result = MagicMock()
    ownership_result.scalar.return_value = uuid4()

    # Second execute: transaction rows -> empty (all days fill with 0)
    tx_result = MagicMock()
    tx_result.all.return_value = []

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ownership_result
        return tx_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_account_sparkline(uuid4(), uuid4(), mock_db)
    assert len(result) == 30
    assert all(p["amount"] == 0.0 for p in result)
    # Dates are sequential ISO strings
    dates = [p["date"] for p in result]
    assert dates == sorted(dates)


@pytest.mark.anyio
async def test_recent_transactions_returns_list():
    from app.services.dashboard_service import get_recent_transactions
    from datetime import date

    row = MagicMock()
    row.id = uuid4()
    row.amount = Decimal("-45.00")
    row.date = date(2025, 8, 1)
    row.description = "Coffee Shop"
    row.merchant_name = "Starbucks"
    row.pending = False
    row.is_hidden = False
    row.is_duplicate = False
    row.category_name = "Food"
    row.category_color = "#ff0000"
    row.category_icon = "🍔"

    mock_result = MagicMock()
    mock_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_recent_transactions(uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["amount"] == -45.0
    assert result[0]["description"] == "Coffee Shop"
    assert result[0]["category_name"] == "Food"
