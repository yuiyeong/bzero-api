"""채팅 메시지 엔티티.

룸 내 사용자들 간의 대화 메시지를 나타냅니다.
메시지는 일반 텍스트, 대화 카드 공유, 시스템 메시지 타입을 가집니다.
"""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, MessageType


@dataclass
class ChatMessage:
    """채팅 메시지 엔티티.

    Attributes:
        message_id: 메시지 고유 식별자 (UUID v7)
        room_id: 메시지가 전송된 룸 ID
        user_id: 메시지 작성자 ID (시스템 메시지의 경우 None)
        content: 메시지 내용 (최대 300자)
        card_id: 공유된 대화 카드 ID (카드 공유 메시지의 경우)
        message_type: 메시지 타입 (TEXT, CARD_SHARED, SYSTEM)
        is_system: 시스템 메시지 여부
        created_at: 생성 일시
        updated_at: 수정 일시
        deleted_at: 삭제 일시 (soft delete)
        expires_at: 만료 일시 (생성 시간 + 3일)
    """

    message_id: Id
    room_id: Id
    user_id: Id | None
    content: MessageContent
    card_id: Id | None
    message_type: MessageType
    is_system: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    expires_at: datetime

    @classmethod
    def create(
        cls,
        room_id: Id,
        user_id: Id,
        content: MessageContent,
        created_at: datetime,
        updated_at: datetime,
        expires_at: datetime,
        card_id: Id | None = None,
    ) -> "ChatMessage":
        """일반 메시지를 생성합니다.

        Args:
            room_id: 메시지가 전송될 룸 ID
            user_id: 메시지 작성자 ID
            content: 메시지 내용
            created_at: 생성 일시
            updated_at: 수정 일시
            expires_at: 만료 일시
            card_id: 선택적으로 첨부할 카드 ID

        Returns:
            새로 생성된 ChatMessage 엔티티 (message_type: TEXT)
        """
        return cls(
            message_id=Id(),
            room_id=room_id,
            user_id=user_id,
            content=content,
            card_id=card_id,
            message_type=MessageType.TEXT,
            is_system=False,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=None,
            expires_at=expires_at,
        )

    @classmethod
    def create_system_message(
        cls,
        room_id: Id,
        content: MessageContent,
        created_at: datetime,
        updated_at: datetime,
        expires_at: datetime,
    ) -> "ChatMessage":
        """시스템 메시지를 생성합니다.

        입장/퇴장 알림 등의 시스템 메시지를 생성할 때 사용합니다.

        Args:
            room_id: 메시지가 전송될 룸 ID
            content: 메시지 내용 (예: "서연님이 입장하셨습니다")
            created_at: 생성 일시
            updated_at: 수정 일시
            expires_at: 만료 일시

        Returns:
            새로 생성된 시스템 메시지 (message_type: SYSTEM, user_id: None)
        """
        return cls(
            message_id=Id(),
            room_id=room_id,
            user_id=None,  # 시스템 메시지는 user_id 없음
            content=content,
            card_id=None,
            message_type=MessageType.SYSTEM,
            is_system=True,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=None,
            expires_at=expires_at,
        )

    @classmethod
    def create_card_shared_message(
        cls,
        room_id: Id,
        user_id: Id,
        card_id: Id,
        content: MessageContent,
        created_at: datetime,
        updated_at: datetime,
        expires_at: datetime,
    ) -> "ChatMessage":
        """대화 카드 공유 메시지를 생성합니다.

        Args:
            room_id: 메시지가 전송될 룸 ID
            user_id: 카드를 공유한 사용자 ID
            card_id: 공유된 대화 카드 ID
            content: 카드 질문 내용
            created_at: 생성 일시
            updated_at: 수정 일시
            expires_at: 만료 일시

        Returns:
            새로 생성된 카드 공유 메시지 (message_type: CARD_SHARED)
        """
        return cls(
            message_id=Id(),
            room_id=room_id,
            user_id=user_id,
            content=content,
            card_id=card_id,
            message_type=MessageType.CARD_SHARED,
            is_system=False,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=None,
            expires_at=expires_at,
        )
