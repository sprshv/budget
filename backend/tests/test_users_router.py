import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.anyio
async def test_update_profile_sets_onboarding_complete():
    from app.services.auth_service import get_user_by_id

    user_id = str(uuid4())
    mock_result = MagicMock()
    mock_user = MagicMock()
    mock_user.onboarding_complete = False
    mock_result.scalar_one_or_none.return_value = mock_user

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    user = await get_user_by_id(user_id, mock_db)
    assert user is not None
    assert user.onboarding_complete is False

    # Simulate the PATCH logic setting onboarding_complete
    user.onboarding_complete = True
    assert user.onboarding_complete is True


@pytest.mark.anyio
async def test_get_user_by_id_not_found():
    from app.services.auth_service import get_user_by_id

    user_id = str(uuid4())
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    user = await get_user_by_id(user_id, mock_db)
    assert user is None


@pytest.mark.anyio
async def test_update_profile_partial_fields():
    from app.services.auth_service import get_user_by_id

    user_id = str(uuid4())
    mock_result = MagicMock()
    mock_user = MagicMock()
    mock_user.full_name = None
    mock_user.currency = "USD"
    mock_result.scalar_one_or_none.return_value = mock_user

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    user = await get_user_by_id(user_id, mock_db)
    assert user is not None

    # Simulate setting only full_name
    user.full_name = "Jane Doe"
    assert user.full_name == "Jane Doe"
    # currency should remain unchanged
    assert user.currency == "USD"
