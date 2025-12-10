"""티켓 리포지토리 인터페이스 (동기).

Celery 워커와 같은 동기 환경에서 사용되는 티켓 저장소의 추상 인터페이스입니다.
비동기 TicketRepository와 동일한 로직을 동기 방식으로 제공합니다.
실제 구현은 Infrastructure 계층의 SqlAlchemyTicketSyncRepository에서 제공합니다.
"""

from abc import ABC, abstractmethod

from bzero.domain.entities.ticket import Ticket
from bzero.domain.value_objects import Id


class TicketSyncRepository(ABC):
    """티켓 리포지토리 인터페이스 (동기).

    Celery 백그라운드 태스크에서 사용되는 동기 리포지토리입니다.
    비동기 환경에서는 TicketRepository를 사용하세요.
    """

    @abstractmethod
    def find_by_id(self, ticket_id: Id) -> Ticket | None:
        """ID로 티켓을 조회합니다.

        Args:
            ticket_id: 조회할 티켓 ID

        Returns:
            조회된 티켓 또는 None
        """

    @abstractmethod
    def update(self, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        현재는 status 필드만 업데이트됩니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            업데이트된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """
