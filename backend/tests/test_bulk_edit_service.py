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
from unittest.mock import AsyncMock
from uuid import uuid4

@pytest.mark.anyio
async def test_bulk_update_rejects_foreign_transaction():
    from app.services.transaction_service import bulk_update_transactions

    user_id = str(uuid4())
    other_user_id = str(uuid4())
    txn_id = uuid4()

    mock_txn = MagicMock()
    mock_txn.id = txn_id
    mock_txn.user_id = other_user_id

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_txn]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(PermissionError, match="do not belong to current user"):
        await bulk_update_transactions(
            transaction_ids=[str(txn_id)],
            updates={"notes": "test"},
            user_id=user_id,
            db=mock_db,
        )

@pytest.mark.anyio
async def test_bulk_update_succeeds_for_owned_transactions():
    from app.services.transaction_service import bulk_update_transactions

    user_id = str(uuid4())
    txn_id1 = uuid4()
    txn_id2 = uuid4()

    mock_txn1 = MagicMock()
    mock_txn1.id = txn_id1
    mock_txn1.user_id = user_id

    mock_txn2 = MagicMock()
    mock_txn2.id = txn_id2
    mock_txn2.user_id = user_id

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_txn1, mock_txn2]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    updated = await bulk_update_transactions(
        transaction_ids=[str(txn_id1), str(txn_id2)],
        updates={"notes": "bulk note"},
        user_id=user_id,
        db=mock_db,
    )

    assert len(updated) == 2
    assert mock_txn1.notes == "bulk note"
    assert mock_txn2.notes == "bulk note"
    mock_db.commit.assert_called_once()

@pytest.mark.anyio
async def test_bulk_update_rejects_missing_ids():
    from app.services.transaction_service import bulk_update_transactions

    user_id = str(uuid4())

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="not found"):
        await bulk_update_transactions(
            transaction_ids=[str(uuid4())],
            updates={"notes": "test"},
            user_id=user_id,
            db=mock_db,
        )

@pytest.mark.anyio
async def test_bulk_update_atomicity_all_or_nothing():
    from app.services.transaction_service import bulk_update_transactions

    user_id = str(uuid4())
    other_user_id = str(uuid4())

    txn1 = MagicMock()
    txn1.id = uuid4()
    txn1.user_id = user_id

    txn2 = MagicMock()
    txn2.id = uuid4()
    txn2.user_id = other_user_id

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [txn1, txn2]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    with pytest.raises(PermissionError):
        await bulk_update_transactions(
            transaction_ids=[str(txn1.id), str(txn2.id)],
            updates={"notes": "test"},
            user_id=user_id,
            db=mock_db,
        )

    mock_db.commit.assert_not_called()
