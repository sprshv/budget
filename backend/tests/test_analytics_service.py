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


def _make_category_row(name, color, total, count):
    row = MagicMock()
    row.id = uuid4()
    row.name = name
    row.color = color
    row.total = Decimal(str(total))
    row.count = count
    return row


@pytest.mark.anyio
async def test_category_spending_returns_absolute_amounts():
    from app.services.analytics_service import get_category_spending

    rows = [
        _make_category_row("Food", "#ff0000", "-300.00", 15),
        _make_category_row("Transport", "#0000ff", "-100.00", 5),
    ]

    mock_result = MagicMock()
    mock_result.all.return_value = rows

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_category_spending(uuid4(), mock_db)

    assert "categories" in result
    assert "start_date" in result
    assert "end_date" in result
    # Amounts should be positive (abs of negative transaction amounts)
    for cat in result["categories"]:
        assert cat["amount"] >= 0


@pytest.mark.anyio
async def test_category_spending_empty_returns_empty_list():
    from app.services.analytics_service import get_category_spending

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_category_spending(uuid4(), mock_db)

    assert result["categories"] == []


@pytest.mark.anyio
async def test_category_spending_accepts_custom_date_range():
    from app.services.analytics_service import get_category_spending

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    start = date(2025, 1, 1)
    end = date(2025, 1, 31)
    result = await get_category_spending(uuid4(), mock_db, start, end)

    assert result["start_date"] == "2025-01-01"
    assert result["end_date"] == "2025-01-31"


@pytest.mark.anyio
async def test_merchant_spending_returns_positive_totals():
    from app.services.analytics_service import get_merchant_spending

    row = MagicMock()
    row.merchant_name = "Starbucks"
    row.total = Decimal("-85.50")
    row.count = 6

    mock_result = MagicMock()
    mock_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_merchant_spending(uuid4(), mock_db)

    assert len(result["merchants"]) == 1
    assert result["merchants"][0]["merchant_name"] == "Starbucks"
    assert result["merchants"][0]["total_spent"] == 85.5  # abs value
    assert result["merchants"][0]["transaction_count"] == 6


@pytest.mark.anyio
async def test_merchant_spending_empty_returns_empty_list():
    from app.services.analytics_service import get_merchant_spending

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_merchant_spending(uuid4(), mock_db)

    assert result["merchants"] == []


@pytest.mark.anyio
async def test_income_vs_expenses_returns_12_months():
    from app.services.analytics_service import get_income_vs_expenses

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count % 2 == 1:  # income queries
            result.scalar.return_value = Decimal("3000.00")
        else:  # expense queries
            result.scalar.return_value = Decimal("-2000.00")
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_income_vs_expenses(uuid4(), mock_db)

    assert len(result) == 12
    assert result[0]["income"] == 3000.0
    assert result[0]["expenses"] == 2000.0
    assert result[0]["net"] == 1000.0
    # months are in ascending order
    assert result[0]["month"] < result[-1]["month"]


@pytest.mark.anyio
async def test_income_vs_expenses_zero_data():
    from app.services.analytics_service import get_income_vs_expenses

    async def mock_execute(query):
        result = MagicMock()
        result.scalar.return_value = None
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_income_vs_expenses(uuid4(), mock_db, months=3)

    assert len(result) == 3
    assert all(r["income"] == 0.0 for r in result)
    assert all(r["expenses"] == 0.0 for r in result)
    assert all(r["net"] == 0.0 for r in result)


@pytest.mark.anyio
async def test_year_over_year_returns_12_months_per_year():
    from app.services.analytics_service import get_year_over_year

    async def mock_execute(query):
        result = MagicMock()
        result.scalar.return_value = Decimal("-500.00")
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_year_over_year(uuid4(), mock_db)

    assert "series" in result
    assert len(result["series"]) == 12
    assert result["series"][0]["month"] == "Jan"
    assert result["series"][11]["month"] == "Dec"
    assert result["series"][0]["current_year"] == 500.0
    assert result["series"][0]["prior_year"] == 500.0
    assert "current_year" in result
    assert "prior_year" in result
    assert result["current_year"] == result["prior_year"] + 1


@pytest.mark.anyio
async def test_year_over_year_zero_when_no_data():
    from app.services.analytics_service import get_year_over_year

    async def mock_execute(query):
        result = MagicMock()
        result.scalar.return_value = None
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_year_over_year(uuid4(), mock_db)

    assert all(m["current_year"] == 0.0 for m in result["series"])
    assert all(m["prior_year"] == 0.0 for m in result["series"])


@pytest.mark.anyio
async def test_tax_summary_aggregates_by_tax_category():
    from app.services.analytics_service import get_tax_summary

    cat_row = MagicMock()
    cat_row.tax_category = "Business"
    cat_row.total = Decimal("-350.00")
    cat_row.count = 5

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # total deductible
            result.scalar.return_value = Decimal("-350.00")
        elif call_count == 2:  # by tax_category
            result.all.return_value = [cat_row]
        else:  # transactions list
            result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_tax_summary(uuid4(), mock_db, year=2024)

    assert result["year"] == 2024
    assert result["total_deductible"] == 350.0
    assert len(result["by_tax_category"]) == 1
    assert result["by_tax_category"][0]["tax_category"] == "Business"
    assert result["by_tax_category"][0]["total"] == 350.0


@pytest.mark.anyio
async def test_tax_summary_zero_when_no_deductible():
    from app.services.analytics_service import get_tax_summary

    async def mock_execute(query):
        result = MagicMock()
        result.scalar.return_value = None
        result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_tax_summary(uuid4(), mock_db, year=2024)

    assert result["total_deductible"] == 0.0
    assert result["by_tax_category"] == []
    assert result["transactions"] == []
