"""DirectMessage Repository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.
"""

from typing import Any

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities.direct_message import DirectMessage
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent
from bzero.infrastructure.db.direct_message_model import DirectMessageModel


class DirectMessageRepositoryCore:
    """DirectMessage Repository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_id(dm_id: Id) -> Select[tuple[DirectMessageModel]]:
        """ID로 메시지를 조회하는 쿼리를 생성합니다."""
        return select(DirectMessageModel).where(
            DirectMessageModel.dm_id == dm_id.value,
            DirectMessageModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_by_dm_room_paginated(
        dm_room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> Select[tuple[DirectMessageModel]]:
        """대화방별 메시지를 cursor 기반 페이지네이션으로 조회하는 쿼리를 생성합니다.

        오래된 메시지부터 조회 (created_at ASC)
        """
        stmt = (
            select(DirectMessageModel)
            .where(
                DirectMessageModel.dm_room_id == dm_room_id.value,
                DirectMessageModel.deleted_at.is_(None),
            )
            .order_by(DirectMessageModel.created_at.asc(), DirectMessageModel.dm_id.asc())
            .limit(limit)
        )

        if cursor is not None:
            # cursor 이후의 메시지 조회
            cursor_stmt = select(DirectMessageModel.created_at).where(
                DirectMessageModel.dm_id == cursor.value,
            )
            stmt = stmt.where(
                (DirectMessageModel.created_at > cursor_stmt.scalar_subquery())
                | (
                    (DirectMessageModel.created_at == cursor_stmt.scalar_subquery())
                    & (DirectMessageModel.dm_id > cursor.value)
                )
            )

        return stmt

    @staticmethod
    def _query_find_latest_by_dm_room(dm_room_id: Id) -> Select[tuple[DirectMessageModel]]:
        """대화방의 가장 최근 메시지를 조회하는 쿼리를 생성합니다."""
        return (
            select(DirectMessageModel)
            .where(
                DirectMessageModel.dm_room_id == dm_room_id.value,
                DirectMessageModel.deleted_at.is_(None),
            )
            .order_by(DirectMessageModel.created_at.desc(), DirectMessageModel.dm_id.desc())
            .limit(1)
        )

    @staticmethod
    def _query_count_unread(dm_room_id: Id, user_id: Id) -> Select[tuple[Any]]:
        """읽지 않은 메시지 개수를 조회하는 쿼리를 생성합니다."""
        return select(func.count(DirectMessageModel.dm_id)).where(
            DirectMessageModel.dm_room_id == dm_room_id.value,
            DirectMessageModel.to_user_id == user_id.value,
            DirectMessageModel.is_read.is_(False),
            DirectMessageModel.deleted_at.is_(None),
        )

    @staticmethod
    def to_entity(model: DirectMessageModel) -> DirectMessage:
        """ORM 모델을 도메인 엔티티로 변환합니다."""
        return DirectMessage(
            dm_id=Id(str(model.dm_id)),
            dm_room_id=Id(str(model.dm_room_id)),
            from_user_id=Id(str(model.from_user_id)),
            to_user_id=Id(str(model.to_user_id)),
            content=MessageContent(model.content),
            is_read=model.is_read,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(entity: DirectMessage) -> DirectMessageModel:
        """도메인 엔티티를 ORM 모델로 변환합니다."""
        return DirectMessageModel(
            dm_id=entity.dm_id.value,
            dm_room_id=entity.dm_room_id.value,
            from_user_id=entity.from_user_id.value,
            to_user_id=entity.to_user_id.value,
            content=entity.content.value,
            is_read=entity.is_read,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, message: DirectMessage) -> DirectMessage:
        """메시지를 생성합니다."""
        model = DirectMessageRepositoryCore.to_model(message)
        session.add(model)
        session.flush()
        session.refresh(model)
        return DirectMessageRepositoryCore.to_entity(model)

    @staticmethod
    def update(session: Session, message: DirectMessage) -> DirectMessage:
        """메시지를 업데이트합니다."""
        stmt = select(DirectMessageModel).where(DirectMessageModel.dm_id == message.dm_id.value)
        result = session.execute(stmt)
        model = result.scalar_one()

        model.is_read = message.is_read
        model.deleted_at = message.deleted_at
        # updated_at은 DB 트리거에 의해 자동으로 갱신됩니다.

        session.flush()
        session.refresh(model)
        return DirectMessageRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_id(session: Session, dm_id: Id) -> DirectMessage | None:
        """ID로 메시지를 조회합니다."""
        stmt = DirectMessageRepositoryCore._query_find_by_id(dm_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return DirectMessageRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_by_dm_room_paginated(
        session: Session,
        dm_room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[DirectMessage]:
        """대화방별 메시지를 cursor 기반 페이지네이션으로 조회합니다."""
        stmt = DirectMessageRepositoryCore._query_find_by_dm_room_paginated(
            dm_room_id, cursor, limit
        )
        result = session.execute(stmt)
        models = result.scalars().all()
        return [DirectMessageRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_latest_by_dm_room(session: Session, dm_room_id: Id) -> DirectMessage | None:
        """대화방의 가장 최근 메시지를 조회합니다."""
        stmt = DirectMessageRepositoryCore._query_find_latest_by_dm_room(dm_room_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return DirectMessageRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def mark_as_read_by_dm_room_and_user(
        session: Session,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """대화방의 사용자가 수신한 메시지를 읽음 처리합니다."""
        stmt = (
            update(DirectMessageModel)
            .where(
                DirectMessageModel.dm_room_id == dm_room_id.value,
                DirectMessageModel.to_user_id == user_id.value,
                DirectMessageModel.is_read.is_(False),
                DirectMessageModel.deleted_at.is_(None),
            )
            .values(is_read=True)
        )
        result = session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    @staticmethod
    def count_unread_by_dm_room_and_user(
        session: Session,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """읽지 않은 메시지 개수를 조회합니다."""
        stmt = DirectMessageRepositoryCore._query_count_unread(dm_room_id, user_id)
        result = session.execute(stmt)
        return result.scalar() or 0
