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
async def test_budget_alert_creates_notification_at_threshold():
    from app.services.budget_alert_service import check_budget_alerts

    user_id = uuid4()
    budget_id = uuid4()
    cat_id = uuid4()

    mock_budget = MagicMock()
    mock_budget.id = budget_id
    mock_budget.category_id = cat_id
    mock_budget.amount = Decimal("100.00")
    # alert_threshold stored as fraction: 0.80 = 80%
    mock_budget.alert_threshold = Decimal("0.80")
    mock_budget.alert_sent = False

    mock_cat = MagicMock()
    mock_cat.id = cat_id
    mock_cat.name = "Food"

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # budgets
            result.scalars.return_value.all.return_value = [mock_budget]
        elif call_count == 2:  # spending
            row = MagicMock()
            row.category_id = cat_id
            row.total = Decimal("-85.00")  # 85% of budget — above 80% threshold
            result.all.return_value = [row]
        else:  # categories
            result.all.return_value = [mock_cat]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute
    mock_db.commit = AsyncMock()

    with patch("app.services.budget_alert_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_budget_alerts(user_id, mock_db)
        assert mock_create.called
        call_args = mock_create.call_args
        assert "Food" in call_args.kwargs.get("title", "") or "Food" in str(call_args)


@pytest.mark.anyio
async def test_budget_alert_skips_when_under_threshold():
    from app.services.budget_alert_service import check_budget_alerts

    user_id = uuid4()
    cat_id = uuid4()

    mock_budget = MagicMock()
    mock_budget.id = uuid4()
    mock_budget.category_id = cat_id
    mock_budget.amount = Decimal("100.00")
    # alert_threshold stored as fraction: 0.80 = 80%
    mock_budget.alert_threshold = Decimal("0.80")
    mock_budget.alert_sent = False

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalars.return_value.all.return_value = [mock_budget]
        elif call_count == 2:
            row = MagicMock()
            row.category_id = cat_id
            row.total = Decimal("-50.00")  # 50% — under 80% threshold
            result.all.return_value = [row]
        else:
            result.all.return_value = []
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.services.budget_alert_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_budget_alerts(user_id, mock_db)
        assert not mock_create.called
