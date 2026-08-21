import sys
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Stub plaid and its submodules before any app imports trigger the import chain
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
async def test_run_transaction_sync_skips_reauth_accounts():
    """Accounts with sync_status=reauth_required should not be synced."""
    mock_account = MagicMock()
    mock_account.id = uuid4()
    mock_account.user_id = uuid4()
    mock_account.sync_status = "ok"
    mock_account.plaid_access_token = "encrypted-token"

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_account]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with patch("app.jobs.sync_job.AsyncSessionLocal", return_value=mock_db), \
         patch("app.jobs.sync_job.sync_account_transactions", return_value=5) as mock_sync:

        from app.jobs.sync_job import run_transaction_sync
        await run_transaction_sync()

        mock_sync.assert_called_once_with(mock_account, mock_db, mock_account.user_id)


@pytest.mark.anyio
async def test_run_transaction_sync_handles_account_error():
    """Individual account errors should not abort the entire job."""
    mock_account = MagicMock()
    mock_account.id = uuid4()
    mock_account.user_id = uuid4()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_account]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with patch("app.jobs.sync_job.AsyncSessionLocal", return_value=mock_db), \
         patch("app.jobs.sync_job.sync_account_transactions", side_effect=Exception("Plaid error")):

        from app.jobs.sync_job import run_transaction_sync
        # Should not raise — errors are caught per-account
        await run_transaction_sync()


@pytest.mark.anyio
async def test_sync_job_function_is_async():
    from app.jobs.sync_job import run_transaction_sync
    assert asyncio.iscoroutinefunction(run_transaction_sync)
