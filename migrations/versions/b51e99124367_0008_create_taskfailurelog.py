"""0008 Create TaskFailureLog

Revision ID: b51e99124367
Revises: d07e6829dd95
Create Date: 2025-12-10 16:26:27.682600

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b51e99124367"
down_revision: str | Sequence[str] | None = "d07e6829dd95"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "task_failure_logs",
        sa.Column("log_id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.String(length=50), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column("args", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("kwargs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("log_id"),
    )

    # update_updated_at_column() 함수는 0001_create_user.py에서 이미 생성됨
    op.execute("""
    CREATE TRIGGER update_task_failure_logs_updated_at
       BEFORE UPDATE ON task_failure_logs
       FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS update_task_failure_logs_updated_at ON task_failure_logs;")
    op.drop_table("task_failure_logs")
