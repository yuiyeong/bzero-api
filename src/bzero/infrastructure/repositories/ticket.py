"""티켓 리포지토리 구현체 (비동기).

SQLAlchemy AsyncSession을 사용하는 티켓 리포지토리 구현입니다.
FastAPI와 같은 비동기 환경에서 사용됩니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities import Ticket
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.repositories.ticket import TicketRepository
from bzero.domain.value_objects import Id, TicketStatus
from bzero.infrastructure.repositories.ticket_base import TicketRepositoryBase


class SqlAlchemyTicketRepository(TicketRepositoryBase, TicketRepository):
    """SQLAlchemy 기반 티켓 리포지토리 (비동기).

    TicketRepositoryBase에서 쿼리 생성 및 변환 로직을 상속받고,
    AsyncSession을 사용하여 비동기 DB 작업을 수행합니다.

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
        model = self.to_model(ticket)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return self.to_entity(model)

    async def update(self, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            업데이트된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """
        stmt = self._query_update(ticket)

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise NotFoundTicketError
        return self.to_entity(model)

    async def find_by_id(self, ticket_id: Id) -> Ticket | None:
        """ID로 티켓을 조회합니다.

        Args:
            ticket_id: 조회할 티켓 ID

        Returns:
            조회된 티켓 또는 None
        """
        stmt = self._query_find_by_id(ticket_id)

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

    async def find_all_by_user_id(self, user_id: Id, offset: int = 0, limit: int = 100) -> list[Ticket]:
        """사용자의 모든 티켓을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            티켓 목록 (출발일시 내림차순 정렬)
        """
        stmt = self._query_find_all_by_user_id(user_id, offset, limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self.to_entity(model) for model in models]

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
        stmt = self._query_find_all_by_user_id_and_status(user_id, status, offset, limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self.to_entity(model) for model in models]

    async def count_by(self, user_id: Id | None = None, status: TicketStatus | None = None) -> int:
        """조건에 맞는 티켓 개수를 조회합니다.

        Args:
            user_id: 사용자 ID (선택)
            status: 티켓 상태 (선택)

        Returns:
            조건에 맞는 티켓 개수
        """
        stmt = self._query_count_by(user_id, status)
        result = await self._session.execute(stmt)
        return result.scalar_one()
