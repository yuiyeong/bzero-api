"""티켓 리포지토리 공통 Base 클래스.

Async/Sync 리포지토리에서 공유하는 쿼리 생성 및 Entity/Model 변환 로직을 제공합니다.
이 패턴을 통해 FastAPI(비동기)와 Celery(동기) 환경에서 동일한 쿼리 로직을 재사용할 수 있습니다.

구조:
    TicketRepositoryBase (쿼리 빌더 + 변환)
         ↑          ↑
         │          │
    SqlAlchemy     SqlAlchemy
    TicketRepo     TicketSyncRepo
    (Async)        (Sync)
"""

from sqlalchemy import Select, Update, func, select, update

from bzero.domain.entities import Ticket
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus
from bzero.infrastructure.db.ticket_model import TicketModel


class TicketRepositoryBase:
    """티켓 리포지토리 공통 Base 클래스.

    쿼리 생성 메서드와 Entity/Model 변환 메서드를 제공합니다.
    Async/Sync Repository에서 이 클래스를 상속받아 사용합니다.
    """

    @staticmethod
    def _query_find_by_id(ticket_id: Id) -> Select[tuple[TicketModel]]:
        """ID로 티켓을 조회하는 쿼리를 생성합니다.

        Args:
            ticket_id: 조회할 티켓 ID

        Returns:
            SQLAlchemy Select 쿼리
        """
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
        """사용자의 모든 티켓을 조회하는 쿼리를 생성합니다.

        Args:
            user_id: 사용자 ID
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            SQLAlchemy Select 쿼리 (출발일시 내림차순 정렬)
        """
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
        """사용자의 특정 상태 티켓을 조회하는 쿼리를 생성합니다.

        Args:
            user_id: 사용자 ID
            status: 필터링할 티켓 상태
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            SQLAlchemy Select 쿼리 (출발일시 내림차순 정렬)
        """
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
        """조건에 맞는 티켓 개수를 조회하는 쿼리를 생성합니다.

        Args:
            user_id: 사용자 ID (선택)
            status: 티켓 상태 (선택)

        Returns:
            SQLAlchemy Select 쿼리 (COUNT)
        """
        stmt = select(func.count()).select_from(TicketModel).where(TicketModel.deleted_at.is_(None))
        if user_id is not None:
            stmt = stmt.where(TicketModel.user_id == user_id.value)
        if status is not None:
            stmt = stmt.where(TicketModel.status == status.value)
        return stmt

    @staticmethod
    def _query_update(ticket: Ticket) -> Update:
        """티켓 상태를 업데이트하는 쿼리를 생성합니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            SQLAlchemy Update 쿼리 (RETURNING 포함)
        """
        return (
            update(TicketModel)
            .where(
                TicketModel.ticket_id == ticket.ticket_id.value,
                TicketModel.deleted_at.is_(None),
            )
            .values(status=ticket.status.value)
            .returning(TicketModel)
        )

    @staticmethod
    def to_model(entity: Ticket) -> TicketModel:
        """Ticket 엔티티를 TicketModel(ORM)로 변환합니다.

        City/Airship 스냅샷은 개별 컬럼으로 펼쳐서 저장합니다.

        Args:
            entity: 변환할 Ticket 엔티티

        Returns:
            TicketModel 인스턴스
        """
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
        """TicketModel(ORM)을 Ticket 엔티티로 변환합니다.

        개별 컬럼으로 저장된 City/Airship 정보를 스냅샷 객체로 조립합니다.

        Args:
            model: 변환할 TicketModel 인스턴스

        Returns:
            Ticket 엔티티
        """
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
