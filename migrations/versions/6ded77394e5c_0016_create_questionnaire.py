"""0016 Create Questionnaire

Revision ID: 6ded77394e5c
Revises: 2e9f761e7765
Create Date: 2025-12-23 12:45:13.981307

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6ded77394e5c"
down_revision: str | Sequence[str] | None = "2e9f761e7765"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "questionnaires",
        sa.Column("questionnaire_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("room_stay_id", sa.UUID(), nullable=False),
        sa.Column("city_question_id", sa.UUID(), nullable=False),
        sa.Column("city_question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("guest_house_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.city_id"],
        ),
        sa.ForeignKeyConstraint(
            ["city_question_id"],
            ["city_questions.city_question_id"],
        ),
        sa.ForeignKeyConstraint(
            ["guest_house_id"],
            ["guest_houses.guest_house_id"],
        ),
        sa.ForeignKeyConstraint(
            ["room_stay_id"],
            ["room_stays.room_stay_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("questionnaire_id"),
    )
    op.create_index(
        "uq_questionnaires_room_stay_question_active",
        "questionnaires",
        ["room_stay_id", "city_question_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_questionnaires_updated_at
       BEFORE UPDATE
       ON questionnaires
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_questionnaires_updated_at ON questionnaires;")

    op.drop_index(
        "uq_questionnaires_room_stay_question_active",
        table_name="questionnaires",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("questionnaires")
