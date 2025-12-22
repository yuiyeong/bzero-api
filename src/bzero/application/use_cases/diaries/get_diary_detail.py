from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import ForbiddenDiaryAccessError
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.user import AuthProvider


class GetDiaryDetailUseCase:
    """일기 상세 조회 유스케이스.

    특정 일기의 상세 정보를 조회합니다.
    본인이 작성한 일기만 조회할 수 있습니다.
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
        diary_id: str,
    ) -> DiaryResult:
        """일기 상세 정보를 조회합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            diary_id: 조회할 일기 ID (hex 문자열)

        Returns:
            일기 상세 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundDiaryError: 일기를 찾을 수 없는 경우
            ForbiddenDiaryAccessError: 본인의 일기가 아닌 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 일기 조회
        diary = await self._diary_service.get_diary_by_id(Id.from_hex(diary_id))

        # 3. 권한 검증 (본인 일기인지 확인)
        if diary.user_id != user.user_id:
            raise ForbiddenDiaryAccessError

        return DiaryResult.create_from(diary)
