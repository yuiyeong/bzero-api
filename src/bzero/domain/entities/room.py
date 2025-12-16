from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidRoomStatusError
from bzero.domain.value_objects import Id


@dataclass
class Room:
    """방 엔티티.

    여행자들이 체류하고 대화하는 동적 공간입니다.
    게스트하우스 내에 동적으로 생성/삭제되며, 최대 6명까지 수용합니다.

    Attributes:
        room_id: 방 고유 식별자 (UUID v7)
        guest_house_id: 소속 게스트하우스 ID (FK)
        max_capacity: 최대 수용 인원 (기본 6명)
        current_capacity: 현재 체류 중인 여행자 수
        created_at: 생성 시각
        updated_at: 수정 시각

    생명주기:
        - 생성: 첫 번째 여행자 체크인 시 자동 생성
        - 활성(ACTIVE): 1~5명 체류 중 (새 여행자 배정 가능)
        - 만원(FULL): 6명 체류 중 (새 여행자 배정 불가)
        - 삭제: 마지막 여행자 체크아웃 시 deleted_at 설정 (soft delete)

    도메인 규칙:
        - 자동 방 배정: 6명 미만인 활성 방에 배정, 없으면 새 룸 생성
        - 동시 입장 시 Race Condition 방지 (트랜잭션 처리)
    """

    room_id: Id
    guest_house_id: Id
    max_capacity: int
    current_capacity: int
    created_at: datetime
    updated_at: datetime

    @property
    def is_full(self) -> bool:
        """방이 만원인지 확인합니다.

        Returns:
            현재 인원이 최대 수용 인원 이상이면 True
        """
        return self.current_capacity >= self.max_capacity

    @property
    def is_empty(self) -> bool:
        """방이 비어있는지 확인합니다.

        Returns:
            현재 인원이 0이면 True
        """
        return self.current_capacity == 0

    def increase_capacity(self) -> None:
        """방의 현재 인원을 1 증가시킵니다.

        여행자가 체크인할 때 호출됩니다.

        Raises:
            InvalidRoomStatusError: 방이 이미 만원인 경우
        """
        if self.is_full:
            raise InvalidRoomStatusError
        self.current_capacity += 1

    def decrease_capacity(self) -> None:
        """방의 현재 인원을 1 감소시킵니다.

        여행자가 체크아웃할 때 호출됩니다.

        Raises:
            InvalidRoomStatusError: 방이 이미 비어있는 경우
        """
        if self.is_empty:
            raise InvalidRoomStatusError
        self.current_capacity -= 1

    @classmethod
    def create(
        cls,
        guest_house_id: Id,
        max_capacity: int,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Room":
        """새 방 엔티티를 생성합니다.

        Args:
            guest_house_id: 소속 게스트하우스 ID
            max_capacity: 최대 수용 인원
            created_at: 생성 시각
            updated_at: 수정 시각

        Returns:
            새로 생성된 Room 엔티티 (ID 자동 생성, 초기 인원 0)
        """
        return cls(
            room_id=Id(),
            guest_house_id=guest_house_id,
            max_capacity=max_capacity,
            current_capacity=0,
            created_at=created_at,
            updated_at=updated_at,
        )
