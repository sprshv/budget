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
from uuid import uuid4


@pytest.mark.anyio
async def test_get_preferences_returns_all_types():
    from app.services.notification_service import get_preferences, NOTIFICATION_TYPES

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_preferences(uuid4(), mock_db)

    assert len(result) == len(NOTIFICATION_TYPES)
    assert all("notif_type" in r for r in result)
    assert all("push_enabled" in r for r in result)


@pytest.mark.anyio
async def test_get_preferences_applies_defaults():
    from app.services.notification_service import get_preferences, DEFAULT_THRESHOLDS

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_preferences(uuid4(), mock_db)
    pref_map = {p["notif_type"]: p for p in result}

    assert pref_map["low_balance"]["threshold_amount"] == DEFAULT_THRESHOLDS["low_balance"]
    assert pref_map["large_purchase"]["threshold_amount"] == DEFAULT_THRESHOLDS["large_purchase"]
    assert pref_map["budget_alert"]["push_enabled"] is True
