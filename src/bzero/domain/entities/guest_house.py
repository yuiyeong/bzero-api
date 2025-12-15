from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import GuestHouseType, Id


@dataclass
class GuestHouse:
    """게스트하우스 엔티티.

    도시에 있는 영구적인 숙소 컨테이너입니다.
    게스트하우스는 도시별로 항상 존재하며, 삭제되지 않습니다.
    Room들의 상위 그룹으로서, 타입별 특성(혼합형/조용한 방)을 정의합니다.

    Attributes:
        guest_house_id: 게스트하우스 고유 식별자 (UUID v7)
        city_id: 소속 도시 ID (FK)
        guest_house_type: 게스트하우스 타입 (MIXED: 혼합형, QUIET: 조용한 방)
        name: 게스트하우스 이름
        description: 게스트하우스 설명
        image_url: 게스트하우스 이미지 URL
        is_active: 활성화 상태
        created_at: 생성 시각
        updated_at: 수정 시각

    Note:
        - 혼합형(MIXED): AI 호스트가 대화 촉진, 구조화된 이벤트 (불멍, 별멍 등)
        - 조용한 방(QUIET): 개인적 대화와 자기성찰 중심, AI는 환영 메시지만 표시
    """

    guest_house_id: Id
    city_id: Id
    guest_house_type: GuestHouseType
    name: str
    description: str | None
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        city_id: Id,
        name: str,
        description: str | None,
        image_url: str | None,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
        guest_house_type: GuestHouseType = GuestHouseType.MIXED,
    ) -> "GuestHouse":
        """새 게스트하우스 엔티티를 생성합니다.

        Args:
            city_id: 소속 도시 ID
            name: 게스트하우스 이름
            description: 게스트하우스 설명 (선택)
            image_url: 게스트하우스 이미지 URL (선택)
            is_active: 활성화 상태
            created_at: 생성 시각
            updated_at: 수정 시각
            guest_house_type: 게스트하우스 타입 (기본값: MIXED)

        Returns:
            새로 생성된 GuestHouse 엔티티 (ID 자동 생성)
        """
        return cls(
            guest_house_id=Id(),
            city_id=city_id,
            guest_house_type=guest_house_type,
            name=name,
            description=description,
            image_url=image_url,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
        )
