from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import ForbiddenDiaryError
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Id


class GetDiaryByIdUseCase:
    """일기 상세 조회 UseCase"""

    def __init__(self, user_service: UserService, diary_service: DiaryService):
        self._user_service = user_service
        self._diary_service = diary_service

    async def execute(self, diary_id: str, provider: str, provider_user_id: str) -> DiaryResult:
        """일기를 ID로 조회합니다 (본인 확인 포함).

        Args:
            diary_id: 일기 ID
            provider: 인증 제공자
            provider_user_id: 제공자의 user_id

        Returns:
            DiaryResult

        Raises:
            NotFoundDiaryError: 일기를 찾을 수 없을 때
            ForbiddenDiaryError: 일기 소유자가 아닐 때
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        diary = await self._diary_service.get_diary_by_id(Id.from_hex(diary_id))

        # 소유권 검증
        if diary.user_id != user.user_id:
            raise ForbiddenDiaryError

        return DiaryResult.create_from(diary)
