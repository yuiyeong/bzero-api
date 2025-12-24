"""1:1 대화 메시지 엔티티.

1:1 대화방(DirectMessageRoom) 내에서 교환되는 개별 메시지를 나타냅니다.
"""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent


@dataclass
class DirectMessage:
    """1:1 대화 메시지 엔티티.

    Attributes:
        dm_id: 메시지 고유 식별자 (UUID v7)
        dm_room_id: 메시지가 속한 대화방 ID
        from_user_id: 발신자 ID
        to_user_id: 수신자 ID
        content: 메시지 내용 (최대 300자, MessageContent VO 재사용)
        is_read: 읽음 여부
        created_at: 생성 일시
        updated_at: 수정 일시
        deleted_at: 삭제 일시 (soft delete, 체크아웃 시)
    """

    dm_id: Id
    dm_room_id: Id
    from_user_id: Id
    to_user_id: Id
    content: MessageContent
    is_read: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        dm_room_id: Id,
        from_user_id: Id,
        to_user_id: Id,
        content: MessageContent,
        created_at: datetime,
        updated_at: datetime,
    ) -> "DirectMessage":
        """새 1:1 메시지를 생성합니다.

        Args:
            dm_room_id: 메시지가 전송될 대화방 ID
            from_user_id: 발신자 ID
            to_user_id: 수신자 ID
            content: 메시지 내용 (최대 300자)
            created_at: 생성 일시
            updated_at: 수정 일시

        Returns:
            새로 생성된 DirectMessage 엔티티 (is_read: False)
        """
        return cls(
            dm_id=Id(),
            dm_room_id=dm_room_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            content=content,
            is_read=False,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=None,
        )

    def mark_as_read(self, now: datetime) -> None:
        """메시지를 읽음 처리합니다.

        Args:
            now: 현재 시간
        """
        if not self.is_read:
            self.is_read = True
            self.updated_at = now
