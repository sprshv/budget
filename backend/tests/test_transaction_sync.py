import sys
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import uuid4

import pytest

# Stub plaid modules before any app imports
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
    "plaid.model.transactions_sync_request",
]:
    sys.modules.setdefault(_mod, MagicMock())


@pytest.mark.anyio
async def test_normalize_merchant_prefers_merchant_name():
    from app.services.transaction_sync_service import _normalize_merchant
    result = _normalize_merchant("AMZN MKTP", "Amazon")
    assert result == "Amazon"


@pytest.mark.anyio
async def test_normalize_merchant_falls_back_to_raw():
    from app.services.transaction_sync_service import _normalize_merchant
    result = _normalize_merchant("walmart supercenter", "")
    assert result == "Walmart Supercenter"


@pytest.mark.anyio
async def test_categorize_transaction_known_category():
    mock_cat = MagicMock()
    mock_cat.id = uuid4()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cat
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.services.categorization_service import categorize_transaction
    cat_id, confidence = await categorize_transaction("FOOD_AND_DRINK", mock_db)

    assert cat_id == mock_cat.id
    assert confidence == 0.7


@pytest.mark.anyio
async def test_categorize_transaction_unknown_falls_back():
    mock_cat = MagicMock()
    mock_cat.id = uuid4()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cat
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.services.categorization_service import categorize_transaction
    cat_id, confidence = await categorize_transaction("UNKNOWN_CATEGORY", mock_db)

    assert cat_id == mock_cat.id
    assert confidence == 0.3


@pytest.mark.anyio
async def test_deduplication_skips_existing_transaction():
    # Verify that sync_account_transactions skips transactions that already exist
    existing_txn = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_txn

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    mock_account = MagicMock()
    mock_account.id = uuid4()
    mock_account.plaid_access_token = "encrypted-token"
    mock_account.plaid_cursor = None

    with patch("app.services.transaction_sync_service.decrypt", return_value="raw-token"), \
         patch("app.services.transaction_sync_service.sync_transactions", return_value={
             "added": [{"transaction_id": "txn-existing", "name": "Test", "amount": 10.0,
                        "date": "2024-01-01", "pending": False}],
             "modified": [], "removed": [], "next_cursor": "cursor-1"
         }):

        from app.services.transaction_sync_service import sync_account_transactions
        count = await sync_account_transactions(mock_account, mock_db, uuid4())

        assert count == 0  # Existing transaction was skipped
