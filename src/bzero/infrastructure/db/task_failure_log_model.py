from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base


class TaskFailureLogModel(Base, AuditMixin):
    __tablename__ = "task_failure_logs"

    log_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(50), nullable=False)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)

    args: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    kwargs: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
