from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.categorization_rule import CategorizationRule
import uuid


async def list_rules(user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(
        select(CategorizationRule)
        .where(CategorizationRule.user_id == user_id)
        .order_by(CategorizationRule.priority.desc(), CategorizationRule.created_at)
    )
    return result.scalars().all()


async def create_rule(user_id: uuid.UUID, data: dict, db: AsyncSession) -> CategorizationRule:
    # Map API field 'operator' -> model column 'match_operator'
    model_data = {k: v for k, v in data.items()}
    if "operator" in model_data:
        model_data["match_operator"] = model_data.pop("operator")
    rule = CategorizationRule(user_id=user_id, **model_data)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def update_rule(
    rule_id: uuid.UUID, user_id: uuid.UUID, data: dict, db: AsyncSession
) -> CategorizationRule:
    result = await db.execute(
        select(CategorizationRule).where(
            CategorizationRule.id == rule_id,
            CategorizationRule.user_id == user_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise ValueError("Rule not found")
    # Map API field 'operator' -> model column 'match_operator'
    update_data = {k: v for k, v in data.items()}
    if "operator" in update_data:
        update_data["match_operator"] = update_data.pop("operator")
    for field, value in update_data.items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_rule(rule_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(CategorizationRule).where(
            CategorizationRule.id == rule_id,
            CategorizationRule.user_id == user_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise ValueError("Rule not found")
    await db.delete(rule)
    await db.commit()
