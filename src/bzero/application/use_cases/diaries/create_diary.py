from datetime import date

from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import ErrorCode
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryContent, DiaryMood
from bzero.domain.value_objects.point_transaction import TransactionReason, TransactionReference


class CreateDiaryUseCase:
    """일기 작성 UseCase

    일기를 작성하고, 하루 1회 포인트(50P)를 지급합니다.
    """

    def __init__(
        self,
        diary_service: DiaryService,
        point_transaction_service: PointTransactionService,
    ):
        self._diary_service = diary_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        user_id: Id,
        title: str | None,
        content: str,
        mood: str,
        diary_date: date,
        city_id: Id | None = None,
    ) -> DiaryResult:
        """일기를 작성합니다.

        Args:
            user_id: 사용자 ID
            title: 일기 제목 (optional)
            content: 일기 내용 (최대 500자)
            mood: 기분 이모지 (😊😐😢😠🥰)
            diary_date: 일기 날짜
            city_id: 도시 ID (optional)

        Returns:
            생성된 DiaryResult

        Raises:
            InvalidDiaryContentError: 내용이 500자 초과
            InvalidDiaryMoodError: 허용되지 않은 기분 이모지
            DuplicatedError: 이미 해당 날짜에 일기 작성
        """
        # 중복 작성 방지 (같은 날짜에 이미 일기가 있는지 확인)
        existing_diary = await self._diary_service.get_diary_by_user_and_date(user_id, diary_date)
        if existing_diary:
            from bzero.domain.errors import BeZeroError

            raise BeZeroError(ErrorCode.DUPLICATED_REWARD)  # 409 Conflict

        # 값 객체 생성 (검증 포함)
        diary_content = DiaryContent(content)
        diary_mood = DiaryMood(mood)

        # 일기 생성
        diary = await self._diary_service.create_diary(
            user_id=user_id,
            title=title,
            content=diary_content,
            mood=diary_mood,
            diary_date=diary_date,
            city_id=city_id,
        )

        # 포인트 지급 (하루 1회 50P)
        DIARY_REWARD_POINTS = 50
        await self._point_transaction_service.earn_points(
            user_id=user_id,
            amount=DIARY_REWARD_POINTS,
            reason=TransactionReason.DIARY,
            description=f"{diary_date.isoformat()} 일기 작성",
            reference_type=TransactionReference.DIARIES,
            reference_id=diary.diary_id,
        )

        # 포인트 획득 처리
        diary.mark_points_earned()
        await self._diary_service._diary_repository.save(diary)

        return DiaryResult.create_from(diary)
