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
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import uuid4


@pytest.mark.anyio
async def test_create_budget_adds_and_commits():
    from app.services.budget_service import create_budget

    mock_budget = MagicMock()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("app.services.budget_service.Budget", return_value=mock_budget):
        result = await create_budget(
            user_id=uuid4(),
            data={
                "category_id": uuid4(),
                "amount": Decimal("500.00"),
                "period_month": 8,
                "period_year": 2026,
                "rollover_enabled": False,
                "alert_threshold": Decimal("0.80"),
            },
            db=mock_db,
        )

    mock_db.add.assert_called_once_with(mock_budget)
    mock_db.commit.assert_called_once()
    assert result == mock_budget


@pytest.mark.anyio
async def test_update_budget_raises_if_not_found():
    from app.services.budget_service import update_budget

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="Budget not found"):
        await update_budget(uuid4(), uuid4(), {"amount": Decimal("200.00")}, mock_db)


@pytest.mark.anyio
async def test_delete_budget_raises_if_not_found():
    from app.services.budget_service import delete_budget

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="Budget not found"):
        await delete_budget(uuid4(), uuid4(), mock_db)


@pytest.mark.anyio
async def test_auto_create_returns_existing_if_present():
    from app.services.budget_service import auto_create_from_previous

    existing_budget = MagicMock()
    with patch("app.services.budget_service.list_budgets", return_value=[existing_budget]):
        mock_db = AsyncMock()
        result = await auto_create_from_previous(uuid4(), 8, 2026, mock_db)

    assert result == [existing_budget]
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_auto_create_copies_from_previous_month():
    from app.services.budget_service import auto_create_from_previous

    prev_budget = MagicMock()
    prev_budget.category_id = uuid4()
    prev_budget.amount = Decimal("300.00")
    prev_budget.rollover_enabled = True
    prev_budget.alert_threshold = Decimal("0.80")

    call_count = 0

    async def mock_list_budgets(user_id, month, year, db):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return []  # no current month budgets
        return [prev_budget]  # previous month has budgets

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("app.services.budget_service.list_budgets", side_effect=mock_list_budgets):
        with patch("app.services.budget_service.Budget", return_value=MagicMock()):
            result = await auto_create_from_previous(uuid4(), 8, 2026, mock_db)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
