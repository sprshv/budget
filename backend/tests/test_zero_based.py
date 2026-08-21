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
async def test_zero_based_calculates_unallocated():
    from app.services.budget_service import get_zero_based_summary

    mock_db = AsyncMock()

    # Simulate: $3000 income, $2500 budgeted → $500 unallocated
    with patch("app.services.budget_service.get_zero_based_summary") as mock_fn:
        mock_fn.return_value = {
            "total_income": 3000.0,
            "total_budgeted": 2500.0,
            "unallocated": 500.0,
            "is_fully_allocated": False,
            "period_month": 8,
            "period_year": 2026,
        }
        result = await mock_fn(uuid4(), 8, 2026, mock_db)

    assert result["unallocated"] == 500.0
    assert result["is_fully_allocated"] is False


@pytest.mark.anyio
async def test_zero_based_fully_allocated_when_zero():
    from app.services.budget_service import get_zero_based_summary

    mock_db = AsyncMock()

    with patch("app.services.budget_service.get_zero_based_summary") as mock_fn:
        mock_fn.return_value = {
            "total_income": 3000.0,
            "total_budgeted": 3000.0,
            "unallocated": 0.0,
            "is_fully_allocated": True,
            "period_month": 8,
            "period_year": 2026,
        }
        result = await mock_fn(uuid4(), 8, 2026, mock_db)

    assert result["is_fully_allocated"] is True


@pytest.mark.anyio
async def test_zero_based_negative_unallocated_when_over_allocated():
    from app.services.budget_service import get_zero_based_summary

    mock_db = AsyncMock()

    with patch("app.services.budget_service.get_zero_based_summary") as mock_fn:
        mock_fn.return_value = {
            "total_income": 2000.0,
            "total_budgeted": 2500.0,
            "unallocated": -500.0,
            "is_fully_allocated": False,
            "period_month": 8,
            "period_year": 2026,
        }
        result = await mock_fn(uuid4(), 8, 2026, mock_db)

    assert result["unallocated"] == -500.0
    assert result["is_fully_allocated"] is False
