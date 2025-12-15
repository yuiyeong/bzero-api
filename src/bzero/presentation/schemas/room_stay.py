from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results import RoomStayResult


class RoomStayResponse(BaseModel):
    """체류 응답 스키마."""

    room_stay_id: str = Field(..., description="체류 ID (UUID v7 hex)")
    user_id: str = Field(..., description="사용자 ID (UUID v7 hex)")
    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    guest_house_id: str = Field(..., description="게스트하우스 ID (UUID v7 hex)")
    room_id: str = Field(..., description="방 ID (UUID v7 hex)")
    ticket_id: str = Field(..., description="티켓 ID (UUID v7 hex)")
    status: str = Field(..., description="체류 상태 (checked_in, checked_out, extended)")
    check_in_at: datetime = Field(..., description="체크인 일시")
    scheduled_check_out_at: datetime = Field(..., description="예정 체크아웃 일시")
    actual_check_out_at: datetime | None = Field(None, description="실제 체크아웃 일시")
    extension_count: int = Field(..., description="연장 횟수")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @classmethod
    def create_from(cls, result: RoomStayResult) -> "RoomStayResponse":
        """RoomStayResult로부터 RoomStayResponse를 생성합니다.

        Args:
            result: 체류 유스케이스 결과 객체

        Returns:
            RoomStayResponse: 체류 응답 스키마
        """
        return cls(
            room_stay_id=result.room_stay_id,
            user_id=result.user_id,
            city_id=result.city_id,
            guest_house_id=result.guest_house_id,
            room_id=result.room_id,
            ticket_id=result.ticket_id,
            status=result.status,
            check_in_at=result.check_in_at,
            scheduled_check_out_at=result.scheduled_check_out_at,
            actual_check_out_at=result.actual_check_out_at,
            extension_count=result.extension_count,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
