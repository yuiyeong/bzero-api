"""0004 Create UserIdentity

Revision ID: 282e91370e30
Revises: 1cfafe0b369e
Create Date: 2025-11-25 12:27:03.577614

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "282e91370e30"
down_revision: str | Sequence[str] | None = "1cfafe0b369e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_identities",
        sa.Column("identity_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("identity_id"),
    )
    op.create_index(
        "idx_user_identities_provider_user",
        "user_identities",
        ["provider", "provider_user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    # Create trigger for cities table (updated_at 자동 업데이트)
    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
        CREATE TRIGGER update_user_identities_updated_at
            BEFORE UPDATE ON user_identities
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS update_user_identities_updated_at ON user_identities;")
    op.drop_index(
        "idx_user_identities_provider_user",
        table_name="user_identities",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("user_identities")
