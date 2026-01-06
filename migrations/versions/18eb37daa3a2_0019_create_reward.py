"""0019 Create Reward

Revision ID: 18eb37daa3a2
Revises: d37203dff9c9
Create Date: 2026-01-06 22:55:50.573987

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "18eb37daa3a2"
down_revision: str | Sequence[str] | None = "d37203dff9c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rewards",
        sa.Column("reward_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("point_transaction_id", sa.UUID(), nullable=True),
        sa.Column("reward_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["point_transaction_id"], ["point_transactions.point_transaction_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("reward_id"),
        sa.UniqueConstraint("user_id", "reward_type", "reference_date", name="uq_reward_user_type_date"),
    )
    op.create_index("ix_rewards_reference_date", "rewards", ["reference_date"], unique=False)
    op.create_index("ix_rewards_user_id", "rewards", ["user_id"], unique=False)

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_rewards_at
       BEFORE UPDATE
       ON rewards
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_rewards_at ON rewards;")

    op.drop_index("ix_rewards_user_id", table_name="rewards")
    op.drop_index("ix_rewards_reference_date", table_name="rewards")
    op.drop_table("rewards")
