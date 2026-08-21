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
async def test_large_purchase_creates_notification_above_threshold():
    from app.services.large_purchase_service import check_large_purchase

    mock_db = AsyncMock()

    with patch("app.services.large_purchase_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_large_purchase(
            user_id=uuid4(),
            transaction_id=uuid4(),
            amount=-750.00,
            description="Flight booking",
            merchant_name="Delta Airlines",
            db=mock_db,
        )
        assert mock_create.called
        call_kwargs = mock_create.call_args.kwargs
        assert "Delta Airlines" in call_kwargs.get("body", "") or "Delta Airlines" in call_kwargs.get("title", "")
        assert "$750" in call_kwargs.get("title", "") or "750" in call_kwargs.get("title", "")


@pytest.mark.anyio
async def test_large_purchase_skips_below_threshold():
    from app.services.large_purchase_service import check_large_purchase

    mock_db = AsyncMock()

    with patch("app.services.large_purchase_service.create_notification", new_callable=AsyncMock) as mock_create:
        await check_large_purchase(
            user_id=uuid4(),
            transaction_id=uuid4(),
            amount=-45.00,  # below $500
            description="Coffee",
            merchant_name="Starbucks",
            db=mock_db,
        )
        assert not mock_create.called
