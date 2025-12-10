"""UserService 단위 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from bzero.core.settings import get_settings
from bzero.domain.entities.user import User
from bzero.domain.entities.user_identity import UserIdentity
from bzero.domain.errors import DuplicatedUserError, NotFoundUserError
from bzero.domain.repositories.user import UserRepository
from bzero.domain.repositories.user_identity import UserIdentityRepository
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Balance, Email, Id, Nickname, Profile


@pytest.fixture
def mock_user_repository() -> MagicMock:
    """Mock UserRepository"""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_user_identity_repository() -> MagicMock:
    """Mock UserIdentityRepository"""
    return MagicMock(spec=UserIdentityRepository)


@pytest.fixture
def user_service(
    mock_user_repository: MagicMock,
    mock_user_identity_repository: MagicMock,
) -> UserService:
    """UserService with mocked repositories"""
    timezone = get_settings().timezone
    return UserService(mock_user_repository, mock_user_identity_repository, timezone)


class TestUserServiceCreateUserWithIdentity:
    """create_user_with_identity 메서드 테스트"""

    async def test_create_user_with_identity_success(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
        mock_user_identity_repository: MagicMock,
    ):
        """User와 UserIdentity를 성공적으로 생성한다"""
        # Given
        provider = AuthProvider.EMAIL
        provider_user_id = "supabase-user-id-123"
        email = "test@example.com"

        mock_user_identity_repository.find_by_provider_user_id = AsyncMock(return_value=None)

        created_user = User(
            user_id=Id(),
            email=Email(email),
            nickname=None,
            profile=None,
            current_points=Balance(0),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.create = AsyncMock(return_value=created_user)

        created_identity = UserIdentity(
            identity_id=Id(),
            user_id=created_user.user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_identity_repository.create = AsyncMock(return_value=created_identity)

        # When
        user, identity = await user_service.create_user_with_identity(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
        )

        # Then
        assert user.email.value == email
        assert user.current_points.value == 0
        assert user.nickname is None
        assert user.profile is None

        assert identity.provider == provider
        assert identity.provider_user_id == provider_user_id
        assert identity.user_id == user.user_id

        mock_user_identity_repository.find_by_provider_user_id.assert_called_once_with(
            provider=provider, provider_user_id=provider_user_id
        )
        mock_user_repository.create.assert_called_once()
        mock_user_identity_repository.create.assert_called_once()

    async def test_create_user_with_identity_raises_duplicated_user_error(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
        mock_user_identity_repository: MagicMock,
    ):
        """이미 존재하는 사용자면 DuplicatedUserError를 발생시킨다"""
        # Given
        provider = AuthProvider.EMAIL
        provider_user_id = "existing-user-id"
        email = "existing@example.com"

        existing_identity = UserIdentity(
            identity_id=Id(),
            user_id=Id(),
            provider=provider,
            provider_user_id=provider_user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_identity_repository.find_by_provider_user_id = AsyncMock(return_value=existing_identity)

        # When & Then
        with pytest.raises(DuplicatedUserError):
            await user_service.create_user_with_identity(
                provider=provider,
                provider_user_id=provider_user_id,
                email=email,
            )

        mock_user_identity_repository.find_by_provider_user_id.assert_called_once()
        mock_user_repository.create.assert_not_called()
        mock_user_identity_repository.create.assert_not_called()

    async def test_create_user_with_identity_creates_user_with_zero_balance(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
        mock_user_identity_repository: MagicMock,
    ):
        """생성된 User의 초기 포인트는 0이다"""
        # Given
        mock_user_identity_repository.find_by_provider_user_id = AsyncMock(return_value=None)

        captured_user = None

        async def capture_user(user: User) -> User:
            nonlocal captured_user
            captured_user = user
            return user

        mock_user_repository.create = AsyncMock(side_effect=capture_user)
        mock_user_identity_repository.create = AsyncMock(side_effect=lambda identity: identity)

        # When
        await user_service.create_user_with_identity(
            provider=AuthProvider.EMAIL,
            provider_user_id="test-id",
            email="test@example.com",
        )

        # Then
        assert captured_user is not None
        assert captured_user.current_points.value == 0


class TestUserServiceFindUserByProviderAndProviderUserId:
    """find_user_by_provider_and_provider_user_id 메서드 테스트"""

    async def test_find_user_by_provider_and_provider_user_id_success(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
    ):
        """provider와 provider_user_id로 사용자를 성공적으로 조회한다"""
        # Given
        provider = AuthProvider.GOOGLE
        provider_user_id = "google-user-123"

        expected_user = User(
            user_id=Id(),
            email=Email("test@gmail.com"),
            nickname=Nickname("테스터"),
            profile=Profile("😎"),
            current_points=Balance(1000),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.find_by_provider_and_provider_user_id = AsyncMock(return_value=expected_user)

        # When
        user = await user_service.find_user_by_provider_and_provider_user_id(
            provider=provider,
            provider_user_id=provider_user_id,
        )

        # Then
        assert user == expected_user
        mock_user_repository.find_by_provider_and_provider_user_id.assert_called_once_with(
            provider=provider.value,
            provider_user_id=provider_user_id,
        )

    async def test_find_user_by_provider_and_provider_user_id_not_found(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
    ):
        """존재하지 않는 사용자 조회 시 NotFoundUserError를 발생시킨다"""
        # Given
        provider = AuthProvider.GOOGLE
        provider_user_id = "nonexistent-user"

        mock_user_repository.find_by_provider_and_provider_user_id = AsyncMock(return_value=None)

        # When & Then
        with pytest.raises(NotFoundUserError):
            await user_service.find_user_by_provider_and_provider_user_id(
                provider=provider,
                provider_user_id=provider_user_id,
            )

        mock_user_repository.find_by_provider_and_provider_user_id.assert_called_once()


class TestUserServiceUpdateUser:
    """update_user 메서드 테스트"""

    async def test_update_user_success(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
    ):
        """사용자 정보를 성공적으로 업데이트한다"""
        # Given
        user = User(
            user_id=Id(),
            email=Email("test@example.com"),
            nickname=Nickname("기존닉네임"),
            profile=Profile("😊"),
            current_points=Balance(1000),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        updated_user = User(
            user_id=user.user_id,
            email=user.email,
            nickname=Nickname("새닉네임"),
            profile=Profile("🌟"),
            current_points=Balance(2000),
            created_at=user.created_at,
            updated_at=datetime.now(),
        )
        mock_user_repository.update = AsyncMock(return_value=updated_user)

        # When
        result = await user_service.update_user(user)

        # Then
        assert result == updated_user
        mock_user_repository.update.assert_called_once_with(user)

    async def test_update_user_not_found(
        self,
        user_service: UserService,
        mock_user_repository: MagicMock,
    ):
        """존재하지 않는 사용자 업데이트 시 NotFoundUserError를 발생시킨다"""
        # Given
        user = User(
            user_id=Id(),
            email=Email("ghost@example.com"),
            nickname=Nickname("유령"),
            profile=Profile("🤔"),
            current_points=Balance(0),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.update = AsyncMock(side_effect=NotFoundUserError)

        # When & Then
        with pytest.raises(NotFoundUserError):
            await user_service.update_user(user)

        mock_user_repository.update.assert_called_once_with(user)
