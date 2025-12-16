from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bzero.domain.entities import Ticket
from bzero.domain.repositories.ticket import TicketRepository, TicketSyncRepository
from bzero.domain.value_objects import Id, TicketStatus
from bzero.infrastructure.repositories.ticket_core import TicketRepositoryCore


class SqlAlchemyTicketRepository(TicketRepository):
    """SQLAlchemy 기반 티켓 리포지토리 (비동기).

    TicketRepositoryCore의 동기 메서드를 run_sync로 호출합니다.
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

    async def create(self, ticket: Ticket) -> Ticket:
        """티켓을 생성합니다.

        Args:
            ticket: 생성할 티켓 엔티티

        Returns:
            생성된 티켓 (DB에서 생성된 타임스탬프 포함)
        """
        return await self._session.run_sync(TicketRepositoryCore.create, ticket)

    async def update(self, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            업데이트된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """
        return await self._session.run_sync(TicketRepositoryCore.update, ticket)

    async def find_by_id(self, ticket_id: Id) -> Ticket | None:
        """ID로 티켓을 조회합니다.

        Args:
            ticket_id: 조회할 티켓 ID

        Returns:
            조회된 티켓 또는 None
        """
        return await self._session.run_sync(TicketRepositoryCore.find_by_id, ticket_id)

    async def find_all_by_user_id(self, user_id: Id, offset: int = 0, limit: int = 100) -> list[Ticket]:
        """사용자의 모든 티켓을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            티켓 목록 (출발일시 내림차순 정렬)
        """
        return await self._session.run_sync(TicketRepositoryCore.find_all_by_user_id, user_id, offset, limit)

    async def find_all_by_user_id_and_status(
        self, user_id: Id, status: TicketStatus, offset: int = 0, limit: int = 100
    ) -> list[Ticket]:
        """사용자의 특정 상태 티켓을 조회합니다.

        Args:
            user_id: 사용자 ID
            status: 필터링할 티켓 상태
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            티켓 목록 (출발일시 내림차순 정렬)
        """
        return await self._session.run_sync(
            TicketRepositoryCore.find_all_by_user_id_and_status,
            user_id,
            status,
            offset,
            limit,
        )

    async def count_by(self, user_id: Id | None = None, status: TicketStatus | None = None) -> int:
        """조건에 맞는 티켓 개수를 조회합니다.

        Args:
            user_id: 사용자 ID (선택)
            status: 티켓 상태 (선택)

        Returns:
            조건에 맞는 티켓 개수
        """
        return await self._session.run_sync(TicketRepositoryCore.count_by, user_id, status)


class SqlAlchemyTicketSyncRepository(TicketSyncRepository):
    """SQLAlchemy 기반 티켓 리포지토리 (동기).

    TicketRepositoryCore의 동기 메서드를 직접 호출합니다.
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

    def find_by_id(self, ticket_id: Id) -> Ticket | None:
        """ID로 티켓을 조회합니다.

        Args:
            ticket_id: 조회할 티켓 ID

        Returns:
            조회된 티켓 또는 None
        """
        return TicketRepositoryCore.find_by_id(self._session, ticket_id)

    def update(self, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            업데이트된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """
        return TicketRepositoryCore.update(self._session, ticket)
