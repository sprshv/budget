"""add recurring transactions table

Revision ID: 20250802_recurring
Revises: 20250801_goals
Create Date: 2025-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250802_recurring"
down_revision = "20250801_goals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("merchant_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("average_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default="USD"),
        sa.Column("frequency", sa.Text(), nullable=False),
        sa.Column("last_date", sa.Date(), nullable=True),
        sa.Column("next_expected_date", sa.Date(), nullable=True),
        sa.Column("is_subscription", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_bill", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("remind_days_before", sa.Integer(), nullable=True, server_default="3"),
        sa.Column("alert_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_recurring_transactions_user_id", "recurring_transactions", ["user_id"])
    op.create_index("idx_recurring_transactions_next_expected_date", "recurring_transactions", ["next_expected_date"])
    op.create_index("idx_recurring_transactions_user_merchant", "recurring_transactions", ["user_id", "merchant_name"])


def downgrade() -> None:
    op.drop_index("idx_recurring_transactions_user_merchant", table_name="recurring_transactions")
    op.drop_index("idx_recurring_transactions_next_expected_date", table_name="recurring_transactions")
    op.drop_index("idx_recurring_transactions_user_id", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")
