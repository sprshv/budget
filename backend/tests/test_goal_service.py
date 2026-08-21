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
from datetime import date


def _make_goal(target=1000.0, current=250.0, is_complete=False):
    goal = MagicMock()
    goal.id = uuid4()
    goal.user_id = uuid4()
    goal.linked_account_id = None
    goal.name = "Vacation Fund"
    goal.goal_type = "savings"
    goal.target_amount = Decimal(str(target))
    goal.current_amount = Decimal(str(current))
    goal.target_date = date(2026, 12, 31)
    goal.auto_contribute = False
    goal.auto_amount = None
    goal.auto_frequency = None
    goal.is_complete = is_complete
    goal.completed_at = None
    goal.icon = "✈️"
    goal.color = "#22b780"
    goal.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
    goal.updated_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
    return goal


@pytest.mark.anyio
async def test_list_goals_returns_formatted_list():
    from app.services.goal_service import list_goals

    goal = _make_goal(target=1000.0, current=250.0)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [goal]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await list_goals(uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["name"] == "Vacation Fund"
    assert result[0]["percentage"] == 25.0  # 250/1000 * 100


@pytest.mark.anyio
async def test_create_goal_adds_to_db():
    from app.services.goal_service import create_goal
    from app.schemas.goal import GoalCreate

    data = GoalCreate(
        name="Emergency Fund",
        goal_type="emergency_fund",
        target_amount=Decimal("5000.00"),
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    async def mock_refresh(obj):
        obj.id = uuid4()
        obj.user_id = uuid4()
        obj.linked_account_id = None
        obj.current_amount = Decimal("0.00")
        obj.is_complete = False
        obj.completed_at = None
        obj.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")
        obj.updated_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")

    mock_db.refresh = mock_refresh

    result = await create_goal(uuid4(), data, mock_db)

    mock_db.add.assert_called_once()
    assert result["name"] == "Emergency Fund"
    assert result["goal_type"] == "emergency_fund"


@pytest.mark.anyio
async def test_get_goal_not_found_raises_404():
    from app.services.goal_service import get_goal
    from fastapi import HTTPException

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await get_goal(uuid4(), uuid4(), mock_db)

    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_contribution_updates_current_amount():
    from app.services.goal_service import add_contribution
    from app.schemas.goal import ContributionCreate

    goal = _make_goal(target=1000.0, current=250.0)
    data = ContributionCreate(amount=Decimal("100.00"))

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = goal

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    async def mock_refresh(obj):
        obj.id = uuid4()
        obj.goal_id = goal.id
        obj.amount = Decimal("100.00")
        obj.note = None
        obj.contributed_at = date.today()
        obj.created_at = MagicMock(isoformat=lambda: "2025-01-01T00:00:00")

    mock_db.refresh = mock_refresh

    result = await add_contribution(goal.id, goal.user_id, data, mock_db)

    # current_amount should be updated on the goal object
    assert float(goal.current_amount) == 350.0
    assert result["amount"] == 100.0


@pytest.mark.anyio
async def test_goal_progress_calculates_fields():
    from app.services.goal_service import get_goal_progress

    goal = MagicMock()
    goal.id = uuid4()
    goal.user_id = uuid4()
    goal.target_amount = Decimal("1000.00")
    goal.current_amount = Decimal("400.00")
    goal.target_date = date(2026, 12, 31)
    goal.is_complete = False
    goal.name = "Test Goal"

    goal_result = MagicMock()
    goal_result.scalar_one_or_none.return_value = goal

    contrib_row = MagicMock()
    contrib_row.__getitem__ = lambda self, i: [5, Decimal("400.00")][i]

    contrib_result = MagicMock()
    contrib_result.one.return_value = contrib_row

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return goal_result
        return contrib_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_goal_progress(goal.id, goal.user_id, mock_db)

    assert result["percentage"] == 40.0
    assert result["remaining"] == 600.0
    assert result["days_remaining"] is not None and result["days_remaining"] > 0
    assert result["required_monthly"] is not None and result["required_monthly"] > 0


@pytest.mark.anyio
async def test_goal_progress_not_found_raises_404():
    from app.services.goal_service import get_goal_progress
    from fastapi import HTTPException

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await get_goal_progress(uuid4(), uuid4(), mock_db)

    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_goal_forecast_no_contributions_returns_none_rate():
    from app.services.goal_service import get_goal_forecast

    goal = MagicMock()
    goal.id = uuid4()
    goal.user_id = uuid4()
    goal.target_amount = Decimal("5000.00")
    goal.current_amount = Decimal("0.00")
    goal.target_date = None
    goal.is_complete = False

    goal_result = MagicMock()
    goal_result.scalar_one_or_none.return_value = goal

    contrib_row = MagicMock()
    contrib_row.total = None
    contrib_row.first_date = None

    contrib_result = MagicMock()
    contrib_result.one.return_value = contrib_row

    call_count = 0

    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return goal_result
        return contrib_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await get_goal_forecast(goal.id, goal.user_id, mock_db)

    assert result["monthly_rate"] is None
    assert result["projected_completion_date"] is None
    assert result["is_complete"] is False


@pytest.mark.anyio
async def test_list_contributions_returns_formatted_list():
    from app.services.goal_service import list_contributions
    from datetime import date

    # First execute: ownership check
    ownership_result = MagicMock()
    ownership_result.scalar.return_value = uuid4()

    # Second execute: contributions
    contrib = MagicMock()
    contrib.id = uuid4()
    contrib.goal_id = uuid4()
    contrib.amount = Decimal("150.00")
    contrib.note = "January savings"
    contrib.contributed_at = MagicMock()
    contrib.contributed_at.isoformat = lambda: "2025-01-15"
    contrib.created_at = MagicMock()
    contrib.created_at.isoformat = lambda: "2025-01-15T00:00:00"

    contrib_result = MagicMock()
    contrib_result.scalars.return_value.all.return_value = [contrib]

    call_count = 0
    async def mock_execute(query):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ownership_result
        return contrib_result

    mock_db = AsyncMock()
    mock_db.execute = mock_execute

    result = await list_contributions(uuid4(), uuid4(), mock_db)

    assert len(result) == 1
    assert result[0]["amount"] == 150.0
    assert result[0]["note"] == "January savings"


@pytest.mark.anyio
async def test_list_contributions_unknown_goal_raises_404():
    from app.services.goal_service import list_contributions
    from fastapi import HTTPException

    ownership_result = MagicMock()
    ownership_result.scalar.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=ownership_result)

    with pytest.raises(HTTPException) as exc_info:
        await list_contributions(uuid4(), uuid4(), mock_db)

    assert exc_info.value.status_code == 404
