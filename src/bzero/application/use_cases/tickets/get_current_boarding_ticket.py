"""현재 탑승 중인 티켓 조회 유스케이스.

사용자가 현재 탑승 중인(BOARDING 상태) 티켓을 조회하는 비즈니스 로직을 담당합니다.
"""

from bzero.application.results import TicketResult
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.services import TicketService, UserService
from bzero.domain.value_objects import AuthProvider, TicketStatus


class GetCurrentBoardingTicketUseCase:
    """현재 탑승 중인 티켓 조회 유스케이스.

    사용자가 현재 비행선에 탑승 중인 티켓(BOARDING 상태)을 조회합니다.
    한 사용자는 동시에 하나의 비행선만 탑승할 수 있으므로,
    BOARDING 상태인 티켓이 최대 1개만 존재합니다.

    사용 시점:
        - 비행 중 화면에서 현재 탑승 정보 표시
        - 도착 예정 시간, 목적지 도시 정보 확인
    """

    def __init__(
        self,
        user_service: UserService,
        ticket_service: TicketService,
    ):
        self._user_service = user_service
        self._ticket_service = ticket_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> TicketResult:
        """현재 탑승 중인 티켓 조회를 실행합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID

        Returns:
            현재 탑승 중인 티켓 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundTicketError: 탑승 중인 티켓이 없는 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. BOARDING 상태인 티켓 조회 (최대 1개)
        tickets, _ = await self._ticket_service.get_all_tickets_by_user_id_and_status(
            user_id=user.user_id, status=TicketStatus.BOARDING, limit=1
        )

        # 3. 탑승 중인 티켓이 없으면 예외 발생
        if not tickets:
            raise NotFoundTicketError

        return TicketResult.create_from(tickets[0])
