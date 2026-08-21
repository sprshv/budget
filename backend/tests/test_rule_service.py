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
from unittest.mock import AsyncMock, patch
from uuid import uuid4


@pytest.mark.anyio
async def test_create_rule_adds_and_commits():
    from app.services.rule_service import create_rule

    user_id = uuid4()
    mock_rule = MagicMock()

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("app.services.rule_service.CategorizationRule", return_value=mock_rule):
        result = await create_rule(
            user_id=user_id,
            data={
                "category_id": uuid4(),
                "match_field": "description",
                "operator": "contains",
                "match_value": "coffee",
                "priority": 1,
            },
            db=mock_db,
        )

    mock_db.add.assert_called_once_with(mock_rule)
    mock_db.commit.assert_called_once()
    assert result == mock_rule


@pytest.mark.anyio
async def test_update_rule_raises_if_not_found():
    from app.services.rule_service import update_rule

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="Rule not found"):
        await update_rule(uuid4(), uuid4(), {"match_value": "new"}, mock_db)


@pytest.mark.anyio
async def test_delete_rule_raises_if_not_found():
    from app.services.rule_service import delete_rule

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="Rule not found"):
        await delete_rule(uuid4(), uuid4(), mock_db)


@pytest.mark.anyio
async def test_delete_rule_deletes_and_commits():
    from app.services.rule_service import delete_rule

    mock_rule = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_rule

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.delete = AsyncMock()
    mock_db.commit = AsyncMock()

    await delete_rule(uuid4(), uuid4(), mock_db)

    mock_db.delete.assert_called_once_with(mock_rule)
    mock_db.commit.assert_called_once()
