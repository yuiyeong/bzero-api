from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bzero.core.settings import Settings


_async_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def setup_db_connection(settings: Settings) -> None:
    """데이터베이스 연결 초기화"""
    global _async_engine, _async_session_maker

    if _async_engine is not None:
        return

    _async_engine = create_async_engine(
        settings.database.async_url,
        echo=settings.is_debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

    _async_session_maker = async_sessionmaker(
        _async_engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


async def close_db_connection() -> None:
    """데이터베이스 연결 종료"""
    global _async_engine, _async_session_maker

    if _async_engine is None:
        return

    await _async_engine.dispose()
    _async_session_maker = None
    _async_engine = None


async def get_async_db_session() -> AsyncIterator[AsyncSession]:
    """
    의존성 주입용 세션 생성

    Raises:
        RuntimeError: 데이터베이스가 초기화되지 않은 경우

    Yields:
        AsyncSession: 데이터베이스 세션
    """
    if _async_session_maker is None:
        raise RuntimeError("Database connection is not initialized. Call setup_db_connection() first.")

    async with _async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()  # 에러 시 롤백 추가
            raise
        finally:
            await session.close()
