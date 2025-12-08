from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import CitySnapshot, Id


@dataclass
class City:
    """도시 엔티티

    B0 프로젝트의 6개 테마별 도시를 나타냅니다.
    """

    city_id: Id
    name: str  # 도시 이름 (예: 세렌시아)
    theme: str  # 도시 테마 (예: 관계의 도시)
    description: str | None  # 도시 설명
    image_url: str | None  # 도시 이미지 URL
    base_cost_points: int  # 기준 가격 (포인트)
    base_duration_hours: int  # 기준 비행 시간 (시간)
    is_active: bool  # 활성화 여부
    display_order: int  # 도시 표시 순서

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def activate(self) -> None:
        """도시를 활성화합니다."""
        self.is_active = True

    def deactivate(self) -> None:
        """도시를 비활성화합니다."""
        self.is_active = False

    def snapshot(self) -> CitySnapshot:
        return CitySnapshot(
            city_id=self.city_id,
            name=self.name,
            theme=self.theme,
            image_url=self.image_url,
            description=self.description,
            base_cost_points=self.base_cost_points,
            base_duration_hours=self.base_duration_hours,
        )

    @classmethod
    def create(
        cls,
        name: str,
        theme: str,
        description: str | None,
        image_url: str | None,
        base_cost_points: int,
        base_duration_hours: int,
        is_active: bool,
        display_order: int,
        created_at: datetime,
        updated_at: datetime,
    ) -> "City":
        """City 엔티티를 생성합니다."""
        return cls(
            city_id=Id(),
            name=name,
            theme=theme,
            description=description,
            image_url=image_url,
            base_cost_points=base_cost_points,
            base_duration_hours=base_duration_hours,
            is_active=is_active,
            display_order=display_order,
            created_at=created_at,
            updated_at=updated_at,
        )
