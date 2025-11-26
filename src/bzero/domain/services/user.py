from datetime import datetime

from bzero.domain.entities.user import User
from bzero.domain.entities.user_identity import UserIdentity
from bzero.domain.errors import DuplicatedUserError, NotFoundUserError
from bzero.domain.repositories.user import UserRepository
from bzero.domain.repositories.user_identity import UserIdentityRepository
from bzero.domain.value_objects import AuthProvider, Balance, Email, Id


class UserService:
    """사용자 도메인 서비스

    User와 UserIdentity 생성/조회를 담당합니다.
    주의: 모든 메서드는 데이터베이스 트랜잭션 내에서 호출되어야 합니다.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        user_identity_repository: UserIdentityRepository,
    ):
        self._user_repository = user_repository
        self._user_identity_repository = user_identity_repository

    async def create_user_with_identity(
        self,
        provider: AuthProvider,
        provider_user_id: str,
        email: Email | None = None,
    ) -> tuple[User, UserIdentity]:
        """User와 UserIdentity를 함께 생성합니다.

        Args:
            provider: 인증 제공자 (예: AuthProvider.EMAIL)
            provider_user_id: 제공자의 user_id (예: Supabase user_id)
            email: 사용자 이메일 (선택사항, 소셜 로그인 시 제공되지 않을 수 있음)

        Returns:
            생성된 User와 UserIdentity 튜플

        Raises:
            DuplicatedUserError: 이미 존재하는 사용자일 때
        """
        # 1. UserIdentity 중복 확인
        existing_identity = await self._user_identity_repository.find_by_provider_user_id(
            provider=provider, provider_user_id=provider_user_id
        )
        if existing_identity:
            raise DuplicatedUserError

        # 2. User 생성 (온보딩 전이므로 nickname, profile은 None)
        user = User(
            user_id=Id(),
            email=email,
            nickname=None,
            profile=None,
            current_points=Balance(0),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        created_user = await self._user_repository.create(user)

        # 3. UserIdentity 생성
        identity = UserIdentity(
            identity_id=Id(),
            user_id=created_user.user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        created_identity = await self._user_identity_repository.create(identity)

        return created_user, created_identity

    async def find_user_by_provider_and_provider_user_id(
        self,
        provider: AuthProvider,
        provider_user_id: str,
        raise_exception: bool = True,
    ) -> User:
        """인증 제공자 정보로 사용자를 조회합니다.

        Args:
            provider: 인증 제공자 (예: AuthProvider.GOOGLE)
            provider_user_id: 제공자의 user_id
            raise_exception: NotFoundUserError 를 발생시킬지

        Returns:
            조회된 User

        Raises:
            NotFoundUserError: 사용자가 존재하지 않을 때
        """
        user = await self._user_repository.find_by_provider_and_provider_user_id(
            provider=provider,
            provider_user_id=provider_user_id,
        )
        if raise_exception and user is None:
            raise NotFoundUserError
        return user

    async def update_user(self, user: User) -> User:
        """사용자 정보를 업데이트합니다.

        Args:
            user: 업데이트할 User 엔티티

        Returns:
            업데이트된 User

        Raises:
            NotFoundUserError: 사용자가 존재하지 않을 때
        """
        return await self._user_repository.update(user)
