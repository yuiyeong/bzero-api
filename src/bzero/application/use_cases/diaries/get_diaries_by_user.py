from bzero.application.results.common import PaginatedResult
from bzero.application.results.diary_result import DiaryResult
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects.user import AuthProvider


class GetDiariesByUserUseCase:
    """사용자 일기 목록 조회 유스케이스.

    사용자가 작성한 일기 목록을 페이지네이션하여 조회합니다.
    """

    def __init__(
        self,
        user_service: UserService,
        diary_service: DiaryService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            user_service: 사용자 도메인 서비스
            diary_service: 일기 도메인 서비스
        """
        self._user_service = user_service
        self._diary_service = diary_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResult[DiaryResult]:
        """사용자의 일기 목록을 조회합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            limit: 조회할 최대 개수 (기본값: 20)
            offset: 건너뛸 개수 (기본값: 0)

        Returns:
            페이지네이션된 일기 목록

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 일기 목록 및 총 개수 조회
        diaries, total = await self._diary_service.get_diaries_by_user_id(
            user_id=user.user_id,
            limit=limit,
            offset=offset,
        )

        # 3. 결과 변환
        items = [DiaryResult.create_from(diary) for diary in diaries]

        return PaginatedResult(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
