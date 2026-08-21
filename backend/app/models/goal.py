from sqlalchemy import Column, String, Boolean, Numeric, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    linked_account_id = Column(UUID(as_uuid=True))
    name = Column(String, nullable=False)
    goal_type = Column(String, nullable=False)  # savings, debt_payoff, emergency_fund, custom
    target_amount = Column(Numeric(12, 2), nullable=False)
    current_amount = Column(Numeric(12, 2), nullable=False, default=0)
    target_date = Column(Date)
    auto_contribute = Column(Boolean, nullable=False, default=False)
    auto_amount = Column(Numeric(12, 2))
    auto_frequency = Column(String)  # weekly, biweekly, monthly
    is_complete = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True))
    icon = Column(String)
    color = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
