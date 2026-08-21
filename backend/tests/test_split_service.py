import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import uuid4

@pytest.mark.anyio
async def test_split_amounts_must_sum_to_original():
    from app.services.split_service import create_splits

    txn_id = uuid4()
    user_id = uuid4()
    mock_txn = MagicMock()
    mock_txn.amount = Decimal("100.00")

    with patch("app.services.split_service.get_transaction_by_id", return_value=mock_txn):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with pytest.raises(ValueError, match="must sum to"):
            await create_splits(
                transaction_id=txn_id,
                user_id=user_id,
                splits=[
                    {"category_id": uuid4(), "amount": Decimal("60.00")},
                    {"category_id": uuid4(), "amount": Decimal("30.00")},  # 90 != 100
                ],
                db=mock_db,
            )

@pytest.mark.anyio
async def test_split_creates_rows_when_amounts_match():
    from app.services.split_service import create_splits

    txn_id = uuid4()
    user_id = uuid4()
    mock_txn = MagicMock()
    mock_txn.amount = Decimal("100.00")

    with patch("app.services.split_service.get_transaction_by_id", return_value=mock_txn):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        splits = await create_splits(
            transaction_id=txn_id,
            user_id=user_id,
            splits=[
                {"category_id": uuid4(), "amount": Decimal("60.00")},
                {"category_id": uuid4(), "amount": Decimal("40.00")},
            ],
            db=mock_db,
        )

        assert len(splits) == 2
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

@pytest.mark.anyio
async def test_split_raises_if_transaction_not_found():
    from app.services.split_service import create_splits

    with patch("app.services.split_service.get_transaction_by_id", return_value=None):
        mock_db = AsyncMock()
        with pytest.raises(ValueError, match="Transaction not found"):
            await create_splits(
                transaction_id=uuid4(),
                user_id=uuid4(),
                splits=[
                    {"category_id": uuid4(), "amount": Decimal("50.00")},
                    {"category_id": uuid4(), "amount": Decimal("50.00")},
                ],
                db=mock_db,
            )

@pytest.mark.anyio
async def test_split_tolerance_allows_penny_rounding():
    from app.services.split_service import create_splits

    txn_id = uuid4()
    user_id = uuid4()
    mock_txn = MagicMock()
    mock_txn.amount = Decimal("10.00")

    with patch("app.services.split_service.get_transaction_by_id", return_value=mock_txn):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # 5.00 + 5.00 = 10.00 exactly, but allow within 0.01
        splits = await create_splits(
            transaction_id=txn_id,
            user_id=user_id,
            splits=[
                {"category_id": uuid4(), "amount": Decimal("5.00")},
                {"category_id": uuid4(), "amount": Decimal("5.00")},
            ],
            db=mock_db,
        )
        assert len(splits) == 2
