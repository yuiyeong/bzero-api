"""0002 Create PointTransaction

Revision ID: 228808d53917
Revises: 08797d4b4a62
Create Date: 2025-11-20 21:57:08.318503

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "228808d53917"
down_revision: str | Sequence[str] | None = "08797d4b4a62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "point_transactions",
        sa.Column("point_transaction_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("balance_before", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("point_transaction_id"),
    )
    op.create_index("idx_transaction_user_status", "point_transactions", ["user_id", "status"], unique=False)
    op.create_index(
        "idx_transactions_reference", "point_transactions", ["reference_type", "reference_id"], unique=False
    )
    op.create_index("idx_transactions_user_created", "point_transactions", ["user_id", "created_at"], unique=False)
    op.create_index("idx_transactions_user_type", "point_transactions", ["user_id", "transaction_type"], unique=False)

    # Create trigger for users table
    op.execute("""
        CREATE TRIGGER update_point_transactions_updated_at
           BEFORE UPDATE ON point_transactions
           FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""

    # Drop trigger first (depends on table and function)
    op.execute("DROP TRIGGER IF EXISTS update_point_transactions_updated_at ON point_transactions;")

    op.drop_index("idx_transactions_user_type", table_name="point_transactions")
    op.drop_index("idx_transactions_user_created", table_name="point_transactions")
    op.drop_index("idx_transactions_reference", table_name="point_transactions")
    op.drop_index("idx_transaction_user_status", table_name="point_transactions")
    op.drop_table("point_transactions")
