"""0003 Create PointTransaction

Revision ID: 1cfafe0b369e
Revises: 019aa594c20e
Create Date: 2025-11-24 13:50:23.690464

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1cfafe0b369e"
down_revision: str | Sequence[str] | None = "019aa594c20e"
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
    op.drop_index(
        op.f("idx_cities_is_active_display_order"), table_name="cities", postgresql_where="(deleted_at IS NULL)"
    )
    # Create trigger for point transaction table
    op.execute("""
    CREATE TRIGGER update_point_transactions_updated_at
       BEFORE UPDATE ON point_transactions
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS update_point_transactions_updated_at ON point_transactions;")

    op.create_index(
        op.f("idx_cities_is_active_display_order"),
        "cities",
        ["is_active", "display_order"],
        unique=False,
        postgresql_where="(deleted_at IS NULL)",
    )
    op.drop_index("idx_transactions_user_type", table_name="point_transactions")
    op.drop_index("idx_transactions_user_created", table_name="point_transactions")
    op.drop_index("idx_transactions_reference", table_name="point_transactions")
    op.drop_index("idx_transaction_user_status", table_name="point_transactions")
    op.drop_table("point_transactions")
    # ### end Alembic commands ###
