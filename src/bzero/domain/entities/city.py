from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id


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
