from datetime import date, datetime

from sqlalchemy import UUID, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import Base


class RewardModel(Base):
    """Reward SQLAlchemy 모델.

    Reward 도메인 엔티티의 영속성을 담당하는 ORM 모델입니다.
    일일 출석 보상 등 각종 보상 지급 내역을 테이블로 매핑합니다.

    Columns:
        reward_id: PK, UUID v7
        user_id: FK → users.user_id (보상 수령자)
        reward_type: 보상 유형 (daily_login 등)
        amount: 지급 포인트
        reference_date: 기준 날짜 (KST)
        point_transaction_id: FK → point_transactions.point_transaction_id (연결된 트랜잭션)
        created_at: 생성 일시

    Constraints:
        - uq_reward_user_type_date: (user_id, reward_type, reference_date) 유니크 제약
          → 같은 날 같은 유형 보상 중복 방지

    Indexes:
        - ix_rewards_user_id: 사용자별 보상 조회
        - ix_rewards_reference_date: 날짜별 보상 조회
    """

    __tablename__ = "rewards"

    # Primary key
    reward_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    point_transaction_id: Mapped[UUID | None] = mapped_column(
        UUID, ForeignKey("point_transactions.point_transaction_id"), nullable=True
    )

    # Reward information
    reward_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "reward_type", "reference_date", name="uq_reward_user_type_date"),
        Index("ix_rewards_user_id", "user_id"),
        Index("ix_rewards_reference_date", "reference_date"),
    )
