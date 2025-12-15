from abc import ABC, abstractmethod
from datetime import datetime

from bzero.domain.entities.room_stay import RoomStay
from bzero.domain.value_objects import Id


class RoomStayRepository(ABC):
    """체류 리포지토리 인터페이스 (비동기)."""

    @abstractmethod
    async def create(self, room_stay: RoomStay) -> RoomStay:
        """체류 기록을 생성합니다.

        Args:
            room_stay: 생성할 체류 엔티티

        Returns:
            생성된 체류 엔티티
        """

    @abstractmethod
    async def find_by_room_stay_id(self, room_stay_id: Id) -> RoomStay | None:
        """체류 ID로 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            체류 엔티티 또는 None
        """

    @abstractmethod
    async def find_checked_in_by_user_id(self, user_id: Id) -> RoomStay | None:
        """사용자의 현재 활성(CHECKED_IN) 체류를 조회합니다.

        한 사용자는 동시에 하나의 활성 체류만 가질 수 있습니다.

        Args:
            user_id: 사용자 ID

        Returns:
            활성 체류 엔티티 또는 None
        """

    @abstractmethod
    async def find_all_checked_in_by_room_id(self, room_id: Id) -> list[RoomStay]:
        """방에서 현재 체류 중인 모든 기록을 조회합니다.

        Args:
            room_id: 방 ID

        Returns:
            해당 방의 활성 체류 목록
        """

    @abstractmethod
    async def find_all_by_ticket_id(self, ticket_id: Id) -> list[RoomStay]:
        """티켓 ID로 모든 체류 기록을 조회합니다.

        Args:
            ticket_id: 티켓 ID

        Returns:
            해당 티켓의 체류 목록
        """

    @abstractmethod
    async def find_all_due_for_check_out(self, before: datetime) -> list[RoomStay]:
        """예정 체크아웃 시간이 지난 모든 체류를 조회합니다.

        Args:
            before: 기준 시각 (이 시각 이전에 체크아웃 예정인 체류)

        Returns:
            체크아웃 대상 체류 목록
        """

    @abstractmethod
    async def update(self, room_stay: RoomStay) -> RoomStay:
        """체류 정보를 업데이트합니다.

        Args:
            room_stay: 업데이트할 체류 엔티티

        Returns:
            업데이트된 체류 엔티티
        """


class RoomStaySyncRepository(ABC):
    """체류 리포지토리 인터페이스 (동기).

    Celery 백그라운드 태스크에서 사용됩니다.
    """

    @abstractmethod
    def create(self, room_stay: RoomStay) -> RoomStay:
        """체류 기록을 생성합니다.

        Args:
            room_stay: 생성할 체류 엔티티

        Returns:
            생성된 체류 엔티티
        """

    @abstractmethod
    def find_by_room_stay_id(self, room_stay_id: Id) -> RoomStay | None:
        """체류 ID로 조회합니다.

        Args:
            room_stay_id: 체류 ID

        Returns:
            체류 엔티티 또는 None
        """

    @abstractmethod
    def find_checked_in_by_user_id(self, user_id: Id) -> RoomStay | None:
        """사용자의 현재 활성(CHECKED_IN) 체류를 조회합니다.

        한 사용자는 동시에 하나의 활성 체류만 가질 수 있습니다.

        Args:
            user_id: 사용자 ID

        Returns:
            활성 체류 엔티티 또는 None
        """

    @abstractmethod
    def find_all_checked_in_by_room_id(self, room_id: Id) -> list[RoomStay]:
        """방에서 현재 체류 중인 모든 기록을 조회합니다.

        Args:
            room_id: 방 ID

        Returns:
            해당 방의 활성 체류 목록
        """

    @abstractmethod
    def find_all_by_ticket_id(self, ticket_id: Id) -> list[RoomStay]:
        """티켓 ID로 모든 체류 기록을 조회합니다.

        Args:
            ticket_id: 티켓 ID

        Returns:
            해당 티켓의 체류 목록
        """

    @abstractmethod
    def find_all_due_for_check_out(self, before: datetime) -> list[RoomStay]:
        """예정 체크아웃 시간이 지난 모든 체류를 조회합니다.

        Args:
            before: 기준 시각 (이 시각 이전에 체크아웃 예정인 체류)

        Returns:
            체크아웃 대상 체류 목록
        """

    @abstractmethod
    def update(self, room_stay: RoomStay) -> RoomStay:
        """체류 정보를 업데이트합니다.

        Args:
            room_stay: 업데이트할 체류 엔티티

        Returns:
            업데이트된 체류 엔티티
        """
