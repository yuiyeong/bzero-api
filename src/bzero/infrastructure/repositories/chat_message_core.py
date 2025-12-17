"""ChatMessage Repository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로, 동기 리포지토리는 직접 호출합니다.

구조:
    ChatMessageRepositoryCore (쿼리 빌더 + 변환 + DB 작업)
         ↑          ↑
    SqlAlchemy     SqlAlchemy
    ChatMessageRepo ChatMessageSyncRepo
    (run_sync)     (직접 호출)
"""

from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities import ChatMessage
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, MessageType
from bzero.infrastructure.db.chat_message_model import ChatMessageModel


class ChatMessageRepositoryCore:
    """ChatMessage Repository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_id(message_id: Id) -> Select[tuple[ChatMessageModel]]:
        """ID로 메시지를 조회하는 쿼리를 생성합니다."""
        return select(ChatMessageModel).where(
            ChatMessageModel.message_id == message_id.value,
            ChatMessageModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_by_room_id_paginated(
        room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> Select[tuple[ChatMessageModel]]:
        """룸별 메시지를 cursor 기반 페이지네이션으로 조회하는 쿼리를 생성합니다."""
        stmt = (
            select(ChatMessageModel)
            .where(
                ChatMessageModel.room_id == room_id.value,
                ChatMessageModel.deleted_at.is_(None),
            )
            .order_by(ChatMessageModel.created_at.desc(), ChatMessageModel.message_id.desc())
            .limit(limit)
        )

        if cursor is not None:
            # cursor 이후의 메시지만 조회
            # (created_at, message_id) < (cursor_created_at, cursor_message_id)
            # 먼저 cursor 메시지를 조회하여 created_at을 가져와야 함
            cursor_stmt = select(ChatMessageModel.created_at).where(
                ChatMessageModel.message_id == cursor.value,
            )
            # 서브쿼리를 사용하여 cursor의 created_at을 가져옴
            stmt = stmt.where(
                (ChatMessageModel.created_at < cursor_stmt.scalar_subquery())
                | (
                    (ChatMessageModel.created_at == cursor_stmt.scalar_subquery())
                    & (ChatMessageModel.message_id < cursor.value)
                )
            )

        return stmt

    @staticmethod
    def _query_find_expired_messages(before_datetime: datetime) -> Select[tuple[ChatMessageModel]]:
        """만료 시간이 지난 메시지를 조회하는 쿼리를 생성합니다."""
        return select(ChatMessageModel).where(
            ChatMessageModel.expires_at < before_datetime,
            ChatMessageModel.deleted_at.is_(None),
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: ChatMessage) -> ChatMessageModel:
        """ChatMessage 엔티티를 Model로 변환합니다."""
        return ChatMessageModel(
            message_id=entity.message_id.value,
            room_id=entity.room_id.value,
            user_id=entity.user_id.value if entity.user_id else None,
            content=entity.content.value,
            card_id=entity.card_id.value if entity.card_id else None,
            message_type=entity.message_type.value,
            is_system=entity.is_system,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def to_entity(model: ChatMessageModel) -> ChatMessage:
        """Model을 ChatMessage 엔티티로 변환합니다."""
        return ChatMessage(
            message_id=Id(model.message_id),
            room_id=Id(model.room_id),
            user_id=Id(model.user_id) if model.user_id else None,
            content=MessageContent(model.content),
            card_id=Id(model.card_id) if model.card_id else None,
            message_type=MessageType(model.message_type),
            is_system=model.is_system,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, message: ChatMessage) -> ChatMessage:
        """메시지를 생성합니다."""
        model = ChatMessageRepositoryCore.to_model(message)
        session.add(model)
        session.flush()
        session.refresh(model)
        return ChatMessageRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_id(session: Session, message_id: Id) -> ChatMessage | None:
        """ID로 메시지를 조회합니다."""
        stmt = ChatMessageRepositoryCore._query_find_by_id(message_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return ChatMessageRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_by_room_id_paginated(
        session: Session,
        room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """룸별 메시지를 cursor 기반 페이지네이션으로 조회합니다."""
        stmt = ChatMessageRepositoryCore._query_find_by_room_id_paginated(room_id, cursor, limit)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [ChatMessageRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_expired_messages(session: Session, before_datetime: datetime) -> list[ChatMessage]:
        """만료 시간이 지난 메시지를 조회합니다."""
        stmt = ChatMessageRepositoryCore._query_find_expired_messages(before_datetime)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [ChatMessageRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def delete_messages(session: Session, message_ids: list[Id]) -> int:
        """메시지를 soft delete 처리합니다."""
        if not message_ids:
            return 0

        message_id_values = [msg_id.value for msg_id in message_ids]
        stmt = (
            update(ChatMessageModel)
            .where(
                ChatMessageModel.message_id.in_(message_id_values),
                ChatMessageModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        result = session.execute(stmt)
        return result.rowcount  # type: ignore
