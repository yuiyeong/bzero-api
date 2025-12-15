"""Ticket Repository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.

구조:
    TicketRepositoryCore (쿼리 빌더 + 변환 + DB 작업)
         ↑          ↑
    SqlAlchemy     SqlAlchemy
    TicketRepo     TicketSyncRepo
    (run_sync)     (직접 호출)
"""

from sqlalchemy import Select, Update, func, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities import Ticket
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus
from bzero.infrastructure.db.ticket_model import TicketModel


class TicketRepositoryCore:
    """Ticket Repository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_id(ticket_id: Id) -> Select[tuple[TicketModel]]:
        """ID로 티켓을 조회하는 쿼리를 생성합니다."""
        return select(TicketModel).where(
            TicketModel.ticket_id == ticket_id.value,
            TicketModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_by_user_id(
        user_id: Id,
        offset: int = 0,
        limit: int = 100,
    ) -> Select[tuple[TicketModel]]:
        """사용자의 모든 티켓을 조회하는 쿼리를 생성합니다."""
        return (
            select(TicketModel)
            .where(
                TicketModel.user_id == user_id.value,
                TicketModel.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
            .order_by(TicketModel.departure_datetime.desc())
        )

    @staticmethod
    def _query_find_all_by_user_id_and_status(
        user_id: Id,
        status: TicketStatus,
        offset: int = 0,
        limit: int = 100,
    ) -> Select[tuple[TicketModel]]:
        """사용자의 특정 상태 티켓을 조회하는 쿼리를 생성합니다."""
        return (
            select(TicketModel)
            .where(
                TicketModel.user_id == user_id.value,
                TicketModel.status == status.value,
                TicketModel.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
            .order_by(TicketModel.departure_datetime.desc())
        )

    @staticmethod
    def _query_count_by(
        user_id: Id | None = None,
        status: TicketStatus | None = None,
    ) -> Select[tuple[int]]:
        """조건에 맞는 티켓 개수를 조회하는 쿼리를 생성합니다."""
        stmt = select(func.count()).select_from(TicketModel).where(TicketModel.deleted_at.is_(None))
        if user_id is not None:
            stmt = stmt.where(TicketModel.user_id == user_id.value)
        if status is not None:
            stmt = stmt.where(TicketModel.status == status.value)
        return stmt

    @staticmethod
    def _query_update(ticket: Ticket) -> Update:
        """티켓 상태를 업데이트하는 쿼리를 생성합니다."""
        return (
            update(TicketModel)
            .where(
                TicketModel.ticket_id == ticket.ticket_id.value,
                TicketModel.deleted_at.is_(None),
            )
            .values(status=ticket.status.value)
            .returning(TicketModel)
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: Ticket) -> TicketModel:
        """Ticket 엔티티를 TicketModel(ORM)로 변환합니다."""
        return TicketModel(
            ticket_id=entity.ticket_id.value,
            user_id=entity.user_id.value,
            ticket_number=entity.ticket_number,
            cost_points=entity.cost_points,
            status=entity.status.value,
            departure_datetime=entity.departure_datetime,
            arrival_datetime=entity.arrival_datetime,
            # City 스냅샷 펼치기
            city_id=entity.city_snapshot.city_id.value,
            city_name=entity.city_snapshot.name,
            city_theme=entity.city_snapshot.theme,
            city_image_url=entity.city_snapshot.image_url,
            city_description=entity.city_snapshot.description,
            city_base_cost_points=entity.city_snapshot.base_cost_points,
            city_base_duration_hours=entity.city_snapshot.base_duration_hours,
            # Airship 스냅샷 펼치기
            airship_id=entity.airship_snapshot.airship_id.value,
            airship_name=entity.airship_snapshot.name,
            airship_image_url=entity.airship_snapshot.image_url,
            airship_description=entity.airship_snapshot.description,
            airship_cost_factor=entity.airship_snapshot.cost_factor,
            airship_duration_factor=entity.airship_snapshot.duration_factor,
        )

    @staticmethod
    def to_entity(model: TicketModel) -> Ticket:
        """TicketModel(ORM)을 Ticket 엔티티로 변환합니다."""
        return Ticket(
            ticket_id=Id(model.ticket_id),
            user_id=Id(model.user_id),
            ticket_number=model.ticket_number,
            cost_points=model.cost_points,
            status=TicketStatus(model.status),
            departure_datetime=model.departure_datetime,
            arrival_datetime=model.arrival_datetime,
            # City 스냅샷 조립
            city_snapshot=CitySnapshot(
                city_id=Id(model.city_id),
                name=model.city_name,
                theme=model.city_theme,
                image_url=model.city_image_url,
                description=model.city_description,
                base_cost_points=model.city_base_cost_points,
                base_duration_hours=model.city_base_duration_hours,
            ),
            # Airship 스냅샷 조립
            airship_snapshot=AirshipSnapshot(
                airship_id=Id(model.airship_id),
                name=model.airship_name,
                image_url=model.airship_image_url,
                description=model.airship_description,
                cost_factor=model.airship_cost_factor,
                duration_factor=model.airship_duration_factor,
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, ticket: Ticket) -> Ticket:
        """티켓을 생성합니다."""
        model = TicketRepositoryCore.to_model(ticket)

        session.add(model)
        session.flush()
        session.refresh(model)

        return TicketRepositoryCore.to_entity(model)

    @staticmethod
    def update(session: Session, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """
        stmt = TicketRepositoryCore._query_update(ticket)

        result = session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise NotFoundTicketError
        return TicketRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_id(session: Session, ticket_id: Id) -> Ticket | None:
        """ID로 티켓을 조회합니다."""
        stmt = TicketRepositoryCore._query_find_by_id(ticket_id)

        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return TicketRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_all_by_user_id(
        session: Session,
        user_id: Id,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Ticket]:
        """사용자의 모든 티켓을 조회합니다."""
        stmt = TicketRepositoryCore._query_find_all_by_user_id(user_id, offset, limit)

        result = session.execute(stmt)
        models = result.scalars().all()
        return [TicketRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_all_by_user_id_and_status(
        session: Session,
        user_id: Id,
        status: TicketStatus,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Ticket]:
        """사용자의 특정 상태 티켓을 조회합니다."""
        stmt = TicketRepositoryCore._query_find_all_by_user_id_and_status(user_id, status, offset, limit)

        result = session.execute(stmt)
        models = result.scalars().all()
        return [TicketRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def count_by(
        session: Session,
        user_id: Id | None = None,
        status: TicketStatus | None = None,
    ) -> int:
        """조건에 맞는 티켓 개수를 조회합니다."""
        stmt = TicketRepositoryCore._query_count_by(user_id, status)
        result = session.execute(stmt)
        return result.scalar_one()
