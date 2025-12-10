"""티켓 도메인 서비스.

티켓의 구매, 취소, 조회 등 핵심 비즈니스 로직을 처리합니다.
도메인 서비스는 여러 엔티티를 조합하여 복잡한 비즈니스 규칙을 수행합니다.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bzero.domain.entities import Airship, City, Ticket, User
from bzero.domain.errors import (
    ForbiddenTicketError,
    InsufficientBalanceError,
    InvalidAirshipStatusError,
    InvalidCityStatusError,
    NotFoundTicketError,
)
from bzero.domain.repositories.ticket import TicketRepository
from bzero.domain.value_objects import Id, TicketStatus


class TicketService:
    """티켓 도메인 서비스.

    비행선 티켓의 구매, 취소, 조회 등 핵심 비즈니스 로직을 담당합니다.

    Attributes:
        _ticket_repository: 티켓 저장소 (비동기)
        _timezone: 시간대 정보 (출발/도착 시간 계산에 사용)
    """

    def __init__(self, ticket_repository: TicketRepository, timezone: ZoneInfo):
        """TicketService를 초기화합니다.

        Args:
            ticket_repository: 티켓 저장소 인터페이스
            timezone: 사용할 시간대 (예: ZoneInfo("Asia/Seoul"))
        """
        self._ticket_repository = ticket_repository
        self._timezone = timezone

    async def purchase_ticket(self, user: User, city: City, airship: Airship) -> Ticket:
        """비행선 티켓을 구매합니다.

        비용 계산: 도시 기본 비용 * 비행선 비용 배율
        시간 계산: 도시 기본 시간 * 비행선 시간 배율

        Args:
            user: 티켓을 구매하는 사용자
            city: 목적지 도시
            airship: 이용할 비행선

        Returns:
            생성된 티켓 (BOARDING 상태로 즉시 탑승)

        Raises:
            InsufficientBalanceError: 포인트가 부족한 경우
            InvalidCityStatusError: 도시가 비활성화된 경우
            InvalidAirshipStatusError: 비행선이 비활성화된 경우
        """
        total_cost = city.base_cost_points * airship.cost_factor
        total_duration = city.base_duration_hours * airship.duration_factor

        if user.current_points.less_than(total_cost):
            raise InsufficientBalanceError

        if not city.is_active:
            raise InvalidCityStatusError

        if not airship.is_active:
            raise InvalidAirshipStatusError

        departure_datetime = datetime.now(self._timezone)
        arrival_datetime = departure_datetime + timedelta(hours=total_duration)
        ticket = Ticket.create(
            user_id=user.user_id,
            city_snapshot=city.snapshot(),
            airship_snapshot=airship.snapshot(),
            cost_points=total_cost,
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            created_at=departure_datetime,
            updated_at=departure_datetime,
        )
        # 구매 즉시 탑승 상태로 변경
        ticket.consume()
        return await self._ticket_repository.create(ticket)

    async def cancel(self, user_id: Id, ticket_id: Id) -> Ticket:
        """티켓을 취소합니다.

        Args:
            user_id: 요청한 사용자 ID (소유권 확인용)
            ticket_id: 취소할 티켓 ID

        Returns:
            취소된 티켓 (CANCELLED 상태)

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
            ForbiddenTicketError: 다른 사용자의 티켓인 경우
            InvalidTicketStatusError: PURCHASED 상태가 아닌 경우
        """
        ticket = await self.get_ticket_by_id(
            ticket_id=ticket_id,
            user_id=user_id,
        )
        ticket.cancel()
        return await self._ticket_repository.update(ticket)

    async def get_ticket_by_id(self, ticket_id: Id, user_id: Id | None = None) -> Ticket:
        """티켓을 ID로 조회합니다.

        Args:
            ticket_id: 조회할 티켓 ID
            user_id: 소유권 확인용 사용자 ID (선택)

        Returns:
            조회된 티켓

        Raises:
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
            ForbiddenTicketError: user_id가 지정되었고 다른 사용자의 티켓인 경우
        """
        ticket = await self._ticket_repository.find_by_id(ticket_id)
        if ticket is None:
            raise NotFoundTicketError

        if user_id and ticket.user_id != user_id:
            raise ForbiddenTicketError

        return ticket

    async def get_all_tickets_by_user_id(
        self, user_id: Id, offset: int = 0, limit: int = 100
    ) -> tuple[list[Ticket], int]:
        """사용자의 모든 티켓을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: 페이지네이션 오프셋 (기본값: 0)
            limit: 최대 조회 개수 (기본값: 100)

        Returns:
            (티켓 목록, 전체 개수) 튜플
        """
        tickets = await self._ticket_repository.find_all_by_user_id(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )
        total = await self._ticket_repository.count_by(user_id=user_id)
        return tickets, total

    async def get_all_tickets_by_user_id_and_status(
        self, user_id: Id, status: TicketStatus, offset: int = 0, limit: int = 100
    ) -> tuple[list[Ticket], int]:
        """사용자의 특정 상태 티켓을 조회합니다.

        Args:
            user_id: 사용자 ID
            status: 필터링할 티켓 상태
            offset: 페이지네이션 오프셋 (기본값: 0)
            limit: 최대 조회 개수 (기본값: 100)

        Returns:
            (티켓 목록, 전체 개수) 튜플
        """
        tickets = await self._ticket_repository.find_all_by_user_id_and_status(
            user_id=user_id,
            status=status,
            offset=offset,
            limit=limit,
        )
        total = await self._ticket_repository.count_by(user_id=user_id, status=status)
        return tickets, total
