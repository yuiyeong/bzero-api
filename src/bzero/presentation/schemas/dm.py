"""DM (1:1 대화) 관련 Pydantic 스키마."""

from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.dm import DirectMessageResult, DirectMessageRoomResult


# ==================== Request 스키마 ====================


class JoinDMRoomRequest(BaseModel):
    """join_dm_room 이벤트 요청 스키마."""

    dm_room_id: str = Field(..., description="대화방 ID")


class SendDMMessageRequest(BaseModel):
    """send_dm_message 이벤트 요청 스키마."""

    dm_room_id: str = Field(..., description="대화방 ID")
    content: str = Field(..., min_length=1, max_length=300, description="메시지 내용 (1-300자)")


class CreateDMRequestRequest(BaseModel):
    """POST /api/v1/dm/requests 요청 스키마."""

    to_user_id: str = Field(..., description="대화 상대방 사용자 ID")


# ==================== Response 스키마 ====================


class DirectMessageResponse(BaseModel):
    """1:1 메시지 응답 스키마."""

    dm_id: str = Field(..., description="메시지 고유 식별자")
    dm_room_id: str = Field(..., description="대화방 고유 식별자")
    from_user_id: str = Field(..., description="발신자 고유 식별자")
    to_user_id: str = Field(..., description="수신자 고유 식별자")
    content: str = Field(..., description="메시지 내용")
    is_read: bool = Field(..., description="읽음 여부")
    created_at: datetime = Field(..., description="생성 일시")

    @classmethod
    def create_from(cls, result: DirectMessageResult) -> "DirectMessageResponse":
        """DirectMessageResult로부터 DirectMessageResponse를 생성합니다."""
        return cls(
            dm_id=result.dm_id,
            dm_room_id=result.dm_room_id,
            from_user_id=result.from_user_id,
            to_user_id=result.to_user_id,
            content=result.content,
            is_read=result.is_read,
            created_at=result.created_at,
        )


class DirectMessageRoomResponse(BaseModel):
    """1:1 대화방 응답 스키마."""

    dm_room_id: str = Field(..., description="대화방 고유 식별자")
    guesthouse_id: str = Field(..., description="게스트하우스 고유 식별자")
    room_id: str = Field(..., description="룸 고유 식별자")
    user1_id: str = Field(..., description="대화 신청자 고유 식별자")
    user2_id: str = Field(..., description="대화 수신자 고유 식별자")
    status: str = Field(..., description="대화방 상태 (pending, accepted, active, rejected, ended)")
    started_at: datetime | None = Field(None, description="대화 시작 일시")
    ended_at: datetime | None = Field(None, description="대화 종료 일시")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")
    last_message: DirectMessageResponse | None = Field(None, description="마지막 메시지")
    unread_count: int = Field(0, description="읽지 않은 메시지 개수")

    @classmethod
    def create_from(cls, result: DirectMessageRoomResult) -> "DirectMessageRoomResponse":
        """DirectMessageRoomResult로부터 DirectMessageRoomResponse를 생성합니다."""
        return cls(
            dm_room_id=result.dm_room_id,
            guesthouse_id=result.guesthouse_id,
            room_id=result.room_id,
            user1_id=result.user1_id,
            user2_id=result.user2_id,
            status=result.status,
            started_at=result.started_at,
            ended_at=result.ended_at,
            created_at=result.created_at,
            updated_at=result.updated_at,
            last_message=(
                DirectMessageResponse.create_from(result.last_message)
                if result.last_message
                else None
            ),
            unread_count=result.unread_count,
        )
