"""pytest 공통 fixtures."""

# ruff: noqa: E402, I001
# 테스트 시작 시 .env.test 로드 (다른 모듈 import 전에 실행해야 함)
from dotenv import load_dotenv

load_dotenv(".env.test", override=True)

import time
from collections.abc import AsyncIterator
from typing import Any

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.database import get_async_db_session
from bzero.core.settings import Settings
from bzero.infrastructure.db.base import Base
from bzero.main import create_app

# 모든 모델을 import하여 Base.metadata.create_all()이 모든 테이블을 생성하도록 함
from bzero.infrastructure.db.airship_model import AirshipModel  # noqa: F401
from bzero.infrastructure.db.city_model import CityModel  # noqa: F401
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel  # noqa: F401
from bzero.infrastructure.db.ticket_model import TicketModel  # noqa: F401
from bzero.infrastructure.db.user_identity_model import UserIdentityModel  # noqa: F401
from bzero.infrastructure.db.user_model import UserModel  # noqa: F401


async def ensure_test_database_exists(settings: Settings) -> None:
    """테스트 데이터베이스가 존재하지 않으면 생성합니다."""
    db_name = settings.database.db

    # 기본 postgres DB에 연결하여 테스트 DB 존재 여부 확인
    admin_url = (
        f"postgresql+asyncpg://{settings.database.user}:"
        f"{settings.database.password.get_secret_value()}@"
        f"{settings.database.host}:{settings.database.port}/postgres"
    )

    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        async with admin_engine.connect() as conn:
            # 데이터베이스 존재 여부 확인
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name},
            )
            exists = result.scalar() is not None

            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        await admin_engine.dispose()


@pytest_asyncio.fixture
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """테스트 데이터베이스 엔진을 생성합니다."""
    settings = Settings()

    # 테스트 DB가 없으면 생성
    await ensure_test_database_exists(settings)

    engine = create_async_engine(
        settings.database.async_url,
        echo=False,
        pool_pre_ping=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """테스트용 DB 세션을 생성합니다.

    SAVEPOINT를 사용하여 UseCase의 commit()이 실제로 동작하면서도
    테스트 종료 시 전체 롤백이 가능하도록 합니다.
    """
    # 테이블 생성 (첫 테스트 시)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 연결 생성
    connection = await test_engine.connect()

    # 트랜잭션 시작
    transaction = await connection.begin()

    # 세션 생성
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

    # 세션 종료 및 롤백
    await session.close()
    await transaction.rollback()
    await connection.close()


# =============================================================================
# E2E 테스트용 fixtures
# =============================================================================


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
