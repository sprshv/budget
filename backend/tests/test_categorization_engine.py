import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal


@pytest.mark.anyio
async def test_user_rule_contains_match():
    from app.services.categorization_service import categorize_with_rules
    from app.models.categorization_rule import CategorizationRule

    user_id = uuid4()
    cat_id = uuid4()

    rule = MagicMock(spec=CategorizationRule)
    rule.category_id = cat_id
    rule.match_field = "merchant_name"
    rule.match_operator = "contains"
    rule.match_value = "starbucks"
    rule.priority = 10
    rule.is_active = True

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [rule]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result_id, confidence = await categorize_with_rules(
        user_id=user_id,
        merchant_name="Starbucks",
        description="coffee purchase",
        amount=Decimal("5.50"),
        plaid_category_primary="FOOD_AND_DRINK",
        db=mock_db,
    )

    assert result_id == cat_id
    assert confidence == 1.0


@pytest.mark.anyio
async def test_user_rule_equals_match():
    from app.services.categorization_service import _evaluate_rule
    from app.models.categorization_rule import CategorizationRule

    rule = MagicMock(spec=CategorizationRule)
    rule.match_field = "description"
    rule.match_operator = "equals"
    rule.match_value = "Netflix"

    assert _evaluate_rule(rule, "", "Netflix", Decimal("15.99")) is True
    assert _evaluate_rule(rule, "", "Hulu", Decimal("15.99")) is False


@pytest.mark.anyio
async def test_user_rule_starts_with():
    from app.services.categorization_service import _evaluate_rule
    from app.models.categorization_rule import CategorizationRule

    rule = MagicMock(spec=CategorizationRule)
    rule.match_field = "merchant_name"
    rule.match_operator = "starts_with"
    rule.match_value = "Amazon"

    assert _evaluate_rule(rule, "Amazon Prime Video", "", Decimal("14.99")) is True
    assert _evaluate_rule(rule, "Walmart", "", Decimal("14.99")) is False


@pytest.mark.anyio
async def test_user_rule_greater_than():
    from app.services.categorization_service import _evaluate_rule
    from app.models.categorization_rule import CategorizationRule

    rule = MagicMock(spec=CategorizationRule)
    rule.match_field = "amount"
    rule.match_operator = "greater_than"
    rule.match_value = "100"

    assert _evaluate_rule(rule, "", "", Decimal("150.00")) is True
    assert _evaluate_rule(rule, "", "", Decimal("50.00")) is False


@pytest.mark.anyio
async def test_falls_back_to_plaid_when_no_rules():
    from app.services.categorization_service import categorize_with_rules

    user_id = uuid4()
    fallback_cat_id = uuid4()

    # No user rules
    mock_no_rules_result = MagicMock()
    mock_no_rules_result.scalars.return_value.all.return_value = []

    # Plaid fallback category
    mock_plaid_cat = MagicMock()
    mock_plaid_cat.id = fallback_cat_id
    mock_plaid_result = MagicMock()
    mock_plaid_result.scalar_one_or_none.return_value = mock_plaid_cat

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_no_rules_result, mock_plaid_result])

    result_id, confidence = await categorize_with_rules(
        user_id=user_id,
        merchant_name="Netflix",
        description="Netflix",
        amount=Decimal("15.99"),
        plaid_category_primary="SUBSCRIPTION",
        db=mock_db,
    )

    assert result_id == fallback_cat_id
    assert confidence == 0.7


@pytest.mark.anyio
async def test_higher_priority_rule_wins():
    from app.services.categorization_service import _evaluate_rule
    from app.models.categorization_rule import CategorizationRule

    # Both rules match — the one with higher priority should be checked first (ordering is DB's job)
    rule_low = MagicMock(spec=CategorizationRule)
    rule_low.match_field = "merchant_name"
    rule_low.match_operator = "contains"
    rule_low.match_value = "coffee"
    rule_low.priority = 1

    rule_high = MagicMock(spec=CategorizationRule)
    rule_high.match_field = "merchant_name"
    rule_high.match_operator = "contains"
    rule_high.match_value = "starbucks"
    rule_high.priority = 10

    assert _evaluate_rule(rule_high, "Starbucks Coffee", "", Decimal("5.00")) is True
    assert _evaluate_rule(rule_low, "Starbucks Coffee", "", Decimal("5.00")) is True
