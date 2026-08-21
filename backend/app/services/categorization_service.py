from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.category import Category
from app.models.categorization_rule import CategorizationRule
from decimal import Decimal
from typing import Optional
import uuid

# Plaid primary category -> our system category name mapping
PLAID_CATEGORY_MAP = {
    "FOOD_AND_DRINK": "Food & Dining",
    "GROCERIES": "Groceries",
    "TRANSPORTATION": "Transportation",
    "GAS_STATIONS": "Gas",
    "RENT_AND_UTILITIES": "Utilities",
    "ENTERTAINMENT": "Entertainment",
    "SUBSCRIPTION": "Subscriptions",
    "GENERAL_MERCHANDISE": "Shopping",
    "MEDICAL": "Health & Medical",
    "TRAVEL": "Travel",
    "EDUCATION": "Education",
    "PERSONAL_CARE": "Personal Care",
    "GIFTS_AND_DONATIONS": "Gifts & Donations",
    "BUSINESS_AND_PROFESSIONAL_SERVICES": "Business",
    "GOVERNMENT_AND_NON_PROFIT": "Taxes",
    "INVESTMENTS": "Investments",
    "TRANSFER_IN": "Other Income",
    "INCOME": "Paycheck",
    "LOAN_PAYMENTS": "Housing",
}


async def get_category_by_name(name: str, db: AsyncSession) -> Optional[Category]:
    result = await db.execute(
        select(Category).where(Category.name == name, Category.is_system == True)
    )
    return result.scalar_one_or_none()


async def categorize_transaction(
    plaid_category_primary: Optional[str],
    db: AsyncSession,
) -> tuple[Optional[uuid.UUID], float]:
    """Returns (category_id, confidence). Falls back to Uncategorized."""
    if plaid_category_primary:
        our_name = PLAID_CATEGORY_MAP.get(plaid_category_primary)
        if our_name:
            cat = await get_category_by_name(our_name, db)
            if cat:
                return cat.id, 0.7

    # Fallback: Uncategorized
    cat = await get_category_by_name("Uncategorized", db)
    if cat:
        return cat.id, 0.3
    return None, 0.0


def _evaluate_rule(rule: CategorizationRule, merchant_name: str, description: str, amount: Decimal) -> bool:
    """Return True if the transaction matches the rule."""
    field_map = {
        "merchant_name": merchant_name or "",
        "description": description or "",
        "amount": str(amount),
    }
    field_value = field_map.get(rule.match_field, "")
    match_value = rule.match_value

    operator = rule.match_operator
    if operator == "contains":
        return match_value.lower() in field_value.lower()
    elif operator == "equals":
        return field_value.lower() == match_value.lower()
    elif operator == "starts_with":
        return field_value.lower().startswith(match_value.lower())
    elif operator == "greater_than":
        try:
            return Decimal(field_value) > Decimal(match_value)
        except Exception:
            return False
    return False


async def categorize_with_rules(
    user_id: uuid.UUID,
    merchant_name: str,
    description: str,
    amount: Decimal,
    plaid_category_primary: Optional[str],
    db,
) -> tuple[Optional[uuid.UUID], float]:
    """
    Full categorization pipeline:
    1. User rules (priority DESC) -> confidence 1.0
    2. Plaid category map -> confidence 0.7
    3. Uncategorized -> confidence 0.3
    """
    # Step 1: User rules
    result = await db.execute(
        select(CategorizationRule).where(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True,
        ).order_by(CategorizationRule.priority.desc())
    )
    rules = result.scalars().all()

    for rule in rules:
        if _evaluate_rule(rule, merchant_name, description, amount):
            return rule.category_id, 1.0

    # Step 2: Plaid category
    return await categorize_transaction(plaid_category_primary, db)
