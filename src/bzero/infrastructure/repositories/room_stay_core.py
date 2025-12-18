"""RoomStayRepository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.

구조:
    RoomStayRepositoryCore (쿼리 빌더 + 변환 + DB 작업)
         ↑          ↑
    SqlAlchemy     SqlAlchemy
    RoomStayRepo   RoomStaySyncRepo
    (run_sync)     (직접 호출)
"""

from datetime import datetime

from sqlalchemy import Select, Update, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities.room_stay import RoomStay
from bzero.domain.errors import NotFoundRoomStayError
from bzero.domain.value_objects import Id, RoomStayStatus
from bzero.infrastructure.db.room_stay_model import RoomStayModel


class RoomStayRepositoryCore:
    """RoomStayRepository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_room_stay_id(room_stay_id: Id) -> Select[tuple[RoomStayModel]]:
        """ID로 룸 스테이를 조회하는 쿼리를 생성합니다."""
        return select(RoomStayModel).where(
            RoomStayModel.room_stay_id == room_stay_id.value,
            RoomStayModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_checked_in_by_user_id(user_id: Id) -> Select[tuple[RoomStayModel]]:
        """사용자의 체크인된 룸 스테이를 조회하는 쿼리를 생성합니다."""
        return select(RoomStayModel).where(
            RoomStayModel.user_id == user_id.value,
            RoomStayModel.status != RoomStayStatus.CHECKED_OUT.value,
            RoomStayModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_checked_in_by_room_id(
        room_id: Id,
    ) -> Select[tuple[RoomStayModel]]:
        """룸의 체크인된 모든 룸 스테이를 조회하는 쿼리를 생성합니다."""
        return select(RoomStayModel).where(
            RoomStayModel.room_id == room_id.value,
            RoomStayModel.status != RoomStayStatus.CHECKED_OUT.value,
            RoomStayModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_by_ticket_id(ticket_id: Id) -> Select[tuple[RoomStayModel]]:
        """티켓 ID로 모든 룸 스테이를 조회하는 쿼리를 생성합니다."""
        return select(RoomStayModel).where(
            RoomStayModel.ticket_id == ticket_id.value,
            RoomStayModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_due_for_check_out(
        before: datetime,
    ) -> Select[tuple[RoomStayModel]]:
        """체크아웃 예정 시간이 지난 룸 스테이를 조회하는 쿼리를 생성합니다."""
        return select(RoomStayModel).where(
            RoomStayModel.scheduled_check_out_at < before,
            RoomStayModel.status != RoomStayStatus.CHECKED_OUT.value,
            RoomStayModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_update(room_stay: RoomStay) -> Update:
        """룸 스테이를 업데이트하는 쿼리를 생성합니다."""
        return (
            update(RoomStayModel)
            .where(
                RoomStayModel.room_stay_id == room_stay.room_stay_id.value,
                RoomStayModel.deleted_at.is_(None),
            )
            .values(
                status=room_stay.status.value,
                scheduled_check_out_at=room_stay.scheduled_check_out_at,
                actual_check_out_at=room_stay.actual_check_out_at,
                extension_count=room_stay.extension_count,
            )
            .returning(RoomStayModel)
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: RoomStay) -> RoomStayModel:
        """RoomStay 엔티티를 RoomStayModel(ORM)로 변환합니다."""
        return RoomStayModel(
            room_stay_id=entity.room_stay_id.value,
            user_id=entity.user_id.value,
            city_id=entity.city_id.value,
            guest_house_id=entity.guest_house_id.value,
            room_id=entity.room_id.value,
            ticket_id=entity.ticket_id.value,
            status=entity.status.value,
            check_in_at=entity.check_in_at,
            scheduled_check_out_at=entity.scheduled_check_out_at,
            actual_check_out_at=entity.actual_check_out_at,
            extension_count=entity.extension_count,
        )

    @staticmethod
    def to_entity(model: RoomStayModel) -> RoomStay:
        """RoomStayModel(ORM)을 RoomStay 엔티티로 변환합니다."""
        return RoomStay(
            room_stay_id=Id(model.room_stay_id),
            user_id=Id(model.user_id),
            city_id=Id(model.city_id),
            guest_house_id=Id(model.guest_house_id),
            room_id=Id(model.room_id),
            ticket_id=Id(model.ticket_id),
            status=RoomStayStatus(model.status),
            check_in_at=model.check_in_at,
            scheduled_check_out_at=model.scheduled_check_out_at,
            actual_check_out_at=model.actual_check_out_at,
            extension_count=model.extension_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, room_stay: RoomStay) -> RoomStay:
        """룸 스테이를 생성합니다."""
        model = RoomStayRepositoryCore.to_model(room_stay)

        session.add(model)
        session.flush()
        session.refresh(model)

        return RoomStayRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_room_stay_id(session: Session, room_stay_id: Id) -> RoomStay | None:
        """ID로 룸 스테이를 조회합니다."""
        stmt = RoomStayRepositoryCore._query_find_by_room_stay_id(room_stay_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return RoomStayRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_checked_in_by_user_id(session: Session, user_id: Id) -> RoomStay | None:
        """사용자의 체크인된 룸 스테이를 조회합니다."""
        stmt = RoomStayRepositoryCore._query_find_checked_in_by_user_id(user_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return RoomStayRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_all_checked_in_by_room_id(session: Session, room_id: Id) -> list[RoomStay]:
        """룸의 체크인된 모든 룸 스테이를 조회합니다."""
        stmt = RoomStayRepositoryCore._query_find_all_checked_in_by_room_id(room_id)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [RoomStayRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_all_by_ticket_id(session: Session, ticket_id: Id) -> list[RoomStay]:
        """티켓 ID로 모든 룸 스테이를 조회합니다."""
        stmt = RoomStayRepositoryCore._query_find_all_by_ticket_id(ticket_id)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [RoomStayRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_all_due_for_check_out(session: Session, before: datetime) -> list[RoomStay]:
        """체크아웃 예정 시간이 지난 룸 스테이를 조회합니다."""
        stmt = RoomStayRepositoryCore._query_find_all_due_for_check_out(before)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [RoomStayRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def update(session: Session, room_stay: RoomStay) -> RoomStay:
        """룸 스테이를 업데이트합니다.

        Raises:
            NotFoundRoomStayError: 룸 스테이를 찾을 수 없는 경우
        """
        stmt = RoomStayRepositoryCore._query_update(room_stay)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundRoomStayError
        return RoomStayRepositoryCore.to_entity(model)
