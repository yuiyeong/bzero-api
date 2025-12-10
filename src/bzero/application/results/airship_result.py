from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import Airship


@dataclass
class AirshipResult:
    """비행선 유스케이스 결과 객체.

    유스케이스에서 프레젠테이션 계층으로 비행선 데이터를 전달할 때 사용됩니다.
    도메인 엔티티의 Id 값 객체를 문자열로 변환하여 API 응답에 적합한 형태로 제공합니다.

    Attributes:
        airship_id: 비행선 고유 식별자 (UUID hex 문자열)
        name: 비행선 이름
        description: 비행선 설명
        image_url: 비행선 이미지 URL (선택)
        cost_factor: 비용 배율
        duration_factor: 소요 시간 배율
        display_order: 목록 표시 순서
        is_active: 활성화 여부
        created_at: 생성 시각
        updated_at: 수정 시각
    """

    airship_id: str
    name: str
    description: str
    image_url: str | None
    cost_factor: int
    duration_factor: int
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: Airship) -> "AirshipResult":
        """도메인 엔티티로부터 결과 객체를 생성합니다.

        Args:
            entity: 변환할 비행선 도메인 엔티티

        Returns:
            생성된 AirshipResult 객체
        """
        return cls(
            airship_id=entity.airship_id.to_hex(),
            name=entity.name,
            description=entity.description,
            image_url=entity.image_url,
            cost_factor=entity.cost_factor,
            duration_factor=entity.duration_factor,
            display_order=entity.display_order,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
