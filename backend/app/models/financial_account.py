from sqlalchemy import Column, String, Boolean, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    plaid_item_id = Column(String)
    plaid_account_id = Column(String, unique=True)
    plaid_access_token = Column(Text)       # Fernet encrypted
    plaid_cursor = Column(String)
    name = Column(String, nullable=False)
    official_name = Column(String)
    nickname = Column(String)
    institution_name = Column(String)
    institution_logo = Column(String)
    account_type = Column(String, nullable=False)
    account_subtype = Column(String)
    is_manual = Column(Boolean, nullable=False, default=False)
    balance_current = Column(Numeric(12, 2))
    balance_available = Column(Numeric(12, 2))
    balance_limit = Column(Numeric(12, 2))
    is_active = Column(Boolean, nullable=False, default=True)
    last_synced_at = Column(DateTime(timezone=True))
    sync_status = Column(String, default="ok")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
