"""Create City table

Revision ID: 019aa594c20e
Revises: 08797d4b4a62
Create Date: 2025-11-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "019aa594c20e"
down_revision: str | Sequence[str] | None = "08797d4b4a62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cities",
        # UUID v7은 애플리케이션 레벨에서 생성 (uuid7 라이브러리)
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("theme", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phase", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("city_id"),
    )

    # 인덱스 생성
    # 활성 도시 조회 최적화 (deleted_at IS NULL 조건으로 soft delete 고려)
    op.create_index(
        index_name="idx_cities_is_active_display_order",
        table_name="cities",
        columns=["is_active", "display_order"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Phase별 도시 조회 최적화
    op.create_index(
        index_name="idx_cities_phase",
        table_name="cities",
        columns=["phase"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Create trigger for cities table (updated_at 자동 업데이트)
    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
        CREATE TRIGGER update_cities_updated_at
            BEFORE UPDATE ON cities
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_cities_updated_at ON cities;")

    # Drop indexes
    op.drop_index("idx_cities_phase", table_name="cities")
    op.drop_index("idx_cities_is_active_display_order", table_name="cities")

    # Drop table
    op.drop_table("cities")
