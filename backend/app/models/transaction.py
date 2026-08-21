from sqlalchemy import Column, String, Boolean, Numeric, Date, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    category_id = Column(UUID(as_uuid=True))
    plaid_transaction_id = Column(String, unique=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    merchant_name = Column(String)
    pending = Column(Boolean, nullable=False, default=False)
    category_confidence = Column(Numeric(3, 2))
    is_manual = Column(Boolean, nullable=False, default=False)
    is_recurring = Column(Boolean, nullable=False, default=False)
    is_duplicate = Column(Boolean, nullable=False, default=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    notes = Column(Text)
    tags = Column(ARRAY(String))
    receipt_url = Column(String)
    is_tax_deductible = Column(Boolean, nullable=False, default=False)
    tax_category = Column(String)
    merchant_city = Column(String)
    merchant_state = Column(String)
    merchant_country = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
