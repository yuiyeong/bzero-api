from bzero.application.results.user_result import UserResult
from bzero.domain.services import UserService
from bzero.domain.value_objects import AuthProvider


class GetMeUseCase:
    """
    현재 로그인한 사용자 정보 조회 UseCase

    JWT 토큰에서 추출한 provider 정보로 사용자를 조회합니다.
    """

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, provider: str, provider_user_id: str) -> UserResult:
        """
        Args:
            provider: 인증 제공자 (예: 'email', 'google')
            provider_user_id: 제공자의 user_id (JWT의 sub claim)

        Returns:
            UserResult

        Raises:
            NotFoundUserError: 사용자가 존재하지 않을 때
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        return UserResult.create_from(user)
