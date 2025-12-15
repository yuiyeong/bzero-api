"""RoomRepository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.

구조:
    RoomRepositoryCore (쿼리 빌더 + 변환 + DB 작업)
         ↑          ↑
    SqlAlchemy     SqlAlchemy
    RoomRepo       RoomSyncRepo
    (run_sync)     (직접 호출)
"""

from typing import ClassVar

from sqlalchemy import Select, Update, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from bzero.domain.entities.room import Room
from bzero.domain.errors import NotFoundRoomError, RoomCapacityLockError
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.room_model import RoomModel


class RoomRepositoryCore:
    """RoomRepository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    LOCK_CONFLICT_STATES: ClassVar[set[str]] = {"55P03", "40P01"}

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_room_id(room_id: Id) -> Select[tuple[RoomModel]]:
        """ID로 룸을 조회하는 쿼리를 생성합니다."""
        return select(RoomModel).where(
            RoomModel.room_id == room_id.value,
            RoomModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_available_by_guest_house_id_for_update(
        guest_house_id: Id,
    ) -> Select[tuple[RoomModel]]:
        """게스트하우스의 이용 가능한 룸을 조회하는 쿼리를 생성합니다."""
        return (
            select(RoomModel)
            .where(
                RoomModel.guest_house_id == guest_house_id.value,
                RoomModel.current_capacity < RoomModel.max_capacity,
                RoomModel.deleted_at.is_(None),
            )
            .limit(1)
            .with_for_update(of=RoomModel, nowait=False)
        )

    @staticmethod
    def _query_update(room: Room) -> Update:
        """룸을 업데이트하는 쿼리를 생성합니다."""
        return (
            update(RoomModel)
            .where(
                RoomModel.room_id == room.room_id.value,
                RoomModel.deleted_at.is_(None),
            )
            .values(
                max_capacity=room.max_capacity,
                current_capacity=room.current_capacity,
            )
            .returning(RoomModel)
        )

    # ==================== 락 충돌 처리 ====================

    @classmethod
    def _is_lock_conflict_error(cls, e: OperationalError) -> bool:
        """PostgreSQL 락 충돌 에러인지 확인합니다."""
        sql_state = (
            getattr(getattr(e, "orig", None), "pgcode", None)
            or getattr(getattr(e, "orig", None), "sqlstate", None)
            or getattr(getattr(getattr(e, "orig", None), "diag", None), "sqlstate", None)
        )
        return sql_state in cls.LOCK_CONFLICT_STATES

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: Room) -> RoomModel:
        """Room 엔티티를 RoomModel(ORM)로 변환합니다."""
        return RoomModel(
            room_id=entity.room_id.value,
            guest_house_id=entity.guest_house_id.value,
            max_capacity=entity.max_capacity,
            current_capacity=entity.current_capacity,
        )

    @staticmethod
    def to_entity(model: RoomModel) -> Room:
        """RoomModel(ORM)을 Room 엔티티로 변환합니다."""
        return Room(
            room_id=Id(model.room_id),
            guest_house_id=Id(model.guest_house_id),
            max_capacity=model.max_capacity,
            current_capacity=model.current_capacity,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, room: Room) -> Room:
        """룸을 생성합니다."""
        model = RoomRepositoryCore.to_model(room)

        session.add(model)
        session.flush()
        session.refresh(model)

        return RoomRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_room_id(session: Session, room_id: Id) -> Room | None:
        """ID로 룸을 조회합니다."""
        stmt = RoomRepositoryCore._query_find_by_room_id(room_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return RoomRepositoryCore.to_entity(model) if model else None

    @classmethod
    def find_available_by_guest_house_id_for_update(cls, session: Session, guest_house_id: Id) -> list[Room]:
        """게스트하우스의 이용 가능한 룸 목록을 조회합니다."""
        stmt = RoomRepositoryCore._query_find_available_by_guest_house_id_for_update(guest_house_id)
        try:
            result = session.execute(stmt)
        except OperationalError as e:
            if cls._is_lock_conflict_error(e):
                raise RoomCapacityLockError from e
            raise e
        models = result.scalars().all()
        return [RoomRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def update(session: Session, room: Room) -> Room:
        """룸을 업데이트합니다.

        Raises:
            NotFoundRoomError: 룸을 찾을 수 없는 경우
        """
        stmt = RoomRepositoryCore._query_update(room)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundRoomError
        return RoomRepositoryCore.to_entity(model)
