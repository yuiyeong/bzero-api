"""GuestHouseRepository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.

구조:
    GuestHouseRepositoryCore (쿼리 빌더 + 변환 + DB 작업)
         ↑          ↑
    SqlAlchemy     SqlAlchemy
    GuestHouseRepo GuestHouseSyncRepo
    (run_sync)     (직접 호출)
"""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from bzero.domain.entities.guest_house import GuestHouse
from bzero.domain.value_objects import GuestHouseType, Id
from bzero.infrastructure.db.guest_house_model import GuestHouseModel


class GuestHouseRepositoryCore:
    """GuestHouseRepository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_guesthouse_id(guesthouse_id: Id) -> Select[tuple[GuestHouseModel]]:
        """ID로 게스트하우스를 조회하는 쿼리를 생성합니다."""
        return select(GuestHouseModel).where(
            GuestHouseModel.guest_house_id == guesthouse_id.value,
            GuestHouseModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_by_city_id(city_id: Id) -> Select[tuple[GuestHouseModel]]:
        """ID로 게스트하우스를 조회하는 쿼리를 생성합니다."""
        return select(GuestHouseModel).where(
            GuestHouseModel.city_id == city_id.value,
            GuestHouseModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_available_one_by_city_id(city_id: Id) -> Select[tuple[GuestHouseModel]]:
        """ID로 게스트하우스를 조회하는 쿼리를 생성합니다."""
        return (
            select(GuestHouseModel)
            .where(
                GuestHouseModel.city_id == city_id.value,
                GuestHouseModel.is_active.is_(True),
                GuestHouseModel.deleted_at.is_(None),
            )
            .limit(1)
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: GuestHouse) -> GuestHouseModel:
        """GuestHouse 엔티티를 GuestHouseModel(ORM)로 변환합니다."""
        return GuestHouseModel(
            guest_house_id=entity.guest_house_id.value,
            city_id=entity.city_id.value,
            guest_house_type=entity.guest_house_type.value,
            name=entity.name,
            description=entity.description,
            image_url=entity.image_url,
            is_active=entity.is_active,
        )

    @staticmethod
    def to_entity(model: GuestHouseModel) -> GuestHouse:
        """GuestHouseModel(ORM)을 GuestHouse 엔티티로 변환합니다."""
        return GuestHouse(
            guest_house_id=Id(model.guest_house_id),
            city_id=Id(model.city_id),
            guest_house_type=GuestHouseType(model.guest_house_type),
            name=model.name,
            description=model.description,
            image_url=model.image_url,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, guesthouse: GuestHouse) -> GuestHouse:
        """게스트하우스를 생성합니다."""
        model = GuestHouseRepositoryCore.to_model(guesthouse)

        session.add(model)
        session.flush()
        session.refresh(model)

        return GuestHouseRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_guesthouse_id(session: Session, guesthouse_id: Id) -> GuestHouse | None:
        """ID로 게스트하우스를 조회합니다."""
        stmt = GuestHouseRepositoryCore._query_find_by_guesthouse_id(guesthouse_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return GuestHouseRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_all_by_city_id(session: Session, city_id: Id) -> list[GuestHouse]:
        stmt = GuestHouseRepositoryCore._query_find_all_by_city_id(city_id)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [GuestHouseRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_available_one_by_city_id(session: Session, city_id: Id) -> GuestHouse | None:
        stmt = GuestHouseRepositoryCore._query_find_available_one_by_city_id(city_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return GuestHouseRepositoryCore.to_entity(model) if model else None
