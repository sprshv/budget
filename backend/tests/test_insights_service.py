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
async def test_spending_changes_detects_increase():
    from app.services.insights_service import get_spending_changes

    cat_id = uuid4()

    # curr month row
    curr_row = MagicMock()
    curr_row.category_id = cat_id
    curr_row.name = "Dining"
    curr_row.color = "#ff0000"
    curr_row.total = Decimal("-300.00")

    # prev month row
    prev_row = MagicMock()
    prev_row.category_id = cat_id
    prev_row.name = "Dining"
    prev_row.color = "#ff0000"
    prev_row.total = Decimal("-200.00")

    # 3-month row
    three_row = MagicMock()
    three_row.category_id = cat_id
    three_row.name = "Dining"
    three_row.color = "#ff0000"
    three_row.total = Decimal("-600.00")  # 200/month avg

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # curr month
            result.all.return_value = [curr_row]
        elif call_count == 2:  # 3-month
            result.all.return_value = [three_row]
        else:  # prev month
            result.all.return_value = [prev_row]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_spending_changes(uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["category_name"] == "Dining"
    assert result[0]["current_month_spend"] == 300.0
    assert result[0]["prior_month_spend"] == 200.0
    assert result[0]["pct_vs_prior_month"] == 50.0  # (300-200)/200*100
    assert result[0]["direction"] == "up"
    assert result[0]["significant"] is True  # >15%


@pytest.mark.anyio
async def test_spending_changes_empty_when_no_transactions():
    from app.services.insights_service import get_spending_changes

    async def mock_execute(query):
        result = MagicMock()
        result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_spending_changes(uuid4(), mock_db)
    assert result == []


@pytest.mark.anyio
async def test_spending_changes_direction_down_when_spending_decreased():
    from app.services.insights_service import get_spending_changes

    cat_id = uuid4()

    curr_row = MagicMock()
    curr_row.category_id = cat_id
    curr_row.name = "Shopping"
    curr_row.color = "#0000ff"
    curr_row.total = Decimal("-100.00")

    prev_row = MagicMock()
    prev_row.category_id = cat_id
    prev_row.name = "Shopping"
    prev_row.color = "#0000ff"
    prev_row.total = Decimal("-200.00")

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.all.return_value = [curr_row]
        elif call_count == 2:
            result.all.return_value = []  # no 3-month data
        else:
            result.all.return_value = [prev_row]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_spending_changes(uuid4(), mock_db)

    assert result[0]["direction"] == "down"
    assert result[0]["pct_vs_prior_month"] == -50.0


@pytest.mark.anyio
async def test_anomalies_flags_outlier_transaction():
    from app.services.insights_service import get_anomalies
    from datetime import date as date_cls

    cat_id = uuid4()

    def make_tx(amount_abs, days_ago=5):
        from datetime import timedelta
        row = MagicMock()
        row.id = uuid4()
        row.category_id = cat_id
        row.category_name = "Food"
        row.description = "Restaurant"
        row.merchant_name = "Big Spender"
        row.date = date_cls.today() - timedelta(days=days_ago)
        row.amount = Decimal(f"-{amount_abs}")
        return row

    # 10 normal transactions at ~$10 each, 1 outlier at $200
    normal_txs = [make_tx(10, days_ago=i+10) for i in range(10)]
    outlier = make_tx(200, days_ago=1)
    all_txs = [outlier] + normal_txs  # ordered by date desc

    mock_result = MagicMock()
    mock_result.all.return_value = all_txs

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_anomalies(uuid4(), mock_db)

    assert len(result) >= 1
    assert result[0]["amount"] == -200.0
    assert result[0]["category_name"] == "Food"
    assert result[0]["overage"] > 0


@pytest.mark.anyio
async def test_anomalies_skips_category_with_fewer_than_3_transactions():
    from app.services.insights_service import get_anomalies
    from datetime import date as date_cls, timedelta

    cat_id = uuid4()

    def make_tx(amount_abs):
        row = MagicMock()
        row.id = uuid4()
        row.category_id = cat_id
        row.category_name = "Travel"
        row.description = "Airline"
        row.merchant_name = "Delta"
        row.date = date_cls.today() - timedelta(days=3)
        row.amount = Decimal(f"-{amount_abs}")
        return row

    # Only 2 transactions — should not flag anything
    txs = [make_tx(500), make_tx(50)]

    mock_result = MagicMock()
    mock_result.all.return_value = txs

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_anomalies(uuid4(), mock_db)
    assert result == []


@pytest.mark.anyio
async def test_forecast_projects_correctly():
    from app.services.insights_service import get_forecast
    from datetime import date as date_cls
    import calendar as cal_module

    today = date_cls.today()
    days_elapsed = today.day
    days_in_month = cal_module.monthrange(today.year, today.month)[1]

    cat_id = uuid4()

    spend_row = MagicMock()
    spend_row.category_id = cat_id
    spend_row.name = "Groceries"
    spend_row.color = "#00ff00"
    spend_row.total = Decimal(f"-{days_elapsed * 10}.00")  # $10/day so far

    budget_row = MagicMock()
    budget_row.category_id = cat_id
    budget_row.amount = Decimal("400.00")

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # spending
            result.all.return_value = [spend_row]
        else:  # budgets
            result.all.return_value = [budget_row]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_forecast(uuid4(), mock_db)

    assert result["days_in_month"] == days_in_month
    assert result["days_elapsed"] == days_elapsed
    assert len(result["categories"]) == 1
    cat = result["categories"][0]
    assert cat["category_name"] == "Groceries"
    # $10/day × days_in_month
    assert cat["projected_month_total"] == pytest.approx(10.0 * days_in_month, rel=1e-3)
    assert cat["daily_rate"] == pytest.approx(10.0, rel=1e-3)


@pytest.mark.anyio
async def test_forecast_empty_when_no_spending():
    from app.services.insights_service import get_forecast

    async def mock_execute(query):
        result = MagicMock()
        result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_forecast(uuid4(), mock_db)

    assert result["total_spent_so_far"] == 0.0
    assert result["total_projected"] == 0.0
    assert result["categories"] == []


@pytest.mark.anyio
async def test_savings_opportunities_flags_overspending_category():
    from app.services.insights_service import get_savings_opportunities

    cat_id = uuid4()

    def make_row(name, total_abs):
        row = MagicMock()
        row.category_id = cat_id
        row.name = name
        row.color = "#ff0000"
        row.total = Decimal(f"-{total_abs}")
        return row

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # current month spend
            result.all.return_value = [make_row("Dining", 300)]
        else:  # 3-month spend (avg = 200/month -> 600 total / 3)
            result.all.return_value = [make_row("Dining", 600)]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_savings_opportunities(uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["category_name"] == "Dining"
    assert result[0]["current_month_spend"] == 300.0
    assert result[0]["three_month_avg"] == 200.0  # 600 / 3
    assert result[0]["overage"] == 100.0
    assert result[0]["pct_over_average"] == 50.0


@pytest.mark.anyio
async def test_savings_opportunities_empty_when_within_110_percent():
    from app.services.insights_service import get_savings_opportunities

    cat_id = uuid4()

    def make_row(name, total_abs):
        row = MagicMock()
        row.category_id = cat_id
        row.name = name
        row.color = "#00ff00"
        row.total = Decimal(f"-{total_abs}")
        return row

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # current month: $210 (within 110% of $200 avg)
            result.all.return_value = [make_row("Groceries", 210)]
        else:  # 3-month: $600 total -> $200 avg
            result.all.return_value = [make_row("Groceries", 600)]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_savings_opportunities(uuid4(), mock_db)
    assert result == []


@pytest.mark.anyio
async def test_budget_recommendations_suggests_create_for_uncategorized():
    from app.services.insights_service import get_budget_recommendations

    cat_id = uuid4()

    def make_row(amt):
        row = MagicMock()
        row.category_id = cat_id
        row.name = "Entertainment"
        row.color = "#8b5cf6"
        row.total = Decimal(f"-{amt}")
        return row

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        # 3 monthly spend queries + 1 budget query
        if call_count <= 3:
            result.all.return_value = [make_row(150)]
        else:  # budget query: no budgets
            result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_budget_recommendations(uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["type"] == "create"
    assert result[0]["category_name"] == "Entertainment"
    assert result[0]["suggested_amount"] == 150.0
    assert result[0]["current_budget"] is None


@pytest.mark.anyio
async def test_budget_recommendations_suggests_raise_when_always_exceeded():
    from app.services.insights_service import get_budget_recommendations

    cat_id = uuid4()

    def make_row(amt):
        row = MagicMock()
        row.category_id = cat_id
        row.name = "Dining"
        row.color = "#f59e0b"
        row.total = Decimal(f"-{amt}")
        return row

    def make_budget():
        row = MagicMock()
        row.category_id = cat_id
        row.amount = Decimal("100.00")  # always exceeded since spend is $200
        return row

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count <= 3:
            result.all.return_value = [make_row(200)]  # always $200, budget is $100
        else:
            result.all.return_value = [make_budget()]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_budget_recommendations(uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["type"] == "raise"
    assert result[0]["suggested_amount"] == 200.0
    assert result[0]["current_budget"] == 100.0


@pytest.mark.anyio
async def test_health_score_returns_all_components():
    from app.services.insights_service import get_health_score

    async def mock_execute(query):
        result = MagicMock()
        result.all.return_value = []
        result.scalar.return_value = None
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_health_score(uuid4(), mock_db)

    assert "overall_score" in result
    assert "components" in result
    components = result["components"]
    assert "budget_adherence" in components
    assert "savings_rate" in components
    assert "debt_to_income" in components
    assert "emergency_fund" in components
    assert "subscription_ratio" in components
    assert 0 <= result["overall_score"] <= 100


@pytest.mark.anyio
async def test_health_score_bounded_0_to_100():
    from app.services.insights_service import get_health_score

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        # Simulate very healthy financials: high income, no debt, no subs
        result.scalar.return_value = Decimal("10000.00")
        result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_health_score(uuid4(), mock_db)

    assert 0 <= result["overall_score"] <= 100
    for comp in result["components"].values():
        assert 0 <= comp["score"] <= 100


@pytest.mark.anyio
async def test_insights_summary_returns_list_with_health_score():
    from app.services.insights_service import get_insights_summary
    from unittest.mock import patch

    with patch("app.services.insights_service.get_spending_changes", return_value=[]), \
         patch("app.services.insights_service.get_anomalies", return_value=[]), \
         patch("app.services.insights_service.get_forecast", return_value={"categories": []}), \
         patch("app.services.insights_service.get_savings_opportunities", return_value=[]), \
         patch("app.services.insights_service.get_health_score", return_value={
             "overall_score": 72.0,
             "components": {},
         }):
        mock_db = AsyncMock()
        result = await get_insights_summary(uuid4(), mock_db)

    assert isinstance(result, list)
    # Health score insight is always included
    types = [i["type"] for i in result]
    assert "health_score" in types
    assert len(result) <= 5


@pytest.mark.anyio
async def test_insights_summary_includes_anomaly_when_present():
    from app.services.insights_service import get_insights_summary
    from unittest.mock import patch

    anomaly = {
        "transaction_id": str(uuid4()),
        "date": "2025-01-15",
        "description": "Big purchase",
        "merchant_name": "Amazon",
        "amount": -500.0,
        "category_name": "Shopping",
        "category_id": str(uuid4()),
        "expected_max": 100.0,
        "mean": 50.0,
        "std_dev": 25.0,
        "overage": 400.0,
    }

    with patch("app.services.insights_service.get_spending_changes", return_value=[]), \
         patch("app.services.insights_service.get_anomalies", return_value=[anomaly]), \
         patch("app.services.insights_service.get_forecast", return_value={"categories": []}), \
         patch("app.services.insights_service.get_savings_opportunities", return_value=[]), \
         patch("app.services.insights_service.get_health_score", return_value={
             "overall_score": 60.0,
             "components": {},
         }):
        mock_db = AsyncMock()
        result = await get_insights_summary(uuid4(), mock_db)

    types = [i["type"] for i in result]
    assert "anomaly" in types
