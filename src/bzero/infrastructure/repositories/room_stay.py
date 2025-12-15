from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bzero.domain.entities.room_stay import RoomStay
from bzero.domain.repositories.room_stay import RoomStayRepository, RoomStaySyncRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.room_stay_core import RoomStayRepositoryCore


class SqlAlchemyRoomStayRepository(RoomStayRepository):
    """SQLAlchemy 기반 RoomStay Repository (비동기).

    RoomStayRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
    이 패턴을 통해 로직 중복 없이 비동기 인터페이스를 제공합니다.

    Attributes:
        _session: SQLAlchemy AsyncSession 인스턴스
    """

    def __init__(self, session: AsyncSession):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self._session = session

    async def create(self, room_stay: RoomStay) -> RoomStay:
        """룸 스테이를 생성합니다.

        Args:
            room_stay: 생성할 룸 스테이 엔티티

        Returns:
            생성된 룸 스테이 (DB에서 생성된 타임스탬프 포함)
        """
        return await self._session.run_sync(RoomStayRepositoryCore.create, room_stay)

    async def find_by_room_stay_id(self, room_stay_id: Id) -> RoomStay | None:
        """ID로 룸 스테이를 조회합니다.

        Args:
            room_stay_id: 조회할 룸 스테이 ID

        Returns:
            조회된 룸 스테이 또는 None
        """
        return await self._session.run_sync(RoomStayRepositoryCore.find_by_room_stay_id, room_stay_id)

    async def find_checked_in_by_user_id(self, user_id: Id) -> RoomStay | None:
        """사용자의 체크인된 룸 스테이를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            체크인된 룸 스테이 또는 None
        """
        return await self._session.run_sync(RoomStayRepositoryCore.find_checked_in_by_user_id, user_id)

    async def find_all_checked_in_by_room_id(self, room_id: Id) -> list[RoomStay]:
        """룸의 체크인된 모든 룸 스테이를 조회합니다.

        Args:
            room_id: 룸 ID

        Returns:
            체크인된 룸 스테이 목록
        """
        return await self._session.run_sync(RoomStayRepositoryCore.find_all_checked_in_by_room_id, room_id)

    async def find_all_by_ticket_id(self, ticket_id: Id) -> list[RoomStay]:
        """티켓 ID로 모든 룸 스테이를 조회합니다.

        Args:
            ticket_id: 티켓 ID

        Returns:
            룸 스테이 목록
        """
        return await self._session.run_sync(RoomStayRepositoryCore.find_all_by_ticket_id, ticket_id)

    async def find_all_due_for_check_out(self, before: datetime) -> list[RoomStay]:
        """체크아웃 예정 시간이 지난 룸 스테이를 조회합니다.

        Args:
            before: 이 시간 이전에 체크아웃 예정인 룸 스테이를 조회

        Returns:
            체크아웃 예정 시간이 지난 룸 스테이 목록
        """
        return await self._session.run_sync(RoomStayRepositoryCore.find_all_due_for_check_out, before)

    async def update(self, room_stay: RoomStay) -> RoomStay:
        """룸 스테이를 업데이트합니다.

        Args:
            room_stay: 업데이트할 룸 스테이 엔티티

        Returns:
            업데이트된 룸 스테이

        Raises:
            NotFoundRoomStayError: 룸 스테이를 찾을 수 없는 경우
        """
        return await self._session.run_sync(RoomStayRepositoryCore.update, room_stay)


class SqlAlchemyRoomStaySyncRepository(RoomStaySyncRepository):
    """SQLAlchemy 기반 RoomStayRepository (동기).

    RoomStayRepositoryCore의 동기 메서드를 직접 호출합니다.
    주로 Celery 백그라운드 태스크에서 사용됩니다.

    Attributes:
        _session: SQLAlchemy Session 인스턴스
    """

    def __init__(self, session: Session):
        """리포지토리를 초기화합니다.

        Args:
            session: SQLAlchemy Session 인스턴스
        """
        self._session = session

    def create(self, room_stay: RoomStay) -> RoomStay:
        """룸 스테이를 생성합니다."""
        return RoomStayRepositoryCore.create(self._session, room_stay)

    def find_by_room_stay_id(self, room_stay_id: Id) -> RoomStay | None:
        """ID로 룸 스테이를 조회합니다."""
        return RoomStayRepositoryCore.find_by_room_stay_id(self._session, room_stay_id)

    def find_checked_in_by_user_id(self, user_id: Id) -> RoomStay | None:
        """사용자의 체크인된 룸 스테이를 조회합니다."""
        return RoomStayRepositoryCore.find_checked_in_by_user_id(self._session, user_id)

    def find_all_checked_in_by_room_id(self, room_id: Id) -> list[RoomStay]:
        """룸의 체크인된 모든 룸 스테이를 조회합니다."""
        return RoomStayRepositoryCore.find_all_checked_in_by_room_id(self._session, room_id)

    def find_all_by_ticket_id(self, ticket_id: Id) -> list[RoomStay]:
        """티켓 ID로 모든 룸 스테이를 조회합니다."""
        return RoomStayRepositoryCore.find_all_by_ticket_id(self._session, ticket_id)

    def find_all_due_for_check_out(self, before: datetime) -> list[RoomStay]:
        """체크아웃 예정 시간이 지난 룸 스테이를 조회합니다."""
        return RoomStayRepositoryCore.find_all_due_for_check_out(self._session, before)

    def update(self, room_stay: RoomStay) -> RoomStay:
        """룸 스테이를 업데이트합니다."""
        return RoomStayRepositoryCore.update(self._session, room_stay)
