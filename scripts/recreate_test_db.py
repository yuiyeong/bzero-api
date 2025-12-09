"""테스트 DB 재생성 스크립트"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from bzero.core.settings import Environment, get_settings


async def recreate_test_db():
    # 테스트 환경 설정 강제
    import os

    os.environ["ENVIRONMENT"] = "test"

    settings = get_settings()
    if settings.environment != Environment.TEST:
        raise RuntimeError("TEST 환경에서만 실행 가능합니다")

    # postgres DB에 연결 (기본 DB)
    postgres_url = settings.database.async_url.replace("/bzero_test", "/postgres")
    engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        # 기존 연결 종료
        await conn.execute(
            text(
                """
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'bzero_test'
                AND pid <> pg_backend_pid()
            """
            )
        )

        # DB 삭제 및 재생성
        await conn.execute(text("DROP DATABASE IF EXISTS bzero_test"))
        await conn.execute(text("CREATE DATABASE bzero_test"))

    await engine.dispose()
    print("✅ 테스트 DB 재생성 완료!")


if __name__ == "__main__":
    asyncio.run(recreate_test_db())
