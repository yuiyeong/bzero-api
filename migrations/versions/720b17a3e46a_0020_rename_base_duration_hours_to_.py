"""0020_rename_base_duration_hours_to_minutes

City와 Ticket 테이블의 base_duration_hours를 base_duration_minutes로 변경합니다.
기존 데이터는 hours * 60으로 변환합니다.

Revision ID: 720b17a3e46a
Revises: 8f1d7cdf0f0e
Create Date: 2026-01-13 14:58:42.280867

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "720b17a3e46a"
down_revision: str | Sequence[str] | None = "8f1d7cdf0f0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    1. cities 테이블: base_duration_hours → base_duration_minutes
    2. tickets 테이블: city_base_duration_hours → city_base_duration_minutes
    3. 데이터 변환: hours * 60 = minutes
    """
    # 1. cities 테이블 컬럼 변경
    op.add_column("cities", sa.Column("base_duration_minutes", sa.Integer(), nullable=True))
    op.execute("UPDATE cities SET base_duration_minutes = base_duration_hours * 60")
    op.alter_column("cities", "base_duration_minutes", nullable=False)
    op.drop_column("cities", "base_duration_hours")

    # 2. tickets 테이블 컬럼 변경
    op.add_column("tickets", sa.Column("city_base_duration_minutes", sa.Integer(), nullable=True))
    op.execute("UPDATE tickets SET city_base_duration_minutes = city_base_duration_hours * 60")
    op.alter_column("tickets", "city_base_duration_minutes", nullable=False)
    op.drop_column("tickets", "city_base_duration_hours")


def downgrade() -> None:
    """Downgrade schema.

    주의: 분→시간 변환 시 정수 나눗셈으로 정밀도 손실 가능
    예: 61분 → 1시간 → 60분
    """
    # 1. tickets 테이블 역변환
    op.add_column("tickets", sa.Column("city_base_duration_hours", sa.Integer(), nullable=True))
    op.execute("UPDATE tickets SET city_base_duration_hours = city_base_duration_minutes / 60")
    op.alter_column("tickets", "city_base_duration_hours", nullable=False)
    op.drop_column("tickets", "city_base_duration_minutes")

    # 2. cities 테이블 역변환
    op.add_column("cities", sa.Column("base_duration_hours", sa.Integer(), nullable=True))
    op.execute("UPDATE cities SET base_duration_hours = base_duration_minutes / 60")
    op.alter_column("cities", "base_duration_hours", nullable=False)
    op.drop_column("cities", "base_duration_minutes")
