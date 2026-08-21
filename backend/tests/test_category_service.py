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
async def test_create_category_sets_is_system_false():
    from app.services.category_service import create_category

    mock_cat = MagicMock()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("app.services.category_service.Category", return_value=mock_cat) as MockCat:
        result = await create_category(
            user_id=uuid4(),
            data={"name": "Coffee", "color": "#6F4E37", "icon": "☕", "parent_id": None, "is_income": False},
            db=mock_db,
        )
    # Confirm is_system=False was passed
    call_kwargs = MockCat.call_args.kwargs
    assert call_kwargs.get("is_system") == False
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_update_system_category_raises():
    from app.services.category_service import update_category

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # system cat filtered out

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="cannot be modified"):
        await update_category(uuid4(), uuid4(), {"name": "New"}, mock_db)


@pytest.mark.anyio
async def test_delete_system_category_raises():
    from app.services.category_service import delete_category

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # system cat filtered out

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="cannot be deleted"):
        await delete_category(uuid4(), uuid4(), mock_db)


@pytest.mark.anyio
async def test_delete_user_category_succeeds():
    from app.services.category_service import delete_category

    mock_cat = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cat

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.delete = AsyncMock()
    mock_db.commit = AsyncMock()

    await delete_category(uuid4(), uuid4(), mock_db)

    mock_db.delete.assert_called_once_with(mock_cat)
    mock_db.commit.assert_called_once()
