"""채팅 메시지 리포지토리 인터페이스 (비동기/동기).

도메인 계층에서 정의하는 채팅 메시지 저장소의 추상 인터페이스입니다.
- ChatMessageRepository: FastAPI와 같은 비동기 환경용
- ChatMessageSyncRepository: Celery 백그라운드 태스크용 (동기)
"""

from abc import ABC, abstractmethod
from datetime import datetime

from bzero.domain.entities.chat_message import ChatMessage
from bzero.domain.value_objects import Id


class ChatMessageRepository(ABC):
    """채팅 메시지 리포지토리 인터페이스 (비동기).

    채팅 메시지 엔티티의 영속성을 담당하는 추상 클래스입니다.
    모든 메서드는 async로 정의되어 비동기 I/O를 지원합니다.
    """

    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        """채팅 메시지를 생성합니다.

        Args:
            message: 생성할 메시지 엔티티

        Returns:
            생성된 메시지 (DB에서 반환된 값 포함)
        """

    @abstractmethod
    async def find_by_id(self, message_id: Id) -> ChatMessage | None:
        """ID로 메시지를 조회합니다.

        Args:
            message_id: 조회할 메시지 ID

        Returns:
            조회된 메시지 또는 None
        """

    @abstractmethod
    async def find_by_room_id_paginated(
        self,
        room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """룸별 메시지 히스토리를 cursor 기반 페이지네이션으로 조회합니다.

        created_at DESC, message_id DESC 순으로 정렬됩니다.
        cursor가 None이면 최신 메시지부터 조회합니다.

        Args:
            room_id: 룸 ID
            cursor: 이전 페이지의 마지막 message_id (None이면 첫 페이지)
            limit: 최대 조회 개수 (기본 50개)

        Returns:
            메시지 목록 (최신순)
        """


class ChatMessageSyncRepository(ABC):
    """채팅 메시지 리포지토리 인터페이스 (동기).

    Celery 백그라운드 태스크에서 사용되는 동기 리포지토리입니다.
    비동기 환경에서는 ChatMessageRepository를 사용하세요.
    """

    @abstractmethod
    def find_expired_messages(self, before_datetime: datetime) -> list[ChatMessage]:
        """만료 시간이 지난 메시지를 조회합니다.

        Args:
            before_datetime: 기준 시간 (expires_at < before_datetime)

        Returns:
            만료된 메시지 목록
        """

    @abstractmethod
    def delete_messages(self, message_ids: list[Id]) -> int:
        """메시지를 soft delete 처리합니다.

        deleted_at을 현재 시간으로 설정합니다.

        Args:
            message_ids: 삭제할 메시지 ID 목록

        Returns:
            삭제된 메시지 개수
        """
