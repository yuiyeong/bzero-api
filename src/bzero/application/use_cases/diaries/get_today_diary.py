from bzero.application.results.diary_result import DiaryResult
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.ticket import TicketService
from bzero.domain.value_objects import Id, TicketStatus


class GetTodayDiaryUseCase:
    """오늘 일기 조회 UseCase

    - 현재 탑승 중인 티켓 기준으로 "오늘" 일기 계산 (없으면 자정 기준)
    """

    def __init__(self, diary_service: DiaryService, ticket_service: TicketService):
        self._diary_service = diary_service
        self._ticket_service = ticket_service

    async def execute(self, user_id: str) -> DiaryResult | None:
        """오늘 일기를 조회합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            DiaryResult 또는 None (일기가 없으면 None)
        """
        # 1. 현재 탑승 중인 티켓 조회
        tickets, _ = await self._ticket_service.get_all_tickets_by_user_id_and_status(
            user_id=Id(user_id),
            status=TicketStatus.BOARDING,
            limit=1,
        )
        current_boarding_ticket = tickets[0] if tickets else None

        # 2. 오늘 일기 날짜 계산 (티켓 기준 또는 자정 기준)
        today = self._diary_service.calculate_diary_date(current_boarding_ticket)

        # 3. 일기 조회
        diary = await self._diary_service.get_diary_by_user_and_date(
            user_id=Id(user_id),
            diary_date=today,
        )
        return DiaryResult.create_from(diary) if diary else None
