from datetime import date

from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import DiaryNotFoundError
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import Id


class GetTodayDiaryUseCase:
    """오늘 일기 조회 UseCase"""

    def __init__(self, diary_service: DiaryService):
        self._diary_service = diary_service

    async def execute(self, user_id: Id, today: date) -> DiaryResult:
        """오늘 작성한 일기를 조회합니다.

        Args:
            user_id: 사용자 ID
            today: 오늘 날짜

        Returns:
            조회된 DiaryResult

        Raises:
            DiaryNotFoundError: 오늘 일기가 없을 때
        """
        diary = await self._diary_service.get_diary_by_user_and_date(user_id, today)
        if diary is None:
            raise DiaryNotFoundError

        return DiaryResult.create_from(diary)
