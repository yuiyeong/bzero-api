"""티켓 상세 조회 유스케이스.

특정 티켓의 상세 정보를 조회하는 비즈니스 로직을 담당합니다.
"""

from bzero.application.results import TicketResult
from bzero.domain.services import TicketService, UserService
from bzero.domain.value_objects import AuthProvider, Id


class GetTicketDetailUseCase:
    """티켓 상세 조회 유스케이스.

    사용자가 자신의 티켓 상세 정보를 조회합니다.
    티켓 소유권 검증이 포함되어 있어 다른 사용자의 티켓은 조회할 수 없습니다.
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
        ticket_id: str,
    ) -> TicketResult:
        """티켓 상세 조회를 실행합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            ticket_id: 조회할 티켓 ID (hex 문자열)

        Returns:
            티켓 상세 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundTicketError: 티켓을 찾을 수 없는 경우
            ForbiddenTicketError: 다른 사용자의 티켓을 조회하려는 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 티켓 조회 (소유권 검증 포함)
        ticket = await self._ticket_service.get_ticket_by_id(Id.from_hex(ticket_id), user.user_id)

        return TicketResult.create_from(ticket)
