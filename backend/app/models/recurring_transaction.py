from sqlalchemy import Column, String, Boolean, Numeric, Date, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    category_id = Column(UUID(as_uuid=True))
    merchant_name = Column(String, nullable=False)
    description = Column(Text)
    average_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    frequency = Column(String, nullable=False)  # weekly, biweekly, monthly, quarterly, annual
    last_date = Column(Date)
    next_expected_date = Column(Date)
    is_subscription = Column(Boolean, nullable=False, default=False)
    is_bill = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    remind_days_before = Column(Integer, default=3)
    alert_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
