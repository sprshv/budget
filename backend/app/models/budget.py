from sqlalchemy import Column, Boolean, Numeric, Integer, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    category_id = Column(UUID(as_uuid=True), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)
    period_month = Column(Integer, nullable=False)
    period_year = Column(Integer, nullable=False)

    # Rollover
    rollover_enabled = Column(Boolean, nullable=False, default=False)
    rollover_amount = Column(Numeric(12, 2), default=0)

    # Alerts
    alert_threshold = Column(Numeric(3, 2), default=0.80)
    alert_sent = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "period_month", "period_year", name="uq_budget_user_category_period"),
    )
