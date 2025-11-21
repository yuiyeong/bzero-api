"""pytest 공통 fixtures."""

from collections.abc import AsyncIterator

import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bzero.core.settings import Settings
from bzero.infrastructure.db.base import Base

# 모든 모델을 import하여 Base.metadata.create_all()이 모든 테이블을 생성하도록 함
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel  # noqa: F401
from bzero.infrastructure.db.user_model import UserModel  # noqa: F401


# 테스트 시작 시 .env.test 로드
load_dotenv(".env.test", override=True)


@pytest_asyncio.fixture
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """테스트 데이터베이스 엔진을 생성합니다."""
    settings = Settings()
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
