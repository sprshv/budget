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
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4


def _make_breakdown_row(cat_id, name, color, total):
    row = MagicMock()
    row.id = cat_id
    row.name = name
    row.color = color
    row.total = Decimal(str(total))
    return row


@pytest.mark.anyio
async def test_spending_breakdown_calculates_percentages():
    from app.services.dashboard_service import get_spending_breakdown

    rows = [
        _make_breakdown_row(uuid4(), "Food", "#ff0000", "-300.00"),
        _make_breakdown_row(uuid4(), "Transport", "#0000ff", "-100.00"),
    ]

    mock_result = MagicMock()
    mock_result.all.return_value = rows

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_spending_breakdown(uuid4(), mock_db)

    assert result["total_spent"] == 400.0
    assert len(result["categories"]) == 2
    food = next(c for c in result["categories"] if c["name"] == "Food")
    assert food["amount"] == 300.0
    assert food["percentage"] == 75.0


@pytest.mark.anyio
async def test_spending_breakdown_empty_month():
    from app.services.dashboard_service import get_spending_breakdown

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await get_spending_breakdown(uuid4(), mock_db)

    assert result["total_spent"] == 0.0
    assert result["categories"] == []
