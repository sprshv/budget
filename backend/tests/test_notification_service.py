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
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone


@pytest.mark.anyio
async def test_list_notifications_returns_unread_count():
    from app.services.notification_service import list_notifications

    notif = MagicMock()
    notif.id = uuid4()
    notif.type = "budget_alert"
    notif.title = "Budget Alert"
    notif.body = "You've used 80% of your Food budget."
    notif.is_read = False
    notif.created_at = datetime.now(timezone.utc)
    notif.read_at = None

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # list query
            result.scalars.return_value.all.return_value = [notif]
        else:  # count query
            result.scalar.return_value = 1
        return result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await list_notifications(uuid4(), mock_db)

    assert result["unread_count"] == 1
    assert len(result["notifications"]) == 1
    assert result["notifications"][0]["type"] == "budget_alert"
    assert result["notifications"][0]["message"] == "You've used 80% of your Food budget."


@pytest.mark.anyio
async def test_mark_all_read_returns_success():
    from app.services.notification_service import mark_all_read

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock())
    mock_db.commit = AsyncMock()

    result = await mark_all_read(uuid4(), mock_db)
    assert result["success"] is True
