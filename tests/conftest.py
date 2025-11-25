"""pytest 공통 fixtures."""

from collections.abc import AsyncIterator

import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import Settings
from bzero.infrastructure.db.base import Base

# 모든 모델을 import하여 Base.metadata.create_all()이 모든 테이블을 생성하도록 함
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel  # noqa: F401
from bzero.infrastructure.db.user_identity_model import UserIdentityModel  # noqa: F401
from bzero.infrastructure.db.user_model import UserModel  # noqa: F401


# 테스트 시작 시 .env.test 로드
load_dotenv(".env.test", override=True)


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
    """각 테스트마다 독립적인 데이터베이스 세션을 제공합니다.

    트랜잭션을 시작하고 테스트 종료 후 롤백하여 테스트 간 격리를 보장합니다.
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

    yield session

    # 세션 종료 및 롤백
    await session.close()
    await transaction.rollback()
    await connection.close()
