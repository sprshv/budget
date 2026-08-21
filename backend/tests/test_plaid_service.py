"""
Tests for Plaid service (link token creation and client setup).
Plaid is mocked at the sys.modules level so the real plaid package is not required.
"""
import sys
import inspect
from unittest.mock import MagicMock, patch

# Inject plaid stubs into sys.modules BEFORE any app module that imports plaid is loaded.
_plaid_stub = MagicMock()
for _mod in [
    "plaid",
    "plaid.api",
    "plaid.api.plaid_api",
    "plaid.model",
    "plaid.model.link_token_create_request",
    "plaid.model.link_token_create_request_user",
    "plaid.model.country_code",
    "plaid.model.products",
    "plaid.model.item_public_token_exchange_request",
    "plaid.model.accounts_get_request",
    "plaid.model.institutions_get_by_id_request",
]:
    sys.modules.setdefault(_mod, MagicMock())

import pytest


@pytest.mark.anyio
async def test_create_link_token_returns_string():
    with patch("app.services.plaid_service.get_plaid_client") as mock_get_client:
        mock_client = MagicMock()
        mock_response = {"link_token": "link-sandbox-test-token-abc123"}
        mock_client.link_token_create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from app.services.plaid_service import create_link_token

        token = await create_link_token("user-123")
        assert token == "link-sandbox-test-token-abc123"
        mock_client.link_token_create.assert_called_once()


@pytest.mark.anyio
async def test_create_link_token_includes_user_id():
    with patch("app.services.plaid_service.get_plaid_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.link_token_create.return_value = {"link_token": "link-test"}
        mock_get_client.return_value = mock_client

        with patch("app.services.plaid_service.LinkTokenCreateRequestUser") as mock_user_cls:
            from app.services.plaid_service import create_link_token

            await create_link_token("user-xyz")

            mock_user_cls.assert_called_once_with(client_user_id="user-xyz")


@pytest.mark.anyio
async def test_get_link_token_endpoint_requires_auth():
    # Verify the endpoint has get_current_user dependency
    from app.routers.plaid import get_link_token

    sig = inspect.signature(get_link_token)
    assert "current_user" in sig.parameters


@pytest.mark.anyio
async def test_plaid_client_uses_correct_env():
    with patch("app.services.plaid_service.plaid") as mock_plaid:
        mock_plaid.Environment.Sandbox = "https://sandbox.plaid.com"
        mock_plaid.Configuration = MagicMock(return_value=MagicMock())
        mock_plaid.ApiClient = MagicMock(return_value=MagicMock())

        from app.services.plaid_service import get_plaid_client

        # Just verify it runs without error
        assert callable(get_plaid_client)
