from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import AirshipSnapshot, Id


@dataclass
class Airship:
    """비행선 도메인 엔티티.

    비행선은 도시로 이동하는 교통수단으로, 각 비행선마다 고유한
    비용 배율(cost_factor)과 소요 시간 배율(duration_factor)을 가집니다.

    Attributes:
        airship_id: 비행선 고유 식별자 (UUID v7)
        name: 비행선 이름 (예: "일반 비행선", "쾌속 비행선")
        description: 비행선 설명
        image_url: 비행선 이미지 URL (선택)
        cost_factor: 비용 배율 (1 = 100%, 기본 비용의 몇 배인지)
        duration_factor: 소요 시간 배율 (1 = 100%, 기본 시간의 몇 배인지)
        display_order: 목록 표시 순서 (낮을수록 먼저 표시)
        is_active: 활성화 여부 (비활성화된 비행선은 목록에 표시되지 않음)
        created_at: 생성 시각
        updated_at: 수정 시각
        deleted_at: 삭제 시각 (소프트 삭제, None이면 삭제되지 않음)
    """

    airship_id: Id
    name: str
    description: str
    image_url: str | None
    cost_factor: int
    duration_factor: int
    display_order: int
    is_active: bool

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def activate(self) -> None:
        """비행선 활성화"""
        self.is_active = True

    def deactivate(self) -> None:
        """비행선 비활성화"""
        self.is_active = False

    def snapshot(self) -> AirshipSnapshot:
        return AirshipSnapshot(
            airship_id=self.airship_id,
            name=self.name,
            image_url=self.image_url,
            description=self.description,
            cost_factor=self.cost_factor,
            duration_factor=self.duration_factor,
        )

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        image_url: str,
        cost_factor: int,
        duration_factor: int,
        display_order: int,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Airship":
        return cls(
            airship_id=Id(),
            name=name,
            description=description,
            image_url=image_url,
            cost_factor=cost_factor,
            duration_factor=duration_factor,
            display_order=display_order,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
        )
