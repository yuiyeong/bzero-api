from sqlalchemy import Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class UserModel(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    profile_emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current_points: Mapped[int] = mapped_column(nullable=False, default=0)

    # Partial unique indexes for soft delete support
    __table_args__ = (
        Index(
            "idx_users_email",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_users_nickname",
            "nickname",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
