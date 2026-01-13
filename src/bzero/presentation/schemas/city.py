from datetime import datetime

from pydantic import BaseModel, Field

from bzero.application.results.city_result import CityResult


class CityResponse(BaseModel):
    """도시 정보 응답 스키마"""

    city_id: str = Field(..., description="도시 ID (UUID v7 hex)")
    name: str = Field(..., description="도시 이름")
    theme: str = Field(..., description="도시 테마")
    description: str | None = Field(None, description="도시 설명")
    image_url: str | None = Field(None, description="도시 이미지 URL")
    base_cost_points: int = Field(..., description="기준 가격 (포인트)")
    base_duration_minutes: int = Field(..., description="기준 비행 시간 (분)")
    is_active: bool = Field(..., description="활성화 여부")
    display_order: int = Field(..., description="표시 순서")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {"from_attributes": True}

    @classmethod
    def create_from(cls, result: CityResult) -> "CityResponse":
        return cls(
            city_id=result.city_id,
            name=result.name,
            theme=result.theme,
            description=result.description,
            image_url=result.image_url,
            base_cost_points=result.base_cost_points,
            base_duration_minutes=result.base_duration_minutes,
            is_active=result.is_active,
            display_order=result.display_order,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class CityCreateRequest(BaseModel):
    """도시 생성 요청 스키마 (Admin)"""

    name: str = Field(..., min_length=1, max_length=50, description="도시 이름")
    theme: str = Field(..., min_length=1, max_length=50, description="도시 테마")
    description: str | None = Field(None, max_length=200, description="도시 설명")
    image_url: str | None = Field(None, description="도시 이미지 URL")
    base_cost_points: int = Field(default=300, ge=0, description="기준 가격 (포인트)")
    base_duration_minutes: int = Field(default=180, ge=1, description="기준 비행 시간 (분)")
    is_active: bool = Field(default=False, description="활성화 여부 (Coming Soon은 false)")
    display_order: int = Field(default=0, ge=0, description="표시 순서")
