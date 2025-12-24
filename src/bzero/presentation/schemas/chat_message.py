from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.chat_message_result import ChatMessageResult


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답 스키마."""

    message_id: str = Field(..., description="메시지 고유 식별자")
    room_id: str = Field(..., description="룸 고유 식별자")
    user_id: str | None = Field(None, description="작성자 고유 식별자 (시스템 메시지인 경우 None)")
    content: str = Field(..., description="메시지 내용")
    card_id: str | None = Field(None, description="공유된 카드 고유 식별자")
    message_type: str = Field(..., description="메시지 타입 (text, card_shared, system)")
    is_system: bool = Field(..., description="시스템 메시지 여부")
    created_at: datetime = Field(..., description="생성 일시")

    @classmethod
    def create_from(cls, result: ChatMessageResult) -> "ChatMessageResponse":
        """ChatMessageResult로부터 ChatMessageResponse를 생성합니다."""
        return cls(
            message_id=result.message_id,
            room_id=result.room_id,
            user_id=result.user_id,
            content=result.content,
            card_id=result.card_id,
            message_type=result.message_type,
            is_system=result.is_system,
            created_at=result.created_at,
        )


class SendMessageRequest(BaseModel):
    """send_message 이벤트 요청 스키마."""

    content: str = Field(..., min_length=1, description="메시지 내용")


class ShareCardRequest(BaseModel):
    """share_card 이벤트 요청 스키마."""

    card_id: str = Field(..., description="공유할 카드 ID")


# GetHistoryRequest 제거됨 (REST API로 마이그레이션)
