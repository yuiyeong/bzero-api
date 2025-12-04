"""UserRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.user import User
from bzero.domain.errors import NotFoundUserError
from bzero.domain.value_objects import AuthProvider, Balance, Email, Id, Nickname, Profile
from bzero.infrastructure.db.user_identity_model import UserIdentityModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository


@pytest.fixture
def user_repository(test_session: AsyncSession) -> SqlAlchemyUserRepository:
    """UserRepository fixture를 생성합니다."""
    return SqlAlchemyUserRepository(test_session)


@pytest.fixture
def sample_user() -> User:
    """테스트용 샘플 사용자를 생성합니다."""
    return User(
        user_id=Id(),
        email=Email("test@example.com"),
        nickname=Nickname("테스트유저"),
        profile=Profile("😎"),
        current_points=Balance(1000),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deleted_at=None,
    )


class TestUserRepositoryCreate:
    """UserRepository.create() 메서드 테스트."""

    async def test_create_user(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """사용자를 생성하고 저장할 수 있어야 합니다."""
        # When: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # Then: 생성된 사용자가 반환됨
        assert created_user is not None
        assert str(created_user.user_id.value) == str(sample_user.user_id.value)
        assert created_user.email == sample_user.email
        assert created_user.nickname == sample_user.nickname
        assert created_user.profile == sample_user.profile
        assert created_user.current_points == sample_user.current_points

    async def test_create_user_persists_to_database(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """생성된 사용자가 데이터베이스에 저장되어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 생성된 사용자를 ID로 조회
        found_user = await user_repository.find_by_user_id(created_user.user_id)

        # Then: 동일한 사용자가 조회됨
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email == created_user.email


class TestUserRepositoryFindByUserId:
    """UserRepository.find_by_user_id() 메서드 테스트."""

    async def test_find_by_user_id_success(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """존재하는 사용자를 ID로 조회할 수 있어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 사용자 ID로 조회
        found_user = await user_repository.find_by_user_id(created_user.user_id)

        # Then: 사용자가 조회됨
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email == created_user.email

    async def test_find_by_user_id_not_found(
        self,
        user_repository: SqlAlchemyUserRepository,
    ):
        """존재하지 않는 사용자 ID로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID
        nonexistent_id = Id()

        # When: 존재하지 않는 ID로 조회
        found_user = await user_repository.find_by_user_id(nonexistent_id)

        # Then: None이 반환됨
        assert found_user is None

    async def test_find_by_user_id_ignores_soft_deleted(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 사용자는 조회되지 않아야 합니다."""
        # Given: 사용자를 생성하고 소프트 삭제
        created_user = await user_repository.create(sample_user)

        # 직접 DB에서 소프트 삭제
        user_model = await test_session.get(UserModel, created_user.user_id.value)
        user_model.soft_delete()
        await test_session.flush()

        # When: 삭제된 사용자를 ID로 조회
        found_user = await user_repository.find_by_user_id(created_user.user_id)

        # Then: None이 반환됨
        assert found_user is None


class TestUserRepositoryFindByEmail:
    """UserRepository.find_by_email() 메서드 테스트."""

    async def test_find_by_email_success(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """존재하는 사용자를 이메일로 조회할 수 있어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 이메일로 조회
        found_user = await user_repository.find_by_email(created_user.email)

        # Then: 사용자가 조회됨
        assert found_user is not None
        assert found_user.email == created_user.email
        assert found_user.user_id == created_user.user_id

    async def test_find_by_email_not_found(
        self,
        user_repository: SqlAlchemyUserRepository,
    ):
        """존재하지 않는 이메일로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 이메일
        nonexistent_email = Email("nonexistent@example.com")

        # When: 존재하지 않는 이메일로 조회
        found_user = await user_repository.find_by_email(nonexistent_email)

        # Then: None이 반환됨
        assert found_user is None

    async def test_find_by_email_ignores_soft_deleted(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 사용자는 이메일로 조회되지 않아야 합니다."""
        # Given: 사용자를 생성하고 소프트 삭제
        created_user = await user_repository.create(sample_user)

        # 직접 DB에서 소프트 삭제
        user_model = await test_session.get(UserModel, created_user.user_id.value)
        user_model.soft_delete()
        await test_session.flush()

        # When: 삭제된 사용자를 이메일로 조회
        found_user = await user_repository.find_by_email(created_user.email)

        # Then: None이 반환됨
        assert found_user is None


class TestUserRepositoryFindByNickname:
    """UserRepository.find_by_nickname() 메서드 테스트."""

    async def test_find_by_nickname_success(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """존재하는 사용자를 닉네임으로 조회할 수 있어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 닉네임으로 조회
        found_user = await user_repository.find_by_nickname(created_user.nickname)

        # Then: 사용자가 조회됨
        assert found_user is not None
        assert found_user.nickname == created_user.nickname
        assert found_user.user_id == created_user.user_id

    async def test_find_by_nickname_not_found(
        self,
        user_repository: SqlAlchemyUserRepository,
    ):
        """존재하지 않는 닉네임으로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 닉네임
        nonexistent_nickname = Nickname("존재하지않는닉네임")

        # When: 존재하지 않는 닉네임으로 조회
        found_user = await user_repository.find_by_nickname(nonexistent_nickname)

        # Then: None이 반환됨
        assert found_user is None

    async def test_find_by_nickname_ignores_soft_deleted(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 사용자는 닉네임으로 조회되지 않아야 합니다."""
        # Given: 사용자를 생성하고 소프트 삭제
        created_user = await user_repository.create(sample_user)

        # 직접 DB에서 소프트 삭제
        user_model = await test_session.get(UserModel, created_user.user_id.value)
        user_model.soft_delete()
        await test_session.flush()

        # When: 삭제된 사용자를 닉네임으로 조회
        found_user = await user_repository.find_by_nickname(created_user.nickname)

        # Then: None이 반환됨
        assert found_user is None


class TestUserRepositoryUpdate:
    """UserRepository.update() 메서드 테스트."""

    async def test_update_user_points_success(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """사용자의 포인트를 성공적으로 업데이트할 수 있어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)
        assert created_user.current_points.value == 1000

        # When: 포인트를 2000으로 변경
        created_user.current_points = Balance(2000)
        updated_user = await user_repository.update(created_user)

        # Then: 포인트가 업데이트됨
        assert updated_user.current_points.value == 2000
        assert updated_user.user_id == created_user.user_id

    async def test_update_user_nickname_and_profile(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """사용자의 닉네임과 프로필을 업데이트할 수 있어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 닉네임과 프로필 변경
        created_user.nickname = Nickname("새닉네임")
        created_user.profile = Profile("😊")
        updated_user = await user_repository.update(created_user)

        # Then: 닉네임과 프로필이 업데이트됨
        assert updated_user.nickname.value == "새닉네임"
        assert updated_user.profile.value == "😊"
        assert updated_user.user_id == created_user.user_id

    async def test_update_user_multiple_fields(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """여러 필드를 동시에 업데이트할 수 있어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 여러 필드를 동시에 변경
        created_user.nickname = Nickname("변경닉네임")
        created_user.profile = Profile("🌟")
        created_user.current_points = Balance(5000)
        updated_user = await user_repository.update(created_user)

        # Then: 모든 필드가 업데이트됨
        assert updated_user.nickname.value == "변경닉네임"
        assert updated_user.profile.value == "🌟"
        assert updated_user.current_points.value == 5000

    async def test_update_user_not_found(
        self,
        user_repository: SqlAlchemyUserRepository,
    ):
        """존재하지 않는 사용자를 업데이트하면 NotFoundUserError가 발생해야 합니다."""
        # Given: 존재하지 않는 사용자 엔티티
        nonexistent_user = User(
            user_id=Id(),
            email=Email("ghost@example.com"),
            nickname=Nickname("유령"),
            profile=Profile("🤔"),
            current_points=Balance(0),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
        )

        # When & Then: 업데이트 시도 시 NotFoundUserError 발생
        with pytest.raises(NotFoundUserError):
            await user_repository.update(nonexistent_user)

    async def test_update_soft_deleted_user_raises_error(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 사용자를 업데이트하면 NotFoundUserError가 발생해야 합니다."""
        # Given: 사용자를 생성하고 소프트 삭제
        created_user = await user_repository.create(sample_user)

        # 직접 DB에서 소프트 삭제
        user_model = await test_session.get(UserModel, created_user.user_id.value)
        user_model.soft_delete()
        await test_session.flush()

        # When & Then: 삭제된 사용자 업데이트 시도 시 NotFoundUserError 발생
        created_user.current_points = Balance(9999)
        with pytest.raises(NotFoundUserError):
            await user_repository.update(created_user)

    async def test_update_user_persists_to_database(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
    ):
        """업데이트된 사용자 정보가 데이터베이스에 반영되어야 합니다."""
        # Given: 사용자를 생성
        created_user = await user_repository.create(sample_user)

        # When: 사용자 정보를 업데이트
        created_user.current_points = Balance(7777)
        await user_repository.update(created_user)

        # Then: DB에서 조회 시 업데이트된 값이 조회됨
        found_user = await user_repository.find_by_user_id(created_user.user_id)
        assert found_user is not None
        assert found_user.current_points.value == 7777


class TestUserRepositoryFindByProviderAndProviderUserId:
    """UserRepository.find_by_provider_and_provider_user_id() 메서드 테스트."""

    async def test_find_by_provider_and_provider_user_id_success(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """provider와 provider_user_id로 사용자를 조회할 수 있어야 합니다."""
        # Given: 사용자를 생성하고 UserIdentity 연결
        created_user = await user_repository.create(sample_user)

        user_identity = UserIdentityModel(
            identity_id=Id().value,
            user_id=created_user.user_id.value,
            provider=AuthProvider.GOOGLE.value,
            provider_user_id="google_user_123",
        )
        test_session.add(user_identity)
        await test_session.flush()

        # When: provider와 provider_user_id로 조회
        found_user = await user_repository.find_by_provider_and_provider_user_id(
            provider=AuthProvider.GOOGLE,
            provider_user_id="google_user_123",
        )

        # Then: 사용자가 조회됨
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email == created_user.email

    async def test_find_by_provider_and_provider_user_id_not_found(
        self,
        user_repository: SqlAlchemyUserRepository,
    ):
        """존재하지 않는 provider_user_id로 조회하면 None을 반환해야 합니다."""
        # When: 존재하지 않는 provider_user_id로 조회
        found_user = await user_repository.find_by_provider_and_provider_user_id(
            provider=AuthProvider.GOOGLE,
            provider_user_id="nonexistent_user_id",
        )

        # Then: None이 반환됨
        assert found_user is None

    async def test_find_by_provider_and_provider_user_id_different_provider(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """다른 provider로 조회하면 None을 반환해야 합니다."""
        # Given: Google provider로 UserIdentity 생성
        created_user = await user_repository.create(sample_user)

        user_identity = UserIdentityModel(
            identity_id=Id().value,
            user_id=created_user.user_id.value,
            provider=AuthProvider.GOOGLE.value,
            provider_user_id="google_user_123",
        )
        test_session.add(user_identity)
        await test_session.flush()

        # When: Apple provider로 조회
        found_user = await user_repository.find_by_provider_and_provider_user_id(
            provider=AuthProvider.APPLE,
            provider_user_id="google_user_123",
        )

        # Then: None이 반환됨
        assert found_user is None

    async def test_find_by_provider_and_provider_user_id_ignores_soft_deleted_user(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 사용자는 조회되지 않아야 합니다."""
        # Given: 사용자를 생성하고 UserIdentity 연결 후 사용자 소프트 삭제
        created_user = await user_repository.create(sample_user)

        user_identity = UserIdentityModel(
            identity_id=Id().value,
            user_id=created_user.user_id.value,
            provider=AuthProvider.GOOGLE.value,
            provider_user_id="google_user_456",
        )
        test_session.add(user_identity)
        await test_session.flush()

        # 사용자 소프트 삭제
        user_model = await test_session.get(UserModel, created_user.user_id.value)
        user_model.soft_delete()
        await test_session.flush()

        # When: provider와 provider_user_id로 조회
        found_user = await user_repository.find_by_provider_and_provider_user_id(
            provider=AuthProvider.GOOGLE,
            provider_user_id="google_user_456",
        )

        # Then: None이 반환됨
        assert found_user is None

    async def test_find_by_provider_and_provider_user_id_ignores_soft_deleted_identity(
        self,
        user_repository: SqlAlchemyUserRepository,
        sample_user: User,
        test_session: AsyncSession,
    ):
        """소프트 삭제된 UserIdentity는 조회되지 않아야 합니다."""
        # Given: 사용자를 생성하고 UserIdentity 연결 후 Identity 소프트 삭제
        created_user = await user_repository.create(sample_user)

        user_identity = UserIdentityModel(
            identity_id=Id().value,
            user_id=created_user.user_id.value,
            provider=AuthProvider.KAKAO.value,
            provider_user_id="kakao_user_789",
        )
        test_session.add(user_identity)
        await test_session.flush()

        # UserIdentity 소프트 삭제
        user_identity.soft_delete()
        await test_session.flush()

        # When: provider와 provider_user_id로 조회
        found_user = await user_repository.find_by_provider_and_provider_user_id(
            provider=AuthProvider.KAKAO,
            provider_user_id="kakao_user_789",
        )

        # Then: None이 반환됨
        assert found_user is None
