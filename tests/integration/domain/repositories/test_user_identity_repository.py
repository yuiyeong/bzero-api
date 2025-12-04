"""UserIdentityRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.settings import get_settings
from bzero.domain.entities.user import User
from bzero.domain.entities.user_identity import UserIdentity
from bzero.domain.value_objects import AuthProvider, Balance, Email, Id, Nickname, Profile
from bzero.infrastructure.db.user_identity_model import UserIdentityModel
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository
from bzero.infrastructure.repositories.user_identity import SqlAlchemyUserIdentityRepository


@pytest.fixture
def user_repository(test_session: AsyncSession) -> SqlAlchemyUserRepository:
    """UserRepository fixture를 생성합니다."""
    return SqlAlchemyUserRepository(test_session)


@pytest.fixture
def user_identity_repository(test_session: AsyncSession) -> SqlAlchemyUserIdentityRepository:
    """UserIdentityRepository fixture를 생성합니다."""
    return SqlAlchemyUserIdentityRepository(test_session)


@pytest.fixture
async def test_user(user_repository: SqlAlchemyUserRepository) -> User:
    """테스트용 사용자를 생성합니다."""
    user = User(
        user_id=Id(),
        email=Email("test@example.com"),
        nickname=Nickname("테스트유저"),
        profile=Profile("😎"),
        current_points=Balance(1000),
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
        deleted_at=None,
    )
    return await user_repository.create(user)


@pytest.fixture
def sample_user_identity(test_user: User) -> UserIdentity:
    """테스트용 샘플 사용자 인증 정보를 생성합니다."""
    return UserIdentity(
        identity_id=Id(),
        user_id=test_user.user_id,
        provider=AuthProvider.GOOGLE,
        provider_user_id="google_12345",
        created_at=datetime.now(get_settings().timezone),
        updated_at=datetime.now(get_settings().timezone),
        deleted_at=None,
    )


class TestUserIdentityRepositoryCreate:
    """UserIdentityRepository.create() 메서드 테스트."""

    async def test_create_user_identity(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        sample_user_identity: UserIdentity,
    ):
        """사용자 인증 정보를 생성하고 저장할 수 있어야 합니다."""
        # When: 사용자 인증 정보를 생성
        created_identity = await user_identity_repository.create(sample_user_identity)

        # Then: 생성된 인증 정보가 반환됨
        assert created_identity is not None
        assert str(created_identity.identity_id.value) == str(sample_user_identity.identity_id.value)
        assert created_identity.user_id == sample_user_identity.user_id
        assert created_identity.provider == sample_user_identity.provider
        assert created_identity.provider_user_id == sample_user_identity.provider_user_id

    async def test_create_user_identity_persists_to_database(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        sample_user_identity: UserIdentity,
    ):
        """생성된 사용자 인증 정보가 데이터베이스에 저장되어야 합니다."""
        # Given: 사용자 인증 정보를 생성
        created_identity = await user_identity_repository.create(sample_user_identity)

        # When: 생성된 인증 정보를 provider와 provider_user_id로 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=created_identity.provider,
            provider_user_id=created_identity.provider_user_id,
        )

        # Then: 동일한 인증 정보가 조회됨
        assert found_identity is not None
        assert found_identity.identity_id == created_identity.identity_id
        assert found_identity.user_id == created_identity.user_id
        assert found_identity.provider == created_identity.provider
        assert found_identity.provider_user_id == created_identity.provider_user_id

    async def test_create_multiple_identities_for_same_user(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        test_user: User,
    ):
        """같은 사용자에게 여러 인증 정보를 추가할 수 있어야 합니다."""
        # Given: Google 인증 정보 생성
        google_identity = UserIdentity(
            identity_id=Id(),
            user_id=test_user.user_id,
            provider=AuthProvider.GOOGLE,
            provider_user_id="google_12345",
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        await user_identity_repository.create(google_identity)

        # When: Kakao 인증 정보 생성
        kakao_identity = UserIdentity(
            identity_id=Id(),
            user_id=test_user.user_id,
            provider=AuthProvider.KAKAO,
            provider_user_id="kakao_67890",
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        await user_identity_repository.create(kakao_identity)

        # Then: 두 인증 정보 모두 조회 가능
        found_google = await user_identity_repository.find_by_provider_user_id(AuthProvider.GOOGLE, "google_12345")
        found_kakao = await user_identity_repository.find_by_provider_user_id(AuthProvider.KAKAO, "kakao_67890")

        assert found_google is not None
        assert found_kakao is not None
        assert found_google.user_id == found_kakao.user_id == test_user.user_id
        assert found_google.provider == AuthProvider.GOOGLE
        assert found_kakao.provider == AuthProvider.KAKAO


class TestUserIdentityRepositoryFindByProviderUserId:
    """UserIdentityRepository.find_by_provider_user_id() 메서드 테스트."""

    async def test_find_by_provider_user_id_success(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        sample_user_identity: UserIdentity,
    ):
        """provider와 provider_user_id로 사용자 인증 정보를 조회할 수 있어야 합니다."""
        # Given: 사용자 인증 정보를 생성
        created_identity = await user_identity_repository.create(sample_user_identity)

        # When: provider와 provider_user_id로 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=created_identity.provider,
            provider_user_id=created_identity.provider_user_id,
        )

        # Then: 인증 정보가 조회됨
        assert found_identity is not None
        assert found_identity.identity_id == created_identity.identity_id
        assert found_identity.user_id == created_identity.user_id
        assert found_identity.provider == created_identity.provider
        assert found_identity.provider_user_id == created_identity.provider_user_id

    async def test_find_by_provider_user_id_not_found_wrong_provider(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        sample_user_identity: UserIdentity,
    ):
        """다른 provider로 조회하면 None을 반환해야 합니다."""
        # Given: Google 인증 정보를 생성
        await user_identity_repository.create(sample_user_identity)

        # When: Kakao provider로 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=AuthProvider.KAKAO,
            provider_user_id=sample_user_identity.provider_user_id,
        )

        # Then: None이 반환됨
        assert found_identity is None

    async def test_find_by_provider_user_id_not_found_wrong_user_id(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        sample_user_identity: UserIdentity,
    ):
        """다른 provider_user_id로 조회하면 None을 반환해야 합니다."""
        # Given: 사용자 인증 정보를 생성
        await user_identity_repository.create(sample_user_identity)

        # When: 다른 provider_user_id로 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=sample_user_identity.provider,
            provider_user_id="wrong_user_id",
        )

        # Then: None이 반환됨
        assert found_identity is None

    async def test_find_by_provider_user_id_not_found_nonexistent(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
    ):
        """존재하지 않는 인증 정보를 조회하면 None을 반환해야 합니다."""
        # Given: 아무런 인증 정보가 없는 상태

        # When: 존재하지 않는 provider와 provider_user_id로 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=AuthProvider.GOOGLE,
            provider_user_id="nonexistent_user_id",
        )

        # Then: None이 반환됨
        assert found_identity is None

    async def test_find_by_provider_user_id_ignores_soft_deleted(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        sample_user_identity: UserIdentity,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 인증 정보는 조회되지 않아야 합니다."""
        # Given: 사용자 인증 정보를 생성하고 소프트 삭제
        created_identity = await user_identity_repository.create(sample_user_identity)

        # 직접 DB에서 소프트 삭제
        identity_model = await test_session.get(UserIdentityModel, created_identity.identity_id.value)
        identity_model.soft_delete()
        await test_session.flush()

        # When: 삭제된 인증 정보를 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=created_identity.provider,
            provider_user_id=created_identity.provider_user_id,
        )

        # Then: None이 반환됨
        assert found_identity is None

    async def test_find_by_provider_user_id_returns_correct_identity_among_multiple(
        self,
        user_identity_repository: SqlAlchemyUserIdentityRepository,
        user_repository: SqlAlchemyUserRepository,
    ):
        """여러 인증 정보 중 정확한 인증 정보를 반환해야 합니다."""
        # Given: 두 명의 사용자와 각각의 Google 인증 정보 생성
        user1 = User(
            user_id=Id(),
            email=Email("user1@example.com"),
            nickname=Nickname("유저1"),
            profile=Profile("😎"),
            current_points=Balance(1000),
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        user2 = User(
            user_id=Id(),
            email=Email("user2@example.com"),
            nickname=Nickname("유저2"),
            profile=Profile("🤩"),
            current_points=Balance(1000),
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        user1 = await user_repository.create(user1)
        user2 = await user_repository.create(user2)

        identity1 = UserIdentity(
            identity_id=Id(),
            user_id=user1.user_id,
            provider=AuthProvider.GOOGLE,
            provider_user_id="google_user1",
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        identity2 = UserIdentity(
            identity_id=Id(),
            user_id=user2.user_id,
            provider=AuthProvider.GOOGLE,
            provider_user_id="google_user2",
            created_at=datetime.now(get_settings().timezone),
            updated_at=datetime.now(get_settings().timezone),
            deleted_at=None,
        )
        await user_identity_repository.create(identity1)
        await user_identity_repository.create(identity2)

        # When: user1의 인증 정보 조회
        found_identity = await user_identity_repository.find_by_provider_user_id(
            provider=AuthProvider.GOOGLE,
            provider_user_id="google_user1",
        )

        # Then: user1의 인증 정보만 반환됨
        assert found_identity is not None
        assert found_identity.user_id == user1.user_id
        assert found_identity.provider_user_id == "google_user1"
