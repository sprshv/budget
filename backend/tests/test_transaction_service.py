import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal
from datetime import date


@pytest.mark.anyio
async def test_get_transactions_filters_by_user_id():
    from app.services.transaction_service import get_transactions

    user_id = uuid4()
    mock_txn = MagicMock()
    mock_txn.user_id = user_id

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_txn]
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 1
    mock_list_result = MagicMock()
    mock_list_result.scalars.return_value = mock_scalars

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

    txns, total = await get_transactions(user_id=user_id, db=mock_db)
    assert total == 1
    assert len(txns) == 1


@pytest.mark.anyio
async def test_get_transactions_limit_enforced():
    from app.services.transaction_service import get_transactions

    mock_count = MagicMock()
    mock_count.scalar_one.return_value = 0
    mock_list = MagicMock()
    mock_list.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_count, mock_list])

    txns, total = await get_transactions(user_id=uuid4(), db=mock_db, limit=10, offset=20)
    assert total == 0
    assert txns == []


@pytest.mark.anyio
async def test_get_transaction_by_id_wrong_user():
    from app.services.transaction_service import get_transaction_by_id

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_transaction_by_id(uuid4(), uuid4(), mock_db)
    assert result is None


@pytest.mark.anyio
async def test_create_transaction_raises_for_wrong_account():
    from app.services.transaction_service import create_transaction

    # Account lookup returns None (wrong owner)
    mock_acct_result = MagicMock()
    mock_acct_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_acct_result)

    with pytest.raises(ValueError, match="Account not found"):
        await create_transaction(
            user_id=uuid4(),
            data={
                "account_id": uuid4(),
                "amount": Decimal("25.00"),
                "date": date(2024, 6, 15),
                "description": "Test purchase",
            },
            db=mock_db,
        )


@pytest.mark.anyio
async def test_update_transaction_sets_tax_fields():
    from app.services.transaction_service import update_transaction

    mock_tx = MagicMock()
    mock_tx.user_id = uuid4()
    mock_tx.is_tax_deductible = False
    mock_tx.tax_category = None

    user_id = mock_tx.user_id

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = mock_tx

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_scalar_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    patch_data = {"is_tax_deductible": True, "tax_category": "Business"}

    await update_transaction(uuid4(), user_id, patch_data, mock_db)

    assert mock_tx.is_tax_deductible is True
    assert mock_tx.tax_category == "Business"


@pytest.mark.anyio
async def test_update_transaction_tax_deductible_false_leaves_category():
    from app.services.transaction_service import update_transaction

    mock_tx = MagicMock()
    mock_tx.user_id = uuid4()
    mock_tx.is_tax_deductible = True
    mock_tx.tax_category = "Medical"

    user_id = mock_tx.user_id

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = mock_tx

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_scalar_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Setting is_tax_deductible to False without including tax_category in patch
    # leaves tax_category unchanged (caller responsible for clearing it)
    patch_data = {"is_tax_deductible": False}

    await update_transaction(uuid4(), user_id, patch_data, mock_db)

    assert mock_tx.is_tax_deductible is False


@pytest.mark.anyio
async def test_export_transactions_csv_returns_csv_string():
    from app.services.transaction_service import export_transactions_csv
    from datetime import date as date_cls
    from decimal import Decimal

    row = MagicMock()
    row.id = uuid4()
    row.date = date_cls(2025, 1, 15)
    row.description = "Coffee"
    row.merchant_name = "Starbucks"
    row.amount = Decimal("-5.50")
    row.notes = None
    row.is_tax_deductible = False
    row.tax_category = None
    row.pending = False
    row.category_name = "Food"
    row.account_name = "Checking"

    mock_result = MagicMock()
    mock_result.all.return_value = [row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    csv_output = await export_transactions_csv(uuid4(), mock_db)

    assert "Date,Description" in csv_output
    assert "Starbucks" in csv_output
    assert "2025-01-15" in csv_output
    assert "-5.5" in csv_output


@pytest.mark.anyio
async def test_export_transactions_csv_empty_returns_header_only():
    from app.services.transaction_service import export_transactions_csv

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    csv_output = await export_transactions_csv(uuid4(), mock_db)

    lines = [l for l in csv_output.strip().split("\n") if l]
    assert len(lines) == 1  # header only
    assert "Date" in lines[0]
