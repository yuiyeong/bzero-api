from bzero.application.results.diary_result import DiaryResult
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.ticket import TicketService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, TicketStatus


class GetTodayDiaryUseCase:
    """오늘 일기 조회 UseCase

    - 가장 최근 완료된 티켓 기준으로 "오늘" 일기 계산 (없으면 자정 기준)
    """

    def __init__(self, user_service: UserService, diary_service: DiaryService, ticket_service: TicketService):
        self._user_service = user_service
        self._diary_service = diary_service
        self._ticket_service = ticket_service

    async def execute(self, provider: str, provider_user_id: str) -> DiaryResult | None:
        """오늘 일기를 조회합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 제공자의 user_id

        Returns:
            DiaryResult 또는 None (일기가 없으면 None)
        """
        # 0. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 1. 가장 최근 완료된 티켓 조회
        tickets, _ = await self._ticket_service.get_all_tickets_by_user_id_and_status(
            user_id=user.user_id,
            status=TicketStatus.COMPLETED,
            limit=1,
        )
        latest_completed_ticket = tickets[0] if tickets else None

        # 2. 오늘 일기 날짜 계산 (티켓 기준 또는 자정 기준)
        today = self._diary_service.calculate_diary_date(latest_completed_ticket)

        # 3. 일기 조회
        diary = await self._diary_service.get_diary_by_user_and_date(
            user_id=user.user_id,
            diary_date=today,
        )
        return DiaryResult.create_from(diary) if diary else None
