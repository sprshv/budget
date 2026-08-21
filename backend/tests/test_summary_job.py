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
async def test_weekly_summary_creates_notification():
    from app.jobs.summary_job import _weekly_summary_for_user

    user_id = uuid4()
    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # curr week spending
            result.scalar.return_value = Decimal("-250.00")
        elif call_count == 2:  # prior week spending
            result.scalar.return_value = Decimal("-200.00")
        elif call_count == 3:  # top category
            row = MagicMock()
            row.name = "Dining"
            result.first.return_value = row
        else:
            result.scalar.return_value = Decimal("0")
            result.first.return_value = None
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.jobs.summary_job.create_notification", new_callable=AsyncMock) as mock_create:
        await _weekly_summary_for_user(user_id, mock_db)
        assert mock_create.called
        call_kwargs = mock_create.call_args.kwargs
        assert "250" in call_kwargs.get("title", "")


@pytest.mark.anyio
async def test_monthly_summary_creates_notification():
    from app.jobs.summary_job import _monthly_summary_for_user

    user_id = uuid4()
    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # income
            result.scalar.return_value = Decimal("3000.00")
        elif call_count == 2:  # expenses
            result.scalar.return_value = Decimal("-2200.00")
        else:  # top merchant
            row = MagicMock()
            row.merchant_name = "Whole Foods"
            result.first.return_value = row
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.jobs.summary_job.create_notification", new_callable=AsyncMock) as mock_create:
        await _monthly_summary_for_user(user_id, mock_db)
        assert mock_create.called
        call_kwargs = mock_create.call_args.kwargs
        assert "summary" in call_kwargs.get("title", "").lower() or "Summary" in call_kwargs.get("title", "")
