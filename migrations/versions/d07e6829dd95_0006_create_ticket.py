"""0006 Create Ticket

Revision ID: d07e6829dd95
Revises: 9b94381f2c77
Create Date: 2025-12-06 20:52:10.510587

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d07e6829dd95"
down_revision: str | Sequence[str] | None = "9b94381f2c77"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tickets",
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("city_name", sa.String(length=100), nullable=False),
        sa.Column("city_theme", sa.String(length=100), nullable=False),
        sa.Column("city_description", sa.Text(), nullable=True),
        sa.Column("city_image_url", sa.String(length=500), nullable=True),
        sa.Column("city_base_cost_points", sa.Integer(), nullable=False),
        sa.Column("city_base_duration_hours", sa.Integer(), nullable=False),
        sa.Column("airship_id", sa.UUID(), nullable=False),
        sa.Column("airship_name", sa.String(length=100), nullable=False),
        sa.Column("airship_description", sa.Text(), nullable=False),
        sa.Column("airship_image_url", sa.String(length=500), nullable=True),
        sa.Column("airship_cost_factor", sa.Integer(), nullable=False),
        sa.Column("airship_duration_factor", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=50), nullable=False),
        sa.Column("cost_points", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("departure_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["airship_id"],
            ["airships.airship_id"],
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.city_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("ticket_id"),
    )
    op.create_index(
        "idx_tickets_user_status",
        "tickets",
        ["user_id", "status", "departure_datetime"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_tickets_updated_at
       BEFORE UPDATE ON tickets
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;")

    op.drop_index("idx_tickets_user_status", table_name="tickets", postgresql_where=sa.text("deleted_at IS NULL"))
    op.drop_table("tickets")
