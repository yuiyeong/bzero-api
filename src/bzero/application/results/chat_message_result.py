from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import ChatMessage


@dataclass
class ChatMessageResult:
    """채팅 메시지 결과 객체.

    Use Case와 API 응답 사이의 데이터 변환을 담당합니다.
    """

    message_id: str
    room_id: str
    user_id: str | None
    content: str
    card_id: str | None
    message_type: str
    is_system: bool
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: ChatMessage) -> "ChatMessageResult":
        """ChatMessage 엔티티로부터 결과 객체를 생성합니다.

        Args:
            entity: ChatMessage 엔티티

        Returns:
            ChatMessageResult 인스턴스
        """
        return cls(
            message_id=entity.message_id.to_hex(),
            room_id=entity.room_id.to_hex(),
            user_id=entity.user_id.to_hex() if entity.user_id else None,
            content=entity.content.value,
            card_id=entity.card_id.to_hex() if entity.card_id else None,
            message_type=entity.message_type.value,
            is_system=entity.is_system,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
