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
from uuid import uuid4
from decimal import Decimal


@pytest.mark.anyio
async def test_low_balance_creates_notification_when_below_threshold():
    from app.services.low_balance_service import check_low_balances

    user_id = uuid4()

    mock_account = MagicMock()
    mock_account.id = uuid4()
    mock_account.user_id = user_id
    mock_account.account_type = "checking"
    mock_account.name = "Chase Checking"
    mock_account.balance_available = Decimal("45.00")  # below $100
    mock_account.balance_current = Decimal("45.00")

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # accounts query
            result.scalars.return_value.all.return_value = [mock_account]
        else:  # dedup check — scalar_one_or_none returns None (no existing notif)
            result.scalar_one_or_none.return_value = None
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.services.low_balance_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_low_balances(user_id, mock_db)
        assert mock_create.called
        # Verify account name appears in title or body
        call_kwargs = mock_create.call_args.kwargs
        assert "Chase Checking" in call_kwargs.get("title", "") or "Chase Checking" in call_kwargs.get("body", "")


@pytest.mark.anyio
async def test_low_balance_skips_when_above_threshold():
    from app.services.low_balance_service import check_low_balances

    user_id = uuid4()

    mock_account = MagicMock()
    mock_account.id = uuid4()
    mock_account.account_type = "savings"
    mock_account.name = "Savings"
    mock_account.balance_available = Decimal("5000.00")  # well above threshold
    mock_account.balance_current = Decimal("5000.00")

    async def mock_execute(query):
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_account]
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.services.low_balance_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_low_balances(user_id, mock_db)
        assert not mock_create.called
