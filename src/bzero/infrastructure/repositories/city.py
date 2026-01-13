from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.city import City
from bzero.domain.repositories.city import CityRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel


class SqlAlchemyCityRepository(CityRepository):
    """SQLAlchemy 기반 도시 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, city: City) -> City:
        city_model = self._to_model(city)
        self._session.add(city_model)
        await self._session.flush()
        await self._session.refresh(city_model)
        return self._to_entity(city_model)

    async def find_by_id(self, city_id: Id) -> City | None:
        stmt = select(CityModel).where(
            CityModel.city_id == city_id.value,
            CityModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_cities(self, offset: int = 0, limit: int = 20, active_only: bool = True) -> list[City]:
        query = select(CityModel).where(CityModel.deleted_at.is_(None))

        if active_only:
            query = query.where(CityModel.is_active.is_(True))

        query = query.order_by(CityModel.display_order.asc()).offset(offset).limit(limit)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_cities(self, active_only: bool = True) -> int:
        query = select(func.count()).select_from(CityModel).where(CityModel.deleted_at.is_(None))

        if active_only:
            query = query.where(CityModel.is_active.is_(True))

        result = await self._session.execute(query)
        return result.scalar_one()

    @staticmethod
    def _to_model(entity: City) -> CityModel:
        return CityModel(
            city_id=entity.city_id.value,
            name=entity.name,
            theme=entity.theme,
            description=entity.description,
            image_url=entity.image_url,
            base_cost_points=entity.base_cost_points,
            base_duration_minutes=entity.base_duration_minutes,
            is_active=entity.is_active,
            display_order=entity.display_order,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def _to_entity(model: CityModel) -> City:
        """ORM 모델을 도메인 엔티티로 변환합니다."""
        return City(
            city_id=Id(model.city_id),
            name=model.name,
            theme=model.theme,
            description=model.description,
            image_url=model.image_url,
            base_cost_points=model.base_cost_points,
            base_duration_minutes=model.base_duration_minutes,
            is_active=model.is_active,
            display_order=model.display_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
