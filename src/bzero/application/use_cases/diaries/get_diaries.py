from bzero.application.results.common import PaginatedResult
from bzero.application.results.diary_result import DiaryResult
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider


class GetDiariesUseCase:
    """일기 목록 조회 UseCase"""

    def __init__(self, user_service: UserService, diary_service: DiaryService):
        self._user_service = user_service
        self._diary_service = diary_service

    async def execute(self, provider: str, provider_user_id: str, offset: int = 0, limit: int = 20) -> PaginatedResult[DiaryResult]:
        """사용자의 일기 목록을 조회합니다.

        Args:
            provider: 인증 제공자
            provider_user_id: 제공자의 user_id
            offset: offset
            limit: limit

        Returns:
            PaginatedResult[DiaryResult]
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        diaries, total = await self._diary_service.get_diaries_by_user(
            user_id=user.user_id,
            offset=offset,
            limit=limit,
        )
        return PaginatedResult(
            items=[DiaryResult.create_from(diary) for diary in diaries],
            total=total,
            offset=offset,
            limit=limit,
        )
