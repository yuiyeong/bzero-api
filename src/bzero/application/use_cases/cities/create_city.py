from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.city_result import CityResult
from bzero.domain.services.city import CityService


class CreateCityUseCase:
    """
    도시 생성 UseCase (Admin)

    새로운 도시를 생성합니다.
    """

    def __init__(self, city_service: CityService, session: AsyncSession):
        self._city_service = city_service
        self._session = session

    async def execute(
        self,
        name: str,
        theme: str,
        description: str | None,
        image_url: str | None,
        base_cost_points: int,
        base_duration_hours: int,
        is_active: bool,
        display_order: int,
    ) -> CityResult:
        """
        Args:
            name: 도시 이름
            theme: 도시 테마
            description: 도시 설명
            image_url: 도시 이미지 URL
            base_cost_points: 기준 가격 (포인트)
            base_duration_hours: 기준 비행 시간 (시간)
            is_active: 활성화 여부
            display_order: 표시 순서

        Returns:
            생성된 도시 정보
        """
        city = await self._city_service.create_city(
            name=name,
            theme=theme,
            description=description,
            image_url=image_url,
            base_cost_points=base_cost_points,
            base_duration_hours=base_duration_hours,
            is_active=is_active,
            display_order=display_order,
        )
        await self._session.commit()
        return CityResult.create_from(city)
