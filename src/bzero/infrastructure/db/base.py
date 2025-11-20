"""SQLAlchemy 베이스 클래스 및 믹스인."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bzero.core.settings import get_settings


class Base(DeclarativeBase):
    pass


class AuditMixin:
    """Audit 을 위한 믹스인 클래스.

    created_at, updated_at 컬럼을 설정
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class SoftDeleteMixin:
    """Soft Delete 패턴을 위한 믹스인 클래스.

    deleted_at 컬럼을 설정
    deleted_at이 NULL이면 활성 상태, 값이 있으면 삭제된 상태
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """삭제 여부를 반환합니다.

        Returns:
            deleted_at이 None이 아니면 True, None이면 False
        """
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Soft Delete를 수행합니다.

        deleted_at을 현재 시간으로 설정합니다.
        """
        self.deleted_at = datetime.now(get_settings().timezone)

    def restore(self) -> None:
        """Soft Delete를 취소하고 복원합니다.

        deleted_at을 None으로 설정합니다.
        """
        self.deleted_at = None
