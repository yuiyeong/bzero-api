from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id, RoomStayStatus


@dataclass
class RoomStay:
    """체류 엔티티.

    개별 여행자의 체류 기록을 관리합니다.
    각 여행자는 고유한 체크인/체크아웃 시간을 가지며, 개별적으로 연장할 수 있습니다.

    Attributes:
        room_stay_id: 체류 고유 식별자 (UUID v7)
        user_id: 여행자 ID (FK)
        city_id: 도시 ID (FK)
        guest_house_id: 게스트하우스 ID (FK)
        room_id: 룸 ID (FK)
        ticket_id: 티켓 ID (FK) - 체크인에 사용된 티켓
        status: 체류 상태 (CHECKED_IN, CHECKED_OUT, EXTENDED)
        check_in_at: 체크인 시각 (개별)
        scheduled_check_out_at: 예정 체크아웃 시각 (개별, 체크인 + 24시간)
        actual_check_out_at: 실제 체크아웃 시각 (nullable)
        extension_count: 연장 횟수 (기본값 0)
        created_at: 생성 시각
        updated_at: 수정 시각

    도메인 규칙:
        - 한 여행자는 동시에 하나의 활성 체류만 가능
        - 초기 체크아웃 시간: check_in_at + 24시간
        - 연장 시: scheduled_check_out_at에 24시간 추가, 300P 차감
        - 연장 제한 없음 (포인트만 있으면 무제한)
        - 체크아웃 시: status를 CHECKED_OUT으로 변경, actual_check_out_at 기록
    """

    room_stay_id: Id
    user_id: Id
    city_id: Id
    guest_house_id: Id
    room_id: Id
    ticket_id: Id
    status: RoomStayStatus
    check_in_at: datetime
    scheduled_check_out_at: datetime
    actual_check_out_at: datetime | None
    extension_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: Id,
        city_id: Id,
        guest_house_id: Id,
        room_id: Id,
        ticket_id: Id,
        check_in_at: datetime,
        scheduled_check_out_at: datetime,
        created_at: datetime,
        updated_at: datetime,
    ) -> "RoomStay":
        """새 체류 엔티티를 생성합니다.

        Args:
            user_id: 여행자 ID
            city_id: 도시 ID
            guest_house_id: 게스트하우스 ID
            room_id: 룸 ID
            ticket_id: 체크인에 사용된 티켓 ID
            check_in_at: 체크인 시각
            scheduled_check_out_at: 예정 체크아웃 시각
            created_at: 생성 시각
            updated_at: 수정 시각

        Returns:
            새로 생성된 RoomStay 엔티티 (ID 자동 생성, CHECKED_IN 상태)
        """
        return cls(
            room_stay_id=Id(),
            user_id=user_id,
            city_id=city_id,
            guest_house_id=guest_house_id,
            room_id=room_id,
            ticket_id=ticket_id,
            status=RoomStayStatus.CHECKED_IN,
            check_in_at=check_in_at,
            scheduled_check_out_at=scheduled_check_out_at,
            actual_check_out_at=None,
            extension_count=0,
            created_at=created_at,
            updated_at=updated_at,
        )
