"""DirectMessageRoom Repository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.
"""

from typing import Any

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.value_objects import DMStatus, Id
from bzero.infrastructure.db.direct_message_room_model import DirectMessageRoomModel


class DirectMessageRoomRepositoryCore:
    """DirectMessageRoom Repository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_id(dm_room_id: Id) -> Select[tuple[DirectMessageRoomModel]]:
        """ID로 대화방을 조회하는 쿼리를 생성합니다."""
        return select(DirectMessageRoomModel).where(
            DirectMessageRoomModel.dm_room_id == dm_room_id.value,
            DirectMessageRoomModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_by_room_and_users(
        room_id: Id,
        requester_id: Id,
        receiver_id: Id,
    ) -> Select[tuple[DirectMessageRoomModel]]:
        """룸과 사용자로 대화방을 조회하는 쿼리를 생성합니다.

        양방향 조회: (requester, receiver) 또는 (receiver, requester) 모두 확인합니다.
        활성 상태 (PENDING, ACCEPTED, ACTIVE)인 대화방만 조회합니다.
        """
        active_statuses = [DMStatus.PENDING.value, DMStatus.ACCEPTED.value, DMStatus.ACTIVE.value]
        return select(DirectMessageRoomModel).where(
            DirectMessageRoomModel.room_id == room_id.value,
            DirectMessageRoomModel.deleted_at.is_(None),
            DirectMessageRoomModel.status.in_(active_statuses),
            or_(
                # (requester_id, receiver_id) 조합
                (DirectMessageRoomModel.requester_id == requester_id.value)
                & (DirectMessageRoomModel.receiver_id == receiver_id.value),
                # (receiver_id, requester_id) 조합 (역방향)
                (DirectMessageRoomModel.requester_id == receiver_id.value)
                & (DirectMessageRoomModel.receiver_id == requester_id.value),
            ),
        )

    @staticmethod
    def _query_find_by_user_and_statuses(
        user_id: Id,
        statuses: list[DMStatus],
        limit: int = 50,
        offset: int = 0,
    ) -> Select[tuple[DirectMessageRoomModel]]:
        """사용자와 상태로 대화방 목록을 조회하는 쿼리를 생성합니다."""
        status_values = [s.value for s in statuses]
        return (
            select(DirectMessageRoomModel)
            .where(
                DirectMessageRoomModel.deleted_at.is_(None),
                DirectMessageRoomModel.status.in_(status_values),
                or_(
                    DirectMessageRoomModel.requester_id == user_id.value,
                    DirectMessageRoomModel.receiver_id == user_id.value,
                ),
            )
            .order_by(DirectMessageRoomModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

    @staticmethod
    def _query_count_by_user_and_statuses(
        user_id: Id,
        statuses: list[DMStatus],
    ) -> Select[tuple[Any]]:
        """사용자와 상태별 대화방 개수를 조회하는 쿼리를 생성합니다."""
        status_values = [s.value for s in statuses]
        return select(func.count(DirectMessageRoomModel.dm_room_id)).where(
            DirectMessageRoomModel.deleted_at.is_(None),
            DirectMessageRoomModel.status.in_(status_values),
            or_(
                DirectMessageRoomModel.requester_id == user_id.value,
                DirectMessageRoomModel.receiver_id == user_id.value,
            ),
        )

    @staticmethod
    def to_entity(model: DirectMessageRoomModel) -> DirectMessageRoom:
        """ORM 모델을 도메인 엔티티로 변환합니다."""
        return DirectMessageRoom(
            dm_room_id=Id(str(model.dm_room_id)),
            guesthouse_id=Id(str(model.guesthouse_id)),
            room_id=Id(str(model.room_id)),
            requester_id=Id(str(model.requester_id)),
            receiver_id=Id(str(model.receiver_id)),
            status=DMStatus(model.status),
            started_at=model.started_at,
            ended_at=model.ended_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(entity: DirectMessageRoom) -> DirectMessageRoomModel:
        """도메인 엔티티를 ORM 모델로 변환합니다."""
        return DirectMessageRoomModel(
            dm_room_id=entity.dm_room_id.value,
            guesthouse_id=entity.guesthouse_id.value,
            room_id=entity.room_id.value,
            requester_id=entity.requester_id.value,
            receiver_id=entity.receiver_id.value,
            status=entity.status.value,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방을 생성합니다."""
        model = DirectMessageRoomRepositoryCore.to_model(dm_room)
        session.add(model)
        session.flush()
        session.refresh(model)
        return DirectMessageRoomRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_id(session: Session, dm_room_id: Id) -> DirectMessageRoom | None:
        """ID로 대화방을 조회합니다."""
        stmt = DirectMessageRoomRepositoryCore._query_find_by_id(dm_room_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return DirectMessageRoomRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_by_room_and_users(
        session: Session,
        room_id: Id,
        requester_id: Id,
        receiver_id: Id,
    ) -> DirectMessageRoom | None:
        """룸과 사용자로 대화방을 조회합니다."""
        stmt = DirectMessageRoomRepositoryCore._query_find_by_room_and_users(
            room_id, requester_id, receiver_id
        )
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return DirectMessageRoomRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_by_user_and_statuses(
        session: Session,
        user_id: Id,
        statuses: list[DMStatus],
        limit: int = 50,
        offset: int = 0,
    ) -> list[DirectMessageRoom]:
        """사용자와 상태로 대화방 목록을 조회합니다."""
        stmt = DirectMessageRoomRepositoryCore._query_find_by_user_and_statuses(
            user_id, statuses, limit, offset
        )
        result = session.execute(stmt)
        models = result.scalars().all()
        return [DirectMessageRoomRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def update(session: Session, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방 정보를 업데이트합니다."""
        stmt = select(DirectMessageRoomModel).where(
            DirectMessageRoomModel.dm_room_id == dm_room.dm_room_id.value
        )
        result = session.execute(stmt)
        model = result.scalar_one()

        # 업데이트할 필드 (updated_at은 DB 트리거에서 자동 업데이트)
        model.status = dm_room.status.value
        model.started_at = dm_room.started_at
        model.ended_at = dm_room.ended_at
        model.deleted_at = dm_room.deleted_at

        session.flush()
        session.refresh(model)
        return DirectMessageRoomRepositoryCore.to_entity(model)

    @staticmethod
    def soft_delete_by_room_id(session: Session, room_id: Id) -> int:
        """룸 ID로 대화방들을 soft delete 처리합니다."""
        stmt = (
            update(DirectMessageRoomModel)
            .where(
                DirectMessageRoomModel.room_id == room_id.value,
                DirectMessageRoomModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        result = session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    @staticmethod
    def count_by_user_and_statuses(
        session: Session,
        user_id: Id,
        statuses: list[DMStatus],
    ) -> int:
        """사용자와 상태별 대화방 개수를 조회합니다."""
        stmt = DirectMessageRoomRepositoryCore._query_count_by_user_and_statuses(user_id, statuses)
        result = session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    def end_active_dm_rooms_by_room_id(session: Session, room_id: Id) -> int:
        """룸 ID로 활성 대화방들을 종료 처리합니다.

        체크아웃 시 해당 룸의 PENDING, ACCEPTED, ACTIVE 상태 대화방을 ENDED로 변경합니다.

        Args:
            session: DB 세션
            room_id: 룸 ID

        Returns:
            종료된 대화방 개수
        """
        active_statuses = [DMStatus.PENDING.value, DMStatus.ACCEPTED.value, DMStatus.ACTIVE.value]
        stmt = (
            update(DirectMessageRoomModel)
            .where(
                DirectMessageRoomModel.room_id == room_id.value,
                DirectMessageRoomModel.deleted_at.is_(None),
                DirectMessageRoomModel.status.in_(active_statuses),
            )
            .values(
                status=DMStatus.ENDED.value,
                ended_at=func.now(),
                updated_at=func.now(),
            )
        )
        result = session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
