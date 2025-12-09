from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import NotFoundDiaryError
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import Id


class GetDiaryByIdUseCase:
    """일기 상세 조회 UseCase"""

    def __init__(self, diary_service: DiaryService):
        self._diary_service = diary_service

    async def execute(self, diary_id: str, user_id: str) -> DiaryResult:
        """일기를 ID로 조회합니다 (본인 확인 포함).

        Args:
            diary_id: 일기 ID
            user_id: 사용자 ID (소유권 검증용)

        Returns:
            DiaryResult

        Raises:
            NotFoundDiaryError: 일기를 찾을 수 없거나 소유자가 아닐 때
        """
        diary = await self._diary_service.get_diary_by_id(Id(diary_id))

        # 소유권 검증
        if diary.user_id.value != user_id:
            raise NotFoundDiaryError

        return DiaryResult.create_from(diary)
