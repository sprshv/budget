"""
Tests for token exchange, encryption, and account storage (Task 2.2).
Plaid is mocked at the sys.modules level so the real plaid package is not required.
"""
import sys
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
async def test_exchange_public_token_returns_access_token_and_item_id():
    with patch("app.services.plaid_service.get_plaid_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.item_public_token_exchange.return_value = {
            "access_token": "access-sandbox-abc",
            "item_id": "item-xyz",
        }
        mock_get_client.return_value = mock_client

        from app.services.plaid_service import exchange_public_token
        result = await exchange_public_token("public-sandbox-token")

        assert result["access_token"] == "access-sandbox-abc"
        assert result["item_id"] == "item-xyz"


@pytest.mark.anyio
async def test_encrypt_decrypt_roundtrip():
    from cryptography.fernet import Fernet
    test_key = Fernet.generate_key().decode()

    with patch("app.services.encryption_service.settings") as mock_settings:
        mock_settings.ENCRYPTION_KEY = test_key

        import app.services.encryption_service as enc_module

        plaintext = "access-sandbox-abc-123"
        ciphertext = enc_module.encrypt(plaintext)

        assert ciphertext != plaintext
        assert enc_module.decrypt(ciphertext) == plaintext


@pytest.mark.anyio
async def test_fetch_accounts_calls_plaid():
    with patch("app.services.plaid_service.get_plaid_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.accounts_get.return_value = {
            "accounts": [
                {
                    "account_id": "acct-1",
                    "name": "Checking",
                    "type": "depository",
                    "balances": {},
                }
            ]
        }
        mock_get_client.return_value = mock_client

        from app.services.plaid_service import fetch_accounts
        accounts = await fetch_accounts("access-token")

        assert len(accounts) == 1
        assert accounts[0]["account_id"] == "acct-1"


@pytest.mark.anyio
async def test_access_token_never_in_response():
    # The ExchangeTokenResponse schema must not include any access token field
    from app.schemas.plaid import ExchangeTokenResponse
    fields = ExchangeTokenResponse.model_fields
    assert "access_token" not in fields
    assert "plaid_access_token" not in fields
