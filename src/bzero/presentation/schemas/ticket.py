"""티켓 관련 스키마."""

from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results import TicketResult


class CitySnapshotResponse(BaseModel):
    """티켓에 저장된 도시 스냅샷 응답 스키마."""

    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    name: str = Field(..., description="도시 이름")
    theme: str = Field(..., description="도시 테마")
    image_url: str | None = Field(None, description="도시 이미지 URL")
    description: str | None = Field(None, description="도시 설명")


class AirshipSnapshotResponse(BaseModel):
    """티켓에 저장된 비행선 스냅샷 응답 스키마."""

    airship_id: str = Field(..., description="비행선 ID (UUID v7 hex)")
    name: str = Field(..., description="비행선 이름")
    image_url: str | None = Field(None, description="비행선 이미지 URL")
    description: str = Field(..., description="비행선 설명")


class PurchaseTicketRequest(BaseModel):
    """티켓 구매 요청 스키마."""

    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    airship_id: str = Field(..., description="비행선 ID (UUID v7 hex)")


class TicketResponse(BaseModel):
    """티켓 응답 스키마."""

    ticket_id: str = Field(..., description="티켓 ID (UUID v7 hex)")
    ticket_number: str = Field(..., description="티켓 번호 (예: B0-2025-1234567890123)")
    city: CitySnapshotResponse = Field(..., description="도시 스냅샷 정보")
    airship: AirshipSnapshotResponse = Field(..., description="비행선 스냅샷 정보")
    cost_points: int = Field(..., description="티켓 비용 (포인트)")
    status: str = Field(..., description="티켓 상태 (boarding, completed, cancelled)")
    departure_datetime: datetime = Field(..., description="출발 일시")
    arrival_datetime: datetime = Field(..., description="도착 일시")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @classmethod
    def create_from(cls, result: TicketResult) -> "TicketResponse":
        """TicketResult로부터 TicketResponse를 생성합니다.

        Args:
            result: 티켓 유스케이스 결과 객체

        Returns:
            TicketResponse: 티켓 응답 스키마
        """
        city_snapshot = CitySnapshotResponse(
            city_id=result.city_snapshot.city_id,
            name=result.city_snapshot.name,
            theme=result.city_snapshot.theme,
            image_url=result.city_snapshot.image_url,
            description=result.city_snapshot.description,
        )
        airship_snapshot = AirshipSnapshotResponse(
            airship_id=result.airship_snapshot.airship_id,
            name=result.airship_snapshot.name,
            image_url=result.airship_snapshot.image_url,
            description=result.airship_snapshot.description,
        )
        return cls(
            ticket_id=result.ticket_id,
            ticket_number=result.ticket_number,
            city=city_snapshot,
            airship=airship_snapshot,
            cost_points=result.cost_points,
            status=result.status,
            departure_datetime=result.departure_datetime,
            arrival_datetime=result.arrival_datetime,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
