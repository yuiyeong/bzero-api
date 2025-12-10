"""사용자 티켓 목록 조회 유스케이스.

사용자가 보유한 모든 티켓을 페이지네이션하여 조회하는 비즈니스 로직을 담당합니다.
"""

from bzero.application.results import PaginatedResult, TicketResult
from bzero.domain.services import TicketService, UserService
from bzero.domain.value_objects import AuthProvider


class GetTicketsByUserUseCase:
    """사용자 티켓 목록 조회 유스케이스.

    사용자가 보유한 모든 티켓을 페이지네이션하여 조회합니다.
    티켓 상태(BOARDING, COMPLETED, CANCELLED)와 관계없이 모든 티켓이 조회됩니다.
    """

    def __init__(
        self,
        user_service: UserService,
        ticket_service: TicketService,
    ):
        self._user_service = user_service
        self._ticket_service = ticket_service

    async def execute(
        self, provider: str, provider_user_id: str, offset: int, limit: int
    ) -> PaginatedResult[TicketResult]:
        """사용자 티켓 목록 조회를 실행합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            offset: 페이지네이션 오프셋 (건너뛸 항목 수)
            limit: 한 페이지에 조회할 최대 항목 수

        Returns:
            페이지네이션된 티켓 목록 (items, total, offset, limit 포함)

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 사용자의 모든 티켓 조회 (페이지네이션)
        tickets, total = await self._ticket_service.get_all_tickets_by_user_id(
            user_id=user.user_id, offset=offset, limit=limit
        )

        # 3. 결과 변환
        items = [TicketResult.create_from(ticket) for ticket in tickets]

        return PaginatedResult(items=items, total=total, offset=offset, limit=limit)
