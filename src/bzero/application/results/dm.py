"""DM (1:1 대화) 관련 결과 DTO.

1:1 대화방 및 메시지 조회 결과를 담는 데이터 클래스입니다.
"""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities.direct_message import DirectMessage
from bzero.domain.entities.direct_message_room import DirectMessageRoom


@dataclass(frozen=True)
class DirectMessageResult:
    """1:1 메시지 조회 결과 DTO.

    Attributes:
        dm_id: 메시지 ID
        dm_room_id: 대화방 ID
        from_user_id: 발신자 ID
        to_user_id: 수신자 ID
        content: 메시지 내용
        is_read: 읽음 여부
        created_at: 생성 일시
    """

    dm_id: str
    dm_room_id: str
    from_user_id: str
    to_user_id: str
    content: str
    is_read: bool
    created_at: datetime

    @classmethod
    def create_from(cls, message: DirectMessage) -> "DirectMessageResult":
        """DirectMessage 엔티티로부터 Result를 생성합니다."""
        return cls(
            dm_id=message.dm_id.value,
            dm_room_id=message.dm_room_id.value,
            from_user_id=message.from_user_id.value,
            to_user_id=message.to_user_id.value,
            content=message.content.value,
            is_read=message.is_read,
            created_at=message.created_at,
        )


@dataclass(frozen=True)
class DirectMessageRoomResult:
    """1:1 대화방 조회 결과 DTO.

    Attributes:
        dm_room_id: 대화방 ID
        guesthouse_id: 게스트하우스 ID
        room_id: 룸 ID
        user1_id: 대화 신청자 ID
        user2_id: 대화 수신자 ID
        status: 대화방 상태 (pending, accepted, active, rejected, ended)
        started_at: 대화 시작 일시 (ACCEPTED 시 기록)
        ended_at: 대화 종료 일시 (ENDED 시 기록)
        created_at: 생성 일시
        updated_at: 수정 일시
        last_message: 마지막 메시지 (옵션)
        unread_count: 읽지 않은 메시지 개수 (옵션)
    """

    dm_room_id: str
    guesthouse_id: str
    room_id: str
    user1_id: str
    user2_id: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    last_message: DirectMessageResult | None = None
    unread_count: int = 0

    @classmethod
    def create_from(
        cls,
        dm_room: DirectMessageRoom,
        last_message: DirectMessage | None = None,
        unread_count: int = 0,
    ) -> "DirectMessageRoomResult":
        """DirectMessageRoom 엔티티로부터 Result를 생성합니다."""
        return cls(
            dm_room_id=dm_room.dm_room_id.value,
            guesthouse_id=dm_room.guesthouse_id.value,
            room_id=dm_room.room_id.value,
            user1_id=dm_room.user1_id.value,
            user2_id=dm_room.user2_id.value,
            status=dm_room.status.value,
            started_at=dm_room.started_at,
            ended_at=dm_room.ended_at,
            created_at=dm_room.created_at,
            updated_at=dm_room.updated_at,
            last_message=DirectMessageResult.create_from(last_message) if last_message else None,
            unread_count=unread_count,
        )
