"""DirectMessage 리포지토리 인터페이스 (비동기).

도메인 계층에서 정의하는 1:1 메시지 저장소의 추상 인터페이스입니다.
"""

from abc import ABC, abstractmethod

from bzero.domain.entities.direct_message import DirectMessage
from bzero.domain.value_objects import Id


class DirectMessageRepository(ABC):
    """DirectMessage 리포지토리 인터페이스 (비동기).

    1:1 메시지 엔티티의 영속성을 담당하는 추상 클래스입니다.
    모든 메서드는 async로 정의되어 비동기 I/O를 지원합니다.
    """

    @abstractmethod
    async def create(self, message: DirectMessage) -> DirectMessage:
        """메시지를 생성합니다.

        Args:
            message: 생성할 메시지 엔티티

        Returns:
            생성된 메시지 (DB에서 반환된 값 포함)
        """

    @abstractmethod
    async def find_by_id(self, dm_id: Id) -> DirectMessage | None:
        """ID로 메시지를 조회합니다.

        Args:
            dm_id: 조회할 메시지 ID

        Returns:
            조회된 메시지 또는 None
        """

    @abstractmethod
    async def find_by_dm_room_paginated(
        self,
        dm_room_id: Id,
        cursor: Id | None = None,
        limit: int = 50,
    ) -> list[DirectMessage]:
        """대화방별 메시지 히스토리를 cursor 기반 페이지네이션으로 조회합니다.

        created_at ASC, dm_id ASC 순으로 정렬됩니다 (오래된 메시지부터).
        cursor가 None이면 처음부터 조회합니다.

        Args:
            dm_room_id: 대화방 ID
            cursor: 이전 페이지의 마지막 dm_id (None이면 첫 페이지)
            limit: 최대 조회 개수 (기본 50개)

        Returns:
            메시지 목록 (오래된 순)
        """

    @abstractmethod
    async def mark_as_read_by_dm_room_and_user(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """대화방의 사용자가 수신한 메시지를 읽음 처리합니다.

        to_user_id == user_id인 메시지들의 is_read를 True로 설정합니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 읽음 처리할 사용자 ID

        Returns:
            읽음 처리된 메시지 개수
        """

    @abstractmethod
    async def count_unread_by_dm_room_and_user(
        self,
        dm_room_id: Id,
        user_id: Id,
    ) -> int:
        """대화방의 읽지 않은 메시지 개수를 조회합니다.

        to_user_id == user_id이고 is_read == False인 메시지 개수입니다.

        Args:
            dm_room_id: 대화방 ID
            user_id: 수신자 ID

        Returns:
            읽지 않은 메시지 개수
        """

    @abstractmethod
    async def find_latest_by_dm_room(self, dm_room_id: Id) -> DirectMessage | None:
        """대화방의 가장 최근 메시지를 조회합니다.

        대화방 목록에서 마지막 메시지를 표시할 때 사용합니다.

        Args:
            dm_room_id: 대화방 ID

        Returns:
            최근 메시지 또는 None
        """
