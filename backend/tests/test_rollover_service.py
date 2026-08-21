import sys
from unittest.mock import MagicMock

# Stub out plaid so imports don't fail without the package installed
sys.modules.setdefault("plaid", MagicMock())
sys.modules.setdefault("plaid.api", MagicMock())
sys.modules.setdefault("plaid.api.plaid_api", MagicMock())
sys.modules.setdefault("plaid.model", MagicMock())
sys.modules.setdefault("plaid.model.link_token_create_request", MagicMock())
sys.modules.setdefault("plaid.configuration", MagicMock())
sys.modules.setdefault("plaid.api_client", MagicMock())

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from uuid import uuid4


def _make_prog(category_id, spent, effective_limit):
    return {
        "budget_id": uuid4(),
        "category_id": category_id,
        "spent": spent,
        "effective_limit": effective_limit,
        "amount": effective_limit,
        "rollover_amount": 0.0,
        "remaining": effective_limit - spent,
        "percentage": (spent / effective_limit * 100) if effective_limit else 0,
        "status": "ok",
        "period_month": 7,
        "period_year": 2026,
    }


@pytest.mark.anyio
async def test_rollover_adds_unused_to_next_month():
    from app.services.rollover_service import apply_rollover_for_user

    user_id = uuid4()
    cat_id = uuid4()

    # Previous budget had $500 limit, $300 spent → $200 unused
    prog = _make_prog(cat_id, 300.0, 500.0)

    prev_budget = MagicMock()
    prev_budget.category_id = cat_id
    prev_budget.rollover_enabled = True

    curr_budget = MagicMock()
    curr_budget.category_id = cat_id
    curr_budget.rollover_amount = Decimal("0.00")

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    with patch("app.services.rollover_service.get_budget_progress", return_value=[prog]):
        with patch(
            "app.services.rollover_service.list_budgets",
            side_effect=[[prev_budget], [curr_budget]],
        ):
            updated = await apply_rollover_for_user(user_id, 8, 2026, mock_db)

    assert updated == 1
    assert curr_budget.rollover_amount == Decimal("200.00")
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_rollover_skips_non_rollover_budgets():
    from app.services.rollover_service import apply_rollover_for_user

    user_id = uuid4()
    cat_id = uuid4()

    prog = _make_prog(cat_id, 100.0, 500.0)

    prev_budget = MagicMock()
    prev_budget.category_id = cat_id
    prev_budget.rollover_enabled = False  # rollover disabled

    curr_budget = MagicMock()
    curr_budget.category_id = cat_id
    curr_budget.rollover_amount = Decimal("0.00")

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    with patch("app.services.rollover_service.get_budget_progress", return_value=[prog]):
        with patch(
            "app.services.rollover_service.list_budgets",
            side_effect=[[prev_budget], [curr_budget]],
        ):
            updated = await apply_rollover_for_user(user_id, 8, 2026, mock_db)

    assert updated == 0
    assert curr_budget.rollover_amount == Decimal("0.00")
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_rollover_skips_over_budget():
    from app.services.rollover_service import apply_rollover_for_user

    user_id = uuid4()
    cat_id = uuid4()

    # Spent more than limit → no unused → no rollover
    prog = _make_prog(cat_id, 600.0, 500.0)

    prev_budget = MagicMock()
    prev_budget.category_id = cat_id
    prev_budget.rollover_enabled = True

    curr_budget = MagicMock()
    curr_budget.category_id = cat_id
    curr_budget.rollover_amount = Decimal("0.00")

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    with patch("app.services.rollover_service.get_budget_progress", return_value=[prog]):
        with patch(
            "app.services.rollover_service.list_budgets",
            side_effect=[[prev_budget], [curr_budget]],
        ):
            updated = await apply_rollover_for_user(user_id, 8, 2026, mock_db)

    assert updated == 0
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_rollover_returns_zero_when_no_prev_budgets():
    from app.services.rollover_service import apply_rollover_for_user

    mock_db = AsyncMock()

    with patch(
        "app.services.rollover_service.get_budget_progress", return_value=[]
    ):
        updated = await apply_rollover_for_user(uuid4(), 8, 2026, mock_db)

    assert updated == 0
    mock_db.commit.assert_not_called()
