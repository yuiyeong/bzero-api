"""DirectMessageRoom 리포지토리 인터페이스 (비동기).

도메인 계층에서 정의하는 1:1 대화방 저장소의 추상 인터페이스입니다.
"""

from abc import ABC, abstractmethod

from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.value_objects import DMStatus, Id


class DirectMessageRoomRepository(ABC):
    """DirectMessageRoom 리포지토리 인터페이스 (비동기).

    1:1 대화방 엔티티의 영속성을 담당하는 추상 클래스입니다.
    모든 메서드는 async로 정의되어 비동기 I/O를 지원합니다.
    """

    @abstractmethod
    async def create(self, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방을 생성합니다.

        Args:
            dm_room: 생성할 대화방 엔티티

        Returns:
            생성된 대화방 (DB에서 반환된 값 포함)
        """

    @abstractmethod
    async def find_by_id(self, dm_room_id: Id) -> DirectMessageRoom | None:
        """ID로 대화방을 조회합니다.

        Args:
            dm_room_id: 조회할 대화방 ID

        Returns:
            조회된 대화방 또는 None
        """

    @abstractmethod
    async def find_by_room_and_users(
        self,
        room_id: Id,
        user1_id: Id,
        user2_id: Id,
    ) -> DirectMessageRoom | None:
        """룸과 사용자로 대화방을 조회합니다.

        중복 신청 방지를 위해 사용합니다.
        양방향 조회: (user1, user2) 또는 (user2, user1) 모두 확인합니다.

        Args:
            room_id: 룸 ID
            user1_id: 사용자 1 ID
            user2_id: 사용자 2 ID

        Returns:
            조회된 대화방 또는 None
        """

    @abstractmethod
    async def find_by_user_and_statuses(
        self,
        user_id: Id,
        statuses: list[DMStatus],
        limit: int = 50,
        offset: int = 0,
    ) -> list[DirectMessageRoom]:
        """사용자와 상태로 대화방 목록을 조회합니다.

        사용자가 참여 중인 (user1 또는 user2인) 대화방을 조회합니다.
        updated_at DESC 순으로 정렬됩니다.

        Args:
            user_id: 사용자 ID
            statuses: 조회할 상태 목록 (예: [PENDING, ACTIVE])
            limit: 최대 조회 개수 (기본 50개)
            offset: 오프셋 (기본 0)

        Returns:
            대화방 목록 (최근 순)
        """

    @abstractmethod
    async def update(self, dm_room: DirectMessageRoom) -> DirectMessageRoom:
        """대화방 정보를 업데이트합니다.

        Args:
            dm_room: 업데이트할 대화방 엔티티

        Returns:
            업데이트된 대화방
        """

    @abstractmethod
    async def soft_delete_by_room_id(self, room_id: Id) -> int:
        """룸 ID로 대화방들을 soft delete 처리합니다.

        체크아웃 시 해당 룸의 모든 대화방을 삭제할 때 사용합니다.

        Args:
            room_id: 룸 ID

        Returns:
            삭제된 대화방 개수
        """

    @abstractmethod
    async def count_by_user_and_statuses(
        self,
        user_id: Id,
        statuses: list[DMStatus],
    ) -> int:
        """사용자와 상태별 대화방 개수를 조회합니다.

        Args:
            user_id: 사용자 ID
            statuses: 조회할 상태 목록

        Returns:
            대화방 개수
        """
