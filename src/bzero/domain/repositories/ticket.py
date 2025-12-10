"""티켓 리포지토리 인터페이스 (비동기).

도메인 계층에서 정의하는 티켓 저장소의 추상 인터페이스입니다.
FastAPI와 같은 비동기 환경에서 사용됩니다.
실제 구현은 Infrastructure 계층의 SqlAlchemyTicketRepository에서 제공합니다.
"""

from abc import ABC, abstractmethod

from bzero.domain.entities.ticket import Ticket
from bzero.domain.value_objects import Id, TicketStatus


class TicketRepository(ABC):
    """티켓 리포지토리 인터페이스 (비동기).

    티켓 엔티티의 영속성을 담당하는 추상 클래스입니다.
    모든 메서드는 async로 정의되어 비동기 I/O를 지원합니다.
    """

    @abstractmethod
    async def create(self, ticket: Ticket) -> Ticket:
        """티켓을 생성합니다.

        Args:
        ticket: 생성할 티켓 엔티티

        Returns:
            생성된 티켓 (DB에서 반환된 값 포함)
        """

    @abstractmethod
    async def update(self, ticket: Ticket) -> Ticket:
        """티켓을 업데이트합니다.

        현재는 status 필드만 업데이트됩니다.

        Args:
            ticket: 업데이트할 티켓 엔티티

        Returns:
            업데이트된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
        """

    @abstractmethod
    async def find_by_id(self, ticket_id: Id) -> Ticket | None:
        """ID로 티켓을 조회합니다.

        Args:
            ticket_id: 조회할 티켓 ID

        Returns:
            조회된 티켓 또는 None
        """

    @abstractmethod
    async def find_all_by_user_id(
        self,
        user_id: Id,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Ticket]:
        """사용자의 모든 티켓을 조회합니다.

        출발 일시 기준 내림차순으로 정렬됩니다.

        Args:
            user_id: 사용자 ID
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            티켓 목록
        """

    @abstractmethod
    async def find_all_by_user_id_and_status(
        self,
        user_id: Id,
        status: TicketStatus,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Ticket]:
        """사용자의 특정 상태 티켓을 조회합니다.

        출발 일시 기준 내림차순으로 정렬됩니다.

        Args:
            user_id: 사용자 ID
            status: 필터링할 티켓 상태
            offset: 페이지네이션 오프셋
            limit: 최대 조회 개수

        Returns:
            티켓 목록
        """

    @abstractmethod
    async def count_by(self, user_id: Id | None = None, status: TicketStatus | None = None) -> int:
        """조건에 맞는 티켓 개수를 조회합니다.

        Args:
            user_id: 사용자 ID (선택)
            status: 티켓 상태 (선택)

        Returns:
            조건에 맞는 티켓 개수
        """
