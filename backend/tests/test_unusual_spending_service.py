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


@pytest.mark.anyio
async def test_unusual_spending_creates_notification_for_anomaly():
    from app.services.unusual_spending_service import check_unusual_spending

    tx_id = str(uuid4())
    anomaly = {
        "transaction_id": tx_id,
        "description": "Big Dinner",
        "merchant_name": "Fancy Restaurant",
        "amount": -450.0,
        "category_name": "Dining",
        "expected_max": 80.0,
        "mean": 35.0,
        "std_dev": 22.5,
        "overage": 370.0,
    }

    async def mock_execute(query):
        result = MagicMock()
        # dedup check: no existing notification
        result.scalars.return_value.first.return_value = None
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    with patch("app.services.unusual_spending_service.get_anomalies", return_value=[anomaly]), \
         patch("app.services.unusual_spending_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_unusual_spending(uuid4(), mock_db)
        assert mock_create.called
        call_kwargs = mock_create.call_args.kwargs
        assert "Fancy Restaurant" in call_kwargs.get("title", "")


@pytest.mark.anyio
async def test_unusual_spending_skips_when_no_anomalies():
    from app.services.unusual_spending_service import check_unusual_spending

    mock_db = AsyncMock()

    with patch("app.services.unusual_spending_service.get_anomalies", return_value=[]), \
         patch("app.services.unusual_spending_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_unusual_spending(uuid4(), mock_db)
        assert not mock_create.called
