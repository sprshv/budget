import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.anyio
async def test_get_or_create_user_creates_new_user():
    from app.services.auth_service import get_or_create_user

    user_id = str(uuid4())
    email = "test@example.com"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    user = await get_or_create_user(user_id, email, mock_db)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_get_or_create_user_returns_existing():
    from app.services.auth_service import get_or_create_user
    from app.models.user import User
    import uuid

    user_id = str(uuid4())
    email = "existing@example.com"

    existing_user = User(id=uuid.UUID(user_id), email=email)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()

    user = await get_or_create_user(user_id, email, mock_db)

    assert user.email == email
    mock_db.add.assert_not_called()


@pytest.mark.anyio
async def test_get_user_by_id_returns_user():
    from app.services.auth_service import get_user_by_id
    from app.models.user import User
    import uuid

    user_id = str(uuid4())
    email = "found@example.com"

    existing_user = User(id=uuid.UUID(user_id), email=email)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    user = await get_user_by_id(user_id, mock_db)

    assert user is not None
    assert user.email == email


@pytest.mark.anyio
async def test_get_user_by_id_returns_none_when_not_found():
    from app.services.auth_service import get_user_by_id

    user_id = str(uuid4())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    user = await get_user_by_id(user_id, mock_db)

    assert user is None
