from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from decimal import Decimal
import uuid
from datetime import date, datetime, timezone


async def list_goals(user_id: uuid.UUID, db: AsyncSession) -> list:
    from app.models.goal import Goal

    result = await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
    )
    goals = result.scalars().all()
    return [_format_goal(g) for g in goals]


async def create_goal(user_id: uuid.UUID, data, db: AsyncSession) -> dict:
    from app.models.goal import Goal

    goal = Goal(
        user_id=user_id,
        name=data.name,
        goal_type=data.goal_type,
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        target_date=data.target_date,
        linked_account_id=data.linked_account_id,
        auto_contribute=data.auto_contribute,
        auto_amount=data.auto_amount,
        auto_frequency=data.auto_frequency,
        icon=data.icon,
        color=data.color,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return _format_goal(goal)


async def get_goal(goal_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.goal import Goal

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
            headers={"X-Error-Code": "GOAL_NOT_FOUND"},
        )
    return _format_goal(goal)


async def update_goal(goal_id: uuid.UUID, user_id: uuid.UUID, data, db: AsyncSession) -> dict:
    from app.models.goal import Goal

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
            headers={"X-Error-Code": "GOAL_NOT_FOUND"},
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)

    # Auto-mark complete if current >= target
    if (
        Decimal(str(goal.current_amount)) >= Decimal(str(goal.target_amount))
        and not goal.is_complete
    ):
        goal.is_complete = True
        goal.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(goal)
    return _format_goal(goal)


async def delete_goal(goal_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    from app.models.goal import Goal

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
            headers={"X-Error-Code": "GOAL_NOT_FOUND"},
        )
    await db.delete(goal)
    await db.commit()


async def add_contribution(
    goal_id: uuid.UUID, user_id: uuid.UUID, data, db: AsyncSession
) -> dict:
    from app.models.goal import Goal
    from app.models.goal_contribution import GoalContribution

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
            headers={"X-Error-Code": "GOAL_NOT_FOUND"},
        )

    contrib = GoalContribution(
        goal_id=goal_id,
        user_id=user_id,
        amount=data.amount,
        note=data.note,
        contributed_at=data.contributed_at or date.today(),
    )
    db.add(contrib)

    # Update current_amount
    goal.current_amount = Decimal(str(goal.current_amount)) + Decimal(str(data.amount))

    # Auto-complete
    if (
        Decimal(str(goal.current_amount)) >= Decimal(str(goal.target_amount))
        and not goal.is_complete
    ):
        goal.is_complete = True
        goal.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(contrib)

    return {
        "id": str(contrib.id),
        "goal_id": str(contrib.goal_id),
        "amount": float(contrib.amount),
        "note": contrib.note,
        "contributed_at": contrib.contributed_at.isoformat(),
        "created_at": contrib.created_at.isoformat(),
    }


async def get_goal_progress(goal_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.goal import Goal
    from app.models.goal_contribution import GoalContribution

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
            headers={"X-Error-Code": "GOAL_NOT_FOUND"},
        )

    target = float(goal.target_amount or 0)
    current = float(goal.current_amount or 0)
    remaining = max(0.0, target - current)
    percentage = round(min(current / target * 100, 100), 1) if target > 0 else 0.0

    # Days remaining to target_date
    days_remaining = None
    if goal.target_date and not goal.is_complete:
        today = date.today()
        days_remaining = (goal.target_date - today).days
        if days_remaining < 0:
            days_remaining = 0

    # Required monthly contribution to hit target by target_date
    required_monthly = None
    if goal.target_date and not goal.is_complete and days_remaining and days_remaining > 0:
        months_remaining = days_remaining / 30.44
        if months_remaining > 0:
            required_monthly = round(remaining / months_remaining, 2)

    # Contribution count and total
    contrib_result = await db.execute(
        select(func.count(GoalContribution.id), func.sum(GoalContribution.amount)).where(
            GoalContribution.goal_id == goal_id,
            GoalContribution.user_id == user_id,
        )
    )
    contrib_row = contrib_result.one()
    contribution_count = contrib_row[0] or 0
    total_contributed = float(contrib_row[1] or 0)

    return {
        "goal_id": str(goal.id),
        "name": goal.name,
        "percentage": percentage,
        "current_amount": current,
        "target_amount": target,
        "remaining": remaining,
        "days_remaining": days_remaining,
        "required_monthly": required_monthly,
        "is_complete": goal.is_complete,
        "contribution_count": contribution_count,
        "total_contributed": total_contributed,
    }


async def get_goal_forecast(goal_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> dict:
    from app.models.goal import Goal
    from app.models.goal_contribution import GoalContribution
    from datetime import timedelta

    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
            headers={"X-Error-Code": "GOAL_NOT_FOUND"},
        )

    target = float(goal.target_amount or 0)
    current = float(goal.current_amount or 0)
    remaining = max(0.0, target - current)

    if goal.is_complete:
        return {
            "goal_id": str(goal.id),
            "is_complete": True,
            "projected_completion_date": goal.completed_at.date().isoformat() if goal.completed_at else None,
            "monthly_rate": None,
            "months_to_completion": None,
            "on_track": True,
        }

    # Compute average monthly contribution from history
    contrib_result = await db.execute(
        select(
            func.sum(GoalContribution.amount).label("total"),
            func.min(GoalContribution.contributed_at).label("first_date"),
        ).where(
            GoalContribution.goal_id == goal_id,
            GoalContribution.user_id == user_id,
        )
    )
    row = contrib_result.one()
    total_contributed = float(row.total or 0)
    first_date = row.first_date

    monthly_rate = None
    projected_completion_date = None
    months_to_completion = None
    on_track = None

    if first_date and total_contributed > 0:
        today = date.today()
        days_tracked = max(1, (today - first_date).days)
        monthly_rate = round(total_contributed / days_tracked * 30.44, 2)

        if monthly_rate > 0 and remaining > 0:
            months_to_completion = remaining / monthly_rate
            projected_date = today + timedelta(days=months_to_completion * 30.44)
            projected_completion_date = projected_date.isoformat()
            months_to_completion = round(months_to_completion, 1)

            # On track = projected date is before or on target_date
            if goal.target_date:
                on_track = projected_date.date() <= goal.target_date
        elif remaining <= 0:
            months_to_completion = 0
            projected_completion_date = today.isoformat()
            on_track = True

    return {
        "goal_id": str(goal.id),
        "is_complete": False,
        "projected_completion_date": projected_completion_date,
        "monthly_rate": monthly_rate,
        "months_to_completion": months_to_completion,
        "on_track": on_track,
    }


async def list_contributions(
    goal_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession,
    limit: int = 50, offset: int = 0
) -> list[dict]:
    from app.models.goal import Goal
    from app.models.goal_contribution import GoalContribution

    # Verify ownership
    result = await db.execute(
        select(Goal.id).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    if result.scalar() is None:
        raise HTTPException(status_code=404, detail="Goal not found", headers={"X-Error-Code": "GOAL_NOT_FOUND"})

    contrib_result = await db.execute(
        select(GoalContribution)
        .where(GoalContribution.goal_id == goal_id, GoalContribution.user_id == user_id)
        .order_by(GoalContribution.contributed_at.desc(), GoalContribution.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    contribs = contrib_result.scalars().all()

    return [
        {
            "id": str(c.id),
            "goal_id": str(c.goal_id),
            "amount": float(c.amount),
            "note": c.note,
            "contributed_at": c.contributed_at.isoformat(),
            "created_at": c.created_at.isoformat(),
        }
        for c in contribs
    ]


def _format_goal(goal) -> dict:
    target = float(goal.target_amount or 0)
    current = float(goal.current_amount or 0)
    percentage = round(min(current / target * 100, 100), 1) if target > 0 else 0.0
    return {
        "id": str(goal.id),
        "user_id": str(goal.user_id),
        "linked_account_id": str(goal.linked_account_id) if goal.linked_account_id else None,
        "name": goal.name,
        "goal_type": goal.goal_type,
        "target_amount": target,
        "current_amount": current,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "auto_contribute": goal.auto_contribute,
        "auto_amount": float(goal.auto_amount) if goal.auto_amount else None,
        "auto_frequency": goal.auto_frequency,
        "is_complete": goal.is_complete,
        "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
        "icon": goal.icon,
        "color": goal.color,
        "percentage": percentage,
        "created_at": goal.created_at.isoformat(),
        "updated_at": goal.updated_at.isoformat(),
    }
