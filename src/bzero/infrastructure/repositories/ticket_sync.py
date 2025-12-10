"""티켓 리포지토리 구현체 (동기).

SQLAlchemy Session을 사용하는 티켓 리포지토리 구현입니다.
Celery 워커와 같은 동기 환경에서 사용됩니다.
"""

from sqlalchemy.orm import Session

from bzero.domain.entities import Ticket
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.repositories.ticket_sync import TicketSyncRepository
from bzero.domain.value_objects import Id
from bzero.infrastructure.repositories.ticket_base import TicketRepositoryBase


class SqlAlchemyTicketSyncRepository(TicketRepositoryBase, TicketSyncRepository):
    """SQLAlchemy 기반 티켓 리포지토리 (동기).

    TicketRepositoryBase에서 쿼리 생성 및 변환 로직을 상속받고,
    동기 Session을 사용하여 DB 작업을 수행합니다.
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
        stmt = self._query_find_by_id(ticket_id)
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

    def update(self, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            업데이트된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """
        stmt = self._query_update(ticket)
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise NotFoundTicketError
        return self.to_entity(model)
