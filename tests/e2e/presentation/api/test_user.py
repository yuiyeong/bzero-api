"""User API e2e 테스트."""

import time
from collections.abc import AsyncIterator
from typing import Any

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.database import get_async_db_session
from bzero.core.settings import Settings
from bzero.infrastructure.db.base import Base
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel  # noqa: F401
from bzero.infrastructure.db.user_identity_model import UserIdentityModel  # noqa: F401
from bzero.infrastructure.db.user_model import UserModel  # noqa: F401
from bzero.main import create_app


def create_test_jwt(
    provider: str = "email",
    provider_user_id: str = "test-user-id-123",
    email: str = "test@example.com",
    secret: str = "test-secret",
) -> str:
    """테스트용 JWT 토큰을 생성합니다."""
    now = int(time.time())
    payload = {
        "aud": "authenticated",
        "exp": now + 3600,
        "iat": now,
        "sub": provider_user_id,
        "email": email,
        "app_metadata": {
            "provider": provider,
            "providers": [provider],
        },
        "user_metadata": {
            "email": email,
            "email_verified": True,
            "phone_verified": False,
        },
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest_asyncio.fixture
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """테스트 데이터베이스 엔진을 생성합니다."""
    settings = Settings()
    engine = create_async_engine(
        settings.database.async_url,
        echo=False,
        pool_pre_ping=True,
    )

    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """테스트용 DB 세션을 생성합니다.

    SAVEPOINT를 사용하여 UseCase의 commit()이 실제로 동작하면서도
    테스트 종료 시 전체 롤백이 가능하도록 합니다.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    session = session_maker()

    # nested transaction (SAVEPOINT) 시작
    nested = await connection.begin_nested()

    # session.commit()이 호출되면 SAVEPOINT만 커밋하고 새 SAVEPOINT 시작
    @event.listens_for(session.sync_session, "after_transaction_end")
    def restart_savepoint(db_session: Any, trans: Any) -> None:
        if trans.nested and not trans._parent.nested:
            # 외부 트랜잭션이 아닌 경우에만 새 SAVEPOINT 시작
            nonlocal nested
            nested = connection.sync_connection.begin_nested()  # type: ignore[union-attr]

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(test_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """테스트용 HTTP 클라이언트를 생성합니다."""
    app = create_app()

    # DB 세션을 테스트 세션으로 오버라이드
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield test_session

    app.dependency_overrides[get_async_db_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """인증 헤더를 반환합니다."""
    settings = Settings()
    token = create_test_jwt(secret=settings.auth.supabase_jwt_secret.get_secret_value())
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_factory() -> Any:
    """커스텀 인증 헤더를 생성하는 팩토리를 반환합니다."""
    settings = Settings()

    def _create_headers(
        provider: str = "email",
        provider_user_id: str = "test-user-id-123",
        email: str = "test@example.com",
    ) -> dict[str, str]:
        token = create_test_jwt(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            secret=settings.auth.supabase_jwt_secret.get_secret_value(),
        )
        return {"Authorization": f"Bearer {token}"}

    return _create_headers


class TestCreateUser:
    """POST /users/me 테스트."""

    async def test_create_user_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """신규 사용자를 성공적으로 생성합니다."""
        # When
        response = await client.post("/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 201

        data = response.json()["data"]
        assert data["email"] == "test@example.com"
        assert data["nickname"] is None
        assert data["profile_emoji"] is None
        assert data["current_points"] == 1000  # 초기 포인트
        assert data["is_profile_complete"] is False
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_user_duplicate_error(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """이미 존재하는 사용자를 생성하면 409 에러를 반환합니다."""
        # Given: 사용자 생성
        response = await client.post("/users/me", headers=auth_headers)
        assert response.status_code == 201

        # When: 동일한 사용자로 다시 생성 시도
        response = await client.post("/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 409

    async def test_create_user_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 401 에러를 반환합니다."""
        # When
        response = await client.post("/users/me")

        # Then
        assert response.status_code == 403  # HTTPBearer는 401이 아닌 403 반환


class TestGetMe:
    """GET /users/me 테스트."""

    async def test_get_me_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """로그인한 사용자 정보를 조회합니다."""
        # Given: 사용자 생성
        await client.post("/users/me", headers=auth_headers)

        # When
        response = await client.get("/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["email"] == "test@example.com"
        assert data["current_points"] == 1000

    async def test_get_me_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """존재하지 않는 사용자를 조회하면 404 에러를 반환합니다."""
        # When: 사용자 생성 없이 조회
        response = await client.get("/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 404

    async def test_get_me_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 403 에러를 반환합니다."""
        # When
        response = await client.get("/users/me")

        # Then
        assert response.status_code == 403


class TestUpdateUser:
    """PATCH /users/me 테스트."""

    async def test_update_user_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자 프로필을 성공적으로 업데이트합니다."""
        # Given: 사용자 생성
        await client.post("/users/me", headers=auth_headers)

        # When
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["nickname"] == "테스터"
        assert data["profile_emoji"] == "😊"
        assert data["is_profile_complete"] is True

    async def test_update_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """존재하지 않는 사용자를 업데이트하면 404 에러를 반환합니다."""
        # When
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 404

    async def test_update_user_invalid_nickname_too_short(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """닉네임이 너무 짧으면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/users/me", headers=auth_headers)

        # When
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "짧", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_invalid_nickname_special_chars(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """닉네임에 특수문자가 있으면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/users/me", headers=auth_headers)

        # When
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "테스터!", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_invalid_emoji_not_emoji(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """이모지가 아닌 문자를 입력하면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/users/me", headers=auth_headers)

        # When: 일반 문자 입력
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "A"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_invalid_emoji_multiple(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """여러 개의 이모지를 입력하면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/users/me", headers=auth_headers)

        # When: 여러 이모지 입력
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "😀😀"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 403 에러를 반환합니다."""
        # When
        response = await client.patch(
            "/users/me",
            json={"nickname": "테스터", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 403


class TestUserFlow:
    """사용자 플로우 통합 테스트."""

    async def test_full_user_flow(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """전체 사용자 플로우를 테스트합니다: 생성 -> 조회 -> 온보딩 완료."""
        # 1. 신규 사용자 등록
        response = await client.post("/users/me", headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["data"]["is_profile_complete"] is False
        assert response.json()["data"]["current_points"] == 1000

        # 2. 사용자 정보 조회
        response = await client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["nickname"] is None

        # 3. 온보딩 완료 (프로필 설정)
        response = await client.patch(
            "/users/me",
            headers=auth_headers,
            json={"nickname": "여행자", "profile_emoji": "🚀"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["is_profile_complete"] is True
        assert response.json()["data"]["nickname"] == "여행자"
        assert response.json()["data"]["profile_emoji"] == "🚀"

        # 4. 업데이트된 정보 조회
        response = await client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["nickname"] == "여행자"

    async def test_multiple_users_isolation(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
    ):
        """다른 사용자의 데이터는 서로 격리됩니다."""
        # Given: 두 명의 사용자 생성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )

        # When: 각각 사용자 생성 및 프로필 설정
        create_resp1 = await client.post("/users/me", headers=headers_user1)
        assert create_resp1.status_code == 201

        create_resp2 = await client.post("/users/me", headers=headers_user2)
        assert create_resp2.status_code == 201

        update_resp1 = await client.patch(
            "/users/me",
            headers=headers_user1,
            json={"nickname": "유저원", "profile_emoji": "😊"},
        )
        assert update_resp1.status_code == 200
        assert update_resp1.json()["data"]["nickname"] == "유저원"

        update_resp2 = await client.patch(
            "/users/me",
            headers=headers_user2,
            json={"nickname": "유저투", "profile_emoji": "🌟"},
        )
        assert update_resp2.status_code == 200
        assert update_resp2.json()["data"]["nickname"] == "유저투"

        # Then: 각 사용자는 자신의 정보만 조회
        response1 = await client.get("/users/me", headers=headers_user1)
        response2 = await client.get("/users/me", headers=headers_user2)

        assert response1.json()["data"]["nickname"] == "유저원"
        assert response1.json()["data"]["email"] == "user1@example.com"

        assert response2.json()["data"]["nickname"] == "유저투"
        assert response2.json()["data"]["email"] == "user2@example.com"
