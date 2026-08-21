import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.anyio
async def test_get_user_accounts_filters_by_user_id():
    from app.services.account_service import get_user_accounts

    user_id = uuid4()
    mock_account = MagicMock()
    mock_account.user_id = user_id
    mock_account.is_active = True

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_account]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    accounts = await get_user_accounts(user_id, mock_db)
    assert len(accounts) == 1
    assert accounts[0].user_id == user_id


@pytest.mark.anyio
async def test_get_accounts_needing_reauth_returns_correct_status():
    from app.services.account_service import get_accounts_needing_reauth

    user_id = uuid4()
    mock_account = MagicMock()
    mock_account.sync_status = "reauth_required"

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_account]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    accounts = await get_accounts_needing_reauth(user_id, mock_db)
    assert len(accounts) == 1
    assert accounts[0].sync_status == "reauth_required"


@pytest.mark.anyio
async def test_get_account_by_id_returns_none_for_wrong_user():
    from app.services.account_service import get_account_by_id

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    account = await get_account_by_id(uuid4(), uuid4(), mock_db)
    assert account is None
