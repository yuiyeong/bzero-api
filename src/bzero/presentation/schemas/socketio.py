from pydantic import BaseModel, Field


class SocketSession(BaseModel):
    """Socket.IO 세션 데이터 모델."""

    user_id: str = Field(..., description="사용자 Koid")
    room_id: str = Field(..., description="입장 중인 룸 ID")


class JoinRoomRequest(BaseModel):
    """join_room 이벤트 요청 스키마."""

    room_id: str = Field(..., description="참여할 룸 ID")
