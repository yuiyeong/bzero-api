from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities import Airship
from bzero.domain.repositories.airship import AirshipRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.airship_model import AirshipModel


class SqlAlchemyAirshipRepository(AirshipRepository):
    """비행선 리포지토리의 SQLAlchemy 구현체.

    비동기 SQLAlchemy 세션을 사용하여 비행선 엔티티의 CRUD 작업을 수행합니다.
    도메인 엔티티(Airship)와 ORM 모델(AirshipModel) 간의 변환을 담당합니다.
    """

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: 비동기 SQLAlchemy 세션
        """
        self._session = session

    async def create(self, airship: Airship) -> Airship:
        """새로운 비행선을 데이터베이스에 저장합니다.

        Args:
            airship: 저장할 비행선 엔티티

        Returns:
            저장된 비행선 엔티티 (DB에서 생성된 타임스탬프 포함)
        """
        model = self._to_model(airship)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return self._to_entity(model)

    async def find_all(self, offset: int = 0, limit: int = 100) -> list[Airship]:
        """모든 비행선을 조회합니다 (소프트 삭제된 항목 제외).

        Args:
            offset: 조회 시작 위치
            limit: 최대 조회 개수

        Returns:
            비행선 엔티티 목록
        """
        stmt = (
            select(AirshipModel)
            .where(AirshipModel.deleted_at.is_(None))
            .order_by(AirshipModel.display_order.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def find_all_by_active_state(self, is_active: bool, offset: int = 0, limit: int = 100) -> list[Airship]:
        """활성화 상태에 따라 비행선을 조회합니다.

        Args:
            is_active: 활성화 여부
            offset: 조회 시작 위치
            limit: 최대 조회 개수

        Returns:
            조건에 맞는 비행선 엔티티 목록
        """
        stmt = (
            select(AirshipModel)
            .where(
                AirshipModel.is_active == is_active,
                AirshipModel.deleted_at.is_(None),
            )
            .order_by(AirshipModel.display_order.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_by(self, is_active: bool | None) -> int:
        """조건에 맞는 비행선 개수를 반환합니다.

        Args:
            is_active: 활성화 여부 필터 (None이면 전체 조회)

        Returns:
            조건에 맞는 비행선 개수
        """
        stmt = select(func.count()).select_from(AirshipModel).where(AirshipModel.deleted_at.is_(None))
        if is_active is not None:
            stmt = stmt.where(AirshipModel.is_active == is_active)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def _to_entity(model: AirshipModel) -> Airship:
        """ORM 모델을 도메인 엔티티로 변환합니다.

        Args:
            model: 변환할 ORM 모델

        Returns:
            변환된 도메인 엔티티
        """
        return Airship(
            airship_id=Id(model.airship_id),
            name=model.name,
            description=model.description,
            image_url=model.image_url,
            cost_factor=model.cost_factor,
            duration_factor=model.duration_factor,
            display_order=model.display_order,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(entity: Airship) -> AirshipModel:
        """도메인 엔티티를 ORM 모델로 변환합니다.

        Args:
            entity: 변환할 도메인 엔티티

        Returns:
            변환된 ORM 모델
        """
        return AirshipModel(
            airship_id=entity.airship_id.value,
            name=entity.name,
            description=entity.description,
            image_url=entity.image_url,
            cost_factor=entity.cost_factor,
            duration_factor=entity.duration_factor,
            display_order=entity.display_order,
            is_active=entity.is_active,
            deleted_at=entity.deleted_at,
        )
