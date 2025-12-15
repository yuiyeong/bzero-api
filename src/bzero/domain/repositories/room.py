from abc import ABC, abstractmethod

from bzero.domain.entities.room import Room
from bzero.domain.value_objects import Id


class RoomRepository(ABC):
    """방 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, room: Room) -> Room:
        """방을 생성합니다.

        Args:
            room: 생성할 방 엔티티

        Returns:
            생성된 방 엔티티
        """

    @abstractmethod
    async def find_by_room_id(self, room_id: Id) -> Room | None:
        """방 ID로 조회합니다.

        Args:
            room_id: 방 ID

        Returns:
            방 엔티티 또는 None
        """

    @abstractmethod
    async def find_available_by_guest_house_id_for_update(self, guesthouse_id: Id) -> list[Room]:
        """게스트하우스에서 배정 가능한 방 목록을 조회합니다 (FOR UPDATE).

        동시성 제어를 위해 SELECT FOR UPDATE 쿼리를 사용합니다.
        만원이 아닌(current_capacity < max_capacity) 방들을 반환합니다.

        Args:
            guesthouse_id: 게스트하우스 ID

        Returns:
            배정 가능한 방 목록
        """

    @abstractmethod
    async def update(self, room: Room) -> Room:
        """방 정보를 업데이트합니다.

        Args:
            room: 업데이트할 방 엔티티

        Returns:
            업데이트된 방 엔티티
        """


class RoomSyncRepository(ABC):
    """방 리포지토리 인터페이스 (동기).

    Celery 백그라운드 태스크에서 사용됩니다.
    """

    @abstractmethod
    def create(self, room: Room) -> Room:
        """방을 생성합니다.

        Args:
            room: 생성할 방 엔티티

        Returns:
            생성된 방 엔티티
        """

    @abstractmethod
    def find_by_room_id(self, room_id: Id) -> Room | None:
        """방 ID로 조회합니다.

        Args:
            room_id: 방 ID

        Returns:
            방 엔티티 또는 None
        """

    @abstractmethod
    def find_available_by_guest_house_id_for_update(self, guesthouse_id: Id) -> list[Room]:
        """게스트하우스에서 배정 가능한 방 목록을 조회합니다 (FOR UPDATE).

        동시성 제어를 위해 SELECT FOR UPDATE 쿼리를 사용합니다.
        만원이 아닌(current_capacity < max_capacity) 방들을 반환합니다.

        Args:
            guesthouse_id: 게스트하우스 ID

        Returns:
            배정 가능한 방 목록
        """

    @abstractmethod
    def update(self, room: Room) -> Room:
        """방 정보를 업데이트합니다.

        Args:
            room: 업데이트할 방 엔티티

        Returns:
            업데이트된 방 엔티티
        """
