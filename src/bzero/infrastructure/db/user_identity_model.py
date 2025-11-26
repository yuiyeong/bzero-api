from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class UserIdentityModel(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "user_identities"

    identity_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Partial unique index for soft delete support
    __table_args__ = (
        Index(
            "idx_user_identities_provider_user",
            "provider",
            "provider_user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
