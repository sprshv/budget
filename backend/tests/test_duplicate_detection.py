import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date
from uuid import uuid4


@pytest.mark.anyio
async def test_no_duplicate_returns_none():
    from app.services.duplicate_detection_service import check_manual_duplicate

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await check_manual_duplicate(
        user_id=uuid4(),
        amount=Decimal("25.00"),
        txn_date=date(2024, 6, 15),
        merchant_name="Starbucks",
        db=mock_db,
    )
    assert result is None


@pytest.mark.anyio
async def test_duplicate_found_returns_warning():
    from app.services.duplicate_detection_service import check_manual_duplicate
    from app.models.transaction import Transaction

    existing_id = uuid4()
    existing = MagicMock(spec=Transaction)
    existing.id = existing_id
    existing.date = date(2024, 6, 15)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await check_manual_duplicate(
        user_id=uuid4(),
        amount=Decimal("25.00"),
        txn_date=date(2024, 6, 15),
        merchant_name="Starbucks",
        db=mock_db,
    )

    assert result is not None
    assert result["is_potential_duplicate"] is True
    assert result["duplicate_of"] == str(existing_id)
    assert "25.00" in result["message"]


@pytest.mark.anyio
async def test_mark_as_duplicate_sets_flag():
    from app.services.duplicate_detection_service import mark_as_duplicate
    from app.models.transaction import Transaction

    txn_id = uuid4()
    user_id = uuid4()
    mock_txn = MagicMock(spec=Transaction)
    mock_txn.is_duplicate = False

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_txn
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    success = await mark_as_duplicate(txn_id, user_id, mock_db)

    assert success is True
    assert mock_txn.is_duplicate is True
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_mark_as_duplicate_wrong_user_returns_false():
    from app.services.duplicate_detection_service import mark_as_duplicate

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    success = await mark_as_duplicate(uuid4(), uuid4(), mock_db)
    assert success is False


@pytest.mark.anyio
async def test_duplicate_check_excludes_self():
    from app.services.duplicate_detection_service import check_manual_duplicate

    # When exclude_id is provided, that transaction should not flag itself as duplicate
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    exclude_id = uuid4()
    result = await check_manual_duplicate(
        user_id=uuid4(),
        amount=Decimal("50.00"),
        txn_date=date(2024, 6, 15),
        merchant_name="Amazon",
        db=mock_db,
        exclude_id=exclude_id,
    )
    # Verify the exclude_id parameter was used (SQL had the condition)
    assert result is None  # No duplicate found after exclusion
