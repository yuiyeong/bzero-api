from bzero.application.results.diary_result import DiaryResult
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import Id


class GetDiariesUseCase:
    """일기 목록 조회 UseCase"""

    def __init__(self, diary_service: DiaryService):
        self._diary_service = diary_service

    async def execute(
        self,
        user_id: Id,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[DiaryResult], int]:
        """사용자의 일기 목록을 조회합니다.

        Args:
            user_id: 사용자 ID
            offset: 조회 시작 위치 (기본값: 0)
            limit: 조회할 최대 개수 (기본값: 20, 최대: 100)

        Returns:
            (일기 목록, 전체 개수) 튜플
        """
        # limit 최대값 제한
        limit = min(limit, 100)

        diaries, total = await self._diary_service.get_diaries_by_user(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )

        diary_results = [DiaryResult.create_from(diary) for diary in diaries]
        return diary_results, total
