import pytest
from unittest.mock import MagicMock, patch


# Patch create_async_engine before any app module is imported so that the
# database.py module-level engine creation does not attempt to load asyncpg.
@pytest.fixture(autouse=True, scope="session")
def patch_db_engine():
    mock_engine = MagicMock()
    mock_session_factory = MagicMock()
    with (
        patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=mock_engine),
        patch("sqlalchemy.ext.asyncio.async_sessionmaker", return_value=mock_session_factory),
    ):
        yield
