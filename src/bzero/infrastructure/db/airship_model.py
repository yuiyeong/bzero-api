from sqlalchemy import Boolean, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class AirshipModel(Base, AuditMixin, SoftDeleteMixin):
    """비행선 데이터베이스 모델.

    airships 테이블에 매핑되는 SQLAlchemy ORM 모델입니다.
    AuditMixin(created_at, updated_at)과 SoftDeleteMixin(deleted_at)을 상속받습니다.

    인덱스:
        - idx_airships_active_display_order: 활성화된 비행선 목록 조회 최적화
          (is_active, display_order) - 삭제되지 않은 항목만 대상
    """

    __tablename__ = "airships"

    # 기본 필드
    airship_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 비행선 이름
    description: Mapped[str] = mapped_column(Text, nullable=False)  # 비행선 설명
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 이미지 URL

    # 비용/시간 배율 (City의 base 값에 곱해짐)
    cost_factor: Mapped[int] = mapped_column(Integer, nullable=False)  # 비용 배율
    duration_factor: Mapped[int] = mapped_column(Integer, nullable=False)  # 소요 시간 배율

    # 표시 설정
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 목록 표시 순서
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 활성화 여부

    __table_args__ = (
        # 활성화된 비행선을 display_order 순으로 조회할 때 사용하는 부분 인덱스
        Index(
            "idx_airships_active_display_order",
            "is_active",
            "display_order",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
