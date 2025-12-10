from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from bzero.core.settings import Settings


_async_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


_sync_engine: Engine | None = None
_sync_session_maker: sessionmaker[Session] | None = None


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


def setup_sync_db_connection(settings: Settings) -> None:
    """동기 데이터베이스 엔진과 세션 팩토리를 초기화합니다 (Celery용)"""
    global _sync_engine, _sync_session_maker

    if _sync_engine is not None:
        return

    _sync_engine = create_engine(
        settings.database.sync_url,
        echo=settings.is_debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

    _sync_session_maker = sessionmaker(
        _sync_engine,
        class_=Session,
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


def close_sync_db_connection() -> None:
    """동기 데이터베이스 연결 종료(celery 용)"""
    global _sync_engine, _sync_session_maker

    if _sync_engine is None:
        return

    _sync_engine.dispose()

    _sync_engine = None
    _sync_session_maker = None


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


@contextmanager
def get_sync_db_session() -> Iterator[Session]:
    """동기 DB 세션을 생성합니다 (Celery용)."""
    if _sync_session_maker is None:
        raise RuntimeError("Sync database connection is not initialized. Call setup_sync_db_connection() first.")

    session = _sync_session_maker()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
