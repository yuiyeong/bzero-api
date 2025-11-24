from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.domain.value_objects import TransactionStatus
from bzero.infrastructure.db.base import AuditMixin, Base


class PointTransactionModel(Base, AuditMixin):
    __tablename__ = "point_transactions"

    # Primary key
    point_transaction_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    # Transaction information
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=TransactionStatus.PENDING.value)

    # Reference(optional)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[UUID | None] = mapped_column(UUID, nullable=True)

    # Balance Tracking
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # Description(Optional)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_transaction_user_status", "user_id", "status"),
        Index("idx_transactions_user_created", "user_id", "created_at"),
        Index("idx_transactions_user_type", "user_id", "transaction_type"),
        Index("idx_transactions_reference", "reference_type", "reference_id"),
    )
