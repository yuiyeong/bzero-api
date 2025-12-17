from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.airship_result import AirshipResult


class AirshipResponse(BaseModel):
    """비행선 응답 스키마."""

    airship_id: str = Field(..., description="비행선 고유 식별자")
    name: str = Field(..., description="비행선 이름")
    description: str = Field(..., description="비행선 설명")
    image_url: str | None = Field(None, description="비행선 이미지 URL")
    cost_factor: int = Field(..., description="비용 배율")
    duration_factor: int = Field(..., description="소요 시간 배율")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @classmethod
    def create_from(cls, result: AirshipResult) -> "AirshipResponse":
        """AirshipResult로부터 AirshipResponse를 생성합니다.

        Args:
            result: 비행선 유스케이스 결과 객체

        Returns:
            AirshipResponse: 비행선 응답 스키마
        """
        return AirshipResponse(
            airship_id=result.airship_id,
            name=result.name,
            description=result.description,
            image_url=result.image_url,
            cost_factor=result.cost_factor,
            duration_factor=result.duration_factor,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
