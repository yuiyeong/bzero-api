"""티켓 관련 값 객체.

티켓의 상태와 구매 시점의 도시/비행선 정보 스냅샷을 정의합니다.
스냅샷은 구매 당시 정보를 불변으로 보존하여, 이후 원본 데이터가 변경되어도
티켓에 기록된 정보는 유지됩니다.
"""

from dataclasses import dataclass
from enum import Enum

from bzero.domain.value_objects import Id


class TicketStatus(str, Enum):
    """티켓 상태를 나타내는 열거형.

    티켓 생명주기:
        PURCHASED → BOARDING → COMPLETED
                  ↘ CANCELLED

    Attributes:
        PURCHASED: 구매 완료 (출발 전)
        BOARDING: 탑승 중 (여행 중)
        COMPLETED: 여행 완료
        CANCELLED: 취소됨
    """

    PURCHASED = "purchased"
    BOARDING = "boarding"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class CitySnapshot:
    """티켓 구매 시점의 도시 정보 스냅샷.

    도시 정보가 변경되어도 티켓에 기록된 정보는 구매 당시 그대로 유지됩니다.

    Attributes:
        city_id: 도시 고유 식별자
        name: 도시 이름 (예: "세렌시아")
        theme: 도시 테마 (예: "관계")
        image_url: 도시 이미지 URL (선택)
        description: 도시 설명 (선택)
        base_cost_points: 기본 비용 포인트
        base_duration_hours: 기본 여행 시간 (시간 단위)
    """

    city_id: Id
    name: str
    theme: str
    image_url: str | None
    description: str | None
    base_cost_points: int
    base_duration_hours: int


@dataclass(frozen=True)
class AirshipSnapshot:
    """티켓 구매 시점의 비행선 정보 스냅샷.

    비행선 정보가 변경되어도 티켓에 기록된 정보는 구매 당시 그대로 유지됩니다.

    Attributes:
        airship_id: 비행선 고유 식별자
        name: 비행선 이름 (예: "일반 비행선", "쾌속 비행선")
        image_url: 비행선 이미지 URL (선택)
        description: 비행선 설명
        cost_factor: 비용 배율 (도시 기본 비용 * 이 값 = 최종 비용)
        duration_factor: 시간 배율 (도시 기본 시간 * 이 값 = 최종 시간)
    """

    airship_id: Id
    name: str
    image_url: str | None
    description: str
    cost_factor: int
    duration_factor: int
