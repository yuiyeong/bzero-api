"""0015 Create CityQuestion

Revision ID: 2e9f761e7765
Revises: fd76fc635285
Create Date: 2025-12-23 12:42:52.555709

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2e9f761e7765"
down_revision: str | Sequence[str] | None = "fd76fc635285"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "city_questions",
        sa.Column("city_question_id", sa.UUID(), nullable=False),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.city_id"]),
        sa.PrimaryKeyConstraint("city_question_id"),
    )
    op.create_index(
        "uq_city_questions_city_id_display_order_active",
        "city_questions",
        ["city_id", "display_order"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_city_questions_updated_at
       BEFORE UPDATE
       ON city_questions
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_city_questions_updated_at ON city_questions;")

    op.drop_index(
        "uq_city_questions_city_id_display_order_active",
        table_name="city_questions",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("city_questions")
