from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import DuplicatedDiaryError
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.ticket import TicketService
from bzero.domain.value_objects import DiaryContent, DiaryMood, Id, TicketStatus, TransactionReason, TransactionReference


class CreateDiaryUseCase:
    """일기 작성 UseCase

    - 현재 탑승 중인 티켓 기준으로 일기 날짜 계산 (없으면 자정 기준)
    - 중복 작성 방지 (같은 날짜에 이미 일기가 있으면 실패)
    - 일기 저장 후 포인트 지급 (50P, 하루 1회)
    """

    DIARY_POINTS = 50

    def __init__(
        self,
        session: AsyncSession,
        diary_service: DiaryService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
    ):
        self._session = session
        self._diary_service = diary_service
        self._ticket_service = ticket_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        user_id: str,
        content: str,
        mood: str,
        title: str | None = None,
        city_id: str | None = None,
    ) -> DiaryResult:
        """일기를 작성합니다.

        Args:
            user_id: 사용자 ID
            content: 일기 내용
            mood: 기분 이모지
            title: 제목 (선택)
            city_id: 관련 도시 ID (선택)

        Returns:
            DiaryResult

        Raises:
            DuplicatedDiaryError: 같은 날짜에 이미 일기가 존재할 때
        """
        try:
            # 1. 현재 탑승 중인 티켓 조회
            tickets, _ = await self._ticket_service.get_all_tickets_by_user_id_and_status(
                user_id=Id(user_id),
                status=TicketStatus.BOARDING,
                limit=1,
            )
            current_boarding_ticket = tickets[0] if tickets else None

            # 2. 일기 날짜 계산 (티켓 기준 또는 자정 기준)
            diary_date = self._diary_service.calculate_diary_date(current_boarding_ticket)

            # 3. 일기 생성
            diary = await self._diary_service.create_diary(
                user_id=Id(user_id),
                content=DiaryContent(content),
                mood=DiaryMood(mood),
                diary_date=diary_date,
                title=title,
                city_id=Id(city_id) if city_id else None,
            )

            # 4. 포인트 지급 (50P, 하루 1회)
            await self._point_transaction_service.earn_points(
                user_id=Id(user_id),
                amount=self.DIARY_POINTS,
                reason=TransactionReason.DIARY,
                reference_type=TransactionReference.DIARIES,
                reference_id=diary.diary_id,
                description=f"일기 작성 보상 ({diary_date})",
            )

            # 5. 포인트 지급 완료 표시
            diary = await self._diary_service.mark_points_earned(diary)

            await self._session.commit()
            return DiaryResult.create_from(diary)

        except Exception:
            await self._session.rollback()
            raise
