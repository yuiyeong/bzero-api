"""ChatMessage Repository 구현체 (비동기/동기).

SqlAlchemy를 사용한 채팅 메시지 리포지토리 구현입니다.
- SqlAlchemyChatMessageRepository: 비동기 (FastAPI용)
- SqlAlchemyChatMessageSyncRepository: 동기 (Celery용)
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bzero.domain.entities import ChatMessage
from bzero.domain.repositories.chat_message import ChatMessageRepository, ChatMessageSyncRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.chat_message_core import ChatMessageRepositoryCore


class SqlAlchemyChatMessageRepository(ChatMessageRepository):
    """SqlAlchemy 기반 채팅 메시지 리포지토리 (비동기).

    AsyncSession을 사용하여 비동기 DB 작업을 수행합니다.
    Core 메서드를 run_sync로 호출합니다.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, message: ChatMessage) -> ChatMessage:
        """메시지를 생성합니다."""
        return await self._session.run_sync(ChatMessageRepositoryCore.create, message)

    async def find_by_id(self, message_id: Id) -> ChatMessage | None:
        """ID로 메시지를 조회합니다."""
        return await self._session.run_sync(ChatMessageRepositoryCore.find_by_id, message_id)

    async def find_by_room_id_paginated(
        self,
        room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """룸별 메시지를 cursor 기반 페이지네이션으로 조회합니다."""
        return await self._session.run_sync(
            ChatMessageRepositoryCore.find_by_room_id_paginated,
            room_id,
            cursor,
            limit,
        )


class SqlAlchemyChatMessageSyncRepository(ChatMessageSyncRepository):
    """SqlAlchemy 기반 채팅 메시지 리포지토리 (동기).

    Celery 백그라운드 태스크에서 사용됩니다.
    Core 메서드를 직접 호출합니다.
    """

    def __init__(self, session: Session):
        self._session = session

    def find_expired_messages(self, before_datetime: datetime) -> list[ChatMessage]:
        """만료 시간이 지난 메시지를 조회합니다."""
        return ChatMessageRepositoryCore.find_expired_messages(self._session, before_datetime)

    def delete_messages(self, message_ids: list[Id]) -> int:
        """메시지를 soft delete 처리합니다."""
        return ChatMessageRepositoryCore.delete_messages(self._session, message_ids)
