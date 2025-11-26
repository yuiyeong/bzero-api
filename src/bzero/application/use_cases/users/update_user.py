from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.user_result import UserResult
from bzero.domain.services import UserService
from bzero.domain.value_objects import AuthProvider, Nickname, Profile


class UpdateUserUseCase:
    """
    사용자 프로필 업데이트 UseCase

    온보딩 완료 시 또는 프로필 수정 시 호출됩니다.
    - 닉네임 변경
    - 프로필 이모지 변경
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
    ):
        self._session = session
        self._user_service = user_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        nickname: str,
        emoji: str,
    ) -> UserResult:
        """
        Args:
            provider: 인증 제공자 (예: 'email', 'google')
            provider_user_id: 제공자의 user_id (JWT의 sub claim)
            nickname: 새 닉네임 (2-10자)
            emoji: 새 프로필 이모지

        Returns:
            UserResult

        Raises:
            NotFoundUserError: 사용자가 존재하지 않을 때
            ValueError: 닉네임 또는 이모지 형식이 잘못되었을 때
        """
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        user.nickname = Nickname(nickname)
        user.profile = Profile(emoji)

        updated_user = await self._user_service.update_user(user)
        await self._session.commit()

        return UserResult.create_from(updated_user)
