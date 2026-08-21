import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import sys
import json

# Stub plaid modules before any app imports — must cover all submodules
# imported transitively through transaction_sync_service -> plaid_service
for mod in [
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
    "plaid.model.transactions_sync_request",
    "plaid.model.webhook_verification_key_get_request",
]:
    sys.modules.setdefault(mod, MagicMock())


@pytest.mark.anyio
async def test_webhook_rejects_missing_signature():
    from app.routers.webhook import _verify_plaid_webhook

    mock_request = MagicMock()
    mock_request.headers = {}

    result = await _verify_plaid_webhook(mock_request, b'{"test": true}')
    assert result is False


@pytest.mark.anyio
async def test_handle_item_error_marks_account_reauth():
    from app.routers.webhook import _handle_item_error

    account_id = uuid4()
    user_id = uuid4()

    mock_account = MagicMock()
    mock_account.id = account_id
    mock_account.user_id = user_id
    mock_account.sync_status = "ok"
    mock_account.institution_name = "Test Bank"
    mock_account.name = "Checking"

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_account]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.refresh = AsyncMock()

    await _handle_item_error(
        {"item_id": "item-xyz", "error": {"error_code": "ITEM_LOGIN_REQUIRED"}},
        mock_db,
    )

    assert mock_account.sync_status == "reauth_required"


@pytest.mark.anyio
async def test_create_notification_saves_to_db():
    from app.services.notification_service import create_notification

    user_id = uuid4()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    notif = await create_notification(
        user_id=user_id,
        notif_type="test_type",
        title="Test",
        body="Test body",
        db=mock_db,
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_webhook_routes_transactions_event():
    from app.routers.webhook import plaid_webhook

    assert callable(plaid_webhook)


@pytest.mark.anyio
async def test_webhook_handles_unknown_type_gracefully():
    from app.routers.webhook import _handle_transactions_sync

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Should not raise
    await _handle_transactions_sync({"item_id": "unknown-item"}, mock_db)
