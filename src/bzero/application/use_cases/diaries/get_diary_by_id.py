from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import ForbiddenError
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import Id


class GetDiaryByIdUseCase:
    """일기 상세 조회 UseCase"""

    def __init__(self, diary_service: DiaryService):
        self._diary_service = diary_service

    async def execute(self, diary_id: Id, current_user_id: Id) -> DiaryResult:
        """일기를 조회합니다. (본인만 조회 가능)

        Args:
            diary_id: 조회할 일기 ID
            current_user_id: 현재 사용자 ID

        Returns:
            조회된 DiaryResult

        Raises:
            DiaryNotFoundError: 일기가 존재하지 않을 때
            ForbiddenError: 다른 사용자의 일기에 접근 시도할 때
        """
        diary = await self._diary_service.get_diary_by_id(diary_id)

        # 소유권 검증 (본인만 조회 가능)
        if str(diary.user_id.value) != str(current_user_id.value):
            raise ForbiddenError

        return DiaryResult.create_from(diary)
